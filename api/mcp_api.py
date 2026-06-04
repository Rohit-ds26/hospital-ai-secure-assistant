from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from models import SessionLocal
from auth.jwt_auth import get_current_user
from services.tool_router import TOOL_SCHEMAS, execute_tool
from security.tool_permissions import tools_for_role

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/mcp/health")
def health():
    return {"status": "ok", "service": "Hospital AI System MCP"}


@router.get("/mcp/tools")
def list_tools(actor=Depends(get_current_user)):
    """List tools available for the authenticated user's role."""

    role_tools = tools_for_role(actor.role, TOOL_SCHEMAS)

    return {
        "role": actor.role,
        "tool_count": len(role_tools),
        "tools": [t["function"]["name"] for t in role_tools],
    }


@router.post("/mcp/invoke")
def invoke_tool(
    req: dict,
    db: Session = Depends(get_db),
    actor=Depends(get_current_user),
):
    """Invoke a specific tool by name with arguments."""

    tool_name = req.get("tool_name")
    arguments = req.get("arguments", {})

    if not tool_name:
        return {"error": "tool_name required"}

    # RBAC check
    allowed_tools = [t["function"]["name"] for t in tools_for_role(actor.role, TOOL_SCHEMAS)]

    if tool_name not in allowed_tools:
        return {
            "error": f"Tool '{tool_name}' is not available for role '{actor.role}'",
            "allowed_tools": allowed_tools,
        }

    # If patient, inject patient_id
    if actor.role == "PATIENT":
        from models import Patient
        patient = db.query(Patient).filter(Patient.user_id == actor.id).first()
        if patient:
            setattr(actor, "patient_id", patient.id)

    result = execute_tool(
        tool_name=tool_name,
        db=db,
        args=arguments,
        actor=actor,
    )

    return {
        "tool": tool_name,
        "result": result,
    }
