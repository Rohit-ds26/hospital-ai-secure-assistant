import os
import time
from datetime import datetime, timedelta
from pathlib import Path

from models import (
    Appointment,
    Billing,
    ClinicalSafetyRule,
    HospitalAnalytics,
    LabReport,
    ManagementReportRequest,
    MedicalRecord,
    Patient,
    Prescription,
    Insurance,
    AuditLog,
)

# ---- Audit Tools ----

def get_audit_logs(db, username=None, action=None, limit=30, actor=None, **kwargs):
    """Retrieve system audit logs for security tracking."""
    query = db.query(AuditLog)
    if username:
        query = query.filter(AuditLog.username == username)
    if action:
        query = query.filter(AuditLog.action == action)
    
    logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return [
        {
            "id": l.id,
            "username": l.username,
            "role": l.role,
            "action": l.action,
            "resource": l.resource,
            "timestamp": str(l.timestamp),
            "details": l.details
        } for l in logs
    ]

# ---- Clinical Safety Tools (FraudRule Equivalent) ----

def get_clinical_safety_rules(db, actor=None, **kwargs):
    """Retrieve all clinical safety and drug interaction rules."""
    rules = db.query(ClinicalSafetyRule).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "description": r.description,
            "trigger": r.trigger_type,
            "risk_level": r.risk_level,
            "is_active": r.is_active
        } for r in rules
    ]

def create_clinical_safety_rule(db, name, description, trigger_type, risk_level="LOW", actor=None, **kwargs):
    """Create a new clinical safety or interaction trigger rule."""
    rule = ClinicalSafetyRule(
        name=name,
        description=description,
        trigger_type=trigger_type,
        risk_level=risk_level,
        is_active=True
    )
    db.add(rule)
    db.commit()
    return {"id": rule.id, "name": rule.name, "status": "created"}

def toggle_clinical_safety_rule(db, rule_id, is_active, actor=None, **kwargs):
    """Enable or disable a clinical safety rule."""
    rule = db.query(ClinicalSafetyRule).filter(ClinicalSafetyRule.id == rule_id).first()
    if not rule:
        return {"error": f"Rule {rule_id} not found"}
    
    rule.is_active = is_active
    db.commit()
    return {"id": rule.id, "is_active": rule.is_active, "status": "updated"}


# ---- Analytics Tools (InternalAnalytics Equivalent) ----

def get_hospital_analytics(db, department=None, actor=None, **kwargs):
    """Retrieve hospital operational metrics and department analytics."""
    query = db.query(HospitalAnalytics)
    if department:
        query = query.filter(HospitalAnalytics.department == department)
    
    stats = query.all()
    return [
        {
            "metric": s.metric_name,
            "department": s.department,
            "value": s.value,
            "unit": s.unit,
            "recorded_at": str(s.recorded_at)
        } for s in stats
    ]


# ---- Management Report Tools ----

VAULT_DIR = Path("secure_vault")


def _write_secure_document(request_id, title, content):
    VAULT_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(ch if ch.isalnum() else "_" for ch in title.lower()).strip("_")[:60]
    path = VAULT_DIR / f"document_{request_id}_{safe_name or 'management_document'}.txt"
    path.write_text(content, encoding="utf-8")
    return str(path)


def _patient_header(patient):
    if not patient:
        return ["Patient: Not found"]
    return [
        f"Patient ID: {patient.id}",
        f"Name: {patient.full_name}",
        f"DOB: {patient.dob}",
        f"Gender: {patient.gender}",
        f"Blood Group: {patient.blood_group}",
        f"Phone: {patient.phone}",
        f"Email: {patient.email}",
        f"Address: {patient.address}",
        f"Assigned Doctor ID: {patient.assigned_doctor_id}",
        f"Disease Summary: {patient.disease_summary}",
    ]


def _section(title, rows):
    if not rows:
        return [title, "- No records found."]
    return [title, *rows]


def _create_vault_request(db, actor, title, document_type, content, patient_id=None):
    request = ManagementReportRequest(
        requested_by_user_id=actor.id,
        requested_by_username=actor.username,
        requested_by_role=actor.role,
        title=title,
        category="document",
        document_type=document_type,
        patient_id=patient_id,
        content="Confidential document generated and stored in Secure Document Vault. Content is not returned in chat.",
        status="PENDING_ADMIN_APPROVAL",
        available_at=datetime.utcnow(),
    )
    db.add(request)
    db.commit()
    request.secure_file_path = _write_secure_document(request.id, request.title, content)
    db.commit()
    return request


