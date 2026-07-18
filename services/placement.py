from typing import List, Dict, Any
from sqlalchemy.orm import Session
from database.models import Placement


def get_placements(db: Session, query: str = "", min_package: float = 0.0) -> List[Dict[str, Any]]:
    """
    Searches placement opportunities by company/role and filters by minimum package.
    """
    records = db.query(Placement).order_by(Placement.package_lpa.desc()).all()
    output = []
    q_clean = query.lower().strip()
    for rec in records:
        if rec.package_lpa < min_package:
            continue
        if q_clean and (
            q_clean not in rec.company.lower()
            and q_clean not in rec.role.lower()
            and q_clean not in rec.eligibility_criteria.lower()
        ):
            continue
        output.append({
            "id": rec.id,
            "company": rec.company,
            "role": rec.role,
            "package_lpa": rec.package_lpa,
            "eligibility_criteria": rec.eligibility_criteria,
            "deadline": rec.deadline,
            "description": rec.description
        })
    return output


def add_placement(db: Session, company: str, role: str, package_lpa: float, eligibility: str, deadline: str, description: str = "") -> bool:
    """
    Admin utility to add a new placement drive.
    """
    place = Placement(
        company=company,
        role=role,
        package_lpa=package_lpa,
        eligibility_criteria=eligibility,
        deadline=deadline,
        description=description
    )
    db.add(place)
    db.commit()
    return True
