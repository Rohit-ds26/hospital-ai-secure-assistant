from models import Doctor


def get_doctor_details(db, doctor_id, actor=None, **kwargs):
    """Get doctor's professional details."""

    # Doctors can only view their own profile (unless admin/supervisor)
    if actor and actor.role == "DOCTOR":
        actor_doc = db.query(Doctor).filter(Doctor.user_id == actor.id).first()
        if actor_doc and actor_doc.id != doctor_id:
            return {"error": "Unauthorized: Doctors can only view their own profile"}

    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()

    if not doctor:
        return {"error": f"Doctor {doctor_id} not found"}

    return {
        "doctor_id": doctor.id,
        "name": doctor.full_name,
        "specialization": doctor.specialization,
        "license_number": doctor.license_number,
        "department": doctor.department,
        "availability": doctor.availability_status,
    }


def update_doctor_availability(db, doctor_id, availability_status, actor=None, **kwargs):
    """Update a doctor's availability status."""

    valid_statuses = ["AVAILABLE", "BUSY", "ON_LEAVE", "OFF_DUTY"]
    status = availability_status.upper()

    if status not in valid_statuses:
        return {"error": f"Invalid status. Must be one of: {valid_statuses}"}

    # Doctors can only update their own availability
    if actor and actor.role == "DOCTOR":
        actor_doc = db.query(Doctor).filter(Doctor.user_id == actor.id).first()
        if not actor_doc or actor_doc.id != doctor_id:
            return {"error": "Unauthorized: You can only update your own availability"}

    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()

    if not doctor:
        return {"error": f"Doctor {doctor_id} not found"}

    old_status = doctor.availability_status
    doctor.availability_status = status
    db.commit()

    return {
        "doctor_id": doctor.id,
        "name": doctor.full_name,
        "old_status": old_status,
        "new_status": doctor.availability_status,
        "updated": True,
    }
