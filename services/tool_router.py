import json
from security.access_control import normalize_patient_scope
from security.audit import log_audit
from security.tool_permissions import ROLE_TOOL_MAP

from tools.patient_tools import patient_profile, patient_medical_history, update_patient_details
from tools.doctor_tools import get_doctor_details, update_doctor_availability
from tools.appointment_tools import book_appointment, cancel_appointment, get_appointments
from tools.medical_record_tools import create_medical_record, get_medical_records, update_treatment_plan
from tools.prescription_tools import create_prescription, get_prescriptions
from tools.lab_tools import upload_lab_report, get_lab_reports, update_lab_report_status
from tools.billing_tools import generate_bill, get_billing_details, update_payment_status
from tools.insurance_tools import submit_insurance_claim, get_insurance_claims, update_claim_status
from tools.doc_tools import search_hospital_docs, get_document_by_category
from tools.admin_tools import (
    get_audit_logs,
    get_clinical_safety_rules,
    create_clinical_safety_rule,
    toggle_clinical_safety_rule,
    get_hospital_analytics,
    create_secure_document_request,
    generate_patient_records_report,
    get_my_report_requests,
    get_approved_management_report,
    list_pending_report_requests,
    approve_report_request,
    reject_report_request,
)
from tools.pharmacy_tools import list_pharmacies, get_pharmacy_details


# =====================================================================
# Tool Schemas — What the LLM sees
# =====================================================================

