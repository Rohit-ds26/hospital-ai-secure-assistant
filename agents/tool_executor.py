from models import MedicalRecord
from security.audit import log_audit


def get_medical_records_legacy(db, actor, patient_id, limit=10):
    """Legacy tool executor with built-in audit logging."""

    records = (
        db.query(MedicalRecord)
        .filter(MedicalRecord.patient_id == patient_id)
        .limit(limit)
        .all()
    )

    log_audit(db, actor, "GET_MEDICAL_RECORDS", f"patient:{patient_id}")

    return records
