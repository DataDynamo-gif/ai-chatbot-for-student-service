from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from database.models import FAQ


def get_all_faqs(db: Session, category: str = "All") -> List[Dict[str, Any]]:
    """
    Retrieves all common campus FAQs, optionally filtered by category.
    """
    query = db.query(FAQ)
    if category and category != "All":
        query = query.filter(FAQ.category == category)
    records = query.all()
    return [
        {
            "id": rec.id,
            "question": rec.question,
            "answer": rec.answer,
            "category": rec.category
        }
        for rec in records
    ]


def match_faq(db: Session, query_text: str) -> Optional[Dict[str, Any]]:
    """
    Matches natural language query against stored FAQ questions and keywords.
    Returns the best matching FAQ immediately if similarity/keyword overlap is high.
    """
    records = db.query(FAQ).all()
    q_words = set(query_text.lower().replace("?", "").replace(".", "").split())
    
    best_match = None
    max_overlap = 0

    for rec in records:
        rec_words = set(rec.question.lower().replace("?", "").replace(".", "").split())
        overlap = len(q_words.intersection(rec_words))
        # If strong keyword match
        if overlap >= 2 and overlap > max_overlap:
            max_overlap = overlap
            best_match = {
                "id": rec.id,
                "question": rec.question,
                "answer": rec.answer,
                "category": rec.category
            }
            
    return best_match
