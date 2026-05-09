# 👁️ ClearVision Clinic — Ophthalmology Appointment Tracker

A full-stack patient appointment management portal for a multi-doctor ophthalmology clinic. Built as a two-phase academic project covering CRUD operations, role-based access, simulated AI, and real LLM integration.

---

## 📋 Project Overview

ClearVision Clinic is a scheduling portal that allows doctors to manage their availability and appointment statuses, while patients can book, reschedule, or cancel visits — all within a clean, role-aware interface tailored to ophthalmology workflows.

**Key differentiators from a generic appointment system:**
- Appointment types specific to eye care (routine vision check, glaucoma screening, fundus exam, etc.)
- Symptom intake form designed around common ophthalmic complaints (blurred vision, eye pain, floaters, photophobia)
- Follow-up reminder logic that suggests rechecks based on examination type

---

## 👥 User Roles

| Role | Permissions |
|---|---|
| **Doctor / Clinic Admin** | Create & delete time slots, view daily patient roster, update appointment status |
| **Patient** | Register & log in, browse open slots, book / cancel / reschedule appointments |

---

## 🗂️ Features

### Phase 1 — MVP (CRUD + Simulated AI)

**Doctor / Admin**
- Create and remove available time slots
- View the full daily patient roster
- Update appointment status: `Scheduled` → `Completed` or `No-Show`

**Patient**
- Register and log in with email
- Browse available slots filtered by doctor or date
- Book a specific time slot and receive a digital confirmation
- Cancel or reschedule an existing appointment
- Receive automated follow-up reminders based on exam type

**Simulated AI Chatbot** (5 hardcoded responses)

| Patient asks | System response |
|---|---|
| "When is my next appointment?" | Matches email to schedule, returns date & time |
| "What slots are available today?" | Filters and returns unclaimed time slots |
| "How do I cancel my appointment?" | Returns step-by-step instructions |
| "Which doctors are available?" | Lists doctors with open slots |
| "What should I prepare for my exam?" | Returns exam-specific preparation notes |

### Phase 2 — AI Integration & Scaling

**Real AI Clinic Assistant (LLM API)**
- Before booking, patients describe their symptoms in natural language (e.g., "my vision has been blurry on the left side and I've been seeing floaters")
- The LLM generates a concise, professional clinical brief
- The brief is automatically attached to the appointment record so the doctor is prepared before the patient arrives

**Additional Phase 2 improvements**
- OOP refactoring: `Doctor`, `Patient`, `Appointment`, and `TimeSlot` classes
- UI iteration based on peer feedback
- Intelligent follow-up reminders: AI suggests optimal recheck intervals based on exam type (e.g., 3 months for glaucoma patients)

---

## 🗃️ Data Model

```json
// Doctor
{
  "id": "doc_01",
  "name": "Dr. Sarah Chen",
  "specialty": "Retinal Disease",
  "available_slots": ["2025-08-01T09:00", "2025-08-01T10:30"]
}

// Patient
{
  "id": "pat_42",
  "name": "James Lee",
  "email": "james@email.com",
  "symptom_notes": "Blurry vision and eye pain for 3 days",
  "appointment_history": []
}

// Appointment
{
  "id": "appt_99",
  "patient_id": "pat_42",
  "doctor_id": "doc_01",
  "datetime": "2025-08-01T09:00",
  "exam_type": "Glaucoma Screening",
  "status": "Scheduled",
  "ai_brief": "Patient reports 3-day onset of blurred vision and periocular pain..."
}
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML / CSS / JavaScript (or React) |
| Backend | Python — Flask or FastAPI |
| Database | JSON flat files (Phase 1) → SQLite (Phase 2) |
| AI — Phase 1 | Hardcoded conditional responses |
| AI — Phase 2 | Claude API or OpenAI API |
| Auth | Session-based login with hashed passwords |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js (if using React frontend)
- An API key from [Anthropic](https://www.anthropic.com) or [OpenAI](https://openai.com) *(Phase 2 only)*

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/clearvision-clinic.git
cd clearvision-clinic

# Install Python dependencies
pip install -r requirements.txt

# Run the development server
python app.py
```

The app will be available at `http://localhost:5000`.

### Environment Variables

Create a `.env` file in the root directory:

```env
SECRET_KEY=your_secret_key_here
AI_API_KEY=your_api_key_here        # Phase 2 only
AI_MODEL=claude-sonnet-4-20250514   # or gpt-4o
```

---

## 📁 Project Structure

```
clearvision-clinic/
├── app.py                  # Main application entry point
├── requirements.txt
├── .env.example
│
├── data/                   # JSON data files (Phase 1)
│   ├── doctors.json
│   ├── patients.json
│   └── appointments.json
│
├── models/                 # OOP classes (Phase 2)
│   ├── doctor.py
│   ├── patient.py
│   └── appointment.py
│
├── routes/
│   ├── auth.py             # Login / register
│   ├── doctor.py           # Doctor CRUD routes
│   ├── patient.py          # Patient CRUD routes
│   └── chatbot.py          # AI assistant routes
│
├── static/
│   └── css/
│       └── style.css
│
└── templates/
    ├── login.html
    ├── dashboard_doctor.html
    ├── dashboard_patient.html
    └── chatbot.html
```

---

## 🔮 Roadmap

- [x] Phase 1: CRUD for both roles
- [x] Phase 1: Simulated chatbot (5 responses)
- [x] Phase 1: Follow-up reminder system
- [ ] Phase 2: LLM-powered symptom intake & clinical brief generation
- [ ] Phase 2: OOP model refactoring
- [ ] Phase 2: UI redesign based on peer feedback
- [ ] Phase 2: AI-suggested follow-up intervals by exam type

---

## 📄 License

This project was developed as an academic capstone. Feel free to fork and build on it.
# Final_project_MISY350
