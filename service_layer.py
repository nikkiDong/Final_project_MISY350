"""
Service / Business-Logic Layer — validation, domain objects, AI assistant.

This module contains:
  - OOP model classes  (User, Patient, Doctor, Appointment)
  - Validation helpers
  - AI assistant class that connects to OpenAI
  - Pure functions for business rules (no Streamlit imports)
"""

from __future__ import annotations

import hashlib
import re
import uuid
from datetime import datetime


# ── Constants ────────────────────────────────────────────────────────────────
CLINIC_ID = "ClearVision-01"
APPOINTMENT_TYPES = [
    "Routine Vision Check",
    "Glaucoma Screening",
    "Fundus Exam",
    "Cataract Evaluation",
    "Retinal Exam",
]
APPT_STATUSES = ["Scheduled", "Completed", "No-Show", "Cancelled"]

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


# ── Utility functions ────────────────────────────────────────────────────────
def hash_password(pw: str) -> str:
    """Return the SHA-256 hex digest of a password string."""
    return hashlib.sha256(pw.encode()).hexdigest()


def normalise_email(email: str) -> str:
    return email.strip().lower()


def is_valid_email(email: str) -> bool:
    return bool(_EMAIL_RE.match(normalise_email(email)))


def format_date(date_str: str) -> str:
    """Turn '2026-05-10' into 'May 10, 2026'."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%b %d, %Y")
    except Exception:
        return date_str


# ═══════════════════════════════════════════════════════════════════════════════
#  OOP MODEL CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

class User:
    """Base class for all users (Patient and Doctor)."""

    def __init__(self, user_id: str, name: str, email: str, password_hash: str, role: str):
        self.user_id = user_id
        self.name = name
        self.email = normalise_email(email)
        self.password_hash = password_hash
        self.role = role

    def check_password(self, plain_password: str) -> bool:
        return self.password_hash == hash_password(plain_password)

    def can_access_page(self, required_role: str) -> bool:
        return self.role == required_role

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "email": self.email,
            "password": self.password_hash,
        }


class Patient(User):
    """A patient who books and manages appointments."""

    def __init__(self, patient_id: str, name: str, email: str, password_hash: str):
        super().__init__(patient_id, name, email, password_hash, role="Patient")
        self.patient_id = patient_id

    def to_dict(self) -> dict:
        base = super().to_dict()
        base["patient_id"] = self.patient_id
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "Patient":
        return cls(
            patient_id=data.get("patient_id", ""),
            name=data.get("name", ""),
            email=data.get("email", ""),
            password_hash=data.get("password", ""),
        )

    @classmethod
    def create_new(cls, name: str, email: str, plain_password: str) -> "Patient":
        return cls(
            patient_id=f"pat_{uuid.uuid4().hex[:8]}",
            name=name.strip(),
            email=normalise_email(email),
            password_hash=hash_password(plain_password),
        )


class Doctor(User):
    """A doctor who manages slots and updates appointment statuses."""

    def __init__(self, doctor_id: str, name: str, email: str,
                 password_hash: str, specialty: str, available_slots: list[str] | None = None):
        super().__init__(doctor_id, name, email, password_hash, role="Doctor")
        self.doctor_id = doctor_id
        self.specialty = specialty
        self.available_slots: list[str] = available_slots or []

    def add_slot(self, slot: str) -> bool:
        if slot not in self.available_slots:
            self.available_slots.append(slot)
            return True
        return False

    def remove_slot(self, slot: str) -> bool:
        if slot in self.available_slots:
            self.available_slots.remove(slot)
            return True
        return False

    def to_dict(self) -> dict:
        base = super().to_dict()
        base["doctor_id"] = self.doctor_id
        base["specialty"] = self.specialty
        base["available_slots"] = self.available_slots
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "Doctor":
        return cls(
            doctor_id=data.get("doctor_id", ""),
            name=data.get("name", ""),
            email=data.get("email", ""),
            password_hash=data.get("password", ""),
            specialty=data.get("specialty", "General"),
            available_slots=list(data.get("available_slots", [])),
        )

    @classmethod
    def create_new(cls, name: str, email: str, plain_password: str, specialty: str) -> "Doctor":
        return cls(
            doctor_id=f"doc_{uuid.uuid4().hex[:8]}",
            name=name.strip(),
            email=normalise_email(email),
            password_hash=hash_password(plain_password),
            specialty=specialty.strip(),
            available_slots=[],
        )


class Appointment:
    """Represents a single appointment record."""

    def __init__(self, data: dict):
        self._data = data

    # ── Convenience accessors ────────────────────────────────────────────
    @property
    def appointment_id(self) -> str:
        return self._data.get("appointment_id", "")

    @property
    def patient_email(self) -> str:
        return normalise_email(self._data.get("patient_email", ""))

    @property
    def doctor_id(self) -> str:
        return self._data.get("doctor_id", "")

    @property
    def status(self) -> str:
        return self._data.get("status", "Scheduled")

    @property
    def appointment_date(self) -> str:
        return self._data.get("appointment_date", "")

    @property
    def appointment_time(self) -> str:
        return self._data.get("appointment_time", "")

    # ── Mutations ────────────────────────────────────────────────────────
    def update_status(self, new_status: str, note: str = ""):
        self._data["status"] = new_status
        self._data["doctor_note"] = note

    def reschedule(self, new_date: str, new_time: str):
        self._data["appointment_date"] = new_date
        self._data["appointment_time"] = new_time

    def cancel(self):
        self._data["status"] = "Cancelled"

    def to_dict(self) -> dict:
        return self._data

    @classmethod
    def create_new(cls, patient_name: str, patient_email: str,
                   doctor: Doctor, slot: str, appt_type: str,
                   symptoms: str) -> "Appointment":
        date, time = slot.split("T")
        return cls({
            "appointment_id": f"appt-{uuid.uuid4().hex[:8]}",
            "clinic_id": CLINIC_ID,
            "patient_name": patient_name,
            "patient_email": normalise_email(patient_email),
            "doctor_id": doctor.doctor_id,
            "doctor_name": doctor.name,
            "appointment_date": date,
            "appointment_time": time,
            "submitted_timestamp": datetime.now().isoformat(),
            "appointment_type": appt_type,
            "symptom_summary": symptoms,
            "status": "Scheduled",
            "doctor_note": "",
        })


# ═══════════════════════════════════════════════════════════════════════════════
#  VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════

def validate_registration(name: str, email: str, password: str,
                          confirm: str, existing_emails: list[str]) -> list[str]:
    """Return a list of error strings; empty list means valid."""
    errors: list[str] = []
    email = normalise_email(email)

    if not name.strip():
        errors.append("Full Name is required.")
    if not is_valid_email(email):
        errors.append("Please enter a valid email address.")
    elif email in existing_emails:
        errors.append("An account with this email already exists.")
    if not password.strip():
        errors.append("Password is required.")
    elif len(password) < 6:
        errors.append("Password must be at least 6 characters.")
    if password != confirm:
        errors.append("Passwords do not match.")
    return errors


def validate_booking(doctor: Doctor | None, appt_type: str,
                     symptoms: str, slot: str | None) -> list[str]:
    errors: list[str] = []
    if not doctor:
        errors.append("Please select a doctor.")
    if appt_type == "— Select appointment type —":
        errors.append("Appointment Type is required.")
    if not symptoms.strip():
        errors.append("Please describe your symptoms.")
    elif len(symptoms.strip()) < 10:
        errors.append("Symptom description is too short (min 10 characters).")
    if not slot:
        errors.append("No available time slots — please ask your doctor to add some.")
    return errors


# ═══════════════════════════════════════════════════════════════════════════════
#  QUERY HELPERS  (pure functions — no Streamlit)
# ═══════════════════════════════════════════════════════════════════════════════

def find_patient_by_email(patients: list[dict], email: str) -> dict | None:
    e = normalise_email(email)
    return next((p for p in patients if normalise_email(p.get("email", "")) == e), None)


def find_doctor_by_email(doctors: list[dict], email: str) -> dict | None:
    e = normalise_email(email)
    return next((d for d in doctors if normalise_email(d.get("email", "")) == e), None)


def find_doctor_by_id(doctors: list[dict], doctor_id: str) -> dict | None:
    return next((d for d in doctors if d.get("doctor_id") == doctor_id), None)


def find_appointment_by_id(appointments: list[dict], aid: str) -> dict | None:
    return next((a for a in appointments if a.get("appointment_id") == aid), None)


def filter_appointments_by_patient(appointments: list[dict], email: str) -> list[dict]:
    e = normalise_email(email)
    return [a for a in appointments if normalise_email(a.get("patient_email", "")) == e]


def filter_appointments_by_doctor(appointments: list[dict], doctor_id: str) -> list[dict]:
    return [a for a in appointments if a.get("doctor_id") == doctor_id]


def filter_scheduled_appointments(appointments: list[dict], email: str) -> list[dict]:
    return [a for a in filter_appointments_by_patient(appointments, email)
            if a.get("status") == "Scheduled"]


# ═══════════════════════════════════════════════════════════════════════════════
#  AI ASSISTANT (OpenAI)
# ═══════════════════════════════════════════════════════════════════════════════

class AIChatAssistant:
    """
    An AI assistant powered by OpenAI that helps users with
    appointment-related questions inside ClearVision Clinic.
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self._client = None

    def _get_client(self):
        """Lazily initialise the OpenAI client."""
        if self._client is None and self.api_key:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except Exception:
                self._client = None
        return self._client

    def _build_system_prompt(self, context: str) -> str:
        return (
            "You are the ClearVision Clinic AI assistant — an ophthalmology "
            "appointment portal helper. Be concise, friendly, and helpful. "
            "Answer questions about appointments, available time slots, "
            "eye-care preparation tips, and general clinic information.\n\n"
            "Here is the current context about the user and their data:\n"
            f"{context}\n\n"
            "If you don't know something, say so politely. "
            "Never make up appointment details that are not in the context."
        )

    def build_context(self, appointments: list[dict], doctors: list[dict],
                      user_email: str, role: str = "Patient",
                      doctor_id: str = "") -> str:
        """Prepare a concise summary of user data for the AI system prompt."""
        lines: list[str] = []

        if role == "Doctor" and doctor_id:
            # Doctor context: show their assigned appointments
            my_appts = filter_appointments_by_doctor(appointments, doctor_id)
            scheduled = [a for a in my_appts if a.get("status") == "Scheduled"]
            completed = [a for a in my_appts if a.get("status") == "Completed"]

            lines.append(f"Doctor email: {user_email}")
            lines.append(f"Your assigned appointments: {len(my_appts)} total "
                         f"({len(scheduled)} scheduled, {len(completed)} completed)")

            if scheduled:
                lines.append("Upcoming scheduled appointments:")
                for a in scheduled:
                    lines.append(
                        f"  - {format_date(a['appointment_date'])} at {a['appointment_time']} "
                        f"— Patient: {a.get('patient_name','N/A')} "
                        f"({a.get('appointment_type','N/A')})")
        else:
            # Patient context
            my_appts = filter_appointments_by_patient(appointments, user_email)
            scheduled = [a for a in my_appts if a.get("status") == "Scheduled"]
            completed = [a for a in my_appts if a.get("status") == "Completed"]

            lines.append(f"Patient email: {user_email}")
            lines.append(f"Total appointments: {len(my_appts)} "
                         f"({len(scheduled)} scheduled, {len(completed)} completed)")

            if scheduled:
                lines.append("Upcoming appointments:")
                for a in scheduled:
                    lines.append(
                        f"  - {format_date(a['appointment_date'])} at {a['appointment_time']} "
                        f"with Dr. {a.get('doctor_name','N/A')} "
                        f"({a.get('appointment_type','N/A')})")

        avail = []
        for d in doctors:
            for s in d.get("available_slots", []):
                avail.append(f"  - Dr. {d['name']} ({d.get('specialty','General')}): "
                             f"{s.replace('T', ' at ')}")
        if avail:
            lines.append("Available slots:")
            lines.extend(avail)

        return "\n".join(lines)

    def generate_response(self, user_message: str, context: str,
                          chat_history: list[dict] | None = None) -> str:
        """
        Send the user's message to OpenAI and return the assistant reply.
        Falls back to a simple keyword-based response if the API key is
        missing or the call fails.
        """
        client = self._get_client()
        if client is None:
            return self._fallback_response(user_message, context)

        messages = [{"role": "system", "content": self._build_system_prompt(context)}]

        # Include recent chat history for continuity (last 10 turns)
        if chat_history:
            for msg in chat_history[-10:]:
                if msg["role"] in ("user", "assistant"):
                    messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": user_message})

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=500,
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception as exc:
            return f"Sorry, I encountered an error: {exc}"

    # ── Fallback (no API key) ────────────────────────────────────────────
    @staticmethod
    def _fallback_response(question: str, context: str) -> str:
        q = question.lower()
        if "next appointment" in q or "upcoming" in q:
            for line in context.split("\n"):
                if line.strip().startswith("- ") and "Scheduled" not in line:
                    continue
                if "at " in line and "Dr." in line:
                    return f"Your next appointment: {line.strip().lstrip('- ')}"
            return "You have no upcoming appointments."
        if "slot" in q or "available" in q:
            slots = [l.strip() for l in context.split("\n") if l.strip().startswith("- Dr.")]
            if slots:
                return "Available slots:\n" + "\n".join(slots)
            return "No available time slots right now."
        if "cancel" in q:
            return ("To cancel an appointment: go to Book Appointment page → "
                    "Cancel tab → select your appointment → click Cancel.")
        if "prepare" in q or "exam" in q or "tip" in q:
            return ("Exam preparation tips:\n"
                    "• Bring your insurance card and photo ID\n"
                    "• Avoid wearing contacts 24 h before retinal/fundus exams\n"
                    "• Arrange a ride home if dilation drops will be used\n"
                    "• Bring a list of current medications")
        if "doctor" in q:
            docs = [l.strip() for l in context.split("\n") if "Dr." in l and "specialty" not in l.lower()]
            if docs:
                return "Our doctors:\n" + "\n".join(docs[:6])
        return ("I can help with: upcoming appointments, available slots, "
                "cancellation steps, exam preparation tips, and doctor info. "
                "Just ask!")