def create_secure_document_request(db, document_type, patient_id=None, title=None, actor=None, **kwargs):
    """
    Create a confidential supervisor/admin document request and store content in the vault.
    Supported document types:
    - patient_full_records
    - hospital_billing_records
    - patient_lab_reports
    - patient_insurance_details
    """
    if not actor or actor.role != "HOSPITAL_SUPERVISOR":
        return {"error": "Only HOSPITAL_SUPERVISOR can create secure document requests"}

    doc_type = str(document_type or "").lower().strip()
    supported = {
        "patient_full_records",
        "hospital_billing_records",
        "patient_lab_reports",
        "patient_insurance_details",
    }
    if doc_type not in supported:
        return {"error": f"Invalid document_type. Use one of: {sorted(supported)}"}

    if doc_type != "hospital_billing_records" and not patient_id:
        return {"error": f"patient_id is required for {doc_type}"}

    patient = db.query(Patient).filter(Patient.id == patient_id).first() if patient_id else None
    if patient_id and not patient:
        return {"error": f"Patient {patient_id} not found"}

    generated_at = datetime.utcnow().isoformat()
    default_titles = {
        "patient_full_records": f"Full Patient Records Document - Patient {patient_id}",
        "hospital_billing_records": "All Hospital Billing Records Document",
        "patient_lab_reports": f"Lab Reports Document - Patient {patient_id}",
        "patient_insurance_details": f"Insurance Details Document - Patient {patient_id}",
    }
    doc_title = title or default_titles[doc_type]

    lines = [
        doc_title,
        "",
        f"Generated by: {actor.username} ({actor.role})",
        f"Generated at: {generated_at} UTC",
        f"Document type: {doc_type}",
        "",
    ]

    if doc_type == "patient_full_records":
        appointments = db.query(Appointment).filter(Appointment.patient_id == patient_id).order_by(Appointment.appointment_date.desc()).all()
        records = db.query(MedicalRecord).filter(MedicalRecord.patient_id == patient_id).order_by(MedicalRecord.created_at.desc()).all()
        prescriptions = db.query(Prescription).filter(Prescription.patient_id == patient_id).order_by(Prescription.created_at.desc()).all()
        labs = db.query(LabReport).filter(LabReport.patient_id == patient_id).order_by(LabReport.created_at.desc()).all()
        bills = db.query(Billing).filter(Billing.patient_id == patient_id).order_by(Billing.created_at.desc()).all()
        claims = db.query(Insurance).filter(Insurance.patient_id == patient_id).order_by(Insurance.created_at.desc()).all()

        lines.extend(_section("Patient Profile", _patient_header(patient)))
        lines.extend([""])
        lines.extend(_section("Appointments", [
            f"- Appointment {a.id}: doctor_id={a.doctor_id}, date={a.appointment_date}, slot={a.time_slot}, status={a.status}, reason={a.reason}"
            for a in appointments
        ]))
        lines.extend([""])
        lines.extend(_section("Medical Records", [
            f"- Record {r.id}: doctor_id={r.doctor_id}, diagnosis={r.diagnosis}, symptoms={r.symptoms}, treatment_plan={r.treatment_plan}, notes={r.notes}, date={r.created_at}"
            for r in records
        ]))
        lines.extend([""])
        lines.extend(_section("Prescriptions", [
            f"- Prescription {p.id}: doctor_id={p.doctor_id}, drug={p.drug_name}, dosage={p.dosage}, frequency={p.frequency}, duration={p.duration}, notes={p.notes}, date={p.created_at}"
            for p in prescriptions
        ]))
        lines.extend([""])
        lines.extend(_section("Lab Reports", [
            f"- Lab {l.id}: doctor_id={l.doctor_id}, test={l.test_type}, value={l.test_value}, normal_range={l.normal_range}, flag={l.flag}, status={l.status}, date={l.created_at}"
            for l in labs
        ]))
        lines.extend([""])
        lines.extend(_section("Billing Records", [
            f"- Bill {b.id}: appointment_id={b.appointment_id}, amount={b.amount}, payment_status={b.payment_status}, payment_method={b.payment_method}, date={b.created_at}"
            for b in bills
        ]))
        lines.extend([""])
        lines.extend(_section("Insurance Details", [
            f"- Claim {c.id}: provider={c.provider_name}, policy_number={c.policy_number}, amount={c.claim_amount}, status={c.claim_status}, date={c.created_at}"
            for c in claims
        ]))

    elif doc_type == "hospital_billing_records":
        bills = db.query(Billing).order_by(Billing.created_at.desc()).all()
        total_amount = sum(float(b.amount or 0) for b in bills)
        pending_amount = sum(float(b.amount or 0) for b in bills if b.payment_status != "PAID")
        lines.extend([
            "Summary",
            f"- Total bills: {len(bills)}",
            f"- Total amount: {total_amount}",
            f"- Pending or unpaid amount: {pending_amount}",
            "",
        ])
        lines.extend(_section("Billing Records", [
            f"- Bill {b.id}: patient_id={b.patient_id}, appointment_id={b.appointment_id}, amount={b.amount}, payment_status={b.payment_status}, payment_method={b.payment_method}, date={b.created_at}"
            for b in bills
        ]))

    elif doc_type == "patient_lab_reports":
        labs = db.query(LabReport).filter(LabReport.patient_id == patient_id).order_by(LabReport.created_at.desc()).all()
        lines.extend(_section("Patient Profile", _patient_header(patient)))
        lines.extend([""])
        lines.extend(_section("Lab Reports", [
            f"- Lab {l.id}: doctor_id={l.doctor_id}, test={l.test_type}, value={l.test_value}, normal_range={l.normal_range}, flag={l.flag}, status={l.status}, date={l.created_at}"
            for l in labs
        ]))

    elif doc_type == "patient_insurance_details":
        claims = db.query(Insurance).filter(Insurance.patient_id == patient_id).order_by(Insurance.created_at.desc()).all()
        lines.extend(_section("Patient Profile", _patient_header(patient)))
        lines.extend([""])
        lines.extend(_section("Insurance Details", [
            f"- Claim {c.id}: provider={c.provider_name}, policy_number={c.policy_number}, amount={c.claim_amount}, status={c.claim_status}, date={c.created_at}"
            for c in claims
        ]))

    lines.extend([
        "",
        "Security Note",
        "This confidential document is stored in Secure Document Vault and is only available after SUPER_ADMIN approval.",
    ])

    request = _create_vault_request(
        db=db,
        actor=actor,
        title=doc_title,
        document_type=doc_type,
        content="\n".join(lines),
        patient_id=patient_id,
    )

    return {
        "status": "PENDING_ADMIN_APPROVAL",
        "request_id": request.id,
        "title": request.title,
        "category": request.category,
        "document_type": request.document_type,
        "patient_id": request.patient_id,
        "message": "Confidential document generated in Secure Document Vault and is awaiting SUPER_ADMIN approval.",
        "content_visible": False,
        "vault_url": "/vault",
    }

