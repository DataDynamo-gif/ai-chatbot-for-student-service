import os
import io
import time
from datetime import datetime
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy.orm import Session

from database.database import get_db, SessionLocal, init_db
from database.models import Student
from auth.login import authenticate_user, create_session, validate_session, destroy_session
from chatbot.response_engine import ResponseEngine

# Service imports
from services.attendance import get_student_attendance, get_subjects_below_75, check_can_skip_tomorrow, update_attendance_record
from services.timetable import get_todays_classes, get_tomorrows_classes, get_next_lecture, get_free_periods
from services.result import get_student_results, upload_result
from services.notices import get_notices, add_notice
from services.fee import get_student_fees, generate_fee_receipt_text
from services.library import search_library_books, get_student_issued_books, renew_book_dummy
from services.placement import get_placements, add_placement
from services.complaints import submit_complaint, get_student_complaints, get_all_complaints, update_complaint_status
from services.faq import get_all_faqs


def apply_minimal_styling(dark_mode: bool = False):
    """
    Applies aesthetic, modern UI styling with high contrast readability,
    clean metric cards, subtle shadows, and responsive layouts in crisp light mode.
    """
    css = """
    <style>
    /* Modern clean light styling */
    :root, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        --text-color: #1a1a1a !important;
        --background-color: #ffffff !important;
        --secondary-background-color: #f8f9fa !important;
    }
    body, .stApp, .stApp > header, .stApp > div, [data-testid="stAppViewContainer"] {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    section[data-testid="stSidebar"], section[data-testid="stSidebar"] > div, div[data-testid="stSidebarContent"] {
        background-color: #f8f9fa !important;
        border-right: 1px solid #e9ecef !important;
    }
    /* Enforce dark text across all components, markdown blocks, lists, and tables while preserving code spans */
    body .stApp [class*="st-"]:not(code):not(pre) *, body .stApp [data-testid]:not(code):not(pre) *, body .stApp p, body .stApp span:not(code), body .stApp label, body .stApp h1, body .stApp h2, body .stApp h3, body .stApp h4, body .stApp h5, body .stApp h6, body .stApp li, body .stApp ul *, body .stApp ol *, body .stApp strong, body .stApp b, body .stApp a, body .stApp caption, body .stApp table, body .stApp th, body .stApp td, body .stApp div[data-testid="stMarkdownContainer"] *:not(code):not(pre), body .stApp div[data-testid="stChatMessage"] *:not(code):not(pre) {
        color: #1a1a1a !important;
    }
    /* Inline Code Badges in Light Mode */
    body .stApp code, body .stApp pre, body .stApp kbd, body .stApp .stMarkdown code, body .stApp p > code, body .stApp li > code, body .stApp td > code, body .stApp span > code, body .stApp div[data-testid="stMarkdownContainer"] code {
        background-color: #f1f5f9 !important;
        color: #0284c7 !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 4px !important;
        padding: 0.15rem 0.45rem !important;
        font-family: 'Consolas', 'Courier New', monospace !important;
        font-weight: 600 !important;
        display: inline-block !important;
    }
    /* Aesthetic Card Containers & Metrics */
    div[data-testid="stMetric"], div[data-testid="stContainer"][style*="border"], div[class*="stContainer"][style*="border"], div[data-testid="stExpander"] {
        background-color: #f8f9fa !important;
        border: 1px solid #e9ecef !important;
        border-radius: 10px !important;
        padding: 1rem !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03) !important;
    }
    div[data-testid="stMetricValue"] > div {
        font-weight: 700 !important;
        color: #0d6efd !important;
    }
    table, th, td {
        background-color: #ffffff !important;
        border-color: #dee2e6 !important;
    }
    /* Primary Buttons */
    body .stApp div.stButton > button, body .stApp div.stDownloadButton > button, body .stApp div.stFormSubmitButton > button,
    body .stApp div[data-testid="stButton"] > button, body .stApp div[data-testid="stDownloadButton"] > button, body .stApp div[data-testid="stFormSubmitButton"] > button,
    body .stApp button[data-testid="stBaseButton-secondary"], body .stApp button[data-testid="stBaseButton-primary"] {
        background: linear-gradient(135deg, #0d6efd 0%, #0a58ca 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0.5rem 1.25rem !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 4px rgba(13, 110, 253, 0.2) !important;
    }
    body .stApp div.stButton > button *, body .stApp div.stDownloadButton > button *, body .stApp div.stFormSubmitButton > button *,
    body .stApp div[data-testid="stButton"] > button *, body .stApp div[data-testid="stDownloadButton"] > button *, body .stApp div[data-testid="stFormSubmitButton"] > button *,
    body .stApp button[data-testid="stBaseButton-secondary"] *, body .stApp button[data-testid="stBaseButton-primary"] * {
        color: #ffffff !important;
        fill: #ffffff !important;
    }
    body .stApp div.stButton > button:hover, body .stApp div.stDownloadButton > button:hover, body .stApp div.stFormSubmitButton > button:hover,
    body .stApp button[data-testid="stBaseButton-secondary"]:hover, body .stApp button[data-testid="stBaseButton-primary"]:hover {
        background: linear-gradient(135deg, #3b82f6 0%, #0d6efd 100%) !important;
        box-shadow: 0 4px 10px rgba(13, 110, 253, 0.35) !important;
    }
    /* Bottom Chat Input Container in Light Mode */
    section[data-testid="stBottom"], div[data-testid="stBottomBlockContainer"], div[class*="stBottom"], div[data-testid="stChatInputContainer"] {
        background-color: #ffffff !important;
        border-top: 1px solid #e9ecef !important;
    }
    div[data-testid="stChatInput"] {
        background-color: #f8f9fa !important;
        border: 1px solid #dee2e6 !important;
        border-radius: 12px !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05) !important;
    }
    /* Chat Message Bubbles */
    div[data-testid="stChatMessage"] {
        background-color: #f8f9fa !important;
        border: 1px solid #e9ecef !important;
        border-radius: 12px !important;
        padding: 1rem 1.25rem !important;
        margin-bottom: 0.85rem !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03) !important;
    }
    div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
        background: linear-gradient(135deg, #eff6ff 0%, #f8f9fa 100%) !important;
        border-color: #bfdbfe !important;
    }
    div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
        background-color: #ffffff !important;
        border-color: #e9ecef !important;
    }
    /* Attendance Alerts & Status Badges */
    body .stApp .low-attendance, body .stApp .low-attendance *, body .stApp div[class*="low-attendance"] * {
        background-color: #ffe6e6 !important;
        color: #b30000 !important;
        padding: 0.85rem 1rem;
        border-left: 5px solid #cc0000;
        border-radius: 6px;
        margin-bottom: 1rem;
        font-weight: 500;
    }
    body .stApp .safe-attendance, body .stApp .safe-attendance *, body .stApp div[class*="safe-attendance"] * {
        background-color: #e6f7eb !important;
        color: #006622 !important;
        padding: 0.85rem 1rem;
        border-left: 5px solid #009933;
        border-radius: 6px;
        margin-bottom: 1rem;
        font-weight: 500;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def generate_pdf_export(chat_history: list, student_name: str, student_id: str) -> bytes:
    """
    Generates a PDF document of the chat history using ReportLab.
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#0d6efd'))
        meta_style = ParagraphStyle('MetaStyle', parent=styles['Normal'], fontSize=10, textColor=colors.gray)
        user_style = ParagraphStyle('UserStyle', parent=styles['Normal'], fontSize=11, fontName='Helvetica-Bold', textColor=colors.HexColor('#1a1a1a'))
        bot_style = ParagraphStyle('BotStyle', parent=styles['Normal'], fontSize=10, fontName='Helvetica', textColor=colors.HexColor('#333333'), leftIndent=15)

        story.append(Paragraph("Student Service Chatbot — Conversation Transcript", title_style))
        story.append(Paragraph(f"Student: {student_name} ({student_id}) | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", meta_style))
        story.append(Spacer(1, 15))

        for msg in chat_history:
            role = "You" if msg["role"] == "user" else "Assistant"
            style = user_style if msg["role"] == "user" else bot_style
            content_clean = msg["content"].replace("\n", "<br/>")
            story.append(Paragraph(f"<b>{role}:</b> {content_clean}", style))
            story.append(Spacer(1, 10))

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as e:
        # Fallback if reportlab encounters formatting issue
        return f"Error generating PDF: {e}".encode()


