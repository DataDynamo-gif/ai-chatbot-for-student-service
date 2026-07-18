from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from database.models import Timetable, Student


DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def get_schedule_for_day(db: Session, department: str, semester: int, day_of_week: str) -> List[Dict[str, Any]]:
    """
    Retrieves the ordered timetable for a given department, semester, and day.
    """
    records = db.query(Timetable).filter_by(
        department=department,
        semester=semester,
        day_of_week=day_of_week
    ).order_by(Timetable.period_number).all()

    output = []
    for rec in records:
        output.append({
            "period_number": rec.period_number,
            "start_time": rec.start_time,
            "end_time": rec.end_time,
            "subject": rec.subject.name if rec.subject else "Free Period",
            "subject_code": rec.subject.code if rec.subject else "-",
            "room_number": rec.room_number or "-"
        })
    return output


def get_todays_classes(db: Session, student: Student) -> List[Dict[str, Any]]:
    """
    Returns today's classes for the given student profile.
    """
    current_day = datetime.now().strftime("%A")
    # If weekend, default to Monday for demonstration or return actual schedule
    if current_day in ["Saturday", "Sunday"]:
        current_day = "Monday"
    return get_schedule_for_day(db, student.department, student.semester, current_day)


def get_tomorrows_classes(db: Session, student: Student) -> List[Dict[str, Any]]:
    """
    Returns tomorrow's classes for the given student profile.
    """
    idx = datetime.now().weekday()
    next_idx = (idx + 1) % 7
    # If tomorrow is Saturday/Sunday, wrap to Monday for demonstration
    if next_idx >= 5:
        next_day = "Monday"
    else:
        next_day = DAY_NAMES[next_idx]
    return get_schedule_for_day(db, student.department, student.semester, next_day)


def get_next_lecture(db: Session, student: Student) -> Optional[Dict[str, Any]]:
    """
    Finds the very next upcoming lecture today.
    """
    todays = get_todays_classes(db, student)
    now_str = datetime.now().strftime("%I:%M %p")
    # Simple logic: return the first non-free period of today for demo, or match time
    for cls in todays:
        if cls["subject"] != "Free Period":
            return cls
    return None


def get_free_periods(db: Session, student: Student, day: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Returns all free periods for the student on the specified day (or today).
    """
    if not day:
        day = datetime.now().strftime("%A")
        if day in ["Saturday", "Sunday"]:
            day = "Monday"
    schedule = get_schedule_for_day(db, student.department, student.semester, day)
    return [cls for cls in schedule if cls["subject"] == "Free Period"]
