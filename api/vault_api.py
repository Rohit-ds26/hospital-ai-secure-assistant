from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth.jwt_auth import get_current_user
from models import ManagementReportRequest, SessionLocal

router = APIRouter()

VAULT_DIR = Path("secure_vault")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _require_vault_user(actor):
    if actor.role not in ("SUPER_ADMIN", "HOSPITAL_SUPERVISOR"):
        raise HTTPException(status_code=403, detail="Secure vault is only available to management users")


def _authorized_query(db: Session, actor):
    query = db.query(ManagementReportRequest).filter(
        ManagementReportRequest.status == "APPROVED",
        ManagementReportRequest.secure_file_path.isnot(None),
    )
    if actor.role != "SUPER_ADMIN":
        query = query.filter(ManagementReportRequest.requested_by_user_id == actor.id)
    return query


def _safe_vault_path(path_value):
    if not path_value:
        raise HTTPException(status_code=404, detail="Vault document file is missing")

    vault_root = VAULT_DIR.resolve()
    path = Path(path_value).resolve()
    if vault_root not in path.parents and path != vault_root:
        raise HTTPException(status_code=403, detail="Invalid vault document path")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Vault document file was not found")
    return path


@router.get("/vault/docs")
def list_vault_docs(db: Session = Depends(get_db), actor=Depends(get_current_user)):
    _require_vault_user(actor)

    docs = (
        _authorized_query(db, actor)
        .order_by(ManagementReportRequest.approved_at.desc())
        .all()
    )

    return {
        "documents": [
            {
                "request_id": doc.id,
                "title": doc.title,
                "category": doc.category,
                "document_type": doc.document_type,
                "patient_id": doc.patient_id,
                "requested_by": doc.requested_by_username,
                "requested_by_role": doc.requested_by_role,
                "created_at": str(doc.created_at),
                "approved_by": doc.approved_by_username,
                "approved_at": str(doc.approved_at) if doc.approved_at else None,
                "view_url": f"/vault/docs/{doc.id}",
            }
            for doc in docs
        ]
    }


@router.get("/vault/docs/{request_id}")
def get_vault_doc(request_id: int, db: Session = Depends(get_db), actor=Depends(get_current_user)):
    _require_vault_user(actor)

    doc = _authorized_query(db, actor).filter(ManagementReportRequest.id == request_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Approved vault document not found")

    path = _safe_vault_path(doc.secure_file_path)

    return {
        "request_id": doc.id,
        "title": doc.title,
        "category": doc.category,
        "document_type": doc.document_type,
        "patient_id": doc.patient_id,
        "approved_by": doc.approved_by_username,
        "approved_at": str(doc.approved_at) if doc.approved_at else None,
        "content": path.read_text(encoding="utf-8"),
    }
