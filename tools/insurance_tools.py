from models import Insurance, Patient
from security.access_control import can_access_patient


def submit_insurance_claim(db, patient_id, provider_name, policy_number, claim_amount, actor=None, **kwargs):
    """Submit a new insurance claim."""

    if actor and not can_access_patient(db, actor, patient_id):
        return {"error": "Unauthorized: You cannot submit claims for this patient"}

    claim = Insurance(
        patient_id=patient_id,
        provider_name=provider_name,
        policy_number=policy_number,
        claim_amount=float(claim_amount),
        claim_status="SUBMITTED",
    )

    db.add(claim)
    db.commit()

    return {
        "claim_id": claim.id,
        "patient_id": claim.patient_id,
        "provider": claim.provider_name,
        "amount": claim.claim_amount,
        "status": "SUBMITTED",
        "created": True,
    }


def get_insurance_claims(db, patient_id, actor=None, limit=20, **kwargs):
    """Get insurance claims for a patient."""

    if actor and not can_access_patient(db, actor, patient_id):
        return {"error": "Unauthorized: You cannot view this patient's claims"}

    claims = (
        db.query(Insurance)
        .filter(Insurance.patient_id == patient_id)
        .order_by(Insurance.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "claim_id": c.id,
            "patient_id": c.patient_id,
            "provider": c.provider_name,
            "policy_number": c.policy_number,
            "claim_amount": c.claim_amount,
            "status": c.claim_status,
            "date": str(c.created_at) if c.created_at else None,
        }
        for c in claims
    ]


def update_claim_status(db, claim_id, claim_status, actor=None, **kwargs):
    """Update insurance claim status (billing staff only)."""

    status = claim_status.upper()
    valid = ["SUBMITTED", "APPROVED", "REJECTED", "UNDER_REVIEW"]
    if status not in valid:
        return {"error": f"Invalid status. Must be one of: {valid}"}

    claim = db.query(Insurance).filter(Insurance.id == claim_id).first()
    if not claim:
        return {"error": f"Claim {claim_id} not found"}

    old_status = claim.claim_status
    claim.claim_status = status
    db.commit()

    return {
        "claim_id": claim.id,
        "old_status": old_status,
        "new_status": claim.claim_status,
        "updated": True,
    }
