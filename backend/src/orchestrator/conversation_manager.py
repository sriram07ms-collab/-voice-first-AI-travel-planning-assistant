"""
Conversation Manager
Manages conversation state, user preferences, and session data.
"""

import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

try:
    from ..utils.config import settings
except ImportError:
    from src.utils.config import settings

logger = logging.getLogger(__name__)


class ConversationSession:
    """Represents a single conversation session."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.preferences: Dict[str, Any] = {
            "city": None,
            "duration_days": None,
            "interests": [],
            "pace": None,
            "budget": None,
            "start_date": None,
            "end_date": None
        }
        self.itinerary: Optional[Dict[str, Any]] = None
        self.conversation_history: List[Dict[str, str]] = []
        self.clarifying_questions_count = 0
        self.clarifying_questions: List[str] = []
        self.sources: List[Dict[str, Any]] = []
        self.evaluation: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "preferences": self.preferences,
            "itinerary": self.itinerary,
            "conversation_history": self.conversation_history,
            "clarifying_questions_count": self.clarifying_questions_count,
            "clarifying_questions": self.clarifying_questions,
            "sources": self.sources,
            "evaluation": self.evaluation
        }
    
    def is_expired(self, timeout_minutes: int = 60) -> bool:
        """Check if session has expired."""
        elapsed = datetime.now() - self.last_activity
        return elapsed > timedelta(minutes=timeout_minutes)


class ConversationManager:
    """
    Manages conversation sessions and state.
    In-memory storage (can be upgraded to Redis/PostgreSQL later).
    """
    
    def __init__(self):
        """Initialize conversation manager."""
        self.sessions: Dict[str, ConversationSession] = {}
        self.session_timeout_minutes = getattr(settings, 'session_timeout_minutes', 60)
        self.max_clarifying_questions = getattr(settings, 'max_clarifying_questions', 6)
        logger.info("ConversationManager initialized")
    
    def create_session(self) -> str:
        """
        Create a new conversation session.
        
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        session = ConversationSession(session_id)
        self.sessions[session_id] = session
        logger.info(f"Created new session: {session_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """
        Get session by ID.
        
        Args:
            session_id: Session ID
        
        Returns:
            ConversationSession or None if not found
        """
        session = self.sessions.get(session_id)
        if session:
            if session.is_expired(self.session_timeout_minutes):
                logger.info(f"Session {session_id} expired, removing")
                del self.sessions[session_id]
                return None
            session.last_activity = datetime.now()
        return session
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str
    ) -> bool:
        """
        Add a message to conversation history.
        
        Args:
            session_id: Session ID
            role: Message role ("user" or "assistant")
            content: Message content
        
        Returns:
            True if successful, False if session not found
        """
        session = self.get_session(session_id)
        if not session:
            logger.warning(f"Session {session_id} not found")
            return False
        
        session.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        session.last_activity = datetime.now()
        logger.debug(f"Added {role} message to session {session_id}")
        return True
    
    def get_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full context for a session.
        
        Args:
            session_id: Session ID
        
        Returns:
            Context dictionary or None if session not found
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        return session.to_dict()
    
    def update_preferences(
        self,
        session_id: str,
        preferences: Dict[str, Any]
    ) -> bool:
        """
        Update user preferences.
        
        Args:
            session_id: Session ID
            preferences: Preferences dictionary
        
        Returns:
            True if successful, False if session not found
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        # Merge preferences (don't overwrite existing non-None values unless explicitly provided)
        for key, value in preferences.items():
            if value is not None:
                session.preferences[key] = value
        
        session.last_activity = datetime.now()
        logger.info(f"Updated preferences for session {session_id}: {preferences}")
        return True
    
    def set_itinerary(
        self,
        session_id: str,
        itinerary: Dict[str, Any]
    ) -> bool:
        """
        Set itinerary for a session.
        
        Args:
            session_id: Session ID
            itinerary: Itinerary dictionary
        
        Returns:
            True if successful, False if session not found
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.itinerary = itinerary
        session.last_activity = datetime.now()
        logger.info(f"Set itinerary for session {session_id}")
        return True
    
    def add_clarifying_question(
        self,
        session_id: str,
        question: str
    ) -> bool:
        """
        Add a clarifying question.
        
        Args:
            session_id: Session ID
            question: Clarifying question text
        
        Returns:
            True if successful, False if session not found or max questions reached
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        if session.clarifying_questions_count >= self.max_clarifying_questions:
            logger.warning(f"Max clarifying questions reached for session {session_id}")
            return False
        
        session.clarifying_questions.append(question)
        session.clarifying_questions_count += 1
        session.last_activity = datetime.now()
        logger.info(f"Added clarifying question to session {session_id} ({session.clarifying_questions_count}/{self.max_clarifying_questions})")
        return True
    
    def can_ask_clarifying_question(self, session_id: str) -> bool:
        """
        Check if we can ask another clarifying question.
        
        Args:
            session_id: Session ID
        
        Returns:
            True if we can ask more questions
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        return session.clarifying_questions_count < self.max_clarifying_questions
    
    def reset_conversation(self, session_id: str) -> bool:
        """
        Reset conversation (clear preferences and history).
        
        Args:
            session_id: Session ID
        
        Returns:
            True if successful, False if session not found
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.preferences = {
            "city": None,
            "duration_days": None,
            "interests": [],
            "pace": None,
            "budget": None,
            "start_date": None,
            "end_date": None
        }
        session.itinerary = None
        session.conversation_history = []
        session.clarifying_questions_count = 0
        session.clarifying_questions = []
        session.sources = []
        session.evaluation = None
        session.last_activity = datetime.now()
        
        logger.info(f"Reset conversation for session {session_id}")
        return True
    
    def set_sources(
        self,
        session_id: str,
        sources: List[Dict[str, Any]]
    ) -> bool:
        """Set sources for a session."""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.sources = sources
        return True
    
    def set_evaluation(
        self,
        session_id: str,
        evaluation: Dict[str, Any]
    ) -> bool:
        """Set evaluation results for a session."""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.evaluation = evaluation
        return True
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions."""
        expired_sessions = [
            session_id for session_id, session in self.sessions.items()
            if session.is_expired(self.session_timeout_minutes)
        ]
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
            logger.info(f"Cleaned up expired session: {session_id}")


# Global conversation manager instance
_conversation_manager: Optional[ConversationManager] = None


def get_conversation_manager() -> ConversationManager:
    """
    Get or create global conversation manager instance.
    
    Returns:
        ConversationManager instance
    """
    global _conversation_manager
    if _conversation_manager is None:
        _conversation_manager = ConversationManager()
    return _conversation_manager
