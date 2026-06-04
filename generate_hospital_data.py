"""
Hospital AI System — Synthetic Data Generator
Run once to populate the SQLite database with realistic test data.
"""

import os
import sys
import random
from datetime import datetime, timedelta, date
from passlib.hash import bcrypt

# Ensure we can import models
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import (
    Base, engine, SessionLocal,
    User, HospitalStaff, Doctor, Patient,
    Appointment, MedicalRecord, Prescription, LabReport,
    Billing, Insurance, HospitalDocument, AuditLog,
    Pharmacy, ClinicalSafetyRule, HospitalAnalytics,
)


def create_tables():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("[OK] All tables created.")


def seed_users(db):
    """Create all 8 role-based users."""

    users_data = [
        ("admin", "Admin@123", "SUPER_ADMIN"),
        ("supervisor1", "Supervisor@123", "HOSPITAL_SUPERVISOR"),
        ("doctor1", "Doctor@123", "DOCTOR"),
        ("doctor2", "Doctor@123", "DOCTOR"),
        ("doctor3", "Doctor@123", "DOCTOR"),
        ("nurse1", "Nurse@123", "NURSE"),
        ("nurse2", "Nurse@123", "NURSE"),
        ("labtech1", "LabTech@123", "LAB_TECH"),
        ("receptionist1", "Reception@123", "RECEPTIONIST"),
        ("billing1", "Billing@123", "BILLING_INSURANCE"),
        ("patient1", "Patient@123", "PATIENT"),
        ("patient2", "Patient@123", "PATIENT"),
        ("patient3", "Patient@123", "PATIENT"),
        ("patient4", "Patient@123", "PATIENT"),
        ("patient5", "Patient@123", "PATIENT"),
    ]

    for username, password, role in users_data:
        user = User(
            username=username,
            password_hash=bcrypt.hash(password),
            role=role,
        )
        db.add(user)

    db.commit()
    print(f"[OK] {len(users_data)} users created.")


def seed_staff(db):
    """Create hospital staff records for non-patient users."""

    staff_data = [
        ("admin", "EMP001", "Administration", "SUPER_ADMIN", "System Administrator"),
        ("supervisor1", "EMP002", "Operations", "HOSPITAL_SUPERVISOR", "Hospital Supervisor"),
        ("nurse1", "EMP003", "General Medicine", "NURSE", "Senior Nurse"),
        ("nurse2", "EMP004", "Emergency", "NURSE", "ER Nurse"),
        ("labtech1", "EMP005", "Pathology", "LAB_TECH", "Lab Technician"),
        ("receptionist1", "EMP006", "Front Desk", "RECEPTIONIST", "Front Desk Officer"),
        ("billing1", "EMP007", "Finance", "BILLING_INSURANCE", "Billing Officer"),
    ]

    for username, emp_id, dept, role, title in staff_data:
        user = db.query(User).filter(User.username == username).first()
        staff = HospitalStaff(
            user_id=user.id,
            employee_id=emp_id,
            department=dept,
            role=role,
            title=title,
        )
        db.add(staff)

    db.commit()
    print(f"[OK] {len(staff_data)} staff records created.")


def seed_doctors(db):
    """Create doctor profiles."""

    doctors_data = [
        ("doctor1", "Dr. Anil Sharma", "Cardiology", "MCI-2019-001", "Cardiology"),
        ("doctor2", "Dr. Priya Patel", "Orthopedics", "MCI-2020-042", "Orthopedics"),
        ("doctor3", "Dr. Rajesh Kumar", "General Medicine", "MCI-2018-103", "General Medicine"),
    ]

    for username, name, spec, license_no, dept in doctors_data:
        user = db.query(User).filter(User.username == username).first()
        doc = Doctor(
            user_id=user.id,
            full_name=name,
            specialization=spec,
            license_number=license_no,
            department=dept,
            availability_status="AVAILABLE",
        )
        db.add(doc)

    db.commit()
    print(f"[OK] {len(doctors_data)} doctors created.")