def _month_window(month="last", year=None):
    today = datetime.utcnow().date()

    if isinstance(month, str) and month.lower() == "last":
        first_this_month = today.replace(day=1)
        end = first_this_month
        start = (first_this_month - timedelta(days=1)).replace(day=1)
        return start, end

    month_num = int(month)
    year_num = int(year or today.year)
    start = datetime(year_num, month_num, 1).date()
    if month_num == 12:
        end = datetime(year_num + 1, 1, 1).date()
    else:
        end = datetime(year_num, month_num + 1, 1).date()
    return start, end


def generate_patient_records_report(db, month="last", year=None, title=None, actor=None, **kwargs):
    """
    Generate a private management document request and hold it for admin approval.
    The requester does not receive document content in chat or normal API responses.
    """
    if not actor or actor.role != "HOSPITAL_SUPERVISOR":
        return {"error": "Only HOSPITAL_SUPERVISOR can generate patient records documents"}

    try:
        start_date, end_date = _month_window(month=month, year=year)
    except Exception:
        return {"error": "Invalid month/year. Use month='last' or month number 1-12 with optional year."}

    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.min.time())

    appointments = db.query(Appointment).filter(
        Appointment.appointment_date >= start_date,
        Appointment.appointment_date < end_date,
    ).all()
    medical_records = db.query(MedicalRecord).filter(
        MedicalRecord.created_at >= start_dt,
        MedicalRecord.created_at < end_dt,
    ).all()
    prescriptions = db.query(Prescription).filter(
        Prescription.created_at >= start_dt,
        Prescription.created_at < end_dt,
    ).all()
    lab_reports = db.query(LabReport).filter(
        LabReport.created_at >= start_dt,
        LabReport.created_at < end_dt,
    ).all()
    bills = db.query(Billing).filter(
        Billing.created_at >= start_dt,
        Billing.created_at < end_dt,
    ).all()

    patient_ids = {
        item.patient_id
        for group in (appointments, medical_records, prescriptions, lab_reports, bills)
        for item in group
        if getattr(item, "patient_id", None)
    }
    patients = db.query(Patient).filter(Patient.id.in_(patient_ids)).all() if patient_ids else []

    abnormal_labs = [r for r in lab_reports if r.flag and r.flag.upper() != "NORMAL"]
    pending_bills = [b for b in bills if b.payment_status != "PAID"]

    report_title = title or f"Patient Records Summary Document ({start_date.isoformat()} to {(end_date - timedelta(days=1)).isoformat()})"
    content = "\n".join([
        report_title,
        "",
        f"Generated by: {actor.username} ({actor.role})",
        f"Period: {start_date.isoformat()} to {(end_date - timedelta(days=1)).isoformat()}",
        "",
        "Summary",
        f"- Unique patients with activity: {len(patient_ids)}",
        f"- Appointments: {len(appointments)}",
        f"- Medical records created: {len(medical_records)}",
        f"- Prescriptions created: {len(prescriptions)}",
        f"- Lab reports created: {len(lab_reports)}",
        f"- Abnormal lab reports: {len(abnormal_labs)}",
        f"- Bills generated: {len(bills)}",
        f"- Pending or unpaid bills: {len(pending_bills)}",
        "",
        "Patients Included",
        *[
            f"- Patient {p.id}: {p.full_name}, assigned_doctor_id={p.assigned_doctor_id}, summary={p.disease_summary}"
            for p in patients
        ],
        "",
        "Governance Note",
        "This document is restricted to senior management. It is a summarized operational report and does not include full raw clinical notes.",
    ])

    delay_seconds = float(os.getenv("REPORT_GENERATION_DELAY_SECONDS", "5"))
    if delay_seconds > 0:
        time.sleep(delay_seconds)

    report = ManagementReportRequest(
        requested_by_user_id=actor.id,
        requested_by_username=actor.username,
        requested_by_role=actor.role,
        title=report_title,
        category="document",
        document_type="patient_records_summary",
        content="Confidential document generated and stored in Secure Document Vault. Content is not returned in chat.",
        status="PENDING_ADMIN_APPROVAL",
        period_start=start_date,
        period_end=end_date - timedelta(days=1),
        available_at=datetime.utcnow(),
    )
    db.add(report)
    db.commit()
    report.secure_file_path = _write_secure_document(report.id, report.title, content)
    db.commit()

    return {
        "status": "PENDING_ADMIN_APPROVAL",
        "request_id": report.id,
        "title": report.title,
        "category": report.category,
        "document_type": report.document_type,
        "period_start": start_date.isoformat(),
        "period_end": (end_date - timedelta(days=1)).isoformat(),
        "message": "Confidential document generated in Secure Document Vault and is awaiting SUPER_ADMIN approval.",
        "content_visible": False,
        "vault_url": "/vault",
    }


