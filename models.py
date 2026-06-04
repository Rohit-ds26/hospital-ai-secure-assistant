from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, DateTime, Boolean, Date
from datetime import datetime
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine("sqlite:///hospital.db", echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# =====================================================================
# 1. Users Table — Authentication & Role
# =====================================================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    role = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)


# =====================================================================
# 2. Hospital Staff Table
# =====================================================================

class HospitalStaff(Base):
    __tablename__ = "hospital_staff"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    employee_id = Column(String, unique=True)
    department = Column(String)
    role = Column(String)
    title = Column(String)

    user = relationship("User")


# =====================================================================
# 3. Doctors Table
# =====================================================================

class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    full_name = Column(String, nullable=False)
    specialization = Column(String)
    license_number = Column(String, unique=True)
    department = Column(String)
    availability_status = Column(String, default="AVAILABLE")

    user = relationship("User")
    appointments = relationship("Appointment", back_populates="doctor")
    medical_records = relationship("MedicalRecord", back_populates="doctor")
    prescriptions = relationship("Prescription", back_populates="doctor")
    lab_reports = relationship("LabReport", back_populates="doctor")


# =====================================================================
# 4. Patients Table
# =====================================================================

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    full_name = Column(String, nullable=False)
    dob = Column(Date)
    gender = Column(String)
    blood_group = Column(String)
    phone = Column(String)
    email = Column(String)
    address = Column(Text)
    emergency_contact = Column(String)
    assigned_doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    disease_summary = Column(Text)

    user = relationship("User")
    assigned_doctor = relationship("Doctor")
    appointments = relationship("Appointment", back_populates="patient")
    medical_records = relationship("MedicalRecord", back_populates="patient")
    prescriptions = relationship("Prescription", back_populates="patient")
    lab_reports = relationship("LabReport", back_populates="patient")
    bills = relationship("Billing", back_populates="patient")
    insurance_claims = relationship("Insurance", back_populates="patient")


# =====================================================================
# 5. Appointments Table
# =====================================================================

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    appointment_date = Column(Date, nullable=False)
    time_slot = Column(String, nullable=False)
    reason = Column(Text)
    status = Column(String, default="SCHEDULED")
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")


# =====================================================================
# 6. Medical Records Table
# =====================================================================

class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    symptoms = Column(Text)
    diagnosis = Column(Text)
    treatment_plan = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="medical_records")
    doctor = relationship("Doctor", back_populates="medical_records")


# =====================================================================
# 7. Prescriptions Table
# =====================================================================

class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    drug_name = Column(String, nullable=False)
    dosage = Column(String)
    frequency = Column(String)
    duration = Column(String)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="prescriptions")
    doctor = relationship("Doctor", back_populates="prescriptions")


# =====================================================================
# 8. Lab Reports Table
# =====================================================================

class LabReport(Base):
    __tablename__ = "lab_reports"

    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    test_type = Column(String, nullable=False)
    test_value = Column(String)
    normal_range = Column(String)
    flag = Column(String, default="NORMAL")
    status = Column(String, default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="lab_reports")
    doctor = relationship("Doctor", back_populates="lab_reports")


# =====================================================================
# 9. Billing Table
# =====================================================================

class Billing(Base):
    __tablename__ = "billing"

    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    amount = Column(Float, nullable=False)
    payment_status = Column(String, default="PENDING")
    payment_method = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="bills")


# =====================================================================
# 10. Insurance Table
# =====================================================================

class Insurance(Base):
    __tablename__ = "insurance"

    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    provider_name = Column(String)
    policy_number = Column(String)
    claim_amount = Column(Float)
    claim_status = Column(String, default="SUBMITTED")
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="insurance_claims")


# =====================================================================
# 11. Hospital Documents Table (for RAG)
# =====================================================================

class HospitalDocument(Base):
    __tablename__ = "hospital_documents"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    category = Column(String)
    content = Column(Text)
    access_level = Column(String, default="internal")


# =====================================================================
# 12. Audit Logs Table
# =====================================================================

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    username = Column(String)
    role = Column(String)
    action = Column(String)
    resource = Column(String)
    success = Column(Boolean, default=True)
    details = Column(Text)
# =====================================================================
# 13. Pharmacy Table (Merchant Equivalent)
# =====================================================================

class Pharmacy(Base):
    __tablename__ = "pharmacies"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    address = Column(Text)
    contact_phone = Column(String)
    license_number = Column(String, unique=True)
    is_internal = Column(Boolean, default=True)


# =====================================================================
# 14. Clinical Safety Rules Table (FraudRule Equivalent)
# =====================================================================

class ClinicalSafetyRule(Base):
    __tablename__ = "clinical_safety_rules"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    trigger_type = Column(String)  # e.g., DRUG_INTERACTION, DOSAGE_VOI, PATIENT_ALLERGY
    risk_level = Column(String, default="LOW")  # LOW, MEDIUM, HIGH, CRITICAL
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# =====================================================================
# 15. Hospital Analytics Table (InternalAnalytics Equivalent)
# =====================================================================

class HospitalAnalytics(Base):
    __tablename__ = "hospital_analytics"

    id = Column(Integer, primary_key=True)
    metric_name = Column(String, nullable=False)
    department = Column(String)
    value = Column(Float)
    unit = Column(String)
    recorded_at = Column(DateTime, default=datetime.utcnow)


# =====================================================================
# 16. Management Report Requests
# =====================================================================

class ManagementReportRequest(Base):
    __tablename__ = "management_report_requests"

    id = Column(Integer, primary_key=True)
    requested_by_user_id = Column(Integer, ForeignKey("users.id"))
    requested_by_username = Column(String)
    requested_by_role = Column(String)
    title = Column(String, nullable=False)
    category = Column(String, default="report")
    document_type = Column(String, default="management_document")
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    content = Column(Text)
    secure_file_path = Column(String, nullable=True)
    status = Column(String, default="GENERATING")
    period_start = Column(Date)
    period_end = Column(Date)
    approved_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by_username = Column(String, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    available_at = Column(DateTime, nullable=True)
