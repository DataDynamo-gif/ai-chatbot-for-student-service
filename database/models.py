from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Text, Date
from sqlalchemy.orm import relationship
from database.database import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(50), unique=True, index=True, nullable=False)
    password = Column(String(100), nullable=False)
    name = Column(String(100), nullable=False)
    roll_number = Column(String(50), unique=True, nullable=False)
    department = Column(String(100), nullable=False)
    semester = Column(Integer, nullable=False)
    section = Column(String(20), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    phone = Column(String(20), nullable=True)
    is_admin = Column(Boolean, default=False)

    # Relationships
    attendances = relationship("Attendance", back_populates="student", cascade="all, delete-orphan")
    results = relationship("Result", back_populates="student", cascade="all, delete-orphan")
    fees = relationship("Fee", back_populates="student", cascade="all, delete-orphan")
    complaints = relationship("Complaint", back_populates="student", cascade="all, delete-orphan")
    messages = relationship("ChatMessage", back_populates="student", cascade="all, delete-orphan")


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(30), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    semester = Column(Integer, nullable=False)

    # Relationships
    attendances = relationship("Attendance", back_populates="subject", cascade="all, delete-orphan")
    timetables = relationship("Timetable", back_populates="subject", cascade="all, delete-orphan")


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(50), ForeignKey("students.student_id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    classes_attended = Column(Integer, default=0, nullable=False)
    total_classes = Column(Integer, default=0, nullable=False)
    last_updated = Column(Date, default=datetime.utcnow)

    # Relationships
    student = relationship("Student", back_populates="attendances")
    subject = relationship("Subject", back_populates="attendances")

    @property
    def percentage(self) -> float:
        if self.total_classes == 0:
            return 0.0
        return round((self.classes_attended / self.total_classes) * 100.0, 2)


class Timetable(Base):
    __tablename__ = "timetable"

    id = Column(Integer, primary_key=True, index=True)
    department = Column(String(100), nullable=False)
    semester = Column(Integer, nullable=False)
    day_of_week = Column(String(20), nullable=False)  # Monday, Tuesday, etc.
    period_number = Column(Integer, nullable=False)
    start_time = Column(String(20), nullable=False)   # e.g., "09:00 AM"
    end_time = Column(String(20), nullable=False)     # e.g., "10:00 AM"
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=True) # Null if free period
    room_number = Column(String(50), nullable=True)

    # Relationships
    subject = relationship("Subject", back_populates="timetables")


class Result(Base):
    __tablename__ = "results"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(50), ForeignKey("students.student_id"), nullable=False)
    semester = Column(Integer, nullable=False)
    sgpa = Column(Float, nullable=False)
    cgpa = Column(Float, nullable=False)
    backlogs = Column(Integer, default=0)
    subject_marks_json = Column(Text, nullable=False)  # JSON representation: [{"subject": "DBMS", "marks": 88, "grade": "A"}]

    # Relationships
    student = relationship("Student", back_populates="results")


class Fee(Base):
    __tablename__ = "fees"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(50), ForeignKey("students.student_id"), nullable=False)
    semester = Column(Integer, nullable=False)
    paid_amount = Column(Float, default=0.0)
    pending_amount = Column(Float, default=0.0)
    due_date = Column(String(30), nullable=False)
    receipt_number = Column(String(50), unique=True, nullable=False)

    # Relationships
    student = relationship("Student", back_populates="fees")


class Notice(Base):
    __tablename__ = "notices"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    date_posted = Column(Date, default=datetime.utcnow)
    category = Column(String(50), default="General")  # Academic, Exam, Event, General


class Placement(Base):
    __tablename__ = "placements"

    id = Column(Integer, primary_key=True, index=True)
    company = Column(String(100), nullable=False)
    role = Column(String(100), nullable=False)
    package_lpa = Column(Float, nullable=False)
    eligibility_criteria = Column(String(200), nullable=False) # e.g., "CGPA >= 7.5, No backlogs"
    deadline = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)


class LibraryBook(Base):
    __tablename__ = "library"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    author = Column(String(150), nullable=False)
    isbn = Column(String(50), unique=True, nullable=False)
    is_available = Column(Boolean, default=True)
    issued_to_student_id = Column(String(50), ForeignKey("students.student_id"), nullable=True)
    due_date = Column(String(30), nullable=True)
    fine_amount = Column(Float, default=0.0)


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(String(50), unique=True, index=True, nullable=False) # e.g., CMP-2026-0001
    student_id = Column(String(50), ForeignKey("students.student_id"), nullable=False)
    category = Column(String(80), nullable=False)  # Academic, Hostel, Canteen, Infrastructure, Other
    description = Column(Text, nullable=False)
    priority = Column(String(20), default="Normal") # Low, Normal, High, Urgent
    status = Column(String(30), default="Open")     # Open, In Progress, Resolved
    date_submitted = Column(Date, default=datetime.utcnow)

    # Relationships
    student = relationship("Student", back_populates="complaints")


class FAQ(Base):
    __tablename__ = "faqs"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(String(300), nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(String(80), default="General")  # Library, Attendance, Exam, Hostel, Scholarship


class ChatMessage(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(50), ForeignKey("students.student_id"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    timestamp = Column(String(50), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # Relationships
    student = relationship("Student", back_populates="messages")
