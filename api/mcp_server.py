"""
Hospital AI System — MCP SSE Server
Implements Model Context Protocol over Server-Sent Events (SSE).
"""

import json
import uuid
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.orm import Session

from models import SessionLocal, User, Patient
from auth.jwt_auth import JWT_SECRET, JWT_ALGORITHM
from services.tool_router import TOOL_SCHEMAS, execute_tool
from security.tool_permissions import tools_for_role
from jose import jwt, JWTError

router = APIRouter()

# In-memory session store
_sessions = {}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _authenticate_from_token(token: str, db):
    """Authenticate user from a bearer token string."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None

    username = payload.get("sub")
    if not username:
        return None

    user = db.query(User).filter(User.username == username).first()
    return user


# =====================================================================
# SSE Connect — GET /mcp/sse
# =====================================================================

@router.get("/mcp/sse")
async def mcp_sse(request: Request):
    """
    SSE endpoint. Client connects here to receive events.
    Auth token is passed via Authorization header or query param.
    """
    session_id = str(uuid.uuid4())

    # Extract auth token
    auth_header = request.headers.get("authorization", "")
    token = None
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
    elif request.query_params.get("token"):
        token = request.query_params.get("token")

    _sessions[session_id] = {
        "token": token,
        "events": [],
    }

    async def event_generator():
        # Send session ID
        yield {
            "event": "endpoint",
            "data": f"/mcp/sse/message?sessionId={session_id}",
        }

        # Keep connection alive
        import asyncio
        try:
            while True:
                # Check for queued events
                if _sessions.get(session_id, {}).get("events"):
                    event = _sessions[session_id]["events"].pop(0)
                    yield event
                await asyncio.sleep(0.5)
        except Exception:
            pass

    return EventSourceResponse(event_generator())


# =====================================================================
# SSE Message — POST /mcp/sse/message
# =====================================================================

@router.post("/mcp/sse/message")
async def mcp_sse_message(request: Request):
    """
    JSON-RPC message handler for MCP SSE.
    """
    session_id = request.query_params.get("sessionId")

    if not session_id or session_id not in _sessions:
        return JSONResponse({"error": "Invalid session"}, status_code=400)

    body = await request.json()
    method = body.get("method")
    params = body.get("params", {})
    msg_id = body.get("id")

    session = _sessions[session_id]
    token = session.get("token")

    # Authenticate
    db = SessionLocal()
    try:
        user = _authenticate_from_token(token, db) if token else None

        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "Hospital AI System", "version": "1.0.0"},
                "capabilities": {"tools": {"listChanged": False}},
            }

        elif method == "tools/list":
            if not user:
                result = {"error": "Authentication required"}
            else:
                role_tools = tools_for_role(user.role, TOOL_SCHEMAS)
                result = {
                    "tools": [
                        {
                            "name": t["function"]["name"],
                            "description": t["function"].get("description", ""),
                            "inputSchema": t["function"].get("parameters", {}),
                        }
                        for t in role_tools
                    ]
                }

        elif method == "tools/call":
            if not user:
                result = {"error": "Authentication required"}
            else:
                tool_name = params.get("name")
                arguments = params.get("arguments", {})

                # RBAC check
                allowed = [t["function"]["name"] for t in tools_for_role(user.role, TOOL_SCHEMAS)]
                if tool_name not in allowed:
                    result = {"error": f"Tool '{tool_name}' not available for role '{user.role}'"}
                else:
                    # Inject patient_id if PATIENT role
                    if user.role == "PATIENT":
                        patient = db.query(Patient).filter(Patient.user_id == user.id).first()
                        if patient:
                            setattr(user, "patient_id", patient.id)

                    tool_result = execute_tool(
                        tool_name=tool_name,
                        db=db,
                        args=arguments,
                        actor=user,
                    )
                    result = {
                        "content": [
                            {"type": "text", "text": json.dumps(tool_result, default=str)}
                        ]
                    }

        elif method == "ping":
            result = {}

        else:
            result = {"error": f"Unknown method: {method}"}

    finally:
        db.close()

    response = {"jsonrpc": "2.0", "id": msg_id, "result": result}

    # Queue event for SSE
    session["events"].append({
        "event": "message",
        "data": json.dumps(response),
    })

    return JSONResponse(response)