def seed_patients(db):
    """Create patient profiles with realistic data."""

    patients_data = [
        ("patient1", "Rohit Kumar", "1990-05-15", "Male", "B+",
         "9876543210", "rohit@email.com", "12, MG Road, Delhi",
         "9876543200", 1, "Hypertension, Chest pain history"),
        ("patient2", "Sneha Gupta", "1985-08-22", "Female", "O+",
         "9876543211", "sneha@email.com", "45, Park Street, Mumbai",
         "9876543201", 2, "Knee injury, Joint pain"),
        ("patient3", "Arjun Singh", "1978-12-03", "Male", "A-",
         "9876543212", "arjun@email.com", "78, Lake View, Bangalore",
         "9876543202", 3, "Type 2 Diabetes, Fatigue"),
        ("patient4", "Meera Joshi", "1995-03-10", "Female", None,
         "9876543213", "meera@email.com", "23, Hill Road, Pune",
         "9876543203", 1, None),
        ("patient5", "Vikram Reddy", "2000-11-25", "Male", "AB+",
         "9876543214", "vikram@email.com", "56, Beach Road, Chennai",
         "", 2, "Pt c/o chest pain x3d.\nRx advised.\nPoss HTN."),
    ]

    for (username, name, dob_str, gender, blood,
         phone, email, address, emergency, doc_id, disease) in patients_data:

        user = db.query(User).filter(User.username == username).first()
        patient = Patient(
            user_id=user.id,
            full_name=name,
            dob=date.fromisoformat(dob_str),
            gender=gender,
            blood_group=blood,
            phone=phone,
            email=email,
            address=address,
            emergency_contact=emergency,
            assigned_doctor_id=doc_id,
            disease_summary=disease,
        )
        db.add(patient)

    db.commit()
    print(f"[OK] {len(patients_data)} patients created.")


def seed_appointments(db):
    """Create realistic appointments."""

    appointments = [
        (1, 1, "2026-05-20", "09:00 AM", "Routine checkup", "COMPLETED"),
        (1, 1, "2026-06-05", "10:00 AM", "Follow-up ECG", "SCHEDULED"),
        (2, 2, "2026-05-18", "11:00 AM", "Knee pain consultation", "COMPLETED"),
        (2, 2, "2026-06-10", "02:00 PM", "X-Ray review", "SCHEDULED"),
        (3, 3, "2026-05-22", "09:30 AM", "Diabetes management", "COMPLETED"),
        (3, 3, "2026-06-15", "10:30 AM", "Blood sugar review", "SCHEDULED"),
        (4, 1, "2026-05-25", "03:00 PM", "General checkup", "COMPLETED"),
        (5, 2, "2026-06-01", "04:00 PM", "Chest pain evaluation", "SCHEDULED"),
    ]

    for pid, did, dt, slot, reason, status in appointments:
        appt = Appointment(
            patient_id=pid,
            doctor_id=did,
            appointment_date=date.fromisoformat(dt),
            time_slot=slot,
            reason=reason,
            status=status,
        )
        db.add(appt)

    db.commit()
    print(f"[OK] {len(appointments)} appointments created.")


def seed_medical_records(db):
    """Create medical records for completed appointments."""

    records = [
        (1, 1, 1, "Chest tightness, breathlessness",
         "Mild Hypertension", "Lifestyle modification, Amlodipine 5mg",
         "Patient advised low-salt diet. Follow up in 2 weeks."),
        (2, 2, 3, "Knee pain, swelling after fall",
         "ACL Sprain Grade II", "Rest, ice, compression. Physiotherapy recommended.",
         "X-ray shows no fracture. MRI advised if no improvement."),
        (3, 3, 5, "Fatigue, frequent urination, thirst",
         "T2DM", "Metformin 500mg BD. Diet control.",
         "HbA1c = 8.2%. Target <7%. Review in 3 months."),
        (4, 1, 7, "Routine health checkup",
         "No significant findings", "Continue existing lifestyle.",
         "All vitals normal. BMI 22.4."),
    ]

    for pid, did, appt_id, symptoms, diagnosis, treatment, notes in records:
        rec = MedicalRecord(
            patient_id=pid,
            doctor_id=did,
            appointment_id=appt_id,
            symptoms=symptoms,
            diagnosis=diagnosis,
            treatment_plan=treatment,
            notes=notes,
        )
        db.add(rec)

    db.commit()
    print(f"[OK] {len(records)} medical records created.")