def generate_txt_export(chat_history: list, student_name: str, student_id: str) -> str:
    """
    Generates a plain text representation of the chat history.
    """
    lines = [
        "=================================================",
        " STUDENT SERVICE CHATBOT — CHAT TRANSCRIPT",
        "=================================================",
        f"Student: {student_name} ({student_id})",
        f"Exported on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=================================================\n"
    ]
    for msg in chat_history:
        role = "Student" if msg["role"] == "user" else "Chatbot"
        lines.append(f"[{msg.get('timestamp', '')}] {role}:")
        lines.append(f"{msg['content']}\n")
        lines.append("-" * 40)
    return "\n".join(lines)


def render_login_page(db: Session):
    """
    Renders the clean, minimal login screen.
    """
    st.title("🎓 College Student Portal & Chatbot")
    st.write("Welcome! Please log in using your Student ID and Password to access your academic records and AI chatbot.")

    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("Login Credentials")
        with st.form("login_form", clear_on_submit=False):
            student_id_input = st.text_input("Student ID", placeholder="e.g. S101 or admin")
            password_input = st.text_input("Password", type="password", placeholder="Enter password")
            submit_btn = st.form_submit_button("Sign In")

            if submit_btn:
                if not student_id_input or not password_input:
                    st.error("Please enter both Student ID and Password.")
                else:
                    user_profile = authenticate_user(db, student_id_input, password_input)
                    if user_profile:
                        st.session_state["user"] = user_profile
                        st.session_state["db_student"] = db.query(Student).filter_by(student_id=user_profile["student_id"]).first()
                        token = create_session(user_profile)
                        st.session_state["session_token"] = token
                        st.query_params["session"] = token
                        st.success("Login successful!")
                        st.components.v1.html(
                            f"""<script>
                            try {{ window.parent.sessionStorage.setItem("chatbot_session_token", "{token}"); }} catch(e) {{}}
                            </script>""",
                            height=0,
                            width=0
                        )
                        st.rerun()
                    else:
                        st.error("Invalid Student ID or Password. Please try again.")

    with col2:
        st.info("""
        **Demo Account Credentials:**
        - **Student 1:** `S101` / `password123` (Aarav Sharma — Computer Science Sem 6)
        - **Student 2:** `S102` / `password123` (Diya Patel — Computer Science Sem 6)
        - **Admin Access:** `admin` / `admin123` (System Administrator Mode)
        """)


