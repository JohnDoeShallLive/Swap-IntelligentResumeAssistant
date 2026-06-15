from typing import Dict, Optional
import uuid
from datetime import datetime, timedelta
from backend.models.session import SessionState, ResumeData

class SessionStore:
    def __init__(self, ttl_minutes: int = 30):
        self._sessions: Dict[str, SessionState] = {}
        self.ttl_minutes = ttl_minutes

    def create_session(self, resume_data: ResumeData) -> str:
        self.cleanup_expired_sessions()
        session_id = str(uuid.uuid4())
        session = SessionState(
            session_id=session_id,
            resume_data=resume_data,
            conversation_history=[],
            created_at=datetime.utcnow()
        )
        self._sessions[session_id] = session
        return session_id

    def get_session(self, session_id: str) -> Optional[SessionState]:
        self.cleanup_expired_sessions()
        return self._sessions.get(session_id)

    def update_session(self, session: SessionState):
        if session.session_id in self._sessions:
            self._sessions[session.session_id] = session

    def cleanup_expired_sessions(self):
        now = datetime.utcnow()
        expired_keys = [
            k for k, v in self._sessions.items()
            if now - v.created_at > timedelta(minutes=self.ttl_minutes)
        ]
        for k in expired_keys:
            del self._sessions[k]

# Global instance for the application
store = SessionStore()