def seed_prescriptions(db):
    """Create prescriptions."""

    prescriptions = [
        (1, 1, "Amlodipine", "5mg", "Once daily", "30 days", "Take in the morning"),
        (1, 1, "Aspirin", "75mg", "Once daily", "30 days", "After meals"),
        (2, 2, "Ibuprofen", "400mg", "Twice daily", "7 days", "After food. Avoid on empty stomach."),
        (3, 3, "Metformin", "500mg", "Twice daily", "90 days", "With meals"),
        (3, 3, "Glimepiride", "1mg", "Once daily", "90 days", "Before breakfast"),
    ]

    for pid, did, drug, dosage, freq, dur, notes in prescriptions:
        presc = Prescription(
            patient_id=pid,
            doctor_id=did,
            drug_name=drug,
            dosage=dosage,
            frequency=freq,
            duration=dur,
            notes=notes,
        )
        db.add(presc)

    db.commit()
    print(f"[OK] {len(prescriptions)} prescriptions created.")


def seed_lab_reports(db):
    """Create lab reports with realistic values including abnormal flags."""

    reports = [
        (1, 1, "Blood Pressure", "140/90 mmHg", "120/80 mmHg", "ABNORMAL", "COMPLETED"),
        (1, 1, "Cholesterol (Total)", "245 mg/dL", "<200 mg/dL", "ABNORMAL", "COMPLETED"),
        (1, 1, "ECG", "Sinus tachycardia", "Normal sinus rhythm", "ABNORMAL", "COMPLETED"),
        (2, 2, "X-Ray (Knee)", "No fracture detected", "Normal", "NORMAL", "COMPLETED"),
        (3, 3, "HbA1c", "8.2%", "<5.7%", "CRITICAL", "COMPLETED"),
        (3, 3, "Fasting Blood Sugar", "185 mg/dL", "70-100 mg/dL", "ABNORMAL", "COMPLETED"),
        (3, 3, "Serum Creatinine", "1.1 mg/dL", "0.7-1.3 mg/dL", "NORMAL", "COMPLETED"),
        (4, 1, "CBC", "All values normal", "Normal", "NORMAL", "COMPLETED"),
        (5, None, "Troponin I", "", "Normal <0.04 ng/mL", "NORMAL", "PENDING"),
    ]

    for pid, did, test, value, normal, flag, status in reports:
        lab = LabReport(
            patient_id=pid,
            doctor_id=did,
            test_type=test,
            test_value=value,
            normal_range=normal,
            flag=flag,
            status=status,
        )
        db.add(lab)

    db.commit()
    print(f"[OK] {len(reports)} lab reports created.")


def seed_billing(db):
    """Create billing records."""

    bills = [
        (1, 1, 1500.00, "PAID", "UPI"),
        (2, 3, 2500.00, "PAID", "Credit Card"),
        (3, 5, 800.00, "PENDING", None),
        (4, 7, 500.00, "PAID", "Cash"),
        (5, None, 3000.00, "PENDING", None),
    ]

    for pid, appt_id, amount, status, method in bills:
        bill = Billing(
            patient_id=pid,
            appointment_id=appt_id,
            amount=amount,
            payment_status=status,
            payment_method=method,
        )
        db.add(bill)

    db.commit()
    print(f"[OK] {len(bills)} billing records created.")


