"""Health assessment questions for PM2.5/pollution symptoms"""

from typing import List, Dict

# Symptom questions with Thai text
SYMPTOM_QUESTIONS: List[Dict] = [
    {
        "id": "cough",
        "question": "ท่านมีอาการไอหรือไม่คะ?",
        "options": [
            {"label": "1. ไม่มี", "value": "none", "score": 0},
            {"label": "2. มีเล็กน้อย", "value": "mild", "score": 1},
            {"label": "3. มีมาก", "value": "severe", "score": 2},
        ]
    },
    {
        "id": "breathing",
        "question": "ท่านมีอาการหายใจลำบาก แน่นหน้าอก หรือหอบเหนื่อยหรือไม่คะ?",
        "options": [
            {"label": "1. ไม่มี", "value": "none", "score": 0},
            {"label": "2. มีเล็กน้อย", "value": "mild", "score": 1},
            {"label": "3. มีมาก", "value": "severe", "score": 2},
        ]
    },
    {
        "id": "eyes",
        "question": "ท่านมีอาการระคายเคืองตา แสบตา หรือน้ำตาไหลหรือไม่คะ?",
        "options": [
            {"label": "1. ไม่มี", "value": "none", "score": 0},
            {"label": "2. มีเล็กน้อย", "value": "mild", "score": 1},
            {"label": "3. มีมาก", "value": "severe", "score": 2},
        ]
    },
    {
        "id": "nose",
        "question": "ท่านมีอาการคัดจมูก น้ำมูกไหล หรือจามหรือไม่คะ?",
        "options": [
            {"label": "1. ไม่มี", "value": "none", "score": 0},
            {"label": "2. มีเล็กน้อย", "value": "mild", "score": 1},
            {"label": "3. มีมาก", "value": "severe", "score": 2},
        ]
    },
    {
        "id": "skin",
        "question": "ท่านมีอาการผื่นคัน หรือระคายเคืองผิวหนังหรือไม่คะ?",
        "options": [
            {"label": "1. ไม่มี", "value": "none", "score": 0},
            {"label": "2. มีเล็กน้อย", "value": "mild", "score": 1},
            {"label": "3. มีมาก", "value": "severe", "score": 2},
        ]
    },
    {
        "id": "headache",
        "question": "ท่านมีอาการปวดศีรษะ มึนงง หรือเวียนศีรษะหรือไม่คะ?",
        "options": [
            {"label": "1. ไม่มี", "value": "none", "score": 0},
            {"label": "2. มีเล็กน้อย", "value": "mild", "score": 1},
            {"label": "3. มีมาก", "value": "severe", "score": 2},
        ]
    },
]

# Risk factor questions
RISK_QUESTIONS: List[Dict] = [
    {
        "id": "age",
        "question": "ท่านอายุอยู่ในช่วงใดคะ?",
        "options": [
            {"label": "1. ต่ำกว่า 18 ปี", "value": "child", "score": 1},
            {"label": "2. 18-60 ปี", "value": "adult", "score": 0},
            {"label": "3. มากกว่า 60 ปี", "value": "elderly", "score": 2},
        ]
    },
    {
        "id": "condition",
        "question": "ท่านมีโรคประจำตัวหรือไม่คะ?",
        "options": [
            {"label": "1. ไม่มี", "value": "none", "score": 0},
            {"label": "2. โรคหอบหืด/ภูมิแพ้", "value": "asthma", "score": 2},
            {"label": "3. โรคหัวใจ", "value": "heart", "score": 2},
            {"label": "4. โรคปอด/ถุงลมโป่งพอง", "value": "lung", "score": 2},
            {"label": "5. อื่นๆ", "value": "other", "score": 1},
        ]
    },
    {
        "id": "outdoor",
        "question": "ท่านต้องทำงานหรือใช้เวลากลางแจ้งเป็นประจำหรือไม่คะ?",
        "options": [
            {"label": "1. ไม่ใช่", "value": "no", "score": 0},
            {"label": "2. ใช่", "value": "yes", "score": 1},
        ]
    },
]

# All questions combined
ALL_QUESTIONS = SYMPTOM_QUESTIONS + RISK_QUESTIONS

# Helper to get question by index
def get_question(index: int) -> Dict:
    if 0 <= index < len(ALL_QUESTIONS):
        return ALL_QUESTIONS[index]
    return None

def get_total_questions() -> int:
    return len(ALL_QUESTIONS)
