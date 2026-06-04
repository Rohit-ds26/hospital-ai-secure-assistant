from models import HospitalDocument
from security.prompt_filter import check_prompt


PUBLIC_TOPICS = {
    "services": (
        "General services include outpatient consultations, emergency care, lab testing, "
        "radiology, pharmacy support, billing help, and insurance guidance."
    ),
    "appointment": (
        "For appointments, patients should sign in to the patient portal or contact reception. "
        "A logged-in patient can view, book, or cancel only their own appointments."
    ),
    "billing": (
        "For billing help, keep your bill number and visit details ready. Personal billing records "
        "are available only after signing in."
    ),
    "insurance": (
        "For insurance support, bring your policy information and required claim documents. "
        "Claim-specific status is available only to authenticated users."
    ),
    "lab": (
        "Routine lab turnaround varies by test type. Personal lab results are private and require "
        "patient sign-in."
    ),
    "records": (
        "Patients can request copies of their medical records through approved hospital channels. "
        "Specific records are never shared in public chat."
    ),
    "emergency": (
        "For emergencies, contact local emergency services or go directly to the emergency department. "
        "Public chat is not a substitute for urgent medical care."
    ),
}

PRIVATE_DATA_TERMS = {
    "my profile",
    "my record",
    "my records",
    "my bill",
    "my bills",
    "my lab",
    "my prescription",
    "patient id",
    "patient_id",
    "medical record",
    "lab report",
    "billing record",
    "prescription",
    "diagnosis",
    "treatment plan",
    "insurance claim",
    "appointment status",
}


def _public_docs(db, prompt):
    if not db:
        return []

    query = db.query(HospitalDocument).filter(HospitalDocument.access_level == "public")

    terms = [word for word in prompt.lower().split() if len(word) > 3]
    for term in terms[:3]:
        query = query.filter(HospitalDocument.content.ilike(f"%{term}%"))

    return query.limit(3).all()


def run_public_chat(db, prompt):
    """Answer anonymous hospital FAQ questions without exposing patient data."""

    if not prompt:
        return {"error": "user_prompt required"}

    if check_prompt(prompt):
        return "Request blocked by security policy."

    normalized = prompt.lower()

    if any(term in normalized for term in PRIVATE_DATA_TERMS):
        return (
            "I can help with general hospital information here, but patient-specific records, "
            "billing, lab results, prescriptions, insurance claims, and appointments require sign-in."
        )

    matched = [
        answer
        for topic, answer in PUBLIC_TOPICS.items()
        if topic in normalized
    ]

    docs = _public_docs(db, prompt)
    if docs:
        matched.extend(f"{doc.title}: {doc.content[:500]}" for doc in docs)

    if matched:
        return "\n\n".join(matched)

    return (
        "I can help with general hospital information such as services, appointments, billing, "
        "insurance, lab turnaround, medical-record request process, and emergency guidance. "
        "For personal hospital data, please sign in to the correct portal."
    )
