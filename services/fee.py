from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from database.models import Fee


def get_student_fees(db: Session, student_id: str) -> List[Dict[str, Any]]:
    """
    Retrieves all fee records for a student.
    """
    records = db.query(Fee).filter(Fee.student_id == student_id).order_by(Fee.semester.desc()).all()
    output = []
    for rec in records:
        output.append({
            "id": rec.id,
            "semester": rec.semester,
            "paid_amount": rec.paid_amount,
            "pending_amount": rec.pending_amount,
            "due_date": rec.due_date,
            "receipt_number": rec.receipt_number,
            "status": "Paid" if rec.pending_amount == 0 else "Pending"
        })
    return output


def generate_fee_receipt_text(fee_record: Dict[str, Any], student_name: str, student_id: str) -> str:
    """
    Generates a dummy formatted fee receipt string ready for download.
    """
    return f"""
=================================================
             COLLEGE FEE RECEIPT
=================================================
Receipt No   : {fee_record['receipt_number']}
Student ID   : {student_id}
Student Name : {student_name}
Semester     : {fee_record['semester']}
-------------------------------------------------
Paid Amount  : INR {fee_record['paid_amount']:,.2f}
Pending Dues : INR {fee_record['pending_amount']:,.2f}
Due Date     : {fee_record['due_date']}
Status       : {fee_record['status'].upper()}
=================================================
Thank you for your payment!
Authorized Signatory (System Generated)
"""