TOOL_SCHEMAS = [

    # ---- Patient Tools ----

    {
        "type": "function",
        "function": {
            "name": "patient_profile",
            "description": "Retrieve a patient's profile information including name, DOB, blood group, contact, and assigned doctor.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "integer", "description": "Patient ID"}
                },
                "required": ["patient_id"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "patient_medical_history",
            "description": "Retrieve a patient's full medical history including records, prescriptions, and lab reports.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "integer", "description": "Patient ID"},
                    "limit": {"type": "integer", "default": 10}
                },
                "required": ["patient_id"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "update_patient_details",
            "description": "Update patient contact details (phone, email, address, emergency_contact).",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "integer", "description": "Patient ID"},
                    "phone": {"type": "string", "description": "New phone number"},
                    "email": {"type": "string", "description": "New email"},
                    "address": {"type": "string", "description": "New address"},
                    "emergency_contact": {"type": "string", "description": "New emergency contact"}
                },
                "required": ["patient_id"]
            }
        }
    },

    # ---- Doctor Tools ----

    {
        "type": "function",
        "function": {
            "name": "get_doctor_details",
            "description": "Retrieve a doctor's professional details including specialization, department, and availability.",
            "parameters": {
                "type": "object",
                "properties": {
                    "doctor_id": {"type": "integer", "description": "Doctor ID"}
                },
                "required": ["doctor_id"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "update_doctor_availability",
            "description": "Update a doctor's availability status (AVAILABLE, BUSY, ON_LEAVE, OFF_DUTY).",
            "parameters": {
                "type": "object",
                "properties": {
                    "doctor_id": {"type": "integer", "description": "Doctor ID"},
                    "availability_status": {"type": "string", "description": "New status: AVAILABLE, BUSY, ON_LEAVE, or OFF_DUTY"}
                },
                "required": ["doctor_id", "availability_status"]
            }
        }
    },

    # ---- Appointment Tools ----

    {
        "type": "function",
        "function": {
            "name": "book_appointment",
            "description": "Book a new appointment for a patient with a doctor.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "integer"},
                    "doctor_id": {"type": "integer"},
                    "appointment_date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                    "time_slot": {"type": "string", "description": "Time slot e.g. 09:00 AM"},
                    "reason": {"type": "string", "description": "Reason for appointment"}
                },
                "required": ["patient_id", "doctor_id", "appointment_date", "time_slot"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "cancel_appointment",
            "description": "Cancel an existing appointment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "appointment_id": {"type": "integer", "description": "Appointment ID to cancel"}
                },
                "required": ["appointment_id"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "get_appointments",
            "description": "Retrieve appointments. Optionally filter by patient_id, doctor_id, or status (SCHEDULED, COMPLETED, CANCELLED).",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "integer", "description": "Filter by patient"},
                    "doctor_id": {"type": "integer", "description": "Filter by doctor"},
                    "status": {"type": "string", "description": "Filter by status"},
                    "limit": {"type": "integer", "default": 20}
                },
                "required": []
            }
        }
    },

    # ---- Medical Record Tools ----

    {
        "type": "function",
        "function": {
            "name": "create_medical_record",
            "description": "Create a new medical record for a patient visit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "integer"},
                    "doctor_id": {"type": "integer"},
                    "symptoms": {"type": "string"},
                    "diagnosis": {"type": "string"},
                    "treatment_plan": {"type": "string"},
                    "notes": {"type": "string"},
                    "appointment_id": {"type": "integer"}
                },
                "required": ["patient_id", "doctor_id", "symptoms", "diagnosis", "treatment_plan"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "get_medical_records",
            "description": "Retrieve medical records for a patient.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "integer", "description": "Patient ID"},
                    "limit": {"type": "integer", "default": 10}
                },
                "required": ["patient_id"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "update_treatment_plan",
            "description": "Update the treatment plan for an existing medical record.",
            "parameters": {
                "type": "object",
                "properties": {
                    "record_id": {"type": "integer", "description": "Medical record ID"},
                    "treatment_plan": {"type": "string", "description": "Updated treatment plan"}
                },
                "required": ["record_id", "treatment_plan"]
            }
        }
    },

    # ---- Prescription Tools ----

    {
        "type": "function",
        "function": {
            "name": "create_prescription",
            "description": "Create a new prescription for a patient.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "integer"},
                    "doctor_id": {"type": "integer"},
                    "drug_name": {"type": "string"},
                    "dosage": {"type": "string"},
                    "frequency": {"type": "string", "description": "e.g. Once daily, Twice daily"},
                    "duration": {"type": "string", "description": "e.g. 30 days"},
                    "notes": {"type": "string"}
                },
                "required": ["patient_id", "doctor_id", "drug_name", "dosage", "frequency", "duration"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "get_prescriptions",
            "description": "Retrieve prescriptions for a patient.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "integer"},
                    "limit": {"type": "integer", "default": 20}
                },
                "required": ["patient_id"]
            }
        }
    },

    # ---- Lab Report Tools ----

    {
        "type": "function",
        "function": {
            "name": "upload_lab_report",
            "description": "Upload a new lab report for a patient.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "integer"},
                    "test_type": {"type": "string", "description": "Type of test e.g. CBC, Blood Sugar"},
                    "test_value": {"type": "string"},
                    "normal_range": {"type": "string"},
                    "flag": {"type": "string", "description": "NORMAL, ABNORMAL, or CRITICAL"},
                    "doctor_id": {"type": "integer"}
                },
                "required": ["patient_id", "test_type", "test_value", "normal_range"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "get_lab_reports",
            "description": "Retrieve lab reports for a patient.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "integer"},
                    "limit": {"type": "integer", "default": 20}
                },
                "required": ["patient_id"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "update_lab_report_status",
            "description": "Update the status of a lab report (PENDING, COMPLETED, REJECTED).",
            "parameters": {
                "type": "object",
                "properties": {
                    "report_id": {"type": "integer"},
                    "status": {"type": "string", "description": "PENDING, COMPLETED, or REJECTED"}
                },
                "required": ["report_id", "status"]
            }
        }
    },

    # ---- Billing Tools ----

    {
        "type": "function",
        "function": {
            "name": "generate_bill",
            "description": "Generate a bill for a patient.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "integer"},
                    "amount": {"type": "number"},
                    "appointment_id": {"type": "integer"},
                    "payment_method": {"type": "string"}
                },
                "required": ["patient_id", "amount"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "get_billing_details",
            "description": "Retrieve billing details for a patient.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "integer"},
                    "limit": {"type": "integer", "default": 20}
                },
                "required": ["patient_id"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "update_payment_status",
            "description": "Update payment status for a bill (PENDING, PAID, OVERDUE, REFUNDED).",
            "parameters": {
                "type": "object",
                "properties": {
                    "bill_id": {"type": "integer"},
                    "payment_status": {"type": "string"},
                    "payment_method": {"type": "string"}
                },
                "required": ["bill_id", "payment_status"]
            }
        }
    },

    # ---- Insurance Tools ----

    {
        "type": "function",
        "function": {
            "name": "submit_insurance_claim",
            "description": "Submit a new insurance claim for a patient.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "integer"},
                    "provider_name": {"type": "string", "description": "Insurance provider name"},
                    "policy_number": {"type": "string"},
                    "claim_amount": {"type": "number"}
                },
                "required": ["patient_id", "provider_name", "policy_number", "claim_amount"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "get_insurance_claims",
            "description": "Retrieve insurance claims for a patient.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "integer"},
                    "limit": {"type": "integer", "default": 20}
                },
                "required": ["patient_id"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "update_claim_status",
            "description": "Update insurance claim status (SUBMITTED, APPROVED, REJECTED, UNDER_REVIEW).",
            "parameters": {
                "type": "object",
                "properties": {
                    "claim_id": {"type": "integer"},
                    "claim_status": {"type": "string"}
                },
                "required": ["claim_id", "claim_status"]
            }
        }
    },

    # ---- Hospital Document Tools ----

    {
        "type": "function",
        "function": {
            "name": "search_hospital_docs",
            "description": "Search internal hospital documentation, policies, and SOPs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search keyword"}
                },
                "required": ["query"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "get_document_by_category",
            "description": "Get hospital documents by category (policy, emergency, compliance, pharmacy, lab, public, finance).",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "Document category"}
                },
                "required": ["category"]
            }
        }
    },

    # ---- Audit Tools ----

    {
        "type": "function",
        "function": {
            "name": "get_audit_logs",
            "description": "Retrieve audit logs. Optionally filter by username or action.",
            "parameters": {
                "type": "object",
                "properties": {
                    "username": {"type": "string", "description": "Filter by username"},
                    "action": {"type": "string", "description": "Filter by action type"},
                    "limit": {"type": "integer", "default": 30}
                },
                "required": []
            }
        }
    },

    # ---- Clinical Safety & Analytics Tools (Advanced Alignment) ----

    {
        "type": "function",
        "function": {
            "name": "get_clinical_safety_rules",
            "description": "Retrieve all clinical safety and drug interaction rules.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "create_clinical_safety_rule",
            "description": "Create a new clinical safety or interaction trigger rule.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "trigger_type": {"type": "string"},
                    "risk_level": {"type": "string"}
                },
                "required": ["name", "description", "trigger_type"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "toggle_clinical_safety_rule",
            "description": "Enable or disable a clinical safety rule.",
            "parameters": {
                "type": "object",
                "properties": {
                    "rule_id": {"type": "integer"},
                    "is_active": {"type": "boolean"}
                },
                "required": ["rule_id", "is_active"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "get_hospital_analytics",
            "description": "Retrieve hospital operational metrics and department analytics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "department": {"type": "string", "description": "Filter by department"}
                },
                "required": []
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "create_secure_document_request",
            "description": "Create a confidential supervisor/admin document request stored in Secure Document Vault. Content is not returned in chat and requires SUPER_ADMIN approval before vault viewing.",
            "parameters": {
                "type": "object",
                "properties": {
                    "document_type": {
                        "type": "string",
                        "description": "One of: patient_full_records, hospital_billing_records, patient_lab_reports, patient_insurance_details"
                    },
                    "patient_id": {
                        "type": "integer",
                        "description": "Required for patient_full_records, patient_lab_reports, and patient_insurance_details"
                    },
                    "title": {
                        "type": "string",
                        "description": "Optional document title"
                    }
                },
                "required": ["document_type"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "generate_patient_records_report",
            "description": "Generate a private patient-records document request. The content is stored in Secure Document Vault and not returned in chat. Use for requests like creating a secure doc for last month's patient records.",
            "parameters": {
                "type": "object",
                "properties": {
                    "month": {"type": "string", "description": "Use 'last' for last month, or month number 1-12"},
                    "year": {"type": "integer", "description": "Optional year when month is a number"},
                    "title": {"type": "string", "description": "Optional report title"}
                },
                "required": []
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "get_my_report_requests",
            "description": "List the current management user's secure document requests and approval statuses without exposing private content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "Optional status filter such as PENDING_ADMIN_APPROVAL, APPROVED, or REJECTED"},
                    "limit": {"type": "integer", "default": 20}
                },
                "required": []
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "get_approved_management_report",
            "description": "Return vault access metadata for an approved management document without exposing content in chat.",
            "parameters": {
                "type": "object",
                "properties": {
                    "request_id": {"type": "integer"}
                },
                "required": ["request_id"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "list_pending_report_requests",
            "description": "SUPER_ADMIN only: list pending private management document requests awaiting approval.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 20}
                },
                "required": []
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "approve_report_request",
            "description": "SUPER_ADMIN only: approve a private management document request so the requester can view it in Secure Document Vault.",
            "parameters": {
                "type": "object",
                "properties": {
                    "request_id": {"type": "integer"}
                },
                "required": ["request_id"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "reject_report_request",
            "description": "SUPER_ADMIN only: reject a private management document request.",
            "parameters": {
                "type": "object",
                "properties": {
                    "request_id": {"type": "integer"},
                    "reason": {"type": "string"}
                },
                "required": ["request_id"]
            }
        }
    },

    # ---- Pharmacy (Merchant) Tools ----

    {
        "type": "function",
        "function": {
            "name": "list_pharmacies",
            "description": "List all pharmacies, optionally filtering by internal/external.",
            "parameters": {
                "type": "object",
                "properties": {
                    "is_internal": {"type": "boolean"}
                },
                "required": []
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "get_pharmacy_details",
            "description": "Get detailed contact and license info for a specific pharmacy.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pharmacy_id": {"type": "integer"}
                },
                "required": ["pharmacy_id"]
            }
        }
    },
]


# =====================================================================
# Tool Execution Map
# =====================================================================

TOOL_EXECUTORS = {

    # Patient
    "patient_profile": patient_profile,
    "patient_medical_history": patient_medical_history,
    "update_patient_details": update_patient_details,

    # Doctor
    "get_doctor_details": get_doctor_details,
    "update_doctor_availability": update_doctor_availability,

    # Appointment
    "book_appointment": book_appointment,
    "cancel_appointment": cancel_appointment,
    "get_appointments": get_appointments,

    # Medical Records
    "create_medical_record": create_medical_record,
    "get_medical_records": get_medical_records,
    "update_treatment_plan": update_treatment_plan,

    # Prescriptions
    "create_prescription": create_prescription,
    "get_prescriptions": get_prescriptions,

    # Lab Reports
    "upload_lab_report": upload_lab_report,
    "get_lab_reports": get_lab_reports,
    "update_lab_report_status": update_lab_report_status,

    # Billing
    "generate_bill": generate_bill,
    "get_billing_details": get_billing_details,
    "update_payment_status": update_payment_status,

    # Insurance
    "submit_insurance_claim": submit_insurance_claim,
    "get_insurance_claims": get_insurance_claims,
    "update_claim_status": update_claim_status,

    # Documents
    "search_hospital_docs": search_hospital_docs,
    "get_document_by_category": get_document_by_category,

    # Admin
    "get_audit_logs": get_audit_logs,
    "get_clinical_safety_rules": get_clinical_safety_rules,
    "create_clinical_safety_rule": create_clinical_safety_rule,
    "toggle_clinical_safety_rule": toggle_clinical_safety_rule,
    "get_hospital_analytics": get_hospital_analytics,
    "create_secure_document_request": create_secure_document_request,
    "generate_patient_records_report": generate_patient_records_report,
    "get_my_report_requests": get_my_report_requests,
    "get_approved_management_report": get_approved_management_report,
    "list_pending_report_requests": list_pending_report_requests,
    "approve_report_request": approve_report_request,
    "reject_report_request": reject_report_request,

    # Pharmacy
    "list_pharmacies": list_pharmacies,
    "get_pharmacy_details": get_pharmacy_details,
}


def execute_tool(tool_name, db, args, actor):

    if tool_name not in TOOL_EXECUTORS:
        if actor:
            log_audit(db, actor, "TOOL_UNKNOWN", tool_name, "Unknown tool requested", success=False)
        return {"error": f"Unknown tool: {tool_name}"}

    if actor:
        allowed_tools = ROLE_TOOL_MAP.get(actor.role, [])
        if tool_name not in allowed_tools:
            log_audit(db, actor, "TOOL_FORBIDDEN", tool_name, "Role is not allowed to use this tool", success=False)
            return {"error": f"Tool '{tool_name}' is not available for role '{actor.role}'"}

    tool = TOOL_EXECUTORS[tool_name]

    if isinstance(args, str):
        try:
            args = json.loads(args)
        except Exception:
            args = {}

    if not isinstance(args, dict):
        args = {}

    args = normalize_patient_scope(db, actor, tool_name, args)

    try:
        result = tool(db=db, actor=actor, **args)
        if actor:
            success = not (isinstance(result, dict) and result.get("error"))
            action = "TOOL_EXECUTED" if success else "TOOL_DENIED"
            details = result.get("error", "") if isinstance(result, dict) else ""
            log_audit(db, actor, action, tool_name, details, success=success)
        return result
    except Exception as e:
        if actor:
            log_audit(db, actor, "TOOL_ERROR", tool_name, str(e), success=False)
        return {"error": f"Tool '{tool_name}' failed: {e}"}
