from models import Prescription, Patient
from security.access_control import can_access_patient


def create_prescription(db, patient_id, doctor_id, drug_name, dosage, frequency, duration, notes=None, actor=None, **kwargs):
    """Create a new prescription (doctor only)."""

    if actor and not can_access_patient(db, actor, patient_id):
        return {"error": "Unauthorized: You cannot prescribe for this patient"}

    presc = Prescription(
        patient_id=patient_id,
        doctor_id=doctor_id,
        drug_name=drug_name,
        dosage=dosage,
        frequency=frequency,
        duration=duration,
        notes=notes or "",
    )

    db.add(presc)
    db.commit()

    return {
        "prescription_id": presc.id,
        "patient_id": presc.patient_id,
        "drug": presc.drug_name,
        "dosage": presc.dosage,
        "created": True,
    }


def get_prescriptions(db, patient_id, actor=None, limit=20, **kwargs):
    """Get prescriptions for a patient."""

    if actor and not can_access_patient(db, actor, patient_id):
        return {"error": "Unauthorized: You cannot view this patient's prescriptions"}

    prescriptions = (
        db.query(Prescription)
        .filter(Prescription.patient_id == patient_id)
        .order_by(Prescription.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "prescription_id": p.id,
            "patient_id": p.patient_id,
            "doctor_id": p.doctor_id,
            "drug": p.drug_name,
            "dosage": p.dosage,
            "frequency": p.frequency,
            "duration": p.duration,
            "notes": p.notes,
            "date": str(p.created_at) if p.created_at else None,
        }
        for p in prescriptions
    ]
