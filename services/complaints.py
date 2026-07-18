from datetime import date
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from database.models import Complaint


def generate_complaint_id(db: Session) -> str:
    """
    Generates a unique complaint ID format: CMP-YYYY-XXXX.
    """
    current_year = date.today().year
    count = db.query(Complaint).count() + 1
    return f"CMP-{current_year}-{count:04d}"


def submit_complaint(db: Session, student_id: str, category: str, description: str, priority: str = "Normal") -> Dict[str, Any]:
    """
    Stores a new complaint in the database and returns the generated complaint ID.
    """
    cmp_id = generate_complaint_id(db)
    complaint = Complaint(
        complaint_id=cmp_id,
        student_id=student_id,
        category=category,
        description=description,
        priority=priority,
        status="Open",
        date_submitted=date.today()
    )
    db.add(complaint)
    db.commit()
    return {
        "status": "success",
        "complaint_id": cmp_id,
        "message": f"Your complaint has been registered with ID: {cmp_id}. Priority: {priority}."
    }


def get_student_complaints(db: Session, student_id: str) -> List[Dict[str, Any]]:
    """
    Retrieves all complaints logged by a specific student.
    """
    records = db.query(Complaint).filter(Complaint.student_id == student_id).order_by(Complaint.id.desc()).all()
    output = []
    for rec in records:
        output.append({
            "id": rec.id,
            "complaint_id": rec.complaint_id,
            "category": rec.category,
            "description": rec.description,
            "priority": rec.priority,
            "status": rec.status,
            "date_submitted": rec.date_submitted.strftime("%Y-%m-%d") if rec.date_submitted else "N/A"
        })
    return output


def get_all_complaints(db: Session) -> List[Dict[str, Any]]:
    """
    Admin utility to view all student complaints across the college.
    """
    records = db.query(Complaint).order_by(Complaint.id.desc()).all()
    output = []
    for rec in records:
        output.append({
            "id": rec.id,
            "complaint_id": rec.complaint_id,
            "student_id": rec.student_id,
            "student_name": rec.student.name if rec.student else "Unknown",
            "category": rec.category,
            "description": rec.description,
            "priority": rec.priority,
            "status": rec.status,
            "date_submitted": rec.date_submitted.strftime("%Y-%m-%d") if rec.date_submitted else "N/A"
        })
    return output


def update_complaint_status(db: Session, complaint_id: str, new_status: str) -> bool:
    """
    Admin utility to update complaint status.
    """
    rec = db.query(Complaint).filter_by(complaint_id=complaint_id).first()
    if not rec:
        return False
    rec.status = new_status
    db.commit()
    return True
