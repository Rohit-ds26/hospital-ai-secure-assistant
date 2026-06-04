# =====================================================================
# Entity Resolver — Map entity references for context
# =====================================================================

ENTITY_COLUMNS = {

    "patient": [
        "id", "full_name", "dob", "gender", "blood_group",
        "phone", "email", "disease_summary",
    ],

    "doctor": [
        "id", "full_name", "specialization", "department",
        "license_number", "availability_status",
    ],

    "appointment": [
        "id", "patient_id", "doctor_id", "appointment_date",
        "time_slot", "reason", "status",
    ],

    "medical_record": [
        "id", "patient_id", "doctor_id", "symptoms",
        "diagnosis", "treatment_plan",
    ],

    "prescription": [
        "id", "patient_id", "doctor_id", "drug_name",
        "dosage", "frequency", "duration",
    ],

    "lab_report": [
        "id", "patient_id", "test_type", "test_value",
        "normal_range", "flag", "status",
    ],

    "billing": [
        "id", "patient_id", "amount",
        "payment_status", "payment_method",
    ],

    "insurance": [
        "id", "patient_id", "provider_name",
        "policy_number", "claim_amount", "claim_status",
    ],
}


def match_entity(reference_dict, entities, entity_type):
    """
    Match entity using multiple attributes.
    """

    if not entities:
        return None

    columns = ENTITY_COLUMNS.get(entity_type, [])

    matches = []

    for e in entities:

        match = True

        for attr, value in reference_dict.items():

            if attr not in columns:
                continue

            entity_val = getattr(e, attr, None)

            if entity_val is None:
                match = False
                break

            if str(value).lower() not in str(entity_val).lower():
                match = False
                break

        if match:
            matches.append(e)

    return matches