def render_sidebar(user: dict) -> str:
    """
    Renders the responsive sidebar navigation and profile details.
    """
    with st.sidebar:
        st.header("👤 Student Profile")
        st.write(f"**Name:** {user['name']}")
        st.write(f"**ID:** `{user['student_id']}` | **Roll:** `{user['roll_number']}`")
        if not user.get("is_admin"):
            st.write(f"**Dept:** {user['department']}")
            st.write(f"**Semester:** {user['semester']} | **Section:** {user['section']}")
            st.write(f"**Email:** {user['email']}")
            st.write(f"**Phone:** {user['phone']}")
        else:
            st.markdown("🛠️ **Administrator Privileges Active**")

        st.divider()

        # Navigation Options
        st.subheader("📌 Navigation")
        options = [
            "💬 AI Chatbot",
            "📊 Attendance",
            "📅 Timetable",
            "🎓 Results",
            "💳 Fees",
            "📢 Notices",
            "💼 Placements",
            "📚 Library",
            "📝 Complaint",
            "❓ FAQ"
        ]
        if user.get("is_admin"):
            options.append("⚙️ Admin Mode")

        selected = st.radio("Select Module:", options, index=0)

        st.divider()
        st.subheader("⚙️ Settings & Actions")
        if st.button("🚪 Logout", use_container_width=True):
            token = st.session_state.get("session_token")
            if token:
                destroy_session(token)
            st.query_params.clear()
            st.session_state.clear()
            st.components.v1.html(
                """<script>
                try { window.parent.sessionStorage.removeItem("chatbot_session_token"); } catch(e) {}
                </script>""",
                height=0,
                width=0
            )
            st.rerun()

        return selected


def render_chatbot_view(db: Session, student: Student, user: dict):
    """
    Renders the main AI Chatbot interface with minimal white background,
    typing indicator, clear history, search previous chats, and export features.
    """
    st.header("💬 AI Student Service Chatbot")
    st.write("Ask anything about your attendance, schedule, results, fees, notices, or general academic guidelines.")

    if "response_engine" not in st.session_state:
        st.session_state["response_engine"] = ResponseEngine()
    engine = st.session_state["response_engine"]

    # Top control bar
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        search_q = st.text_input("🔍 Search Previous Chats", placeholder="Filter history by keyword...")
    with col2:
        st.write("")
        st.write("")
        if st.button("🧹 Clear History"):
            engine.clear_chat_history(db, student.student_id)
            st.success("Chat history cleared!")
            st.rerun()

    # Load history
    history = engine.get_chat_history(db, student.student_id)
    filtered_history = history
    if search_q.strip():
        filtered_history = [m for m in history if search_q.lower() in m["content"].lower()]

    with col3:
        st.write("")
        st.write("")
        if history:
            txt_data = generate_txt_export(history, user["name"], user["student_id"])
            st.download_button("📥 Export TXT", data=txt_data, file_name=f"chat_history_{user['student_id']}.txt", mime="text/plain")
    with col4:
        st.write("")
        st.write("")
        if history:
            pdf_data = generate_pdf_export(history, user["name"], user["student_id"])
            st.download_button("📄 Export PDF", data=pdf_data, file_name=f"chat_history_{user['student_id']}.pdf", mime="application/pdf")

    st.divider()

    # Display chat window
    chat_container = st.container(height=430, border=True)
    with chat_container:
        if not filtered_history:
            st.info("No messages to display. Start chatting below!")
        else:
            for msg in filtered_history:
                avatar = "🧑‍🎓" if msg["role"] == "user" else "🤖"
                with st.chat_message(msg["role"], avatar=avatar):
                    st.markdown(msg["content"])
                    st.caption(f"🕒 {msg.get('timestamp', '')}")

    # One chat input box at the bottom
    user_query = st.chat_input("Ask a question (e.g. 'What is my attendance?' or 'Show today's timetable')...")
    if user_query:
        # Show immediate user message
        with chat_container:
            with st.chat_message("user", avatar="🧑‍🎓"):
                st.markdown(user_query)

            # Show typing indicator / loading spinner
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("Analyzing academic records..."):
                    time.sleep(0.3)  # Brief natural delay for UX
                    bot_reply = engine.generate_response(db, student, user_query)
                    st.markdown(bot_reply)
        st.rerun()