def get_my_report_requests(db, status=None, limit=20, actor=None, **kwargs):
    """List report requests created by the current management user without exposing private content."""
    if not actor or actor.role not in ("SUPER_ADMIN", "HOSPITAL_SUPERVISOR"):
        return {"error": "Only management users can list management report requests"}

    query = db.query(ManagementReportRequest).filter(
        ManagementReportRequest.requested_by_user_id == actor.id
    )
    if status:
        query = query.filter(ManagementReportRequest.status == status)

    reports = query.order_by(ManagementReportRequest.created_at.desc()).limit(limit).all()
    return {
        "requests": [
            {
                "request_id": r.id,
                "title": r.title,
                "category": r.category,
                "document_type": r.document_type,
                "patient_id": r.patient_id,
                "status": r.status,
                "period_start": str(r.period_start),
                "period_end": str(r.period_end),
                "created_at": str(r.created_at),
                "approved_by": r.approved_by_username,
                "approved_at": str(r.approved_at) if r.approved_at else None,
                "rejection_reason": r.rejection_reason,
                "content_visible": False,
                "vault_url": "/vault" if r.status == "APPROVED" else None,
            }
            for r in reports
        ]
    }


def get_approved_management_report(db, request_id, actor=None, **kwargs):
    """Return vault access metadata only after admin approval."""
    if not actor or actor.role not in ("SUPER_ADMIN", "HOSPITAL_SUPERVISOR"):
        return {"error": "Only management users can read approved management reports"}

    report = db.query(ManagementReportRequest).filter(ManagementReportRequest.id == request_id).first()
    if not report:
        return {"error": f"Report request {request_id} not found"}

    if actor.role != "SUPER_ADMIN" and report.requested_by_user_id != actor.id:
        return {"error": "You can only read reports requested by your own account"}

    if report.status != "APPROVED":
        return {
            "request_id": report.id,
            "status": report.status,
            "message": "Document content is private until SUPER_ADMIN approval.",
            "content_visible": False,
        }

    return {
        "request_id": report.id,
        "title": report.title,
        "status": report.status,
        "category": report.category,
        "document_type": report.document_type,
        "patient_id": report.patient_id,
        "period_start": str(report.period_start),
        "period_end": str(report.period_end),
        "approved_by": report.approved_by_username,
        "approved_at": str(report.approved_at),
        "message": "Document is approved. Open the Secure Document Vault and sign in again to view it.",
        "vault_url": "/vault",
        "content_visible": False,
    }