def seed_insurance(db):
    """Create insurance claims."""

    claims = [
        (1, "Star Health Insurance", "SH-2024-78901", 1500.00, "APPROVED"),
        (2, "ICICI Lombard", "IL-2024-45612", 2500.00, "SUBMITTED"),
        (3, "Max Bupa", "MB-2024-33210", 800.00, "REJECTED"),
        (5, "Star Health Insurance", "SH-2024-88100", 3000.00, "SUBMITTED"),
    ]

    for pid, provider, policy, amount, status in claims:
        ins = Insurance(
            patient_id=pid,
            provider_name=provider,
            policy_number=policy,
            claim_amount=amount,
            claim_status=status,
        )
        db.add(ins)

    db.commit()
    print(f"[OK] {len(claims)} insurance claims created.")


def seed_hospital_documents(db):
    """Create internal hospital documents for RAG retrieval."""

    docs = [
        ("Patient Admission Policy", "policy",
         "All patients must be registered at the front desk before admission. "
         "Emergency cases bypass registration and are admitted directly to the ER. "
         "Patient identity must be verified using government-issued ID. "
         "Insurance details should be captured at intake.",
         "internal"),

        ("Emergency Protocol — Cardiac Arrest", "emergency",
         "In the event of cardiac arrest: 1. Call Code Blue immediately. "
         "2. Begin CPR within 30 seconds. 3. Use AED if available. "
         "4. Notify the on-duty cardiologist. 5. Document time of arrest and interventions.",
         "restricted"),

        ("Data Privacy & PHI Guidelines", "compliance",
         "All patient health information (PHI) must be handled in compliance with hospital policy. "
         "Staff must not share patient records across departments without authorization. "
         "Electronic records must be accessed only through authenticated systems. "
         "Unauthorized access will result in immediate disciplinary action.",
         "restricted"),

        ("Medicine Dispensing SOP", "pharmacy",
         "All prescriptions must be verified by the pharmacist before dispensing. "
         "Controlled substances require dual authorization. "
         "Expired medications must be returned to the supplier. "
         "Stock levels must be updated in the inventory system after every transaction.",
         "internal"),

        ("Lab Report Turnaround Times", "lab",
         "Routine blood tests: 4-6 hours. Specialized tests (HbA1c, Lipid Panel): 12-24 hours. "
         "Radiology (X-Ray): 2 hours. MRI/CT Scan: 24-48 hours. "
         "Critical results must be reported to the attending physician within 30 minutes.",
         "internal"),

        ("Patient Rights & Responsibilities", "public",
         "Every patient has the right to receive respectful and compassionate care. "
         "Patients can request copies of their medical records at any time. "
         "Patients must provide accurate health information to their physicians. "
         "Patients can refuse treatment after being informed of consequences.",
         "public"),

        ("Insurance Claim Processing", "finance",
         "Insurance claims must be submitted within 48 hours of discharge. "
         "All claim forms must include the patient ID, diagnosis code (ICD-10), and treatment summary. "
         "Rejected claims should be reviewed by the billing supervisor before resubmission. "
         "Cashless claims require pre-authorization from the insurance provider.",
         "internal"),

        ("HIV & Mental Health Confidentiality", "compliance",
         "HIV status and mental health records are classified as highly sensitive PHI. "
         "Access is restricted to the treating physician and authorized personnel only. "
         "These records must never appear in general medical summaries or discharge notes. "
         "Violation of this policy is grounds for termination and legal action.",
         "restricted"),
    ]

    for title, category, content, access_level in docs:
        doc = HospitalDocument(
            title=title,
            category=category,
            content=content,
            access_level=access_level,
        )
        db.add(doc)

    db.commit()
    print(f"[OK] {len(docs)} hospital documents created.")