def render_attendance_view(db: Session, user: dict):
    st.header("📊 Attendance Tracking Dashboard")
    st.write("Monitor your attendance metrics, subject-wise trends, and evaluate risk factors across all courses.")

    att_records = get_student_attendance(db, user["student_id"])
    if not att_records:
        st.warning("No attendance records found.")
        return

    # Calculate summary metrics
    total_attended = sum(r["classes_attended"] for r in att_records)
    total_classes = sum(r["total_classes"] for r in att_records)
    overall_pct = round((total_attended / total_classes) * 100, 1) if total_classes > 0 else 0
    below_75 = get_subjects_below_75(db, user["student_id"])

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Attended / Classes", f"{total_attended} / {total_classes}", f"{total_attended - (int(total_classes * 0.75))} vs 75% target")
    col2.metric("Overall Attendance", f"{overall_pct}%", f"{round(overall_pct - 75.0, 1)}% margin")
    col3.metric("Subjects Below 75%", f"{len(below_75)} Subject(s)", "Immediate Action Required" if below_75 else "All Safe", delta_color="inverse" if below_75 else "normal")

    if below_75:
        st.markdown(f'<div class="low-attendance">⚠️ <b>Attendance Shortage Warning!</b> You have <b>{len(below_75)}</b> subject(s) below 75%. Please attend upcoming lectures.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="safe-attendance">✅ <b>Safe Attendance!</b> All your enrolled subjects meet the mandatory 75% attendance threshold.</div>', unsafe_allow_html=True)

    # Plotly Visualizations
    st.subheader("📈 Subject-Wise Attendance Visualizer")
    df_att = pd.DataFrame(att_records)
    df_att["Status"] = df_att["below_75"].apply(lambda x: "At Risk (< 75%)" if x else "Safe (≥ 75%)")
    df_att["Color"] = df_att["below_75"].apply(lambda x: "#ef4444" if x else "#22c55e")

    col_chart1, col_chart2 = st.columns([2, 1])
    with col_chart1:
        fig_bar = px.bar(
            df_att,
            x="subject_code",
            y="percentage",
            color="Status",
            color_discrete_map={"Safe (≥ 75%)": "#22c55e", "At Risk (< 75%)": "#ef4444"},
            hover_data=["subject_name", "classes_attended", "total_classes"],
            title="Attendance Percentage per Subject vs 75% Threshold",
            labels={"subject_code": "Subject Code", "percentage": "Attendance (%)"}
        )
        fig_bar.add_hline(y=75, line_dash="dash", line_color="#ff4d4d", annotation_text="Mandatory 75% Goal")
        fig_bar.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color=st.session_state.get("dark_mode") and "#f0f0f0" or "#1a1a1a"),
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_chart2:
        df_pie = pd.DataFrame({
            "Category": ["Classes Attended", "Classes Missed"],
            "Count": [total_attended, total_classes - total_attended]
        })
        fig_donut = px.pie(
            df_pie,
            names="Category",
            values="Count",
            hole=0.55,
            color="Category",
            color_discrete_map={"Classes Attended": "#3b82f6", "Classes Missed": "#f97316"},
            title="Overall Semester Breakdown"
        )
        fig_donut.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color=st.session_state.get("dark_mode") and "#f0f0f0" or "#1a1a1a"),
            margin=dict(l=10, r=10, t=40, b=10)
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    # Table view
    st.subheader("Detailed Records Table")
    table_data = []
    for r in att_records:
        status_flag = "🔴 Below 75%" if r["below_75"] else "🟢 Safe"
        table_data.append({
            "Subject Code": r["subject_code"],
            "Subject Name": r["subject_name"],
            "Classes Attended": r["classes_attended"],
            "Total Classes": r["total_classes"],
            "Percentage (%)": f"{r['percentage']}%",
            "Status": status_flag
        })
    st.table(table_data)

    # "Can I skip tomorrow?" tool
    st.divider()
    st.subheader("🚀 'Can I Skip Tomorrow?' Calculator")
    st.write("Select a subject or check your overall eligibility if you take a day off tomorrow.")
    
    subj_names = ["All Subjects"] + [r["subject_name"] for r in att_records]
    selected_subj = st.selectbox("Select Subject to check:", subj_names)
    if st.button("Evaluate Skipping Risk"):
        query_subj = None if selected_subj == "All Subjects" else selected_subj
        res = check_can_skip_tomorrow(db, user["student_id"], query_subj)
        if res.get("can_skip"):
            st.success("✅ Yes! You can safely skip tomorrow. Your attendance will remain at or above 75%.")
        else:
            st.error("❌ No! Skipping tomorrow will cause one or more subjects to fall below the mandatory 75% limit.")
            for d in res["details"]:
                if not d["safe_to_skip"]:
                    st.write(f"- **{d['subject']}** will drop from `{d['current_percentage']}%` to `{d['percentage_if_skipped']}%`.")


def render_timetable_view(db: Session, db_student: Student):
    st.header("📅 Timetable & Schedule Dashboard")
    st.write("View your daily class schedules, upcoming lectures, and free slots across the academic week.")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Today's Classes", "Tomorrow's Schedule", "Next Lecture", "Free Periods"])
    with tab1:
        classes = get_todays_classes(db, db_student)
        if not classes:
            st.info("No classes scheduled for today.")
        else:
            for cls in classes:
                with st.container(border=True):
                    c1, c2, c3 = st.columns([2, 3, 2])
                    c1.write(f"⏰ **{cls['start_time']} - {cls['end_time']}**")
                    c2.write(f"📘 **{cls['subject']}** (`{cls['subject_code']}`)")
                    c3.write(f"🏢 Room: `{cls['room_number']}`<br/>🧑‍🏫 {cls['instructor']}", unsafe_allow_html=True)
    with tab2:
        t_classes = get_tomorrows_classes(db, db_student)
        if not t_classes:
            st.info("No classes scheduled for tomorrow.")
        else:
            for cls in t_classes:
                with st.container(border=True):
                    c1, c2, c3 = st.columns([2, 3, 2])
                    c1.write(f"⏰ **{cls['start_time']} - {cls['end_time']}**")
                    c2.write(f"📘 **{cls['subject']}** (`{cls['subject_code']}`)")
                    c3.write(f"🏢 Room: `{cls['room_number']}`<br/>🧑‍🏫 {cls['instructor']}", unsafe_allow_html=True)
    with tab3:
        nxt = get_next_lecture(db, db_student)
        if nxt:
            with st.container(border=True):
                st.subheader("⚡ Next Upcoming Lecture")
                c1, c2, c3 = st.columns([2, 3, 2])
                c1.write(f"⏰ **{nxt['start_time']} - {nxt['end_time']}**")
                c2.write(f"📘 **{nxt['subject']}** (`{nxt['subject_code']}`)")
                c3.write(f"🏢 Room: `{nxt['room_number']}`<br/>🧑‍🏫 {nxt['instructor']}", unsafe_allow_html=True)
        else:
            st.info("You have no more remaining lectures today.")
    with tab4:
        frees = get_free_periods(db, db_student)
        if frees:
            for fp in frees:
                with st.container(border=True):
                    st.write(f"🟢 **Free Period ({fp['day']})**: `{fp['start_time']} - {fp['end_time']}`")
        else:
            st.info("No free periods today.")


