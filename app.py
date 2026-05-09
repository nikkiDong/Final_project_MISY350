"""
ClearVision Clinic — Ophthalmology Appointment Portal
======================================================
UI Layer (Streamlit)

All data persistence is handled by  data_layer.py   (DataManager).
All business logic is handled by    service_layer.py (classes & functions).
This file contains ONLY the Streamlit interface code.
"""

from __future__ import annotations

import os

import streamlit as st
from dotenv import load_dotenv

# Load OPENAI_API_KEY (and any other env vars) from a local .env file if present.
load_dotenv()

# ── Import layers ────────────────────────────────────────────────────────────
from data_layer import DataManager, PATH_APPOINTMENTS, PATH_DOCTORS, PATH_PATIENTS
from service_layer import (
    APPOINTMENT_TYPES, APPT_STATUSES,
    Patient, Doctor, Appointment, AIChatAssistant,
    validate_registration, validate_booking,
    normalise_email, is_valid_email, hash_password, format_date,
    find_patient_by_email, find_doctor_by_email, find_doctor_by_id,
    find_appointment_by_id, filter_appointments_by_patient,
    filter_appointments_by_doctor, filter_scheduled_appointments,
)

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ClearVision Clinic",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Test account credentials (shown on login page) ──────────────────────────
TEST_ACCOUNTS = {
    "Patient": {"email": "james@email.com",    "password": "pass123"},
    "Doctor":  {"email": "dr.chen@clinic.com",  "password": "pass123"},
}

# ── Session defaults ─────────────────────────────────────────────────────────
_SESSION_DEFAULTS = {
    "logged_in": False,
    "role": None,
    "current_user_name": None,
    "current_user_email": None,
    "current_doctor_id": None,
    "page": "login",
    "selected_appointment_id": None,
    "_reg_success": None,
    "messages": [
        {"role": "assistant",
         "content": "Hi! I'm the ClearVision Clinic AI assistant. "
                    "Ask me about appointments, available slots, exam tips, or anything else!"}
    ],
}
for _k, _v in _SESSION_DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ── AI assistant (initialised once) ─────────────────────────────────────────
@st.cache_resource
def get_ai_assistant():
    """
    Create a single AIChatAssistant.

    Looks for the OpenAI key in this order:
      1. .env  / OS environment variable  OPENAI_API_KEY
      2. Streamlit secrets (.streamlit/secrets.toml)
    Falls back to the rule-based assistant if no key is found.
    """
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        try:
            key = st.secrets["OPENAI_API_KEY"]
        except Exception:
            key = None
    return AIChatAssistant(api_key=key)

ai_assistant = get_ai_assistant()

