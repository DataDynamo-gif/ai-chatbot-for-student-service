from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from database.models import Attendance, Subject


def get_student_attendance(db: Session, student_id: str) -> List[Dict[str, Any]]:
    """
    Retrieves all attendance records for a specific student.
    Returns structured data with percentage and below_75 flag.
    """
    records = db.query(Attendance).filter(Attendance.student_id == student_id).all()
    output = []
    for rec in records:
        output.append({
            "id": rec.id,
            "subject_code": rec.subject.code if rec.subject else "N/A",
            "subject_name": rec.subject.name if rec.subject else "Unknown Subject",
            "classes_attended": rec.classes_attended,
            "total_classes": rec.total_classes,
            "percentage": rec.percentage,
            "below_75": rec.percentage < 75.0
        })
    return output


def get_subjects_below_75(db: Session, student_id: str) -> List[Dict[str, Any]]:
    """
    Filters and returns only subjects where attendance percentage is below 75%.
    """
    all_att = get_student_attendance(db, student_id)
    return [item for item in all_att if item["below_75"]]


def get_subject_attendance(db: Session, student_id: str, subject_query: str) -> Optional[Dict[str, Any]]:
    """
    Finds attendance for a specific subject by code or name match (case-insensitive).
    """
    all_att = get_student_attendance(db, student_id)
    q_clean = subject_query.lower().strip()
    for item in all_att:
        if q_clean in item["subject_code"].lower() or q_clean in item["subject_name"].lower():
            return item
    return None


def check_can_skip_tomorrow(db: Session, student_id: str, subject_query: Optional[str] = None) -> Dict[str, Any]:
    """
    Calculates whether skipping tomorrow's lecture(s) will drop attendance below 75%.
    If subject_query is provided, checks for that subject. Otherwise checks overall summary.
    """
    all_att = get_student_attendance(db, student_id)
    if not all_att:
        return {"status": "error", "message": "No attendance records found."}

    if subject_query:
        target = get_subject_attendance(db, student_id, subject_query)
        if not target:
            return {"status": "error", "message": f"Subject matching '{subject_query}' not found."}
        subjects_to_check = [target]
    else:
        subjects_to_check = all_att

    results = []
    can_skip_all = True
    for subj in subjects_to_check:
        attended = subj["classes_attended"]
        total = subj["total_classes"] + 1  # If student skips tomorrow, total increases by 1 while attended stays same
        new_pct = round((attended / total) * 100.0, 2) if total > 0 else 0.0
        would_drop = new_pct < 75.0
        if would_drop:
            can_skip_all = False

        results.append({
            "subject": subj["subject_name"],
            "current_percentage": subj["percentage"],
            "percentage_if_skipped": new_pct,
            "safe_to_skip": not would_drop
        })

    return {
        "status": "success",
        "can_skip": can_skip_all,
        "details": results
    }


def update_attendance_record(db: Session, student_id: str, subject_id: int, attended: int, total: int) -> bool:
    """
    Admin utility to update or insert an attendance record.
    """
    record = db.query(Attendance).filter_by(student_id=student_id, subject_id=subject_id).first()
    if not record:
        record = Attendance(student_id=student_id, subject_id=subject_id, classes_attended=attended, total_classes=total)
        db.add(record)
    else:
        record.classes_attended = attended
        record.total_classes = total
    db.commit()
    return True
