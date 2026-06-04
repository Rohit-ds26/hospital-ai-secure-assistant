from models import Pharmacy

def list_pharmacies(db, is_internal=None, actor=None, **kwargs):
    """List all pharmacies, optionally filtering by internal/external."""
    query = db.query(Pharmacy)
    if is_internal is not None:
        query = query.filter(Pharmacy.is_internal == is_internal)
    
    pharmacies = query.all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "address": p.address,
            "phone": p.contact_phone,
            "is_internal": p.is_internal
        } for p in pharmacies
    ]

def get_pharmacy_details(db, pharmacy_id, actor=None, **kwargs):
    """Get detailed contact and license info for a specific pharmacy."""
    p = db.query(Pharmacy).filter(Pharmacy.id == pharmacy_id).first()
    if not p:
        return {"error": f"Pharmacy {pharmacy_id} not found"}
    
    return {
        "id": p.id,
        "name": p.name,
        "address": p.address,
        "phone": p.contact_phone,
        "license": p.license_number,
        "is_internal": p.is_internal
    }
