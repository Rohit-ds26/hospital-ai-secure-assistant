from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import logging
from sqlalchemy import text

from api.auth_api import router as auth_router
from api.chat_api import router as chat_router
from api.mcp_api import router as mcp_router
from api.mcp_server import router as mcp_server_router
from api.vault_api import router as vault_router
import traceback

from models import Base, engine

app = FastAPI(title="Hospital AI System")

Base.metadata.create_all(bind=engine)


def ensure_management_request_columns():
    columns = {
        "document_type": "VARCHAR DEFAULT 'management_document'",
        "patient_id": "INTEGER",
        "secure_file_path": "VARCHAR",
    }

    with engine.begin() as conn:
        existing = {
            row[1]
            for row in conn.execute(text("PRAGMA table_info(management_report_requests)"))
        }
        for name, definition in columns.items():
            if name not in existing:
                conn.execute(text(f"ALTER TABLE management_report_requests ADD COLUMN {name} {definition}"))


ensure_management_request_columns()

@app.middleware("http")
async def error_handling_middleware(request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        logging.exception("Unhandled request error")
        raise e

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(mcp_router)
app.include_router(mcp_server_router)
app.include_router(vault_router)

# Serve static files from the 'static' directory
if not os.path.exists("static"):
    os.makedirs("static")

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def root():
    """Redirect or serve the UI dashboard"""
    return FileResponse("static/index.html")


@app.get("/patient")
def patient_ui():
    return FileResponse("static/patient.html")


@app.get("/staff")
def staff_ui():
    return FileResponse("static/staff.html")


@app.get("/management")
def management_ui():
    return FileResponse("static/management.html")


@app.get("/vault")
def vault_ui():
    return FileResponse("static/vault.html")


@app.get("/api/status")
def api_status():
    return {
        "service": "Hospital AI System",
        "version": "1.0.0",
        "status": "running",
        "ui": "/",
        "docs": "/docs",
        "health": "/mcp/health",
    }
