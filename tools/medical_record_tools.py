from models import MedicalRecord, Patient
from security.access_control import can_access_patient


def create_medical_record(db, patient_id, doctor_id, symptoms, diagnosis, treatment_plan, notes=None, appointment_id=None, actor=None, **kwargs):
    """Create a new medical record (doctor only)."""

    if actor and not can_access_patient(db, actor, patient_id):
        return {"error": "Unauthorized: You cannot create records for this patient"}

    record = MedicalRecord(
        patient_id=patient_id,
        doctor_id=doctor_id,
        appointment_id=appointment_id,
        symptoms=symptoms,
        diagnosis=diagnosis,
        treatment_plan=treatment_plan,
        notes=notes or "",
    )

    db.add(record)
    db.commit()

    return {
        "record_id": record.id,
        "patient_id": record.patient_id,
        "doctor_id": record.doctor_id,
        "diagnosis": record.diagnosis,
        "created": True,
    }


def get_medical_records(db, patient_id, actor=None, limit=10, **kwargs):
    """Get medical records for a patient."""

    if actor and not can_access_patient(db, actor, patient_id):
        return {"error": "Unauthorized: You cannot view this patient's records"}

    records = (
        db.query(MedicalRecord)
        .filter(MedicalRecord.patient_id == patient_id)
        .order_by(MedicalRecord.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "record_id": r.id,
            "patient_id": r.patient_id,
            "doctor_id": r.doctor_id,
            "symptoms": r.symptoms,
            "diagnosis": r.diagnosis,
            "treatment_plan": r.treatment_plan,
            "notes": r.notes if actor and actor.role != "NURSE" else "[restricted]",
            "date": str(r.created_at) if r.created_at else None,
        }
        for r in records
    ]


def update_treatment_plan(db, record_id, treatment_plan, actor=None, **kwargs):
    """Update treatment plan for a medical record (doctor only)."""

    record = db.query(MedicalRecord).filter(MedicalRecord.id == record_id).first()

    if not record:
        return {"error": f"Medical record {record_id} not found"}

    old_plan = record.treatment_plan
    record.treatment_plan = treatment_plan
    db.commit()

    return {
        "record_id": record.id,
        "old_treatment_plan": old_plan,
        "new_treatment_plan": record.treatment_plan,
        "updated": True,
    }
