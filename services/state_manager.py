"""User state management for conversation flow"""

import json
import os
from typing import Dict, Optional
from datetime import datetime, timedelta
from enum import Enum


class ConversationState(str, Enum):
    """States in the conversation flow"""
    IDLE = "idle"                    # Initial state, waiting for user
    ASSESSMENT = "assessment"         # In symptom assessment questionnaire
    WAITING_CONFIRM = "waiting_confirm"  # Waiting for assessment start confirmation
    FAQ_MENU = "faq_menu"            # Showing FAQ menu
    AWAITING_LOCATION = "awaiting_location"  # Waiting for user to share location


class UserSession:
    """User session data"""
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.state = ConversationState.IDLE
        self.current_question_index = 0
        self.answers: Dict[str, int] = {}  # question_id -> score
        self.total_score = 0
        self.last_activity = datetime.now()

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "state": self.state.value,
            "current_question_index": self.current_question_index,
            "answers": self.answers,
            "total_score": self.total_score,
            "last_activity": self.last_activity.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UserSession":
        session = cls(data["user_id"])
        session.state = ConversationState(data["state"])
        session.current_question_index = data["current_question_index"]
        session.answers = data["answers"]
        session.total_score = data["total_score"]
        session.last_activity = datetime.fromisoformat(data["last_activity"])
        return session

    def reset(self):
        """Reset session for new assessment"""
        self.state = ConversationState.IDLE
        self.current_question_index = 0
        self.answers = {}
        self.total_score = 0
        self.last_activity = datetime.now()


class StateManager:
    """Manages user conversation states with file persistence"""

    STATE_FILE = "user_states.json"
    SESSION_TIMEOUT_HOURS = 24

    def __init__(self):
        self._sessions: Dict[str, UserSession] = {}
        self._load_states()

    def _load_states(self):
        """Load states from file"""
        if os.path.exists(self.STATE_FILE):
            try:
                with open(self.STATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for user_id, session_data in data.items():
                        session = UserSession.from_dict(session_data)
                        # Check if session expired
                        if datetime.now() - session.last_activity < timedelta(hours=self.SESSION_TIMEOUT_HOURS):
                            self._sessions[user_id] = session
            except Exception as e:
                print(f"Error loading states: {e}")
                self._sessions = {}

    def _save_states(self):
        """Save states to file"""
        try:
            data = {user_id: session.to_dict() for user_id, session in self._sessions.items()}
            with open(self.STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving states: {e}")

    def get_session(self, user_id: str) -> UserSession:
        """Get or create user session"""
        if user_id not in self._sessions:
            self._sessions[user_id] = UserSession(user_id)
            self._save_states()

        session = self._sessions[user_id]
        session.last_activity = datetime.now()
        return session

    def update_session(self, session: UserSession):
        """Update and save session"""
        session.last_activity = datetime.now()
        self._sessions[session.user_id] = session
        self._save_states()

    def reset_session(self, user_id: str):
        """Reset user session"""
        if user_id in self._sessions:
            self._sessions[user_id].reset()
            self._save_states()

    def add_answer(self, user_id: str, question_id: str, score: int):
        """Record an answer and update score"""
        session = self.get_session(user_id)
        session.answers[question_id] = score
        session.total_score = sum(session.answers.values())
        self.update_session(session)


# Singleton instance
_state_manager: Optional[StateManager] = None


def get_state_manager() -> StateManager:
    """Get singleton state manager"""
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager
