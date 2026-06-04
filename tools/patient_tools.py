from models import Patient, Doctor
from security.access_control import can_access_patient


def patient_profile(db, patient_id, actor=None, **kwargs):
    """Retrieve a patient's profile information."""

    if actor and not can_access_patient(db, actor, patient_id):
        return {"error": "Unauthorized: You cannot access this patient profile"}

    patient = db.query(Patient).filter(Patient.id == patient_id).first()

    if not patient:
        return {"error": f"Patient {patient_id} not found"}

    doctor = db.query(Doctor).filter(Doctor.id == patient.assigned_doctor_id).first() if patient.assigned_doctor_id else None

    return {
        "patient_id": patient.id,
        "name": patient.full_name,
        "dob": str(patient.dob) if patient.dob else None,
        "gender": patient.gender,
        "blood_group": patient.blood_group,
        "phone": patient.phone,
        "email": patient.email,
        "address": patient.address,
        "emergency_contact": patient.emergency_contact,
        "assigned_doctor": doctor.full_name if doctor else None,
        "disease_summary": patient.disease_summary,
    }


def patient_medical_history(db, patient_id, actor=None, limit=10, **kwargs):
    """Retrieve a patient's medical history (records, prescriptions, labs)."""
    from models import MedicalRecord, Prescription, LabReport

    if actor and not can_access_patient(db, actor, patient_id):
        return {"error": "Unauthorized: You cannot access this patient's history"}

    # Nurse gets limited view
    records = db.query(MedicalRecord).filter(MedicalRecord.patient_id == patient_id).limit(limit).all()
    prescriptions = db.query(Prescription).filter(Prescription.patient_id == patient_id).limit(limit).all()
    labs = db.query(LabReport).filter(LabReport.patient_id == patient_id).limit(limit).all()

    result = {
        "patient_id": patient_id,
        "medical_records": [
            {
                "id": r.id,
                "doctor_id": r.doctor_id,
                "symptoms": r.symptoms,
                "diagnosis": r.diagnosis,
                "treatment_plan": r.treatment_plan,
                "notes": r.notes if actor and actor.role != "NURSE" else "[restricted]",
                "date": str(r.created_at) if r.created_at else None,
            }
            for r in records
        ],
        "prescriptions": [
            {
                "id": p.id,
                "drug": p.drug_name,
                "dosage": p.dosage,
                "frequency": p.frequency,
                "duration": p.duration,
            }
            for p in prescriptions
        ],
        "lab_reports": [
            {
                "id": l.id,
                "test": l.test_type,
                "value": l.test_value,
                "flag": l.flag,
                "status": l.status,
            }
            for l in labs
        ],
    }

    return result


def update_patient_details(db, patient_id, actor=None, **kwargs):
    """Update patient details (phone, email, address, emergency_contact)."""

    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        return {"error": f"Patient {patient_id} not found"}

    if actor and not can_access_patient(db, actor, patient_id):
        return {"error": "Unauthorized: You cannot update this patient"}

    updated_fields = []
    for field in ["phone", "email", "address", "emergency_contact"]:
        if field in kwargs and kwargs[field]:
            setattr(patient, field, kwargs[field])
            updated_fields.append(field)

    if not updated_fields:
        return {"error": "No valid fields provided to update"}

    db.commit()

    return {
        "patient_id": patient.id,
        "updated_fields": updated_fields,
        "success": True,
    }
