# hospital_ai/backends/mock_backend.py

class MockBackend:
    def __init__(self, cfg=None):
        self.name = "Mock Clinical Engine"

    def chat(self, messages, model=None, timeout=None):
        # A simple response for general chat
        return {
            "content": "I am the Hospital AI Mock Engine. I am processing your request using internal clinical logic.",
            "role": "assistant"
        }

    def embed(self, texts, model=None, timeout=None):
        # Return dummy embeddings (0.1, 0.2, ...)
        return [[0.1] * 128 for _ in texts]

def chat_with_tools(messages, tools, model=None, timeout=None):
    """
    Simulate tool calling for the demo.
    """
    last_msg_obj = messages[-1]
    last_role = last_msg_obj.get("role")
    last_content = (last_msg_obj.get("content") or "").lower()

    # 1. If we just got a tool result, summarize it
    if last_role == "tool":
        import json
        name = last_msg_obj.get("name", "the tool")
        content = last_msg_obj.get("content") or "{}"
        try:
            parsed = json.loads(content)
        except Exception:
            parsed = content

        if isinstance(parsed, dict) and parsed.get("error"):
            return {
                "text": f"Unable to complete {name}: {parsed['error']}",
                "tool_calls": []
            }

        return {
            "text": f"Here is the result from {name}:\n{content}",
            "tool_calls": []
        }

    # 2. Rule-based triggers for local demo mode. More specific clinical
    # workflows must be checked before generic "patient" profile requests.
    import re

    def first_number(default=1):
        match = re.search(r"\b(\d+)\b", last_content)
        return int(match.group(1)) if match else default

    t_calls = []

    is_doc_request = "report" in last_content or "document" in last_content or "doc" in last_content or "request" in last_content

    if "pending" in last_content and is_doc_request:
        t_calls.append({"name": "list_pending_report_requests", "arguments": {"limit": 10}})
    elif ("read" in last_content or "show" in last_content or "open" in last_content) and "approved" in last_content and is_doc_request:
        t_calls.append({"name": "get_approved_management_report", "arguments": {"request_id": first_number()}})
    elif re.search(r"\bapprove\b", last_content) and is_doc_request:
        t_calls.append({"name": "approve_report_request", "arguments": {"request_id": first_number()}})
    elif re.search(r"\breject\b", last_content) and is_doc_request:
        t_calls.append({"name": "reject_report_request", "arguments": {"request_id": first_number(), "reason": "Rejected from management chat"}})
    elif ("my" in last_content or "status" in last_content) and is_doc_request:
        t_calls.append({"name": "get_my_report_requests", "arguments": {"limit": 10}})
    elif (
        ("create" in last_content or "generate" in last_content or "make" in last_content)
        and ("doc" in last_content or "document" in last_content)
        and ("billing" in last_content or "bill" in last_content)
        and ("all" in last_content or "hospital" in last_content)
    ):
        t_calls.append({"name": "create_secure_document_request", "arguments": {"document_type": "hospital_billing_records"}})
    elif (
        ("create" in last_content or "generate" in last_content or "make" in last_content)
        and ("doc" in last_content or "document" in last_content)
        and ("lab" in last_content or "test" in last_content)
    ):
        t_calls.append({"name": "create_secure_document_request", "arguments": {"document_type": "patient_lab_reports", "patient_id": first_number()}})
    elif (
        ("create" in last_content or "generate" in last_content or "make" in last_content)
        and ("doc" in last_content or "document" in last_content)
        and ("insurance" in last_content or "claim" in last_content)
    ):
        t_calls.append({"name": "create_secure_document_request", "arguments": {"document_type": "patient_insurance_details", "patient_id": first_number()}})
    elif (
        ("create" in last_content or "generate" in last_content or "make" in last_content)
        and ("doc" in last_content or "document" in last_content)
        and ("specific" in last_content or "full" in last_content or "total" in last_content)
        and "patient" in last_content
    ):
        t_calls.append({"name": "create_secure_document_request", "arguments": {"document_type": "patient_full_records", "patient_id": first_number()}})
    elif (
        ("create" in last_content or "generate" in last_content or "make" in last_content)
        and ("doc" in last_content or "document" in last_content or "report" in last_content)
        and ("patient" in last_content or "records" in last_content)
    ):
        args = {"month": "last"} if "last month" in last_content else {}
        t_calls.append({"name": "generate_patient_records_report", "arguments": args})
    elif "analytics" in last_content or "wait time" in last_content or "metrics" in last_content:
        args = {}
        if "emergency" in last_content:
            args["department"] = "Emergency"
        t_calls.append({"name": "get_hospital_analytics", "arguments": args})
    elif "audit" in last_content or "log" in last_content:
        t_calls.append({"name": "get_audit_logs", "arguments": {"limit": 5}})
    elif "lab" in last_content or "test result" in last_content or "diagnostic" in last_content:
        t_calls.append({"name": "get_lab_reports", "arguments": {"patient_id": first_number()}})
    elif "appointment" in last_content or "schedule" in last_content:
        t_calls.append({"name": "get_appointments", "arguments": {"patient_id": first_number()}})
    elif "prescription" in last_content or "medicine" in last_content or "medication" in last_content:
        t_calls.append({"name": "get_prescriptions", "arguments": {"patient_id": first_number()}})
    elif "bill" in last_content or "invoice" in last_content or "payment" in last_content:
        t_calls.append({"name": "get_billing_details", "arguments": {"patient_id": first_number()}})
    elif "insurance" in last_content or "claim" in last_content:
        t_calls.append({"name": "get_insurance_claims", "arguments": {"patient_id": first_number()}})
    elif "document" in last_content or "policy" in last_content or "sop" in last_content or "emergency" in last_content:
        query = "emergency" if "emergency" in last_content else "policy"
        t_calls.append({"name": "search_hospital_docs", "arguments": {"query": query}})
    elif "doctor" in last_content:
        t_calls.append({"name": "get_doctor_details", "arguments": {"doctor_id": first_number()}})
    elif "patient" in last_content or "profile" in last_content or "my record" in last_content:
        t_calls.append({"name": "patient_profile", "arguments": {"patient_id": first_number()}})

    if t_calls:
        return {
            "text": "Fetching clinical data...",
            "tool_calls": t_calls
        }

    # 3. Default
    return {
        "text": "I've analyzed your clinical query. Please proceed with the dashboard tools or ask about specific patient data.",
        "tool_calls": []
    }
