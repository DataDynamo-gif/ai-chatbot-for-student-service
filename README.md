# Student Service Chatbot 🎓

A production-quality, modular, AI-powered Student Service Chatbot and academic management portal built with **Python 3.12**, **FastAPI**, **Streamlit**, **SQLAlchemy (SQLite)**, and **OpenAI**.

This application provides college students with a clean, minimal chat interface and sidebar navigation to access critical academic information including Attendance, Timetable, Results, Fees, Notices, Placements, Library records, Complaints, and FAQs.

---

## Features

- **Clean Minimal UI**: Crisp white background design with sidebar navigation, no distractions, highly responsive.
- **AI Chatbot Interface**: Understands natural language queries (`"What is my attendance in DBMS?"`, `"Show my latest result"`, `"Can I skip tomorrow's class?"`, `"Are there any new placement drives?"`). Uses direct SQLite execution for academic records and **OpenAI API** for general reasoning/synthesis when required.
- **Comprehensive Academic Modules**:
  - **Profile**: View roll number, department, semester, section, email, and contact info.
  - **Attendance**: Real-time attendance percentage breakdown with automatic highlighting for subjects under 75% and "Can I skip tomorrow?" calculator.
  - **Timetable**: View today's schedule, tomorrow's schedule, upcoming lectures, and free periods.
  - **Results**: Check semester SGPA, overall CGPA, active backlogs, and detailed subject-wise marks.
  - **Fees**: Track paid amount, pending dues, deadlines, and download dummy fee receipts.
  - **Notices**: Searchable and sortable campus notice board.
  - **Placements**: Searchable placement drive directory with eligibility criteria, packages (LPA), and deadlines.
  - **Library**: Search library catalog, check due dates, calculate fine amounts, and renew books.
  - **Complaints**: Submit detailed complaints with priority selection and automatic ID generation (`CMP-YYYY-XXXX`).
  - **FAQ**: Instant answers to common campus policies (hostel timing, scholarship rules, library hours, etc.).
- **Hidden Admin Mode**: Accessible via admin login credentials to manage students, edit attendance records, upload results, post notices, add placement drives, and resolve student complaints.
- **Extra Productivity Features**: Dark mode toggle, chat history search, PDF export of chat history, TXT export of chat history, and typing/loading indicators.
- **Robust Error Handling**: Graceful fallback when offline, missing OpenAI API key, or invalid database queries.

---

## Project Structure

```text
student_chatbot/
│
├── app.py                 # Main entry point (Streamlit UI + optional FastAPI launcher)
├── requirements.txt       # Project dependencies
├── README.md              # Project documentation
├── .env                   # Environment variable configuration
│
├── database/
│   ├── database.py        # SQLAlchemy engine and session setup
│   ├── models.py          # ORM models for all database entities
│   └── seed.py            # Sample data seeding script
│
├── services/
│   ├── attendance.py      # Attendance service queries and calculations
│   ├── timetable.py       # Timetable and schedule queries
│   ├── result.py          # Academic results and marks service
│   ├── notices.py         # Campus notice board service
│   ├── fee.py             # Fee status and receipt generation
│   ├── library.py         # Library book search and circulation service
│   ├── placement.py       # Placement drives and eligibility service
│   ├── complaints.py      # Complaint registration and tracking service
│   └── faq.py             # Frequently asked questions service
│
├── chatbot/
│   ├── intent_classifier.py # Hybrid natural language intent classification
│   ├── response_engine.py   # Query execution and OpenAI integration engine
│   └── prompts.py           # AI system prompts and response templates
│
├── auth/
│   └── login.py           # Student & Admin authentication verification
│
├── ui/
│   └── interface.py       # Modular Streamlit user interface components
│
└── data/
    └── students.db        # SQLite database file
```

---

## Installation & Setup

### 1. Prerequisites
- **Python 3.12+** installed on your system.

### 2. Create and Activate Virtual Environment
Open terminal inside the `student_chatbot` folder:

**Windows (PowerShell/CMD):**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables (`.env`)
Open `.env` in the root directory and set your OpenAI API key (optional, for enhanced general reasoning):
```env
OPENAI_API_KEY="sk-your-actual-api-key-here"
DATABASE_URL="sqlite:///./data/students.db"
```
*(Note: If `OPENAI_API_KEY` is not set or unavailable, the chatbot automatically falls back to intelligent direct SQLite query processing so all academic functions still work completely locally!)*

### 5. Initialize Database & Seed Sample Data
Execute the seed script to create all database tables and populate rich sample data:
```bash
python database/seed.py
```

---

## Running Instructions

You can run the application directly using either of the following commands:

### Using Streamlit CLI (Recommended)
```bash
streamlit run app.py
```

### Or using standard Python command
```bash
python app.py
```

Once launched, open your web browser at `http://localhost:8501`.

---

## Default Login Credentials

### Student Account (Sample 1)
- **Student ID**: `S101`
- **Password**: `password123`
- **Details**: Aarav Sharma (Computer Science, Sem 6, Section A)

### Student Account (Sample 2)
- **Student ID**: `S102`
- **Password**: `password123`
- **Details**: Diya Patel (Computer Science, Sem 6, Section A)

### Hidden Admin Account
- **Student ID**: `admin`
- **Password**: `admin123`
- **Details**: Grants access to the **Admin Management Dashboard** in the sidebar to manage database entries.

---

## Example Chatbot Queries to Try

Once logged in, type any of these in the chat box:
- *"What is my attendance right now?"*
- *"Which subjects are below 75% attendance?"*
- *"Can I skip tomorrow's lectures?"*
- *"What classes do I have today?"*
- *"When is my next lecture?"*
- *"Show my SGPA and CGPA results."*
- *"Do I have any pending fee balance?"*
- *"Are there any new placement drives for Computer Science?"*
- *"What is the library timing?"*
- *"I want to check notices about exams."*