def render_results_view(db: Session, user: dict):
    st.header("🎓 Academic Results & GPA Visualizer")
    results = get_student_results(db, user["student_id"])
    if not results:
        st.warning("No results uploaded.")
        return

    results_sorted = sorted(results, key=lambda x: x["semester"])
    latest_res = results_sorted[-1]
    total_backlogs = sum(r.get("backlogs", 0) for r in results_sorted)

    col1, col2, col3 = st.columns(3)
    col1.metric("Current CGPA", f"{latest_res['cgpa']} / 10.0", "Top Tier Performance" if float(latest_res['cgpa']) >= 8.5 else "Good Standing")
    col2.metric("Latest Semester SGPA", f"{latest_res['sgpa']} / 10.0", f"Semester {latest_res['semester']}")
    col3.metric("Total Active Backlogs", f"{total_backlogs}", "All Cleared ✅" if total_backlogs == 0 else "Needs Clearance ⚠️", delta_color="inverse" if total_backlogs > 0 else "normal")

    st.subheader("📈 SGPA vs CGPA Semester Trend")
    df_trend = pd.DataFrame({
        "Semester": [f"Sem {r['semester']}" for r in results_sorted],
        "SGPA": [float(r["sgpa"]) for r in results_sorted],
        "CGPA": [float(r["cgpa"]) for r in results_sorted]
    })
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(x=df_trend["Semester"], y=df_trend["SGPA"], mode="lines+markers", name="SGPA (Semester)", line=dict(color="#3b82f6", width=3), marker=dict(size=8)))
    fig_trend.add_trace(go.Scatter(x=df_trend["Semester"], y=df_trend["CGPA"], mode="lines+markers", name="CGPA (Cumulative)", line=dict(color="#10b981", width=3, dash="dot"), marker=dict(size=8)))
    fig_trend.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=st.session_state.get("dark_mode") and "#f0f0f0" or "#1a1a1a"),
        yaxis=dict(range=[0, 10.0], title="Grade Points (out of 10)"),
        xaxis=dict(title="Academic Semester"),
        margin=dict(l=20, r=20, t=30, b=20)
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    st.subheader("📊 Subject Marks Performance")
    sem_options = [f"Semester {r['semester']}" for r in results_sorted]
    selected_sem_str = st.selectbox("Select Semester for Detailed Breakdown:", sem_options, index=len(sem_options)-1)
    selected_sem_num = int(selected_sem_str.split(" ")[1])
    selected_res = next(r for r in results_sorted if r["semester"] == selected_sem_num)

    if selected_res["subject_marks"]:
        df_marks = pd.DataFrame(selected_res["subject_marks"])
        # Ensure numerical marks
        df_marks["obtained"] = pd.to_numeric(df_marks["marks_obtained"], errors="coerce").fillna(0)
        df_marks["total"] = pd.to_numeric(df_marks["total_marks"], errors="coerce").fillna(100)

        fig_bar = px.bar(
            df_marks,
            x="subject",
            y=["obtained", "total"],
            barmode="group",
            color_discrete_map={"obtained": "#0d6efd", "total": "#cbd5e1"},
            title=f"Marks Obtained vs Total Marks ({selected_sem_str})",
            labels={"value": "Marks", "subject": "Subject Name", "variable": "Score Type"}
        )
        fig_bar.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color=st.session_state.get("dark_mode") and "#f0f0f0" or "#1a1a1a"),
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    for res in results:
        with st.expander(f"Detailed Report: Semester {res['semester']} (SGPA: {res['sgpa']} | CGPA: {res['cgpa']} | Backlogs: {res['backlogs']})", expanded=False):
            if res["subject_marks"]:
                st.table(res["subject_marks"])


