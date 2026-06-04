from models import HospitalDocument


def search_hospital_docs(db, query, actor=None, **kwargs):
    """Search hospital documents by keyword."""

    docs = (
        db.query(HospitalDocument)
        .filter(HospitalDocument.content.ilike(f"%{query}%"))
        .limit(5)
        .all()
    )

    results = []

    for d in docs:
        # Restrict based on access level and role
        if d.access_level == "restricted":
            if actor and actor.role in ("PATIENT", "RECEPTIONIST", "BILLING_INSURANCE", "LAB_TECH"):
                continue
        if d.access_level == "internal":
            if actor and actor.role == "PATIENT":
                continue

        results.append({
            "title": d.title,
            "category": d.category,
            "access_level": d.access_level,
            "snippet": d.content[:400],
        })

    if results:
        return {"status": "completed", "results": results}
    else:
        return {"status": "No matching documents found"}


def get_document_by_category(db, category, actor=None, limit=5, **kwargs):
    """Get hospital documents by category."""

    docs = (
        db.query(HospitalDocument)
        .filter(HospitalDocument.category == category.lower())
        .limit(limit)
        .all()
    )

    results = []

    for d in docs:
        # Restrict based on access level
        if d.access_level == "restricted":
            if actor and actor.role not in ("SUPER_ADMIN", "HOSPITAL_SUPERVISOR", "DOCTOR"):
                continue
        if d.access_level == "internal":
            if actor and actor.role == "PATIENT":
                continue

        results.append({
            "id": d.id,
            "title": d.title,
            "category": d.category,
            "access_level": d.access_level,
            "content": d.content[:600],
        })

    if results:
        return {"status": "completed", "results": results}
    else:
        return {"status": f"No documents found for category: {category}"}
