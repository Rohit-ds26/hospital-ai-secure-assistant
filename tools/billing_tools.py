from models import Billing, Patient
from security.access_control import can_access_patient


def generate_bill(db, patient_id, amount, appointment_id=None, payment_method=None, actor=None, **kwargs):
    """Generate a bill for a patient (billing staff only)."""

    if actor and not can_access_patient(db, actor, patient_id):
        return {"error": "Unauthorized: You cannot generate bills for this patient"}

    bill = Billing(
        patient_id=patient_id,
        appointment_id=appointment_id,
        amount=float(amount),
        payment_status="PENDING",
        payment_method=payment_method,
    )

    db.add(bill)
    db.commit()

    return {
        "bill_id": bill.id,
        "patient_id": bill.patient_id,
        "amount": bill.amount,
        "status": bill.payment_status,
        "created": True,
    }


def get_billing_details(db, patient_id, actor=None, limit=20, **kwargs):
    """Get billing details for a patient."""

    if actor and not can_access_patient(db, actor, patient_id):
        return {"error": "Unauthorized: You cannot view this patient's bills"}

    bills = (
        db.query(Billing)
        .filter(Billing.patient_id == patient_id)
        .order_by(Billing.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "bill_id": b.id,
            "patient_id": b.patient_id,
            "appointment_id": b.appointment_id,
            "amount": b.amount,
            "payment_status": b.payment_status,
            "payment_method": b.payment_method,
            "date": str(b.created_at) if b.created_at else None,
        }
        for b in bills
    ]


def update_payment_status(db, bill_id, payment_status, payment_method=None, actor=None, **kwargs):
    """Update payment status for a bill (billing staff only)."""

    status = payment_status.upper()
    valid = ["PENDING", "PAID", "OVERDUE", "REFUNDED"]
    if status not in valid:
        return {"error": f"Invalid status. Must be one of: {valid}"}

    bill = db.query(Billing).filter(Billing.id == bill_id).first()
    if not bill:
        return {"error": f"Bill {bill_id} not found"}

    old_status = bill.payment_status
    bill.payment_status = status
    if payment_method:
        bill.payment_method = payment_method
    db.commit()

    return {
        "bill_id": bill.id,
        "old_status": old_status,
        "new_status": bill.payment_status,
        "updated": True,
    }
