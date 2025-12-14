"""Assessment service for health scoring and recommendations"""

from typing import Dict, Optional, Tuple
from data.questions import ALL_QUESTIONS, get_question, get_total_questions
from data.recommendations import get_recommendation
from data.faq import find_faq, get_faq_list, get_faq_by_number
from services.state_manager import (
    get_state_manager,
    ConversationState,
    UserSession
)


class AssessmentService:
    """Service for managing health assessments"""

    def __init__(self):
        self.state_manager = get_state_manager()

    def start_assessment(self, user_id: str) -> str:
        """Start a new assessment for user"""
        session = self.state_manager.get_session(user_id)
        session.reset()
        session.state = ConversationState.ASSESSMENT
        session.current_question_index = 0
        self.state_manager.update_session(session)

        # Return first question
        return self._format_question(0)

    def _format_question(self, index: int) -> str:
        """Format question with options"""
        question = get_question(index)
        if not question:
            return None

        progress = f"📝 คำถามที่ {index + 1}/{get_total_questions()}\n\n"
        q_text = question["question"] + "\n\n"
        options = "\n".join([opt["label"] for opt in question["options"]])

        return progress + q_text + options + "\n\nกรุณาตอบเป็นตัวเลขค่ะ"

    def process_answer(self, user_id: str, answer: str) -> Tuple[str, bool]:
        """
        Process user's answer
        Returns (response_message, is_assessment_complete)
        """
        session = self.state_manager.get_session(user_id)

        if session.state != ConversationState.ASSESSMENT:
            return None, False

        question = get_question(session.current_question_index)
        if not question:
            return self._complete_assessment(user_id), True

        # Parse answer (expect number 1, 2, 3, etc.)
        answer_num = self._parse_answer(answer, len(question["options"]))
        if answer_num is None:
            return f"กรุณาตอบเป็นตัวเลข 1-{len(question['options'])} ค่ะ", False

        # Record answer
        selected_option = question["options"][answer_num - 1]
        self.state_manager.add_answer(
            user_id,
            question["id"],
            selected_option["score"]
        )

        # Move to next question
        session = self.state_manager.get_session(user_id)
        session.current_question_index += 1

        if session.current_question_index >= get_total_questions():
            # Assessment complete
            return self._complete_assessment(user_id), True
        else:
            # Next question
            self.state_manager.update_session(session)
            return self._format_question(session.current_question_index), False

    def _parse_answer(self, answer: str, max_options: int) -> Optional[int]:
        """Parse answer text to option number"""
        answer = answer.strip()

        # Try to extract number
        for char in answer:
            if char.isdigit():
                num = int(char)
                if 1 <= num <= max_options:
                    return num
        return None

    def _complete_assessment(self, user_id: str) -> str:
        """Complete assessment and return recommendation"""
        session = self.state_manager.get_session(user_id)
        total_score = session.total_score

        # Get recommendation
        recommendation = get_recommendation(total_score)

        # Reset session
        session.state = ConversationState.IDLE
        self.state_manager.update_session(session)

        # Format result
        result = recommendation["message"]
        result += f"\n\n📋 คะแนนรวม: {total_score} คะแนน"
        result += "\n\nพิมพ์ 'ประเมินอาการ' เพื่อประเมินใหม่"
        result += "\nหรือถามคำถามเกี่ยวกับ PM2.5 ได้เลยค่ะ"

        return result

    def handle_faq_query(self, query: str) -> Optional[str]:
        """Handle FAQ queries"""
        # Check if query is a number
        try:
            num = int(query.strip())
            faq = get_faq_by_number(num)
            if faq:
                return faq["answer"]
        except ValueError:
            pass

        # Search by keywords
        faq = find_faq(query)
        if faq:
            return faq["answer"]

        return None

    def get_faq_menu(self) -> str:
        """Get FAQ menu"""
        return get_faq_list()

    def cancel_assessment(self, user_id: str) -> str:
        """Cancel current assessment"""
        session = self.state_manager.get_session(user_id)
        session.reset()
        self.state_manager.update_session(session)
        return "ยกเลิกการประเมินแล้วค่ะ\n\nพิมพ์ 'ประเมินอาการ' เพื่อเริ่มใหม่ หรือถามคำถามเกี่ยวกับ PM2.5 ได้เลยค่ะ"


# Singleton instance
_assessment_service: Optional[AssessmentService] = None


def get_assessment_service() -> AssessmentService:
    """Get singleton assessment service"""
    global _assessment_service
    if _assessment_service is None:
        _assessment_service = AssessmentService()
    return _assessment_service
