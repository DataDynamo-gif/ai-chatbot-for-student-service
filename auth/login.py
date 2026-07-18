import os
import json
import time
import secrets
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from database.models import Student

# Global session registry: { token: {"user": user_profile, "created_at": timestamp, "last_active": timestamp} }
ACTIVE_SESSIONS: Dict[str, Dict[str, Any]] = {}

# Maximum login duration: 3600 seconds (1 hour)
MAX_SESSION_DURATION = 3600

SESSIONS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "sessions.json")


def _load_sessions():
    global ACTIVE_SESSIONS
    if os.path.exists(SESSIONS_FILE):
        try:
            with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
                ACTIVE_SESSIONS = json.load(f)
        except Exception:
            ACTIVE_SESSIONS = {}


def _save_sessions():
    try:
        os.makedirs(os.path.dirname(SESSIONS_FILE), exist_ok=True)
        with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(ACTIVE_SESSIONS, f, indent=2)
    except Exception:
        pass


def authenticate_user(db: Session, student_id: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Verifies student/admin credentials against database records.
    Returns structured user profile info on success or None on failure.
    """
    if not student_id or not password:
        return None

    user = db.query(Student).filter(Student.student_id == student_id.strip()).first()
    if not user:
        return None

    if user.password != password:
        return None

    return {
        "id": user.id,
        "student_id": user.student_id,
        "name": user.name,
        "roll_number": user.roll_number,
        "department": user.department,
        "semester": user.semester,
        "section": user.section,
        "email": user.email,
        "phone": user.phone or "N/A",
        "is_admin": user.is_admin
    }


def create_session(user_profile: Dict[str, Any]) -> str:
    """
    Creates a new session token for the authenticated user and records timestamp.
    """
    _load_sessions()
    token = secrets.token_urlsafe(24)
    now = time.time()
    ACTIVE_SESSIONS[token] = {
        "user": user_profile,
        "created_at": now,
        "last_active": now
    }
    _save_sessions()
    return token


def validate_session(token: str) -> Optional[Dict[str, Any]]:
    """
    Checks if session token exists and is within the allowed duration.
    If valid, updates last_active and returns user profile.
    If expired or invalid, destroys session and returns None.
    """
    _load_sessions()
    if not token or token not in ACTIVE_SESSIONS:
        return None

    session_data = ACTIVE_SESSIONS[token]
    now = time.time()

    # Check if session has exceeded maximum duration (logged in for too long)
    if now - session_data.get("created_at", 0) > MAX_SESSION_DURATION:
        destroy_session(token)
        return None

    session_data["last_active"] = now
    ACTIVE_SESSIONS[token] = session_data
    _save_sessions()
    return session_data["user"]


def destroy_session(token: str):
    """
    Removes session token from active registry.
    """
    _load_sessions()
    if token in ACTIVE_SESSIONS:
        del ACTIVE_SESSIONS[token]
        _save_sessions()


