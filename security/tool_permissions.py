# =====================================================================
# RBAC: Role → Tool Access Map
# =====================================================================

ROLE_TOOL_MAP = {

    "SUPER_ADMIN": [
        # All tools
        "patient_profile", "patient_medical_history", "update_patient_details",
        "get_doctor_details", "update_doctor_availability",
        "book_appointment", "cancel_appointment", "get_appointments",
        "create_medical_record", "get_medical_records", "update_treatment_plan",
        "create_prescription", "get_prescriptions",
        "upload_lab_report", "get_lab_reports", "update_lab_report_status",
        "generate_bill", "get_billing_details", "update_payment_status",
        "submit_insurance_claim", "get_insurance_claims", "update_claim_status",
        "search_hospital_docs", "get_document_by_category",
        "get_audit_logs",
        "get_clinical_safety_rules", "create_clinical_safety_rule", "toggle_clinical_safety_rule",
        "get_hospital_analytics",
        "get_my_report_requests", "get_approved_management_report",
        "list_pending_report_requests", "approve_report_request", "reject_report_request",
        "list_pharmacies", "get_pharmacy_details",
    ],

    "HOSPITAL_SUPERVISOR": [
        "patient_profile",
        "get_doctor_details",
        "get_appointments",
        "search_hospital_docs", "get_document_by_category",
        "get_audit_logs",
        "get_hospital_analytics",
        "get_clinical_safety_rules",
        "create_secure_document_request",
        "generate_patient_records_report",
        "get_my_report_requests", "get_approved_management_report",
        "list_pharmacies",
    ],

    "DOCTOR": [
        "patient_profile", "patient_medical_history", "update_patient_details",
        "get_doctor_details", "update_doctor_availability",
        "get_appointments",
        "create_medical_record", "get_medical_records", "update_treatment_plan",
        "create_prescription", "get_prescriptions",
        "get_lab_reports",
        "search_hospital_docs", "get_document_by_category",
        "get_clinical_safety_rules",
        "list_pharmacies", "get_pharmacy_details",
    ],

    "NURSE": [
        "patient_profile", "patient_medical_history", "update_patient_details",
        "get_medical_records",
        "get_prescriptions",
        "get_lab_reports",
        "search_hospital_docs",
    ],

    "LAB_TECH": [
        "upload_lab_report", "get_lab_reports", "update_lab_report_status",
        "search_hospital_docs",
    ],

    "RECEPTIONIST": [
        "patient_profile", "update_patient_details",
        "get_doctor_details",
        "book_appointment", "cancel_appointment", "get_appointments",
        "search_hospital_docs",
    ],

    "BILLING_INSURANCE": [
        "generate_bill", "get_billing_details", "update_payment_status",
        "submit_insurance_claim", "get_insurance_claims", "update_claim_status",
    ],

    "PATIENT": [
        "patient_profile", "patient_medical_history",
        "book_appointment", "cancel_appointment", "get_appointments",
        "get_medical_records",
        "get_prescriptions",
        "get_lab_reports",
        "get_billing_details",
        "submit_insurance_claim", "get_insurance_claims",
    ],
}


def tools_for_role(role, all_tool_schemas):
    """Filter tool schemas to only include tools allowed for the role."""

    allowed = ROLE_TOOL_MAP.get(role, [])

    filtered = []

    for schema in all_tool_schemas:
        name = schema["function"]["name"]
        if name in allowed:
            filtered.append(schema)

    return filtered
