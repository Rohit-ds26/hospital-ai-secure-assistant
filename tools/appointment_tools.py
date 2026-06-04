from models import Appointment, Patient
from datetime import date
from security.access_control import can_access_patient


def book_appointment(db, patient_id, doctor_id, appointment_date, time_slot, reason=None, actor=None, **kwargs):
    """Book a new appointment."""

    if actor and not can_access_patient(db, actor, patient_id):
        return {"error": "Unauthorized: You cannot book appointments for this patient"}

    appt = Appointment(
        patient_id=patient_id,
        doctor_id=doctor_id,
        appointment_date=date.fromisoformat(str(appointment_date)),
        time_slot=str(time_slot),
        reason=reason or "",
        status="SCHEDULED",
    )

    db.add(appt)
    db.commit()

    return {
        "appointment_id": appt.id,
        "patient_id": appt.patient_id,
        "doctor_id": appt.doctor_id,
        "date": str(appt.appointment_date),
        "time_slot": appt.time_slot,
        "status": "SCHEDULED",
        "created": True,
    }


def cancel_appointment(db, appointment_id, actor=None, **kwargs):
    """Cancel an existing appointment."""

    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()

    if not appt:
        return {"error": f"Appointment {appointment_id} not found"}

    # Patient can only cancel their own
    if actor and actor.role == "PATIENT":
        actor_patient = db.query(Patient).filter(Patient.user_id == actor.id).first()
        if not actor_patient or actor_patient.id != appt.patient_id:
            return {"error": "Unauthorized: You can only cancel your own appointments"}

    if appt.status == "CANCELLED":
        return {"error": "Appointment is already cancelled"}

    old_status = appt.status
    appt.status = "CANCELLED"
    db.commit()

    return {
        "appointment_id": appt.id,
        "old_status": old_status,
        "new_status": "CANCELLED",
        "cancelled": True,
    }


def get_appointments(db, actor, patient_id=None, doctor_id=None, status=None, limit=20, **kwargs):
    """Get appointments with optional filters."""

    query = db.query(Appointment)

    # Patients can only see their own. Doctors only see assigned appointments
    # unless a narrower doctor_id filter is supplied for their own doctor profile.
    if actor and actor.role == "PATIENT":
        actor_patient = db.query(Patient).filter(Patient.user_id == actor.id).first()
        if not actor_patient:
            return {"error": "Patient profile not found"}
        query = query.filter(Appointment.patient_id == actor_patient.id)
    elif actor and actor.role == "DOCTOR":
        from security.access_control import actor_doctor_id
        current_doctor_id = actor_doctor_id(db, actor)
        if not current_doctor_id:
            return {"error": "Doctor profile not found"}
        query = query.filter(Appointment.doctor_id == current_doctor_id)
    else:
        if patient_id:
            query = query.filter(Appointment.patient_id == patient_id)
        if doctor_id:
            query = query.filter(Appointment.doctor_id == doctor_id)

    if status:
        query = query.filter(Appointment.status == status.upper())

    appointments = query.order_by(Appointment.appointment_date.desc()).limit(limit).all()

    return [
        {
            "appointment_id": a.id,
            "patient_id": a.patient_id,
            "doctor_id": a.doctor_id,
            "date": str(a.appointment_date),
            "time_slot": a.time_slot,
            "reason": a.reason,
            "status": a.status,
        }
        for a in appointments
    ]
