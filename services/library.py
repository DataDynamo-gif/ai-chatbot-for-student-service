from typing import List, Dict, Any
from sqlalchemy.orm import Session
from database.models import LibraryBook


def search_library_books(db: Session, query: str = "") -> List[Dict[str, Any]]:
    """
    Searches library books by title, author, or ISBN.
    """
    records = db.query(LibraryBook).all()
    output = []
    q_clean = query.lower().strip()
    for rec in records:
        if q_clean and (
            q_clean not in rec.title.lower()
            and q_clean not in rec.author.lower()
            and q_clean not in rec.isbn.lower()
        ):
            continue
        output.append({
            "id": rec.id,
            "title": rec.title,
            "author": rec.author,
            "isbn": rec.isbn,
            "is_available": rec.is_available,
            "issued_to": rec.issued_to_student_id or "-",
            "due_date": rec.due_date or "-",
            "fine_amount": rec.fine_amount
        })
    return output


def get_student_issued_books(db: Session, student_id: str) -> List[Dict[str, Any]]:
    """
    Returns books currently issued to the student, along with due dates and fines.
    """
    records = db.query(LibraryBook).filter(LibraryBook.issued_to_student_id == student_id).all()
    output = []
    for rec in records:
        output.append({
            "id": rec.id,
            "title": rec.title,
            "author": rec.author,
            "due_date": rec.due_date or "N/A",
            "fine_amount": rec.fine_amount
        })
    return output


def renew_book_dummy(db: Session, book_id: int, student_id: str) -> Dict[str, Any]:
    """
    Dummy action to renew an issued book and extend its due date.
    """
    book = db.query(LibraryBook).filter_by(id=book_id, issued_to_student_id=student_id).first()
    if not book:
        return {"status": "error", "message": "Book not found or not issued to your account."}
    
    # Dummy extension
    book.due_date = "Extended (+14 Days)"
    if book.fine_amount > 0:
        return {"status": "warning", "message": f"Renewed! Please pay pending fine of INR {book.fine_amount} at the counter."}
    db.commit()
    return {"status": "success", "message": f"Successfully renewed '{book.title}' for 14 additional days."}
