"""Message handler for Line chatbot"""

from typing import Optional
from services.state_manager import get_state_manager, ConversationState
from services.assessment_service import get_assessment_service
from services.dust_service import get_dust_service


class MessageHandler:
    """Handles incoming Line messages"""

    # Keywords for different intents (be specific to avoid matching FAQ queries)
    START_KEYWORDS = ["ประเมินอาการ", "เริ่มประเมิน", "ตรวจอาการ", "start", "assess", "วินิจฉัย"]
    CANCEL_KEYWORDS = ["ยกเลิก", "cancel", "หยุด", "เลิก", "ออก"]
    GREETING_KEYWORDS = ["สวัสดี", "hello", "hi", "หวัดดี", "ดีครับ", "ดีค่ะ"]
    HELP_KEYWORDS = ["help", "ช่วย", "วิธี", "ใช้งาน", "menu", "เมนู"]
    CHECK_DUST_KEYWORDS = ["ตรวจสอบค่าฝุ่น", "เช็คค่าฝุ่น", "ค่าฝุ่นวันนี้", "ดูค่าฝุ่น", "pm2.5 วันนี้", "ค่าฝุ่นตอนนี้", "aqi"]

    def __init__(self):
        self.state_manager = get_state_manager()
        self.assessment_service = get_assessment_service()
        self.dust_service = get_dust_service()

    async def handle_message(self, user_id: str, text: str) -> str:
        """Process incoming message and return response"""
        text_lower = text.lower().strip()
        session = self.state_manager.get_session(user_id)

        # Check for cancel during assessment or awaiting location
        if session.state in [ConversationState.ASSESSMENT, ConversationState.AWAITING_LOCATION]:
            if self._matches_keywords(text_lower, self.CANCEL_KEYWORDS):
                if session.state == ConversationState.ASSESSMENT:
                    return self.assessment_service.cancel_assessment(user_id)
                else:
                    session.state = ConversationState.IDLE
                    self.state_manager.update_session(session)
                    return "ยกเลิกการตรวจสอบค่าฝุ่นแล้วค่ะ\n\nสามารถถามคำถามเกี่ยวกับ PM2.5 ได้เลยค่ะ"

        # Handle assessment answers
        if session.state == ConversationState.ASSESSMENT:
            # Process as answer
            response, is_complete = self.assessment_service.process_answer(user_id, text)
            if response:
                return response

        # If awaiting location but got text, remind user to share location
        if session.state == ConversationState.AWAITING_LOCATION:
            return self._get_location_request_message()

        # Check for greetings
        if self._matches_keywords(text_lower, self.GREETING_KEYWORDS):
            return self._get_welcome_message()

        # Check for help
        if self._matches_keywords(text_lower, self.HELP_KEYWORDS):
            return self._get_help_message()

        # Check for dust level check - ask for location
        if self._matches_keywords(text_lower, self.CHECK_DUST_KEYWORDS):
            session.state = ConversationState.AWAITING_LOCATION
            self.state_manager.update_session(session)
            return self._get_location_request_message()

        # Check for start assessment
        if self._matches_keywords(text_lower, self.START_KEYWORDS):
            return self.assessment_service.start_assessment(user_id)

        # Try to answer from FAQ knowledge base
        faq_response = self.assessment_service.handle_faq_query(text)
        if faq_response:
            return faq_response

        # Default response
        return self._get_default_message()

    def _matches_keywords(self, text: str, keywords: list) -> bool:
        """Check if text contains any keyword"""
        return any(kw in text for kw in keywords)

    def _get_welcome_message(self) -> str:
        """Get welcome message"""
        return """สวัสดีค่ะ ยินดีต้อนรับสู่ระบบให้คำปรึกษาเรื่องฝุ่น PM2.5 ค่ะ

สามารถถามเกี่ยวกับฝุ่น PM2.5 ได้เลยค่ะ เช่น
• PM2.5 คืออะไร
• หน้ากากแบบไหนดี
• วิธีป้องกันตัวเอง

หรือพิมพ์ 'ตรวจสอบค่าฝุ่น' เพื่อตรวจสอบค่าฝุ่นจากตำแหน่งที่ตั้ง

หรือพิมพ์ 'ประเมินอาการ' เพื่อประเมินอาการสุขภาพค่ะ

⚠️ นี่เป็นการให้คำปรึกษาเบื้องต้น ไม่สามารถใช้แทนการวินิจฉัยจากแพทย์ได้นะคะ"""

    def _get_help_message(self) -> str:
        """Get help message"""
        return """วิธีใช้งาน:

💬 ถามคำถาม:
   ถามเกี่ยวกับ PM2.5 ได้เลยค่ะ เช่น
   "PM2.5 คืออะไร"
   "ค่าฝุ่นเท่าไหร่ถึงอันตราย"
   "หน้ากากแบบไหนป้องกันได้"

📍 ตรวจสอบค่าฝุ่น:
   พิมพ์ 'ตรวจสอบค่าฝุ่น' เพื่อดูค่าฝุ่นจากตำแหน่งที่ตั้ง

📋 ประเมินอาการ:
   พิมพ์ 'ประเมินอาการ' เพื่อเริ่มประเมินอาการ
   ตอบคำถาม 9 ข้อ แล้วรับคำแนะนำค่ะ

🚫 ยกเลิก:
   พิมพ์ 'ยกเลิก' เพื่อยกเลิกการประเมิน

หากมีอาการรุนแรง กรุณาพบแพทย์ค่ะ
📞 สายด่วนสุขภาพ: 1330"""

    def _get_default_message(self) -> str:
        """Get default message for unrecognized input"""
        return """ขออภัยค่ะ ไม่พบข้อมูลที่ตรงกับคำถาม

ลองถามใหม่ เช่น:
• "PM2.5 คืออะไร"
• "หน้ากากแบบไหนดี"
• "กลุ่มเสี่ยงมีใครบ้าง"
• "วิธีลดฝุ่นในบ้าน"

หรือพิมพ์ 'ตรวจสอบค่าฝุ่น' หรือ 'ประเมินอาการ' ค่ะ"""

    def _get_location_request_message(self) -> str:
        """Get message asking user to share location"""
        return """📍 กรุณาแชร์ตำแหน่งที่ตั้งของคุณค่ะ

วิธีแชร์ตำแหน่ง:
1. กดปุ่ม + ที่มุมล่างซ้าย
2. เลือก "ตำแหน่ง" (Location)
3. เลือกตำแหน่งปัจจุบันหรือค้นหาสถานที่
4. กด "แชร์" (Share)

พิมพ์ 'ยกเลิก' เพื่อยกเลิกค่ะ"""

    async def handle_location(self, user_id: str, latitude: float, longitude: float) -> str:
        """Handle location message from user"""
        session = self.state_manager.get_session(user_id)

        # Reset state
        session.state = ConversationState.IDLE
        self.state_manager.update_session(session)

        # Get dust report for the location
        return await self.dust_service.get_dust_report_by_location(latitude, longitude)


# Singleton instance
_message_handler: Optional[MessageHandler] = None


def get_message_handler() -> MessageHandler:
    """Get singleton message handler"""
    global _message_handler
    if _message_handler is None:
        _message_handler = MessageHandler()
    return _message_handler
