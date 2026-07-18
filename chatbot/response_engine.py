import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from database.models import ChatMessage, Student
from chatbot.intent_classifier import classify_intent
from chatbot.prompts import SYSTEM_PROMPT

# Import service queries
from services.attendance import get_student_attendance, get_subjects_below_75, check_can_skip_tomorrow
from services.timetable import get_todays_classes, get_tomorrows_classes, get_next_lecture, get_free_periods
from services.result import get_student_results, get_latest_result
from services.notices import get_notices
from services.fee import get_student_fees
from services.library import search_library_books, get_student_issued_books
from services.placement import get_placements
from services.faq import match_faq, get_all_faqs
from services.complaints import submit_complaint, get_student_complaints


class ResponseEngine:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.openai_client = None
        if self.api_key and self.api_key != "sk-your-actual-api-key-here":
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=self.api_key)
            except Exception as e:
                print(f"Notice: OpenAI client initialization failed ({e}). Running in offline SQLite mode.")

    def save_message(self, db: Session, student_id: str, role: str, content: str):
        """Saves a message to chat history."""
        msg = ChatMessage(student_id=student_id, role=role, content=content)
        db.add(msg)
        db.commit()

    def get_chat_history(self, db: Session, student_id: str) -> List[Dict[str, str]]:
        """Retrieves past chat history for a student."""
        records = db.query(ChatMessage).filter(ChatMessage.student_id == student_id).order_by(ChatMessage.id).all()
        return [{"role": rec.role, "content": rec.content, "timestamp": rec.timestamp} for rec in records]

    def clear_chat_history(self, db: Session, student_id: str):
        """Clears all previous chat history for the student."""
        db.query(ChatMessage).filter(ChatMessage.student_id == student_id).delete()
        db.commit()

    def generate_response(self, db: Session, student: Student, query: str) -> str:
        """
        Main query processing hub. Classifies intent, queries SQLite directly for structured records,
        and uses OpenAI API when synthesis or reasoning is required.
        """
        # Save user query
        self.save_message(db, student.student_id, "user", query)

        intent = classify_intent(query, self.openai_client)
        q_lower = query.lower()
        response_text = ""

        try:
            # 1. ATTENDANCE
            if intent == "attendance":
                if "below 75" in q_lower or "shortage" in q_lower or "low" in q_lower:
                    low_subjs = get_subjects_below_75(db, student.student_id)
                    if not low_subjs:
                        response_text = "🎉 Great news! None of your subjects have attendance below 75%. You are safely meeting all attendance requirements."
                    else:
                        lines = ["⚠️ **Warning! You have attendance below 75% in the following subject(s):**"]
                        for s in low_subjs:
                            lines.append(f"- **{s['subject_name']} ({s['subject_code']})**: `{s['percentage']}%` ({s['classes_attended']}/{s['total_classes']} classes attended)")
                        lines.append("\n*Please attend your upcoming lectures to avoid exam debarment.*")
                        response_text = "\n".join(lines)
                elif "skip" in q_lower or "tomorrow" in q_lower:
                    res = check_can_skip_tomorrow(db, student.student_id)
                    if res.get("can_skip"):
                        response_text = "✅ **Yes, you can skip tomorrow's lectures.** Your attendance will remain at or above 75% across all your subjects."
                    else:
                        lines = ["❌ **No, it is NOT safe to skip tomorrow's class across all subjects!** Here is what happens if you skip:"]
                        for item in res["details"]:
                            status = "🟢 Safe" if item["safe_to_skip"] else "🔴 WILL DROP BELOW 75%"
                            lines.append(f"- **{item['subject']}**: Current: `{item['current_percentage']}%` ➔ If Skipped: `{item['percentage_if_skipped']}%` ({status})")
                        response_text = "\n".join(lines)
                else:
                    att = get_student_attendance(db, student.student_id)
                    lines = [f"📊 **Attendance Summary for {student.name} ({student.roll_number}):**"]
                    for a in att:
                        icon = "🟢" if not a["below_75"] else "🔴 (Below 75%)"
                        lines.append(f"- **{a['subject_name']}**: `{a['percentage']}%` ({a['classes_attended']}/{a['total_classes']} attended) {icon}")
                    response_text = "\n".join(lines)

            # 2. TIMETABLE
            elif intent == "timetable":
                if "tomorrow" in q_lower:
                    classes = get_tomorrows_classes(db, student)
                    title = "📅 **Tomorrow's Schedule:**"
                elif "next" in q_lower:
                    next_cls = get_next_lecture(db, student)
                    if next_cls:
                        response_text = f"⏰ **Your Next Lecture:**\n- **Subject**: {next_cls['subject']} ({next_cls['subject_code']})\n- **Time**: {next_cls['start_time']} - {next_cls['end_time']}\n- **Room**: `{next_cls['room_number']}`"
                    else:
                        response_text = "🎉 You have no more scheduled lectures remaining today!"
                    self.save_message(db, student.student_id, "assistant", response_text)
                    return response_text
                elif "free" in q_lower:
                    frees = get_free_periods(db, student)
                    if frees:
                        lines = ["🛋️ **Your Free Periods Today:**"]
                        for f in frees:
                            lines.append(f"- Period {f['period_number']} ({f['start_time']} - {f['end_time']})")
                        response_text = "\n".join(lines)
                    else:
                        response_text = "📅 You have no free periods scheduled today. Packed schedule!"
                    self.save_message(db, student.student_id, "assistant", response_text)
                    return response_text
                else:
                    classes = get_todays_classes(db, student)
                    title = "📅 **Today's Class Schedule:**"

                lines = [title]
                for c in classes:
                    icon = "🛋️" if c["subject"] == "Free Period" else "📖"
                    lines.append(f"{icon} **Period {c['period_number']} ({c['start_time']} - {c['end_time']})**: {c['subject']} (`Room: {c['room_number']}`)")
                response_text = "\n".join(lines)

            # 3. RESULTS
            elif intent == "result":
                results = get_student_results(db, student.student_id)
                if not results:
                    response_text = "📭 No semester results found in your academic record yet."
                elif "cgpa" in q_lower or "sgpa" in q_lower or "latest" in q_lower or len(results) == 1:
                    latest = results[0]
                    lines = [f"🎓 **Latest Semester {latest['semester']} Result for {student.name}:**"]
                    lines.append(f"- **SGPA**: `{latest['sgpa']}` | **Overall CGPA**: `{latest['cgpa']}` | **Backlogs**: `{latest['backlogs']}`\n")
                    lines.append("**Subject-wise Marks Breakdown:**")
                    for m in latest.get("subject_marks", []):
                        lines.append(f"- {m['subject']} ({m.get('code', '-')}) : **{m['marks']} / 100** (Grade: `{m['grade']}`)")
                    response_text = "\n".join(lines)
                else:
                    lines = [f"🎓 **Overall Academic Record for {student.name}:**"]
                    for r in results:
                        lines.append(f"- **Semester {r['semester']}**: SGPA `{r['sgpa']}` | CGPA `{r['cgpa']}` | Backlogs: `{r['backlogs']}`")
                    response_text = "\n".join(lines)

            # 4. FEES
            elif intent == "fee":
                fees = get_student_fees(db, student.student_id)
                if not fees:
                    response_text = "💳 You have no fee records in the system."
                else:
                    lines = [f"💳 **Fee Status Summary for {student.name}:**"]
                    for f in fees:
                        icon = "✅" if f["pending_amount"] == 0 else "⏳"
                        lines.append(f"{icon} **Semester {f['semester']}**: Paid INR `{f['paid_amount']:,.2f}` | **Pending Dues**: INR `{f['pending_amount']:,.2f}` (`Due Date: {f['due_date']}`)")
                    lines.append("\n💡 *Tip: You can download your official fee receipt anytime from the Fees tab in the sidebar.*")
                    response_text = "\n".join(lines)

            # 5. NOTICES
            elif intent == "notice":
                notices = get_notices(db, query="" if "all" in q_lower or "latest" in q_lower else query)
                if not notices:
                    response_text = "📢 No relevant notices found matching your query on the campus notice board."
                else:
                    lines = ["📢 **Latest Campus Notices:**"]
                    for n in notices[:4]:  # Show top 4
                        lines.append(f"📌 **{n['title']}** *(Posted: {n['date_posted']} | Category: `{n['category']}`)*\n> {n['content']}\n")
                    response_text = "\n".join(lines)

            # 6. PLACEMENTS
            elif intent == "placement":
                placements = get_placements(db, query="")
                if not placements:
                    response_text = "💼 No active placement drives are currently listed."
                else:
                    lines = ["💼 **Active Campus Placement Drives:**"]
                    for p in placements:
                        lines.append(f"🏢 **{p['company']}** — *{p['role']}*\n- **Package**: `{p['package_lpa']} LPA`\n- **Eligibility**: {p['eligibility_criteria']}\n- **Deadline**: `{p['deadline']}`\n- *{p['description']}*\n")
                    response_text = "\n".join(lines)

            # 7. LIBRARY
            elif intent == "library":
                if "issued" in q_lower or "my book" in q_lower or "fine" in q_lower or "due" in q_lower:
                    issued = get_student_issued_books(db, student.student_id)
                    if not issued:
                        response_text = "📚 You currently have no books issued from the central library, and zero fines."
                    else:
                        lines = ["📚 **Books Issued to Your Account:**"]
                        for b in issued:
                            fine_str = f" | ⚠️ **Fine Due: INR {b['fine_amount']}**" if b['fine_amount'] > 0 else " | No Fine"
                            lines.append(f"- **{b['title']}** by {b['author']} (`Return Due: {b['due_date']}`{fine_str})")
                        response_text = "\n".join(lines)
                else:
                    books = search_library_books(db, query="" if "library" in q_lower else query)
                    lines = ["📚 **Central Library Catalog Sample:**"]
                    for b in books[:4]:
                        status = "🟢 Available" if b["is_available"] else f"🔴 Issued (Return: {b['due_date']})"
                        lines.append(f"- **{b['title']}** by {b['author']} (`ISBN: {b['isbn']}`) — {status}")
                    response_text = "\n".join(lines)

            # 8. FAQ & COMPLAINT
            elif intent in ["faq", "complaint"]:
                faq_match = match_faq(db, query)
                if faq_match and intent == "faq":
                    response_text = f"💡 **Campus Policy Answer ({faq_match['category']}):**\n\n**Q: {faq_match['question']}**\n> {faq_match['answer']}"
                elif intent == "complaint":
                    if any(k in q_lower for k in ["status", "my complaint", "check complaint", "list complaint", "show complaint"]):
                        my_cmps = get_student_complaints(db, student.student_id)
                        if not my_cmps:
                            response_text = "📭 You have not logged any complaints yet. You can register one directly here in chat!"
                        else:
                            lines = [f"📝 **Complaint Status for {student.name}:**"]
                            for c in my_cmps:
                                lines.append(f"- **{c['complaint_id']}** (`{c['category']}` - {c['priority']} Priority): **{c['status']}**\n  *{c['description']}*")
                            response_text = "\n".join(lines)
                    elif len(query.split()) <= 6 and any(k in q_lower for k in ["how", "where", "what"]):
                        response_text = "📝 **To register a complaint:**\nYou can tell me what happened right here in chat (e.g. *'Register urgent complaint about hostel water supply'* or *'Complain about misbehavior by seniors'*), OR you can open the **Complaint** tab from the left sidebar!"
                    else:
                        # Extract category
                        if any(w in q_lower for w in ["hostel", "room", "mess", "warden", "water", "electricity"]):
                            cat = "Hostel"
                        elif any(w in q_lower for w in ["canteen", "food", "cafeteria", "lunch", "snack"]):
                            cat = "Canteen"
                        elif any(w in q_lower for w in ["academic", "exam", "marks", "teacher", "professor", "lecture", "class", "result", "grade"]):
                            cat = "Academic"
                        elif any(w in q_lower for w in ["infra", "projector", "fan", "bench", "wifi", "internet", "lab", "computer", "cleanliness"]):
                            cat = "Infrastructure"
                        else:
                            cat = "Other"

                        # Extract priority
                        if any(w in q_lower for w in ["urgent", "emergency", "immediately", "ragging", "misbehave", "misbehavior", "harass", "harassment", "threat", "severe"]):
                            prio = "Urgent"
                        elif any(w in q_lower for w in ["high", "soon", "broken", "critical"]):
                            prio = "High"
                        else:
                            prio = "Normal"

                        # Clean up description
                        desc = query
                        for prefix in ["register a complaint about ", "register complaint about ", "register a complain about ", "register complain about ", "register a complain on behalf of me about ", "register complaint that ", "file a complaint about ", "file complaint about ", "please register complaint: ", "complain about "]:
                            if q_lower.startswith(prefix):
                                desc = query[len(prefix):].strip()
                                break
                        if not desc:
                            desc = query

                        res = submit_complaint(db, student.student_id, cat, desc, prio)
                        response_text = f"✅ **Complaint Registered Successfully!**\n\n- **Tracking ID:** `{res['complaint_id']}`\n- **Category:** `{cat}`\n- **Priority:** `{prio}`\n- **Description:** *\"{desc}\"*\n- **Status:** `Open`\n\nYour grievance has been officially filed in the college database and forwarded to the administration. You can ask me to check its status anytime!"
                else:
                    faqs = get_all_faqs(db)[:3]
                    lines = ["💡 **Here are some common questions answered:**"]
                    for f in faqs:
                        lines.append(f"- **{f['question']}**\n  *{f['answer']}*\n")
                    response_text = "\n".join(lines)

            # 9. GENERAL REASONING OR FALLBACK TO OPENAI
            else:
                if self.openai_client:
                    try:
                        # Feed basic context about the student
                        ctx = f"Student Context: Name={student.name}, Roll={student.roll_number}, Dept={student.department}, Sem={student.semester}."
                        response = self.openai_client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": f"{SYSTEM_PROMPT}\n{ctx}"},
                                {"role": "user", "content": query}
                            ],
                            temperature=0.6,
                            max_tokens=300
                        )
                        response_text = response.choices[0].message.content.strip()
                    except Exception as e:
                        response_text = f"🤖 I am currently running in offline SQLite mode (`OpenAI API not reachable`). How else can I help you with your academic records, attendance, timetable, or fees?"
                else:
                    # Check if query matches any FAQ before giving general reply
                    faq_match = match_faq(db, query)
                    if faq_match:
                        response_text = f"💡 **{faq_match['question']}**\n> {faq_match['answer']}"
                    else:
                        response_text = f"👋 Hello {student.name}! I am your AI Student Service Chatbot running in high-speed SQLite mode. You can ask me anytime about your **Attendance**, **Timetable**, **Results**, **Fees**, **Notices**, **Placements**, or **Library books**!"

        except Exception as ex:
            response_text = f"⚠️ An error occurred while fetching information (`{ex}`). Please verify your query or try navigating via the sidebar."

        # Save assistant reply
        self.save_message(db, student.student_id, "assistant", response_text)
        return response_text