def seed_audit_logs(db):
    """Create sample audit logs."""

    logs = [
        ("admin", "SUPER_ADMIN", "CREATE_USER", "users", True, "Created user doctor1"),
        ("doctor1", "DOCTOR", "VIEW_PATIENT", "patients/1", True, "Viewed patient Rohit Kumar"),
        ("nurse1", "NURSE", "UPDATE_VITALS", "patients/3", True, "Updated BP for patient 3"),
        ("patient1", "PATIENT", "VIEW_OWN_RECORD", "medical_records", True, "Viewed own medical records"),
        ("labtech1", "LAB_TECH", "UPLOAD_REPORT", "lab_reports", True, "Uploaded CBC for patient 4"),
        ("patient2", "PATIENT", "ATTEMPT_ACCESS", "patients/1", False, "Attempted to view another patient's record — BLOCKED"),
    ]

    for username, role, action, resource, success, details in logs:
        log = AuditLog(
            username=username,
            role=role,
            action=action,
            resource=resource,
            success=success,
            details=details,
        )
        db.add(log)

    db.commit()
    print(f"[OK] {len(logs)} audit logs created.")


def seed_pharmacies(db):
    """Create pharmacy records."""
    pharmacies = [
        ("Acme Internal Pharmacy", "Floor 1, Hospital Block A", "555-0101", "PHARM-2024-001", True),
        ("City Central Meds", "Sector 5, Downtown", "555-0102", "PHARM-2024-002", False),
        ("Wellness Drugstore", "Gali 4, East Side", "555-0103", "PHARM-2024-003", False),
    ]
    for name, addr, phone, lic, internal in pharmacies:
        pharmacy = Pharmacy(name=name, address=addr, contact_phone=phone, license_number=lic, is_internal=internal)
        db.add(pharmacy)
    db.commit()
    print(f"[OK] {len(pharmacies)} pharmacies created.")


def seed_clinical_safety_rules(db):
    """Create clinical safety rules."""
    rules = [
        ("Warfarin-Aspirin Interaction", "Severe bleeding risk when taken together.", "DRUG_INTERACTION", "CRITICAL"),
        ("Penicillin Allergy Alert", "Automatic trigger for patients with known penicillin allergy.", "PATIENT_ALLERGY", "HIGH"),
        ("Max Daily Morphine Dosage", "Alert if daily dosage exceeds 50mg.", "DOSAGE_VOI", "MEDIUM"),
        ("Beta Blocker - Asthma Contraindication", "Check for asthma history before prescribing beta blockers.", "DRUG_INTERACTION", "HIGH"),
    ]
    for name, desc, trigger, risk in rules:
        rule = ClinicalSafetyRule(name=name, description=desc, trigger_type=trigger, risk_level=risk, is_active=True)
        db.add(rule)
    db.commit()
    print(f"[OK] {len(rules)} clinical safety rules created.")


def seed_hospital_analytics(db):
    """Create sample hospital analytics data."""
    analytics = [
        ("Patient Wait Time", "Emergency", 12.5, "minutes"),
        ("Bed Occupancy Rate", "General Ward", 88.0, "%"),
        ("Average Discharge Time", "Orthopedics", 4.2, "days"),
        ("Lab Report TAT", "Pathology", 5.5, "hours"),
        ("Surgical Success Rate", "Cardiology", 96.5, "%"),
    ]
    for name, dept, value, unit in analytics:
        stat = HospitalAnalytics(metric_name=name, department=dept, value=value, unit=unit)
        db.add(stat)
    db.commit()
    print(f"[OK] {len(analytics)} analytics metrics created.")


# =====================================================================
# Main
# =====================================================================

if __name__ == "__main__":

    print("\n========================================")
    print("  Hospital AI System — Data Generator")
    print("========================================\n")

    create_tables()

    db = SessionLocal()

    try:
        seed_users(db)
        seed_staff(db)
        seed_doctors(db)
        seed_patients(db)
        seed_appointments(db)
        seed_medical_records(db)
        seed_prescriptions(db)
        seed_lab_reports(db)
        seed_billing(db)
        seed_insurance(db)
        seed_hospital_documents(db)
        seed_audit_logs(db)
        seed_pharmacies(db)
        seed_clinical_safety_rules(db)
        seed_hospital_analytics(db)
    finally:
        db.close()

    print("\n========================================")
    print("  Database populated successfully!")
    print("  File: hospital.db")
    print("========================================\n")
