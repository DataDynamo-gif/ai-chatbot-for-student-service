import re
import os
from typing import Optional, Any
from chatbot.prompts import INTENT_CLASSIFICATION_PROMPT


def classify_intent_local(query: str) -> str:
    """
    Fast, reliable, offline-compatible keyword and regex classification engine.
    Ensures zero latency and high accuracy for standard student queries.
    """
    q = query.lower().strip()

    # Attendance
    if any(k in q for k in ["attendance", "75%", "skip tomorrow", "skip class", "absent", "present", "classes attended", "shortage"]):
        return "attendance"

    # Timetable
    if any(k in q for k in ["timetable", "schedule", "tomorrow timetable", "next lecture", "free period", "period", "room number", "room"]) or ("class" in q and "today" in q) or ("classes" in q and "today" in q) or ("class" in q and "tomorrow" in q):
        return "timetable"

    # Result
    if any(k in q for k in ["result", "sgpa", "cgpa", "marks", "grade", "backlog", "score", "semester marks"]):
        return "result"

    # Fee
    if any(k in q for k in ["fee", "dues", "pending amount", "paid amount", "receipt", "due date", "tuition", "balance"]):
        return "fee"

    # Notice
    if any(k in q for k in ["notice", "announcement", "circular", "came today", "latest notice"]):
        return "notice"

    # Placement
    if any(k in q for k in ["placement", "company", "package", "lpa", "recruitment", "drive", "eligibility", "deadline"]):
        return "placement"

    # Library
    if any(k in q for k in ["library", "book", "isbn", "fine", "renew", "author", "due book"]):
        return "library"

    # Complaint
    if any(k in q for k in ["complaint", "complain", "issue", "grief", "grievance", "report", "ragging", "misbehave", "misbehavior", "harass", "senior", "canteen food", "hostel issue"]):
        return "complaint"

    # FAQ
    if any(k in q for k in ["timing", "policy", "hostel rules", "scholarship", "rules", "exam rules", "library timing"]):
        return "faq"

    return "general_reasoning"


def classify_intent(query: str, openai_client: Optional[Any] = None) -> str:
    """
    Classifies user intent. First checks local high-confidence keywords.
    If ambiguous and OpenAI client is available, leverages LLM for deep classification.
    """
    local_intent = classify_intent_local(query)
    if local_intent != "general_reasoning":
        return local_intent

    if openai_client:
        try:
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": INTENT_CLASSIFICATION_PROMPT},
                    {"role": "user", "content": query}
                ],
                temperature=0.0,
                max_tokens=10
            )
            llm_intent = response.choices[0].message.content.strip().lower()
            valid_intents = {
                "attendance", "timetable", "result", "fee", "notice",
                "placement", "library", "complaint", "faq", "general_reasoning"
            }
            if llm_intent in valid_intents:
                return llm_intent
        except Exception as e:
            # Fall back to general reasoning
            pass

    return "general_reasoning"