# ── Global CSS ───────────────────────────────────────────────────────────────
st.markdown("""<style>
.section-header{font-size:1.3rem;font-weight:600;color:#1565c0;border-bottom:3px solid #1565c0;padding-bottom:.4rem;margin-bottom:1.2rem}
.status-scheduled{background:#d4edda;color:#155724;padding:.25rem .55rem;border-radius:.25rem;font-weight:600;font-size:.82rem}
.status-completed{background:#cfe2ff;color:#084298;padding:.25rem .55rem;border-radius:.25rem;font-weight:600;font-size:.82rem}
.status-cancelled{background:#f8d7da;color:#842029;padding:.25rem .55rem;border-radius:.25rem;font-weight:600;font-size:.82rem}
.status-no-show{background:#fff3cd;color:#664d03;padding:.25rem .55rem;border-radius:.25rem;font-weight:600;font-size:.82rem}
.slot-card{background:#f8f9fa;border:1px solid #dee2e6;border-radius:.5rem;padding:1rem;margin-bottom:.75rem;box-shadow:0 1px 2px rgba(0,0,0,.05)}
.slot-card-date{font-weight:600;color:#1565c0}
.slot-card-time{color:#495057;font-size:.95rem}
.appt-card{background:#fff;border:1px solid #dee2e6;border-radius:.5rem;padding:1rem 1.25rem;margin-bottom:.6rem;box-shadow:0 1px 3px rgba(0,0,0,.06)}
.appt-card-type{font-size:1rem;font-weight:600;color:#212529}
.appt-card-meta{color:#6c757d;font-size:.85rem;margin-top:.3rem}
.test-box{background:#e3f2fd;border:1px solid #90caf9;border-radius:.5rem;padding:.75rem 1rem;font-size:.85rem;margin-top:.75rem}
.clinic-footer{text-align:center;padding:2rem 0 1rem;border-top:1px solid #e0e0e0;color:#6c757d;font-size:.85rem}
div[data-testid="stMetric"]{padding:.5rem 0}
.stTabs [data-baseweb="tab-panel"]{padding-top:1rem}
</style>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  UI HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

_STATUS_CSS = {
    "Scheduled": "status-scheduled", "Completed": "status-completed",
    "Cancelled": "status-cancelled",  "No-Show":   "status-no-show",
}

def status_badge(status: str) -> str:
    return f'<span class="{_STATUS_CSS.get(status, "status-scheduled")}">{status}</span>'

def show_errors(errors: list[str]):
    if errors:
        st.error("Please fix the following:\n" + "\n".join(f"• {e}" for e in errors))

def show_success(msg: str):
    st.success(f"✅ {msg}")

def render_appt_cards(appointments: list[dict]):
    """Display appointments as styled cards."""
    for a in appointments:
        booked = a.get("submitted_timestamp", "")[:10] if a.get("submitted_timestamp") else "—"
        st.markdown(f"""
        <div class="appt-card">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <span class="appt-card-type">{a.get('appointment_type','N/A')}</span>
            {status_badge(a.get('status','Scheduled'))}
          </div>
          <div class="appt-card-meta">
            📅 {format_date(a.get('appointment_date',''))} &nbsp;·&nbsp;
            ⏰ {a.get('appointment_time','')} &nbsp;·&nbsp;
            🩺 Dr. {a.get('doctor_name','N/A')} &nbsp;·&nbsp;
            👤 {a.get('patient_name','N/A')}
          </div>
          <div style="color:#adb5bd;font-size:.78rem;margin-top:.2rem;">
            ID: {a.get('appointment_id','')} &nbsp;·&nbsp; Booked: {booked}
          </div>
        </div>""", unsafe_allow_html=True)

def appt_selectbox(label: str, appointments: list[dict], key: str):
    """Selectbox for choosing an appointment; stores selection in session."""
    lbl_to_id = {
        f"{format_date(a.get('appointment_date','?'))}  {a.get('appointment_time','')}  |  "
        f"{a.get('appointment_type','?')}  |  {a.get('status','?')}": a.get("appointment_id", "")
        for a in appointments
    }
    cur_id  = st.session_state.get("selected_appointment_id")
    cur_lbl = next((l for l, i in lbl_to_id.items() if i == cur_id), None)
    options = ["— Select an appointment —"] + list(lbl_to_id)
    chosen  = st.selectbox(label, options,
                           index=options.index(cur_lbl) if cur_lbl in options else 0,
                           key=key)
    st.session_state["selected_appointment_id"] = (
        None if chosen == options[0] else lbl_to_id[chosen]
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  NAVIGATION HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def reset_session():
    st.session_state.update(_SESSION_DEFAULTS)

def nav(page: str):
    st.session_state["page"] = page
    st.session_state["selected_appointment_id"] = None
    st.rerun()

def require_role(role: str) -> bool:
    if st.session_state.get("logged_in") and st.session_state.get("role") == role:
        return True
    nav("login")
    return False


# ═══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════

def render_sidebar():
    role = st.session_state.get("role", "")
    with st.sidebar:
        st.markdown("## 👁️ ClearVision Clinic")
        st.divider()
        icon = "🩺" if role == "Doctor" else "👤"
        st.markdown(f"{icon} **{st.session_state.get('current_user_name', 'User')}**")
        st.caption(f"Role: {role}")
        st.divider()

        if role == "Patient":
            if st.button("🏠 My Appointments", key="nav_pat_dash", use_container_width=True):
                nav("patient_dashboard")
            if st.button("📅 Book Appointment", key="nav_pat_book", use_container_width=True):
                nav("patient_book")
            if st.button("🤖 AI Assistant", key="nav_pat_ai", use_container_width=True):
                nav("patient_ai")
        elif role == "Doctor":
            if st.button("📊 Dashboard", key="nav_doc_dash", use_container_width=True):
                nav("doctor_dashboard")
            if st.button("⏰ Manage Slots", key="nav_doc_slots", use_container_width=True):
                nav("doctor_slots")
            if st.button("🤖 AI Assistant", key="nav_doc_ai", use_container_width=True):
                nav("doctor_ai")
        st.divider()
        if st.button("🚪 Log Out", key="sidebar_logout", use_container_width=True):
            reset_session()
            nav("login")


# ═══════════════════════════════════════════════════════════════════════════════
#  LOGIN / REGISTRATION PAGE
# ═══════════════════════════════════════════════════════════════════════════════

def render_login(all_patients: list[dict], all_doctors: list[dict]):
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("<h1 style='text-align:center;'>👁️ ClearVision Clinic</h1>",
                    unsafe_allow_html=True)
        st.markdown("<p style='text-align:center;color:#666;'>"
                    "<em>Ophthalmology Appointment Portal</em></p>",
                    unsafe_allow_html=True)
        st.divider()

        # ── Registration success flash ───────────────────────────────────
        if msg := st.session_state.pop("_reg_success", None):
            show_success(msg)

        # ── Test account info ────────────────────────────────────────────
        st.markdown(
            '<div class="test-box">'
            '<strong>🔑 Test Accounts</strong><br>'
            f'<b>Patient:</b> {TEST_ACCOUNTS["Patient"]["email"]} / '
            f'{TEST_ACCOUNTS["Patient"]["password"]}<br>'
            f'<b>Doctor:</b> {TEST_ACCOUNTS["Doctor"]["email"]} / '
            f'{TEST_ACCOUNTS["Doctor"]["password"]}'
            '</div>', unsafe_allow_html=True)
        st.write("")

        tab_p, tab_d = st.tabs(["🧑 Patient", "🩺 Doctor"])

        # ── Patient tab ──────────────────────────────────────────────────
        with tab_p:
            mode = st.radio("Mode", ["Login", "Register"],
                            key="patient_mode", horizontal=True,
                            label_visibility="collapsed")
            st.divider()
            if mode == "Login":
                _render_patient_login(all_patients)
            else:
                _render_patient_register(all_patients)

        # ── Doctor tab ───────────────────────────────────────────────────
        with tab_d:
            mode = st.radio("Mode", ["Login", "Register"],
                            key="doctor_mode", horizontal=True,
                            label_visibility="collapsed")
            st.divider()
            if mode == "Login":
                _render_doctor_login(all_doctors)
            else:
                _render_doctor_register(all_doctors)


def _render_patient_login(all_patients):
    st.subheader("Patient Login")
    with st.form("pat_login_form"):
        email = st.text_input("Email", placeholder="yourname@email.com")
        pw    = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log In as Patient",
                                          type="primary", use_container_width=True)
    if submitted:
        if not is_valid_email(email):
            st.error("⚠️ Please enter a valid email address.")
        elif not pw.strip():
            st.error("⚠️ Password is required.")
        else:
            matched = find_patient_by_email(all_patients, email)
            if matched and matched.get("password") == hash_password(pw):
                st.session_state.update({
                    "logged_in": True, "role": "Patient",
                    "current_user_name":  matched["name"],
                    "current_user_email": matched["email"],
                })
                nav("patient_dashboard")
            else:
                st.error("⚠️ Incorrect email or password.")


def _render_patient_register(all_patients):
    st.subheader("Create Patient Account")
    with st.form("pat_register_form"):
        name    = st.text_input("Full Name *",        placeholder="James Lee")
        email   = st.text_input("Email *",            placeholder="yourname@email.com")
        pw      = st.text_input("Password *",         type="password",
                                help="At least 6 characters.")
        confirm = st.text_input("Confirm Password *", type="password")
        submitted = st.form_submit_button("Create Account",
                                          type="primary", use_container_width=True)
    if submitted:
        existing_emails = [normalise_email(p.get("email", "")) for p in all_patients]
        errors = validate_registration(name, email, pw, confirm, existing_emails)
        if errors:
            show_errors(errors)
        else:
            new_pat = Patient.create_new(name, email, pw)
            all_patients.append(new_pat.to_dict())
            ok, msg = DataManager.save_patients(all_patients)
            if ok:
                st.session_state["_reg_success"] = (
                    f"Account created for {new_pat.name}! Please log in.")
                st.session_state["patient_mode"] = "Login"
                nav("login")
            else:
                all_patients.pop()
                st.error(f"⚠️ {msg}")


def _render_doctor_login(all_doctors):
    st.subheader("Doctor Login")
    with st.form("doc_login_form"):
        email = st.text_input("Email", placeholder="doctor@clinic.com")
        pw    = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log In as Doctor",
                                          type="primary", use_container_width=True)
    if submitted:
        if not is_valid_email(email):
            st.error("⚠️ Please enter a valid email address.")
        elif not pw.strip():
            st.error("⚠️ Password is required.")
        else:
            matched = find_doctor_by_email(all_doctors, email)
            if matched and matched.get("password") == hash_password(pw):
                st.session_state.update({
                    "logged_in": True, "role": "Doctor",
                    "current_user_name":  matched["name"],
                    "current_user_email": matched["email"],
                    "current_doctor_id":  matched["doctor_id"],
                })
                nav("doctor_dashboard")
            else:
                st.error("⚠️ Incorrect email or password.")


def _render_doctor_register(all_doctors):
    st.subheader("Create Doctor Account")
    with st.form("doc_register_form"):
        name      = st.text_input("Full Name *",        placeholder="Dr. Jane Smith")
        email     = st.text_input("Email *",            placeholder="doctor@clinic.com")
        specialty = st.text_input("Specialty *",        placeholder="e.g. Retinal Disease")
        pw        = st.text_input("Password *",         type="password",
                                  help="At least 6 characters.")
        confirm   = st.text_input("Confirm Password *", type="password")
        submitted = st.form_submit_button("Create Doctor Account",
                                          type="primary", use_container_width=True)
    if submitted:
        existing_emails = [normalise_email(d.get("email", "")) for d in all_doctors]
        errors = validate_registration(name, email, pw, confirm, existing_emails)
        if not specialty.strip():
            errors.insert(2, "Specialty is required.")
        if errors:
            show_errors(errors)
        else:
            new_doc = Doctor.create_new(name, email, pw, specialty)
            all_doctors.append(new_doc.to_dict())
            ok, msg = DataManager.save_doctors(all_doctors)
            if ok:
                st.session_state["_reg_success"] = (
                    f"Doctor account created for {new_doc.name}! Please log in.")
                st.session_state["doctor_mode"] = "Login"
                nav("login")
            else:
                all_doctors.pop()
                st.error(f"⚠️ {msg}")


# ═══════════════════════════════════════════════════════════════════════════════
#  PATIENT DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

def render_patient_dashboard(all_appointments, all_doctors, patient_email, patient_name):
    if not require_role("Patient"):
        return

    if flash := st.session_state.pop("_flash_success", None):
        show_success(flash)

    appts = filter_appointments_by_patient(all_appointments, patient_email)
    st.title("📋 My Appointments")
    st.caption(f"Logged in as **{patient_name}** ({patient_email})")
    st.divider()

    # ── Metrics row ──────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total",     len(appts))
    m2.metric("Scheduled", sum(1 for a in appts if a.get("status") == "Scheduled"))
    m3.metric("Completed", sum(1 for a in appts if a.get("status") == "Completed"))
    m4.metric("Cancelled", sum(1 for a in appts if a.get("status") == "Cancelled"))
    st.divider()

    # ── Cards ────────────────────────────────────────────────────────────
    if appts:
        render_appt_cards(appts)
    else:
        st.info("🗓️ No appointments yet. Use **Book Appointment** to get started.")

    # ── Detail view ──────────────────────────────────────────────────────
    if appts:
        st.divider()
        st.markdown('<div class="section-header">📝 Appointment Details</div>',
                    unsafe_allow_html=True)
        appt_selectbox("Select an appointment:", appts, key="pd_appt_sel")
        if appt := find_appointment_by_id(all_appointments,
                                          st.session_state.get("selected_appointment_id")):
            with st.container(border=True):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**Doctor:** Dr. {appt.get('doctor_name','N/A')}")
                    st.markdown(f"**Date:** {format_date(appt.get('appointment_date',''))} "
                                f"at {appt.get('appointment_time','')}")
                    st.markdown(f"**Type:** {appt.get('appointment_type','N/A')}")
                with c2:
                    st.markdown(f"**Status:** {status_badge(appt.get('status',''))}",
                                unsafe_allow_html=True)
                    st.markdown(f"**Booked:** {appt.get('submitted_timestamp','N/A')}")
                    st.markdown(f"**Doctor Note:** "
                                f"{appt.get('doctor_note','').strip() or '(none)'}")
                with st.expander("📄 Symptom Summary & Notes", expanded=True):
                    st.info(appt.get("symptom_summary", "No symptom notes provided."))
                    if appt.get("doctor_note", "").strip():
                        st.write(f"**Doctor's note:** {appt['doctor_note']}")

                # ── Cancel button (only for Scheduled) ──────────────────────
                if appt.get("status") == "Scheduled":
                    st.divider()
                    aid = appt["appointment_id"]
                    confirm_key = f"pd_cancel_confirm_{aid}"
                    if not st.session_state.get(confirm_key):
                        if st.button("❌ Cancel This Appointment",
                                     key=f"pd_cancel_btn_{aid}",
                                     type="secondary",
                                     use_container_width=True):
                            st.session_state[confirm_key] = True
                            st.rerun()
                    else:
                        st.warning("Are you sure you want to cancel this appointment?")
                        cc1, cc2 = st.columns(2)
                        with cc1:
                            if st.button("✅ Yes, cancel it",
                                         key=f"pd_cancel_yes_{aid}",
                                         type="primary",
                                         use_container_width=True):
                                live_appt = find_appointment_by_id(all_appointments, aid)
                                if not live_appt or live_appt.get("status") != "Scheduled":
                                    st.error("⚠️ This appointment is no longer active.")
                                    st.session_state.pop(confirm_key, None)
                                else:
                                    old_slot = (f"{live_appt['appointment_date']}T"
                                                f"{live_appt['appointment_time']}")
                                    appt_obj = Appointment(live_appt)
                                    appt_obj.cancel()
                                    live_doc = find_doctor_by_id(
                                        all_doctors, live_appt["doctor_id"])
                                    if (live_doc and old_slot
                                            not in live_doc.get("available_slots", [])):
                                        live_doc["available_slots"].append(old_slot)
                                    ok, msg = DataManager.save_multiple(
                                        (PATH_APPOINTMENTS, all_appointments),
                                        (PATH_DOCTORS, all_doctors))
                                    if ok:
                                        st.session_state.pop(confirm_key, None)
                                        st.session_state["_flash_success"] = (
                                            "Appointment cancelled. "
                                            "Time slot has been freed.")
                                        st.rerun()
                                    else:
                                        live_appt["status"] = "Scheduled"
                                        if (live_doc and old_slot
                                                in live_doc.get("available_slots", [])):
                                            live_doc["available_slots"].remove(old_slot)
                                        st.error(f"⚠️ Could not save cancellation: {msg}")
                        with cc2:
                            if st.button("↩️ Keep appointment",
                                         key=f"pd_cancel_no_{aid}",
                                         use_container_width=True):
                                st.session_state.pop(confirm_key, None)
                                st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
#  PATIENT BOOK PAGE
# ═══════════════════════════════════════════════════════════════════════════════

def render_patient_book(all_appointments, all_doctors, patient_name, patient_email):
    if not require_role("Patient"):
        return

    st.title("📅 Book Appointment")
    st.caption(f"Logged in as **{patient_name}**")
    st.divider()

    tab_book, tab_resched, tab_cancel = st.tabs(["📝 Book New", "🔄 Reschedule", "❌ Cancel"])

    # ── BOOK NEW ─────────────────────────────────────────────────────────
    with tab_book:
        st.subheader("New Appointment")
        col1, col2 = st.columns([3, 2])
        with col1:
            if all_doctors:
                id_to_lbl = {d["doctor_id"]: f"Dr. {d['name']} — {d.get('specialty','General')}"
                             for d in all_doctors}
                sel_id = st.selectbox("Select Doctor *", list(id_to_lbl),
                                      format_func=id_to_lbl.get, key="pb_doc")
                form_doc_data = find_doctor_by_id(all_doctors, sel_id)
                form_doc = Doctor.from_dict(form_doc_data) if form_doc_data else None
            else:
                st.warning("No doctors registered yet.")
                form_doc = None

            appt_type = st.selectbox("Appointment Type *",
                                     ["— Select appointment type —"] + APPOINTMENT_TYPES,
                                     key="pb_type")
            symptoms = st.text_area("Describe your symptoms *", height=120,
                                    key="pb_symptoms",
                                    placeholder="e.g. Blurry vision, floaters…")
            slots = sorted(form_doc.available_slots) if form_doc else []
            slot = (st.selectbox("Available Time Slot *", slots, key="pb_slot",
                                 format_func=lambda x: x.replace("T", "  "))
                    if slots else None)
            if form_doc and not slots:
                st.info("⏰ No available slots for this doctor.")

            if st.button("Book Appointment", key="pb_book_btn",
                         type="primary", use_container_width=True):
                errors = validate_booking(form_doc, appt_type, symptoms, slot)
                if errors:
                    show_errors(errors)
                elif form_doc and slot:
                    # Verify slot still available
                    live = find_doctor_by_id(all_doctors, form_doc.doctor_id)
                    if not live or slot not in live.get("available_slots", []):
                        st.error("⚠️ This slot was just taken. Please choose another.")
                    else:
                        appt = Appointment.create_new(
                            patient_name, patient_email, form_doc,
                            slot, appt_type, symptoms.strip())
                        all_appointments.append(appt.to_dict())
                        live["available_slots"].remove(slot)
                        ok, msg = DataManager.save_multiple(
                            (PATH_APPOINTMENTS, all_appointments),
                            (PATH_DOCTORS, all_doctors))
                        if ok:
                            st.session_state["_flash_success"] = (
                                f"Booked for {format_date(appt.appointment_date)} "
                                f"at {appt.appointment_time} with Dr. {form_doc.name}.")
                            st.balloons()
                            nav("patient_dashboard")
                        else:
                            all_appointments.pop()
                            live["available_slots"].append(slot)
                            st.error(f"⚠️ Booking failed: {msg}")

        with col2:
            st.subheader("ℹ️ Booking Tips")
            with st.container(border=True):
                st.markdown(
                    "- Choose your doctor and available slot\n"
                    "- Describe your symptoms clearly\n"
                    "- You can reschedule or cancel later\n"
                    "- Check the **AI Assistant** page for exam prep tips"
                )
            with st.expander("🩺 About Our Doctors"):
                for d in all_doctors:
                    st.markdown(f"**Dr. {d['name']}** — {d.get('specialty','General')}")
                    slot_count = len(d.get("available_slots", []))
                    st.caption(f"{slot_count} slot{'s' if slot_count != 1 else ''} available")
                    st.divider()

    # ── RESCHEDULE ───────────────────────────────────────────────────────
    with tab_resched:
        st.subheader("Reschedule an Appointment")
        scheduled = filter_scheduled_appointments(all_appointments, patient_email)
        if not scheduled:
            st.info("No scheduled appointments to reschedule.")
        else:
            opts = {
                f"Dr. {a['doctor_name']} | {format_date(a['appointment_date'])} "
                f"{a['appointment_time']} | {a['appointment_type']}": a["appointment_id"]
                for a in scheduled}
            lbl     = st.selectbox("Select appointment", list(opts), key="pb_resched_sel")
            rs_appt = find_appointment_by_id(all_appointments, opts[lbl])
            rs_doc  = find_doctor_by_id(all_doctors, rs_appt["doctor_id"]) if rs_appt else None
            new_slots = sorted(rs_doc.get("available_slots", [])) if rs_doc else []

            if not new_slots:
                st.warning("No alternative slots available for this doctor.")
            else:
                new_slot = st.selectbox("New Time Slot", new_slots,
                                        key="pb_resched_slot",
                                        format_func=lambda x: x.replace("T", "  "))
                if st.button("Confirm Reschedule", key="pb_resched_btn",
                             type="primary", use_container_width=True):
                    live_appt = find_appointment_by_id(all_appointments, rs_appt["appointment_id"])
                    live_doc  = find_doctor_by_id(all_doctors, rs_doc["doctor_id"]) if rs_doc else None
                    if not live_appt or live_appt.get("status") != "Scheduled":
                        st.error("⚠️ This appointment is no longer active.")
                    elif not live_doc or new_slot not in live_doc.get("available_slots", []):
                        st.error("⚠️ That slot was just taken.")
                    else:
                        old_slot = f"{live_appt['appointment_date']}T{live_appt['appointment_time']}"
                        date, time = new_slot.split("T")
                        appt_obj = Appointment(live_appt)
                        appt_obj.reschedule(date, time)
                        live_doc["available_slots"].remove(new_slot)
                        live_doc["available_slots"].append(old_slot)
                        ok, msg = DataManager.save_multiple(
                            (PATH_APPOINTMENTS, all_appointments),
                            (PATH_DOCTORS, all_doctors))
                        if ok:
                            show_success(f"Rescheduled to {format_date(date)} at {time}.")
                            st.rerun()
                        else:
                            appt_obj.reschedule(rs_appt["appointment_date"],
                                                rs_appt["appointment_time"])
                            live_doc["available_slots"].append(new_slot)
                            live_doc["available_slots"].remove(old_slot)
                            st.error(f"⚠️ Reschedule failed: {msg}")

    # ── CANCEL ───────────────────────────────────────────────────────────
    with tab_cancel:
        st.subheader("Cancel an Appointment")
        scheduled = filter_scheduled_appointments(all_appointments, patient_email)
        if not scheduled:
            st.info("No scheduled appointments to cancel.")
        else:
            render_appt_cards(scheduled)
            st.divider()
            opts = {
                f"Dr. {a['doctor_name']} | {format_date(a['appointment_date'])} "
                f"{a['appointment_time']} | {a['appointment_type']}": a["appointment_id"]
                for a in scheduled}
            lbl = st.selectbox("Select appointment to cancel", list(opts),
                               key="pb_cancel_sel")
            if st.button("Cancel Appointment", key="pb_cancel_btn",
                         type="primary", use_container_width=True):
                aid = opts[lbl]
                live_appt = find_appointment_by_id(all_appointments, aid)
                if not live_appt or live_appt.get("status") != "Scheduled":
                    st.error("⚠️ This appointment is no longer active.")
                else:
                    old_slot = f"{live_appt['appointment_date']}T{live_appt['appointment_time']}"
                    appt_obj = Appointment(live_appt)
                    appt_obj.cancel()
                    live_doc = find_doctor_by_id(all_doctors, live_appt["doctor_id"])
                    if live_doc and old_slot not in live_doc.get("available_slots", []):
                        live_doc["available_slots"].append(old_slot)
                    ok, msg = DataManager.save_multiple(
                        (PATH_APPOINTMENTS, all_appointments),
                        (PATH_DOCTORS, all_doctors))
                    if ok:
                        show_success("Appointment cancelled. Time slot has been freed.")
                        st.rerun()
                    else:
                        live_appt["status"] = "Scheduled"
                        if live_doc and old_slot in live_doc.get("available_slots", []):
                            live_doc["available_slots"].remove(old_slot)
                        st.error(f"⚠️ Could not save cancellation: {msg}")


# ═══════════════════════════════════════════════════════════════════════════════
#  AI ASSISTANT PAGE (shared by both roles)
# ═══════════════════════════════════════════════════════════════════════════════

def render_ai_assistant(all_appointments, all_doctors, user_email, user_name, role):
    st.title("🤖 AI Assistant")
    st.caption(f"Chat with our clinic assistant — logged in as **{user_name}** ({role})")
    if ai_assistant.api_key:
        st.success("🟢 Connected to OpenAI (gpt-4o-mini)")
    else:
        st.warning("🟡 No OpenAI API key found — using built-in fallback responses. "
                   "Add `OPENAI_API_KEY=...` to a `.env` file to enable GPT replies.")
    st.divider()

    col_chat, col_info = st.columns([3, 1])

    with col_info:
        if st.button("🗑️ Clear Chat", key="ai_clear"):
            st.session_state["messages"] = [_SESSION_DEFAULTS["messages"][0]]
            st.rerun()

        with st.expander("ℹ️ About the AI Assistant"):
            st.markdown(
                "This assistant is powered by **OpenAI** and has access to "
                "your appointment data and clinic information. "
                "It can help with scheduling questions, exam preparation, "
                "and general clinic inquiries."
            )

    with col_chat:
        # Build context for the AI
        doctor_id = st.session_state.get("current_doctor_id", "")
        context = ai_assistant.build_context(
            all_appointments, all_doctors, user_email,
            role=role, doctor_id=doctor_id)

        # Display chat history
        chat_container = st.container(height=420)
        with chat_container:
            for msg in st.session_state.get("messages", []):
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])

        # Quick-suggestion dropdown — picking one auto-sends it as a question
        if role == "Patient":
            suggestions = [
                "What is my next appointment?",
                "What slots are available?",
                "How should I prepare for an eye exam?",
                "How do I cancel an appointment?",
                "Tell me about glaucoma screening",
            ]
        else:
            suggestions = [
                "How many appointments do I have today?",
                "Which patients are scheduled this week?",
                "Tips for fundus examination",
                "What should I note for a no-show?",
            ]
        SUGGEST_PLACEHOLDER = "💡 Try asking… (pick a sample question)"

        # Picking a suggestion fills the text input but does NOT auto-send;
        # the user can edit, then click Send (or press Enter).
        def _on_suggestion_pick():
            picked = st.session_state.get("ai_suggestion")
            if picked and picked != SUGGEST_PLACEHOLDER:
                st.session_state["ai_input_text"] = picked
                st.session_state["ai_suggestion"] = SUGGEST_PLACEHOLDER

        st.selectbox(
            "Quick suggestions",
            [SUGGEST_PLACEHOLDER] + suggestions,
            key="ai_suggestion",
            on_change=_on_suggestion_pick,
            label_visibility="collapsed",
        )

        # Combined text input + send button (Enter inside form also submits)
        with st.form("ai_chat_form", clear_on_submit=True, border=False):
            txt_col, btn_col = st.columns([6, 1])
            with txt_col:
                user_text = st.text_input(
                    "Your question",
                    key="ai_input_text",
                    placeholder="Ask me anything about your appointments…",
                    label_visibility="collapsed",
                )
            with btn_col:
                submitted = st.form_submit_button(
                    "Send ➤", type="primary", use_container_width=True)

        if submitted and user_text.strip():
            st.session_state["messages"].append(
                {"role": "user", "content": user_text})
            with st.spinner("Thinking…"):
                reply = ai_assistant.generate_response(
                    user_text, context,
                    chat_history=st.session_state["messages"])
            st.session_state["messages"].append(
                {"role": "assistant", "content": reply})
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
#  DOCTOR DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

def render_doctor_dashboard(all_appointments, all_doctors, doctor_id, doctor_name):
    if not require_role("Doctor"):
        return

    if flash := st.session_state.pop("_flash_success", None):
        show_success(flash)

    schedule = filter_appointments_by_doctor(all_appointments, doctor_id)
    st.title("📊 Appointment Dashboard")
    st.caption(f"Patient roster for **{doctor_name}**")
    st.divider()

    # ── Metrics row ──────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("My Appointments", len(schedule))
    m2.metric("Scheduled", sum(1 for a in schedule if a.get("status") == "Scheduled"))
    m3.metric("Completed", sum(1 for a in schedule if a.get("status") == "Completed"))
    m4.metric("No-Show",   sum(1 for a in schedule if a.get("status") == "No-Show"))
    st.divider()

    if schedule:
        render_appt_cards(schedule)
    else:
        st.info("No appointments assigned to you yet.")

    # ── Update section ───────────────────────────────────────────────────
    if schedule:
        st.divider()
        st.markdown('<div class="section-header">✏️ Update Appointment Status</div>',
                    unsafe_allow_html=True)
        appt_selectbox("Select an appointment:", schedule, key="dd_appt_sel")
        if appt := find_appointment_by_id(
                all_appointments, st.session_state.get("selected_appointment_id")):
            with st.container(border=True):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**Patient:** {appt.get('patient_name','N/A')}")
                    st.markdown(f"**Email:** {appt.get('patient_email','N/A')}")
                    st.markdown(f"**Date:** {format_date(appt.get('appointment_date',''))} "
                                f"at {appt.get('appointment_time','')}")
                with c2:
                    st.markdown(f"**Type:** {appt.get('appointment_type','N/A')}")
                    st.markdown(f"**Status:** {status_badge(appt.get('status',''))}",
                                unsafe_allow_html=True)
                    st.markdown(f"**Booked:** {appt.get('submitted_timestamp','N/A')}")

                with st.expander("📄 Symptom Summary", expanded=True):
                    st.info(appt.get("symptom_summary", "No symptom notes."))
                st.divider()

                aid = appt["appointment_id"]
                current = appt.get("status", "Scheduled")
                s1, s2 = st.columns(2)
                with s1:
                    new_status = st.selectbox(
                        "Update Status", APPT_STATUSES,
                        index=(APPT_STATUSES.index(current)
                               if current in APPT_STATUSES else 0),
                        key=f"dd_st_{aid}")
                with s2:
                    new_note = st.text_input("Doctor Note",
                                             value=appt.get("doctor_note", ""),
                                             key=f"dd_nt_{aid}")
                if st.button("💾 Save Changes", key=f"dd_save_{aid}",
                             type="primary", use_container_width=True):
                    appt_obj = Appointment(appt)
                    appt_obj.update_status(new_status, new_note)
                    ok, msg = DataManager.save_appointments(all_appointments)
                    if ok:
                        show_success("Appointment updated successfully.")
                        st.rerun()
                    else:
                        st.error(f"⚠️ {msg}")

                # ── Doctor-initiated cancellation (Scheduled only) ──────────
                if appt.get("status") == "Scheduled":
                    st.divider()
                    confirm_key = f"dd_cancel_confirm_{aid}"
                    if not st.session_state.get(confirm_key):
                        if st.button("❌ Cancel Appointment (Clinic-Initiated)",
                                     key=f"dd_cancel_btn_{aid}",
                                     use_container_width=True):
                            st.session_state[confirm_key] = True
                            st.rerun()
                    else:
                        st.warning("Cancelling will free this time slot and notify "
                                   "the patient via the appointment record. "
                                   "A reason is required.")
                        reason = st.text_area(
                            "Reason for cancellation (visible to patient)",
                            key=f"dd_cancel_reason_{aid}",
                            placeholder="e.g. Doctor unavailable due to emergency")
                        cc1, cc2 = st.columns(2)
                        with cc1:
                            if st.button("✅ Confirm cancellation",
                                         key=f"dd_cancel_yes_{aid}",
                                         type="primary",
                                         use_container_width=True):
                                if not reason.strip():
                                    st.error("Please provide a reason before "
                                             "cancelling.")
                                else:
                                    live_appt = find_appointment_by_id(
                                        all_appointments, aid)
                                    if (not live_appt
                                            or live_appt.get("status") != "Scheduled"):
                                        st.error("⚠️ This appointment is no longer "
                                                 "active.")
                                        st.session_state.pop(confirm_key, None)
                                    else:
                                        old_slot = (f"{live_appt['appointment_date']}T"
                                                    f"{live_appt['appointment_time']}")
                                        prior_note = live_appt.get("doctor_note", "")
                                        appt_obj = Appointment(live_appt)
                                        appt_obj.cancel()
                                        live_appt["doctor_note"] = (
                                            f"[Cancelled by clinic] {reason.strip()}")
                                        live_doc = find_doctor_by_id(
                                            all_doctors, live_appt["doctor_id"])
                                        if (live_doc and old_slot
                                                not in live_doc.get(
                                                    "available_slots", [])):
                                            live_doc["available_slots"].append(old_slot)
                                        ok, msg = DataManager.save_multiple(
                                            (PATH_APPOINTMENTS, all_appointments),
                                            (PATH_DOCTORS, all_doctors))
                                        if ok:
                                            st.session_state.pop(confirm_key, None)
                                            st.session_state["_flash_success"] = (
                                                "Appointment cancelled. Time slot "
                                                "returned to your availability.")
                                            st.rerun()
                                        else:
                                            live_appt["status"] = "Scheduled"
                                            live_appt["doctor_note"] = prior_note
                                            if (live_doc and old_slot
                                                    in live_doc.get(
                                                        "available_slots", [])):
                                                live_doc["available_slots"].remove(
                                                    old_slot)
                                            st.error(
                                                f"⚠️ Could not save cancellation: {msg}")
                        with cc2:
                            if st.button("↩️ Keep appointment",
                                         key=f"dd_cancel_no_{aid}",
                                         use_container_width=True):
                                st.session_state.pop(confirm_key, None)
                                st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
#  DOCTOR SLOTS PAGE
# ═══════════════════════════════════════════════════════════════════════════════

def render_doctor_slots(all_doctors, doctor_id, doctor_name):
    if not require_role("Doctor"):
        return

    doc_data = find_doctor_by_id(all_doctors, doctor_id)
    doc = Doctor.from_dict(doc_data) if doc_data else None

    st.title("⏰ Manage Time Slots")
    st.caption(f"Managing slots for **{doctor_name}**")
    st.divider()

    tab_add, tab_remove = st.tabs(["➕ Add Slot", "➖ Remove Slot"])

    with tab_add:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Add a New Slot")
            slot_date = st.date_input("Date", key="ds_date")
            slot_hour = st.selectbox("Hour",
                                     [f"{h:02d}:00" for h in range(8, 18)],
                                     key="ds_hour")
            if st.button("Add Slot", key="ds_add", type="primary",
                         use_container_width=True):
                new_slot = f"{slot_date}T{slot_hour}"
                if doc and not doc.add_slot(new_slot):
                    st.warning("This slot already exists.")
                elif doc:
                    doc_data["available_slots"] = doc.available_slots
                    ok, msg = DataManager.save_doctors(all_doctors)
                    if ok:
                        show_success(f"Slot added: {format_date(str(slot_date))} at {slot_hour}")
                        st.rerun()
                    else:
                        st.error(f"⚠️ {msg}")
        with col2:
            st.subheader("Your Current Slots")
            slots = sorted(doc.available_slots) if doc else []
            if slots:
                for s in slots:
                    parts = s.split("T")
                    st.markdown(
                        f'<div class="slot-card">'
                        f'<div class="slot-card-date">{format_date(parts[0])}</div>'
                        f'<div class="slot-card-time">⏰ {parts[1] if len(parts)>1 else "N/A"}</div>'
                        f'</div>', unsafe_allow_html=True)
            else:
                st.info("No available slots at the moment.")

    with tab_remove:
        st.subheader("Remove a Slot")
        slots = sorted(doc.available_slots) if doc else []
        if slots:
            to_remove = st.selectbox("Select slot to remove", slots,
                                     key="ds_rm_sel",
                                     format_func=lambda x: x.replace("T", "  "))
            if st.button("Remove Slot", key="ds_rm_btn", type="primary",
                         use_container_width=True):
                if doc:
                    doc.remove_slot(to_remove)
                    doc_data["available_slots"] = doc.available_slots
                    ok, msg = DataManager.save_doctors(all_doctors)
                    if ok:
                        parts = to_remove.split("T")
                        show_success(f"Slot removed: {format_date(parts[0])} "
                                     f"at {parts[1] if len(parts)>1 else ''}")
                        st.rerun()
                    else:
                        st.error(f"⚠️ {msg}")
        else:
            st.info("No slots to remove.")


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN — Load data, route pages
# ═══════════════════════════════════════════════════════════════════════════════

all_patients     = DataManager.load_patients()
all_doctors      = DataManager.load_doctors()
all_appointments = DataManager.load_appointments()

if st.session_state.get("logged_in"):
    render_sidebar()

ss   = st.session_state
page = ss.get("page", "login")

if page == "login":
    render_login(all_patients, all_doctors)
elif page == "patient_dashboard":
    render_patient_dashboard(all_appointments, all_doctors,
                             ss.get("current_user_email", ""),
                             ss.get("current_user_name", ""))
elif page == "patient_book":
    render_patient_book(all_appointments, all_doctors,
                        ss.get("current_user_name", ""),
                        ss.get("current_user_email", ""))
elif page == "patient_ai":
    render_ai_assistant(all_appointments, all_doctors,
                        ss.get("current_user_email", ""),
                        ss.get("current_user_name", ""), "Patient")
elif page == "doctor_dashboard":
    render_doctor_dashboard(all_appointments, all_doctors,
                            ss.get("current_doctor_id", ""),
                            ss.get("current_user_name", ""))
elif page == "doctor_slots":
    render_doctor_slots(all_doctors, ss.get("current_doctor_id", ""),
                        ss.get("current_user_name", ""))
elif page == "doctor_ai":
    render_ai_assistant(all_appointments, all_doctors,
                        ss.get("current_user_email", ""),
                        ss.get("current_user_name", ""), "Doctor")

st.markdown(
    '<div class="clinic-footer">'
    '<strong>ClearVision Clinic</strong> · Ophthalmology Appointment Portal<br>'
    '© 2026 ClearVision. All rights reserved.'
    '</div>', unsafe_allow_html=True)