def render_fees_view(db: Session, user: dict):
    st.header("💳 Fee & Billing Dashboard")
    st.write("Track semester invoices, pending balance, and generate official payment receipts.")
    fees = get_student_fees(db, user["student_id"])
    if not fees:
        st.info("No fee records found.")
        return

    total_paid = sum(f["paid_amount"] for f in fees)
    total_pending = sum(f["pending_amount"] for f in fees)
    total_fee = total_paid + total_pending

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Course Fee", f"₹ {total_fee:,.2f}")
    col2.metric("Total Paid Amount", f"₹ {total_paid:,.2f}", f"{round((total_paid/total_fee)*100 if total_fee else 0, 1)}% cleared")
    col3.metric("Pending Balance", f"₹ {total_pending:,.2f}", "Fully Cleared ✅" if total_pending == 0 else "Due Soon ⚠️", delta_color="inverse" if total_pending > 0 else "normal")

    st.subheader("🥧 Fee Breakdown Overview")
    col_donut, col_list = st.columns([1, 2])
    with col_donut:
        df_fee_pie = pd.DataFrame({
            "Status": ["Paid Amount", "Pending Balance"],
            "Amount": [total_paid, total_pending]
        })
        fig_pie = px.pie(
            df_fee_pie,
            names="Status",
            values="Amount",
            hole=0.5,
            color="Status",
            color_discrete_map={"Paid Amount": "#10b981", "Pending Balance": "#ef4444"},
            title="Overall Payment Status"
        )
        fig_pie.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color=st.session_state.get("dark_mode") and "#f0f0f0" or "#1a1a1a"),
            margin=dict(l=10, r=10, t=40, b=10)
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_list:
        st.write("### Semester Invoices")
        for f in fees:
            status_badge = "🟢 Paid" if f["status"].lower() == "paid" else "🔴 Pending"
            with st.container(border=True):
                c1, c2, c3 = st.columns([2, 2, 2])
                c1.write(f"**Semester {f['semester']} Fee**<br/>Status: `{status_badge}`", unsafe_allow_html=True)
                c2.write(f"**Paid:** `₹ {f['paid_amount']:,.2f}`<br/>**Pending:** `₹ {f['pending_amount']:,.2f}`", unsafe_allow_html=True)
                c3.write(f"**Due Date:** `{f['due_date']}`<br/>**Receipt:** #{f['receipt_number']}", unsafe_allow_html=True)

                receipt_txt = generate_fee_receipt_text(f, user["name"], user["student_id"])
                st.download_button(
                    label=f"📥 Download Receipt ({f['receipt_number']})",
                    data=receipt_txt,
                    file_name=f"fee_receipt_{user['student_id']}_Sem{f['semester']}.txt",
                    mime="text/plain",
                    use_container_width=True
                )


def render_notices_view(db: Session):
    st.header("📢 Campus Notice Board")
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input("🔍 Search Notices by keyword:", placeholder="e.g. exam, symposium, curfew...")
    with col2:
        category_filter = st.selectbox("Category:", ["All", "Academic", "Exam", "Event", "General"])

    notices = get_notices(db, query=search_term, category=category_filter)
    if not notices:
        st.info("No notices found matching criteria.")
    else:
        for n in notices:
            with st.container(border=True):
                st.subheader(n["title"])
                st.caption(f"🗓️ Posted on: {n['date_posted']} | 🏷️ Category: `{n['category']}`")
                st.write(n["content"])


def render_placements_view(db: Session):
    st.header("💼 Campus Placements & Salary Analytics")
    st.write("Explore top recruiting companies, compare salary packages (LPA), and track application deadlines.")
    
    all_drives = get_placements(db, query="", min_package=0.0)
    if all_drives:
        avg_pkg = round(sum(d["package_lpa"] for d in all_drives) / len(all_drives), 1)
        max_pkg = max(d["package_lpa"] for d in all_drives)
        col1, col2, col3 = st.columns(3)
        col1.metric("Active Placement Drives", f"{len(all_drives)} Companies")
        col2.metric("Highest Package Offered", f"{max_pkg} LPA", "Top CTC")
        col3.metric("Average Campus Package", f"{avg_pkg} LPA", "Above Industry Average")

        st.subheader("📊 Top Salary Packages by Company (LPA)")
        df_pkg = pd.DataFrame(all_drives)
        df_pkg = df_pkg.sort_values(by="package_lpa", ascending=True)
        fig_bar = px.bar(
            df_pkg,
            x="package_lpa",
            y="company",
            orientation="h",
            color="package_lpa",
            color_continuous_scale="Blues" if not st.session_state.get("dark_mode") else "Teal",
            hover_data=["role", "deadline"],
            title="Compensation Comparison (Cost to Company in LPA)",
            labels={"package_lpa": "Package (LPA)", "company": "Recruiting Company"}
        )
        fig_bar.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color=st.session_state.get("dark_mode") and "#f0f0f0" or "#1a1a1a"),
            margin=dict(l=20, r=20, t=40, b=20),
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("🔍 Filter & Search Placement Opportunities")
    col1, col2 = st.columns([2, 1])
    with col1:
        q = st.text_input("Search company or role:", placeholder="e.g. Google, Python, Backend...")
    with col2:
        min_pkg = st.number_input("Minimum Package (LPA):", min_value=0.0, max_value=100.0, step=2.0, value=0.0)

    drives = get_placements(db, query=q, min_package=min_pkg)
    if not drives:
        st.info("No placement drives matching your criteria.")
    else:
        for d in drives:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                c1.subheader(f"🏢 {d['company']} — {d['role']}")
                c2.metric("Offered CTC", f"{d['package_lpa']} LPA")
                
                col_a, col_b = st.columns(2)
                col_a.write(f"📌 **Application Deadline:** `{d['deadline']}`")
                col_b.write(f"🎯 **Eligibility:** `{d['eligibility_criteria']}`")
                if d["description"]:
                    st.write(f"📝 **Job Description:** {d['description']}")


