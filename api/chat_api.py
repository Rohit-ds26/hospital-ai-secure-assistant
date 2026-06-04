from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import SessionLocal, Patient
from services.chat_service import run_chat_agent
from services.public_chat_service import run_public_chat
from auth.jwt_auth import get_current_user, get_optional_current_user
from services.tool_router import TOOL_SCHEMAS
from security.tool_permissions import tools_for_role

router = APIRouter()


CHATBOT_PROFILES = {
    "patient": {
        "label": "Patient Assistant",
        "allowed_roles": {"PATIENT"},
        "conversation_prefix": "patient",
        "instructions": """
You are the external Patient Assistant.
Only help with patient-facing workflows such as the signed-in patient's own profile,
appointments, prescriptions, lab reports, billing, insurance claims, and simple hospital guidance.
Do not expose internal staff workflows, audit logs, analytics, restricted documents,
or information about other patients.
""",
    },
    "staff": {
        "label": "Hospital Staff Assistant",
        "allowed_roles": {"DOCTOR", "NURSE", "LAB_TECH", "RECEPTIONIST", "BILLING_INSURANCE"},
        "conversation_prefix": "staff",
        "instructions": """
You are the internal Hospital Staff Assistant.
Support normal hospital operations for the authenticated staff member.
Respect the actor role and only use tools available to that role.
Do not provide senior management functions such as audit logs, hospital analytics,
or governance controls unless the role and chatbot surface explicitly allow them.
""",
    },
    "management": {
        "label": "Management Assistant",
        "allowed_roles": {"SUPER_ADMIN", "HOSPITAL_SUPERVISOR"},
        "conversation_prefix": "management",
        "instructions": """
You are the senior Management Assistant.
Support governance, audit review, hospital analytics, safety rules, and high-level operations.
Use the authenticated user's role permissions as the final boundary.
""",
    },
}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _patient_id_for_actor(db: Session, actor):
    if actor.role != "PATIENT":
        return None

    patient = db.query(Patient).filter(Patient.user_id == actor.id).first()
    if patient:
        setattr(actor, "patient_id", patient.id)
        return patient.id

    return None


def _run_chat(req: dict, chatbot_key: str, db: Session, actor):
    if chatbot_key not in CHATBOT_PROFILES:
        raise HTTPException(status_code=400, detail=f"Unknown chatbot '{chatbot_key}'")

    profile = CHATBOT_PROFILES[chatbot_key]

    if actor.role not in profile["allowed_roles"]:
        raise HTTPException(
            status_code=403,
            detail=f"{profile['label']} is not available for role '{actor.role}'",
        )

    user_prompt = req.get("user_prompt")

    if not user_prompt:
        return {"error": "user_prompt required"}

    role_tools = tools_for_role(actor.role, TOOL_SCHEMAS)
    patient_id = _patient_id_for_actor(db, actor)
    conversation_id = req.get("conversation_id", f"{profile['conversation_prefix']}-default")

    answer = run_chat_agent(
        db=db,
        actor=actor,
        prompt=req["user_prompt"],
        conversation_id=conversation_id,
        tools=role_tools,
        patient_id=patient_id,
        chatbot_name=profile["label"],
        chatbot_instructions=profile["instructions"],
    )

    return {
        "answer": answer,
        "conversation_id": conversation_id,
        "chatbot": chatbot_key,
        "chatbot_label": profile["label"],
    }


@router.post("/chat/patient")
def patient_chat(req: dict,
                 db: Session = Depends(get_db),
                 actor=Depends(get_optional_current_user)):
    if actor is None:
        user_prompt = req.get("user_prompt")
        answer = run_public_chat(db=db, prompt=user_prompt)
        return {
            "answer": answer,
            "conversation_id": req.get("conversation_id", "patient-public-default"),
            "chatbot": "patient",
            "chatbot_label": "Patient Assistant",
            "mode": "public",
        }

    return _run_chat(req, "patient", db, actor)


@router.post("/chat/staff")
def staff_chat(req: dict,
               db: Session = Depends(get_db),
               actor=Depends(get_current_user)):
    return _run_chat(req, "staff", db, actor)


@router.post("/chat/management")
def management_chat(req: dict,
                    db: Session = Depends(get_db),
                    actor=Depends(get_current_user)):
    return _run_chat(req, "management", db, actor)
