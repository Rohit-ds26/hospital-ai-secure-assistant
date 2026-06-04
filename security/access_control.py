from models import Doctor, Patient


PATIENT_SCOPED_TOOLS = {
    "patient_profile",
    "patient_medical_history",
    "update_patient_details",
    "book_appointment",
    "get_appointments",
    "create_medical_record",
    "get_medical_records",
    "create_prescription",
    "get_prescriptions",
    "upload_lab_report",
    "get_lab_reports",
    "generate_bill",
    "get_billing_details",
    "submit_insurance_claim",
    "get_insurance_claims",
}


def actor_patient_id(db, actor):
    if not actor or actor.role != "PATIENT":
        return None
    patient = db.query(Patient).filter(Patient.user_id == actor.id).first()
    return patient.id if patient else None


def actor_doctor_id(db, actor):
    if not actor or actor.role != "DOCTOR":
        return None
    doctor = db.query(Doctor).filter(Doctor.user_id == actor.id).first()
    return doctor.id if doctor else None


def can_access_patient(db, actor, patient_id):
    if not actor:
        return False

    if actor.role in {"SUPER_ADMIN", "HOSPITAL_SUPERVISOR", "RECEPTIONIST", "BILLING_INSURANCE", "LAB_TECH"}:
        return True

    if actor.role in {"NURSE", "COMPOUNDER"}:
        return True

    if actor.role == "PATIENT":
        return actor_patient_id(db, actor) == patient_id

    if actor.role == "DOCTOR":
        doctor_id = actor_doctor_id(db, actor)
        if not doctor_id:
            return False
        return db.query(Patient).filter(
            Patient.id == patient_id,
            Patient.assigned_doctor_id == doctor_id,
        ).first() is not None

    return False


def normalize_patient_scope(db, actor, tool_name, args):
    if not actor or actor.role != "PATIENT" or tool_name not in PATIENT_SCOPED_TOOLS:
        return args

    own_patient_id = actor_patient_id(db, actor)
    if own_patient_id:
        setattr(actor, "patient_id", own_patient_id)
        if "patient_id" in args or tool_name in {
            "patient_profile",
            "patient_medical_history",
            "update_patient_details",
            "book_appointment",
            "get_medical_records",
            "get_prescriptions",
            "get_lab_reports",
            "get_billing_details",
            "submit_insurance_claim",
            "get_insurance_claims",
        }:
            args["patient_id"] = own_patient_id

    return args