def render_library_view(db: Session, user: dict):
    st.header("📚 Central Library & Catalog Portal")
    st.write("Search campus digital catalog, manage your borrowed books, and track due dates.")

    issued = get_student_issued_books(db, user["student_id"])
    total_fines = sum(b.get("fine_amount", 0) for b in issued) if issued else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Books Currently Issued", f"{len(issued) if issued else 0} Book(s)")
    col2.metric("Pending Fines", f"₹ {total_fines:,.2f}", "Zero Due ✅" if total_fines == 0 else "Fine Accrued ⚠️", delta_color="inverse" if total_fines > 0 else "normal")
    col3.metric("Library Account Status", "Active & Valid 🟢")

    tab1, tab2 = st.tabs(["Search Books Catalog", "My Borrowed Books & Renewals"])
    
    with tab1:
        q = st.text_input("🔍 Search catalog by Title, Author, or ISBN:", placeholder="e.g. Clean Code, Cormen, Database...")
        books = search_library_books(db, query=q)
        if books:
            for bk in books:
                with st.container(border=True):
                    c1, c2 = st.columns([4, 1])
                    c1.write(f"📘 **{bk['title']}**<br/>By *{bk['author']}* | Category: `{bk.get('category', 'General')}` | ISBN: `{bk.get('isbn', 'N/A')}`", unsafe_allow_html=True)
                    avail = bk.get('available_copies', 1)
                    c2.metric("Available", f"{avail} copies")
        else:
            st.info("No books matched your query.")

    with tab2:
        if not issued:
            st.success("You have no books currently issued and zero pending fines.")
        else:
            for b in issued:
                with st.container(border=True):
                    col1, col2, col3 = st.columns([3, 2, 2])
                    col1.write(f"📘 **{b['title']}**<br/>Author: *{b['author']}*", unsafe_allow_html=True)
                    col2.write(f"📅 **Issued:** `{b['issue_date']}`<br/>⏳ **Due Date:** `{b['due_date']}`", unsafe_allow_html=True)
                    col3.metric("Fine Accrued", f"₹ {b['fine_amount']}")
                    if st.button(f"🔄 Renew Book #{b['id']}", key=f"renew_{b['id']}"):
                        res = renew_book_dummy(db, b["id"], user["student_id"])
                        if res["status"] == "success":
                            st.success(res["message"])
                        else:
                            st.warning(res["message"])
                        st.rerun()


def render_complaints_view(db: Session, user: dict):
    st.header("📝 Student Complaint & Grievance Portal")
    tab1, tab2 = st.tabs(["Register New Complaint", "My Complaint Status"])
    
    with tab1:
        with st.form("complaint_form", clear_on_submit=True):
            category = st.selectbox("Category:", ["Academic", "Hostel", "Canteen", "Infrastructure", "Other"])
            priority = st.selectbox("Priority:", ["Normal", "Low", "High", "Urgent"])
            desc = st.text_area("Detailed Description:", placeholder="Describe the issue clearly...")
            if st.form_submit_button("Submit Complaint"):
                if not desc.strip():
                    st.error("Please provide a description.")
                else:
                    res = submit_complaint(db, user["student_id"], category, desc, priority)
                    st.success(res["message"])
                    st.rerun()

    with tab2:
        my_cmps = get_student_complaints(db, user["student_id"])
        if not my_cmps:
            st.info("You have not submitted any complaints.")
        else:
            st.table(my_cmps)


def render_faq_view(db: Session):
    st.header("❓ Frequently Asked Questions (FAQ)")
    faqs = get_all_faqs(db)
    for f in faqs:
        with st.expander(f"📌 {f['question']} (Category: {f['category']})"):
            st.write(f.get("answer", ""))