def list_pending_report_requests(db, limit=20, actor=None, **kwargs):
    """Admin-only queue of private report requests awaiting approval."""
    if not actor or actor.role != "SUPER_ADMIN":
        return {"error": "Only SUPER_ADMIN can list pending report approval requests"}

    reports = (
        db.query(ManagementReportRequest)
        .filter(ManagementReportRequest.status == "PENDING_ADMIN_APPROVAL")
        .order_by(ManagementReportRequest.created_at.asc())
        .limit(limit)
        .all()
    )
    return {
        "pending_requests": [
            {
                "request_id": r.id,
                "title": r.title,
                "requested_by": r.requested_by_username,
                "requested_by_role": r.requested_by_role,
                "category": r.category,
                "document_type": r.document_type,
                "patient_id": r.patient_id,
                "period_start": str(r.period_start),
                "period_end": str(r.period_end),
                "created_at": str(r.created_at),
                "content_preview": "Confidential document content is stored in Secure Document Vault and hidden from chat/API previews.",
            }
            for r in reports
        ]
    }


def approve_report_request(db, request_id, actor=None, **kwargs):
    """Admin-only approval for a private report request."""
    if not actor or actor.role != "SUPER_ADMIN":
        return {"error": "Only SUPER_ADMIN can approve report requests"}

    report = db.query(ManagementReportRequest).filter(ManagementReportRequest.id == request_id).first()
    if not report:
        return {"error": f"Report request {request_id} not found"}
    if report.status != "PENDING_ADMIN_APPROVAL":
        return {"error": f"Report request {request_id} is not pending approval"}

    report.status = "APPROVED"
    report.approved_by_user_id = actor.id
    report.approved_by_username = actor.username
    report.approved_at = datetime.utcnow()
    db.commit()
    return {
        "request_id": report.id,
        "status": report.status,
        "approved_by": report.approved_by_username,
        "message": "Document approved. The requester can now sign in to the Secure Document Vault to view it.",
        "vault_url": "/vault",
    }


def reject_report_request(db, request_id, reason=None, actor=None, **kwargs):
    """Admin-only rejection for a private report request."""
    if not actor or actor.role != "SUPER_ADMIN":
        return {"error": "Only SUPER_ADMIN can reject report requests"}

    report = db.query(ManagementReportRequest).filter(ManagementReportRequest.id == request_id).first()
    if not report:
        return {"error": f"Report request {request_id} not found"}
    if report.status != "PENDING_ADMIN_APPROVAL":
        return {"error": f"Report request {request_id} is not pending approval"}

    report.status = "REJECTED"
    report.rejection_reason = reason or "Rejected by administrator"
    report.approved_by_user_id = actor.id
    report.approved_by_username = actor.username
    report.approved_at = datetime.utcnow()
    db.commit()
    return {
        "request_id": report.id,
        "status": report.status,
        "reason": report.rejection_reason,
    }
