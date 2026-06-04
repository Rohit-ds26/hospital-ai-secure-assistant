from models import LabReport, Patient
from security.access_control import can_access_patient


def upload_lab_report(db, patient_id, test_type, test_value, normal_range, flag="NORMAL", doctor_id=None, actor=None, **kwargs):
    """Upload a new lab report (lab tech only)."""

    if actor and not can_access_patient(db, actor, patient_id):
        return {"error": "Unauthorized: You cannot upload lab reports for this patient"}

    flag = flag.upper()
    valid_flags = ["NORMAL", "ABNORMAL", "CRITICAL"]
    if flag not in valid_flags:
        return {"error": f"Invalid flag. Must be one of: {valid_flags}"}

    report = LabReport(
        patient_id=patient_id,
        doctor_id=doctor_id,
        test_type=test_type,
        test_value=test_value,
        normal_range=normal_range,
        flag=flag,
        status="COMPLETED",
    )

    db.add(report)
    db.commit()

    return {
        "report_id": report.id,
        "patient_id": report.patient_id,
        "test_type": report.test_type,
        "flag": report.flag,
        "uploaded": True,
    }


def get_lab_reports(db, patient_id, actor=None, limit=20, **kwargs):
    """Get lab reports for a patient."""

    if actor and not can_access_patient(db, actor, patient_id):
        return {"error": "Unauthorized: You cannot view this patient's lab reports"}

    reports = (
        db.query(LabReport)
        .filter(LabReport.patient_id == patient_id)
        .order_by(LabReport.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "report_id": r.id,
            "patient_id": r.patient_id,
            "doctor_id": r.doctor_id,
            "test_type": r.test_type,
            "test_value": r.test_value,
            "normal_range": r.normal_range,
            "flag": r.flag,
            "status": r.status,
            "date": str(r.created_at) if r.created_at else None,
        }
        for r in reports
    ]


def update_lab_report_status(db, report_id, status, actor=None, **kwargs):
    """Update lab report status (lab tech only)."""

    status = status.upper()
    valid_statuses = ["PENDING", "COMPLETED", "REJECTED"]
    if status not in valid_statuses:
        return {"error": f"Invalid status. Must be one of: {valid_statuses}"}

    report = db.query(LabReport).filter(LabReport.id == report_id).first()

    if not report:
        return {"error": f"Lab report {report_id} not found"}

    old_status = report.status
    report.status = status
    db.commit()

    return {
        "report_id": report.id,
        "old_status": old_status,
        "new_status": report.status,
        "updated": True,
    }