def render_admin_mode(db: Session):
    """
    Renders the hidden Admin Dashboard allowing database modification across modules.
    """
    st.header("⚙️ Admin Management Dashboard")
    st.write("Modify campus records, upload semester results, post notices, or resolve student complaints.")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Edit Attendance", "Upload Result", "Post Notice", "Add Placement", "Manage Complaints"
    ])

    with tab1:
        st.subheader("Update Student Attendance")
        with st.form("admin_att_form"):
            s_id = st.text_input("Student ID (e.g. S101):")
            sub_id = st.number_input("Subject ID (1=DBMS, 2=AI, 3=CN, 4=OS, 5=Cloud):", min_value=1, max_value=100, value=1)
            attended = st.number_input("Classes Attended:", min_value=0, max_value=200, value=30)
            total = st.number_input("Total Classes:", min_value=1, max_value=200, value=40)
            if st.form_submit_button("Save Attendance"):
                update_attendance_record(db, s_id.strip(), sub_id, attended, total)
                st.success(f"Attendance updated for student {s_id} in Subject ID {sub_id}!")

    with tab2:
        st.subheader("Upload Student Semester Result")
        with st.form("admin_res_form"):
            s_id = st.text_input("Student ID (e.g. S101):", key="res_s_id")
            sem = st.number_input("Semester:", min_value=1, max_value=8, value=6)
            sgpa = st.number_input("SGPA:", min_value=0.0, max_value=10.0, value=8.5)
            cgpa = st.number_input("CGPA:", min_value=0.0, max_value=10.0, value=8.2)
            backlogs = st.number_input("Backlogs:", min_value=0, max_value=10, value=0)
            marks_example = '[{"subject": "DBMS", "code": "CS601", "marks": 88, "grade": "A"}]'
            marks_raw = st.text_area("Subject Marks JSON:", value=marks_example)
            if st.form_submit_button("Upload Result"):
                import json
                try:
                    m_data = json.loads(marks_raw)
                    upload_result(db, s_id.strip(), sem, sgpa, cgpa, backlogs, m_data)
                    st.success(f"Result uploaded successfully for {s_id}!")
                except Exception as e:
                    st.error(f"Invalid JSON data: {e}")

    with tab3:
        st.subheader("Post New Campus Notice")
        with st.form("admin_not_form", clear_on_submit=True):
            n_title = st.text_input("Notice Title:")
            n_cat = st.selectbox("Category:", ["Academic", "Exam", "Event", "General"])
            n_content = st.text_area("Notice Content:")
            if st.form_submit_button("Publish Notice"):
                if not n_title or not n_content:
                    st.error("Title and Content required.")
                else:
                    add_notice(db, n_title, n_content, n_cat)
                    st.success("Notice published successfully!")

    with tab4:
        st.subheader("Add New Placement Drive")
        with st.form("admin_place_form", clear_on_submit=True):
            p_comp = st.text_input("Company Name:")
            p_role = st.text_input("Role Title:")
            p_pkg = st.number_input("Package (LPA):", min_value=1.0, max_value=150.0, value=12.0)
            p_elig = st.text_input("Eligibility Criteria:", value="CGPA >= 7.0, No backlogs")
            p_dead = st.text_input("Application Deadline:", value="2026-08-30")
            p_desc = st.text_area("Job Description:")
            if st.form_submit_button("Add Placement Drive"):
                add_placement(db, p_comp, p_role, p_pkg, p_elig, p_dead, p_desc)
                st.success("Placement drive added to portal!")

    with tab5:
        st.subheader("Review & Resolve Student Complaints")
        all_cmps = get_all_complaints(db)
        if not all_cmps:
            st.info("No complaints submitted across the college.")
        else:
            st.table(all_cmps)
            for c in all_cmps:
                col1, col2 = st.columns([3, 1])
                col1.write(f"**{c['complaint_id']}** by {c['student_name']} (`Status: {c['status']}`)")
                new_st = col2.selectbox("Set Status:", ["Open", "In Progress", "Resolved"], key=f"st_{c['complaint_id']}", index=["Open", "In Progress", "Resolved"].index(c["status"]))
                if new_st != c["status"]:
                    update_complaint_status(db, c["complaint_id"], new_st)
                    st.success(f"Status updated for {c['complaint_id']}!")
                    st.rerun()


def run_interface():
    """
    Main UI entrypoint managing session state and module rendering.
    """
    st.set_page_config(page_title="College Student Service Chatbot", page_icon="🎓", layout="wide")

    # Initialize database if needed
    init_db()
    db = next(get_db())

    # Ensure session state variables exist
    if "dark_mode" not in st.session_state:
        st.session_state["dark_mode"] = False
    if "user" not in st.session_state:
        st.session_state["user"] = None

    apply_minimal_styling(st.session_state["dark_mode"])

    # Check query params for existing session token across page refresh (F5)
    url_token = st.query_params.get("session")
    if not st.session_state["user"] and url_token:
        # Check browser sessionStorage to verify F5 refresh vs tab close restoration
        if not st.session_state.get("sessionStorage_checked"):
            st.session_state["sessionStorage_checked"] = True
            st.components.v1.html(
                f"""<script>
                try {{
                    const stored = window.parent.sessionStorage.getItem("chatbot_session_token");
                    const urlParam = "{url_token}";
                    if (!stored || stored !== urlParam) {{
                        // Tab was closed and reopened, so sessionStorage is empty! Clear query param and redirect to login
                        const url = new URL(window.parent.location);
                        url.searchParams.delete("session");
                        window.parent.location.href = url.toString();
                    }}
                }} catch(e) {{}}
                </script>""",
                height=0,
                width=0
            )

        # Validate against backend expiration (logged in for too long check)
        user_profile = validate_session(url_token)
        if user_profile:
            st.session_state["user"] = user_profile
            st.session_state["session_token"] = url_token
            st.session_state["db_student"] = db.query(Student).filter_by(student_id=user_profile["student_id"]).first()
        else:
            # Token expired because user was logged in for too long
            st.query_params.clear()
            st.warning("⚠️ Your session expired because you were logged in for too long. Please sign in again.")

    # Check authentication
    if not st.session_state["user"]:
        render_login_page(db)
        return

    user = st.session_state["user"]
    db_student = st.session_state.get("db_student")
    if not db_student:
        db_student = db.query(Student).filter_by(student_id=user["student_id"]).first()
        st.session_state["db_student"] = db_student

    # Render sidebar and get selected view
    selected_module = render_sidebar(user)

    # Render the chosen view
    if selected_module == "💬 AI Chatbot":
        render_chatbot_view(db, db_student, user)
    elif selected_module == "📊 Attendance":
        render_attendance_view(db, user)
    elif selected_module == "📅 Timetable":
        render_timetable_view(db, db_student)
    elif selected_module == "🎓 Results":
        render_results_view(db, user)
    elif selected_module == "💳 Fees":
        render_fees_view(db, user)
    elif selected_module == "📢 Notices":
        render_notices_view(db)
    elif selected_module == "💼 Placements":
        render_placements_view(db)
    elif selected_module == "📚 Library":
        render_library_view(db, user)
    elif selected_module == "📝 Complaint":
        render_complaints_view(db, user)
    elif selected_module == "❓ FAQ":
        render_faq_view(db)
    elif selected_module == "⚙️ Admin Mode" and user.get("is_admin"):
        render_admin_mode(db)
    else:
        render_chatbot_view(db, db_student, user)
