import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from database.models import Result


def get_student_results(db: Session, student_id: str) -> List[Dict[str, Any]]:
    """
    Fetches all semester results for the given student.
    Parses JSON marks and returns structured dictionaries.
    """
    records = db.query(Result).filter(Result.student_id == student_id).order_by(Result.semester.desc()).all()
    output = []
    for rec in records:
        try:
            marks_list = json.loads(rec.subject_marks_json)
        except Exception:
            marks_list = []
        output.append({
            "semester": rec.semester,
            "sgpa": rec.sgpa,
            "cgpa": rec.cgpa,
            "backlogs": rec.backlogs,
            "subject_marks": marks_list
        })
    return output


def get_latest_result(db: Session, student_id: str) -> Optional[Dict[str, Any]]:
    """
    Returns the most recent semester result for a student.
    """
    results = get_student_results(db, student_id)
    return results[0] if results else None


def upload_result(db: Session, student_id: str, semester: int, sgpa: float, cgpa: float, backlogs: int, marks_data: List[Dict[str, Any]]) -> bool:
    """
    Admin utility to upload or update a student's semester result.
    """
    marks_json = json.dumps(marks_data)
    record = db.query(Result).filter_by(student_id=student_id, semester=semester).first()
    if not record:
        record = Result(
            student_id=student_id,
            semester=semester,
            sgpa=sgpa,
            cgpa=cgpa,
            backlogs=backlogs,
            subject_marks_json=marks_json
        )
        db.add(record)
    else:
        record.sgpa = sgpa
        record.cgpa = cgpa
        record.backlogs = backlogs
        record.subject_marks_json = marks_json
    db.commit()
    return True
