# Health Line Chatbot - Pre-Diagnosis & Symptom Assessment

## Overview
A Line chatbot that helps users assess their health symptoms related to air pollution (PM2.5) and provides pre-diagnosis recommendations, similar to https://pollutionclinic.nopparat.go.th/

## Features

### 1. Symptom Assessment Flow
- Ask questions about symptoms (cough, breathing difficulty, eye irritation, etc.)
- Collect risk factors (outdoor worker, existing conditions, age)
- Calculate risk level based on answers

### 2. Pre-Diagnosis
- Low/Medium/High risk classification
- Recommendations based on severity
- When to see a doctor

### 3. FAQ
- Common questions about PM2.5 health effects
- Prevention tips
- Mask recommendations

### 4. Air Quality Info (Optional)
- Current AQI for user's location
- Health recommendations based on AQI level

---

## Conversation Flow

```
User: สวัสดีค่ะ / เริ่มตรวจ / ประเมินอาการ

Bot: สวัสดีค่ะ 🏥 ยินดีต้อนรับสู่ระบบประเมินสุขภาพเบื้องต้นค่ะ
     กรุณาเลือกบริการ:
     1. ประเมินอาการจากมลพิษ
     2. ความรู้เรื่อง PM2.5
     3. คำถามที่พบบ่อย

User: 1

Bot: เริ่มการประเมินอาการค่ะ 📋

     คำถามที่ 1/6:
     ท่านมีอาการไอหรือไม่คะ?
     1. ไม่มี
     2. มีเล็กน้อย
     3. มีมาก

User: 2

Bot: คำถามที่ 2/6:
     ท่านมีอาการหายใจลำบากหรือไม่คะ?
     1. ไม่มี
     2. มีเล็กน้อย
     3. มีมาก

... (continue questions)

Bot: 📊 ผลการประเมินเบื้องต้น:

     ระดับความเสี่ยง: ปานกลาง 🟡

     คำแนะนำ:
     - หลีกเลี่ยงการออกกำลังกายกลางแจ้ง
     - สวมหน้ากาก N95 เมื่อออกนอกบ้าน
     - หากอาการแย่ลง ควรพบแพทย์

     ⚠️ นี่เป็นการประเมินเบื้องต้นเท่านั้น
     ไม่สามารถใช้แทนการวินิจฉัยจากแพทย์ได้ค่ะ
```

---

## Technical Architecture

```
┌─────────────────┐      ┌──────────────────────┐
│   Line App      │ ───► │  FastAPI Webhook     │
│  (Users)        │ ◄─── │  + State Machine     │
└─────────────────┘      └──────────────────────┘
                                   │
                                   ▼
                         ┌──────────────────────┐
                         │  Questionnaire       │
                         │  Engine              │
                         │  (Pattern Matching)  │
                         └──────────────────────┘
```

## Assessment Questions

### Symptom Questions (6 questions)
1. **ไอ (Cough)**: ไม่มี / เล็กน้อย / มาก
2. **หายใจลำบาก (Breathing difficulty)**: ไม่มี / เล็กน้อย / มาก
3. **ระคายเคืองตา (Eye irritation)**: ไม่มี / เล็กน้อย / มาก
4. **คัดจมูก/น้ำมูกไหล (Nasal congestion)**: ไม่มี / เล็กน้อย / มาก
5. **ผื่นผิวหนัง (Skin rash)**: ไม่มี / เล็กน้อย / มาก
6. **ปวดศีรษะ (Headache)**: ไม่มี / เล็กน้อย / มาก

### Risk Factor Questions (3 questions)
1. **อายุ**: <18 / 18-60 / >60
2. **โรคประจำตัว**: ไม่มี / หอบหืด / โรคหัวใจ / โรคปอด / อื่นๆ
3. **ทำงานกลางแจ้ง**: ใช่ / ไม่ใช่

### Scoring
- Each symptom: None=0, Mild=1, Severe=2
- Risk factors add bonus points
- Total score → Risk level:
  - 0-4: Low (Green) 🟢
  - 5-9: Medium (Yellow) 🟡
  - 10+: High (Red) 🔴

---

## Project Structure

```
health-chatbot/
├── main.py                 # FastAPI entry point
├── config.py               # Environment settings
├── requirements.txt        # Dependencies
├── .env.example
├── handlers/
│   ├── __init__.py
│   └── message_handler.py  # Line message processing
├── services/
│   ├── __init__.py
│   ├── assessment_service.py   # Questionnaire logic
│   └── state_manager.py        # User session state
├── data/
│   ├── questions.py        # Question definitions
│   ├── recommendations.py  # Recommendations by risk level
│   └── faq.py              # FAQ data
└── models/
    ├── __init__.py
    └── schemas.py          # Pydantic models
```

---

## Dependencies

```
fastapi>=0.104.0
uvicorn>=0.24.0
line-bot-sdk>=3.5.0
httpx>=0.25.0
python-dotenv>=1.0.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
```

---

## Implementation Steps

1. Create project structure
2. Define questions and scoring system
3. Implement state machine for conversation flow
4. Implement assessment scoring logic
5. Create Line webhook handler
6. Add FAQ functionality
7. Test and refine Thai language responses

---

## Future Enhancements

- [ ] Integrate real-time AQI API
- [ ] Add location-based recommendations
- [ ] Store assessment history
- [ ] Connect to actual clinic appointment system
- [ ] Add symptom tracking over time
