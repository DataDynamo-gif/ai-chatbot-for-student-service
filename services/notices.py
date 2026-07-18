from typing import List, Dict, Any
from sqlalchemy.orm import Session
from database.models import Notice


def get_notices(db: Session, query: str = "", category: str = "All") -> List[Dict[str, Any]]:
    """
    Fetches notices sorted by newest date first.
    Allows searching by keywords across title/content and filtering by category.
    """
    db_query = db.query(Notice)
    if category and category != "All":
        db_query = db_query.filter(Notice.category == category)
    
    records = db_query.order_by(Notice.date_posted.desc()).all()
    output = []
    q_clean = query.lower().strip()
    for rec in records:
        if q_clean and q_clean not in rec.title.lower() and q_clean not in rec.content.lower():
            continue
        output.append({
            "id": rec.id,
            "title": rec.title,
            "content": rec.content,
            "date_posted": rec.date_posted.strftime("%B %d, %Y") if rec.date_posted else "N/A",
            "category": rec.category
        })
    return output


def add_notice(db: Session, title: str, content: str, category: str = "General") -> bool:
    """
    Admin utility to post a new campus notice.
    """
    notice = Notice(title=title, content=content, category=category)
    db.add(notice)
    db.commit()
    return True
