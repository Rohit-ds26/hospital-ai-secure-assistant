# hospital_ai/config.py
import os
from dotenv import load_dotenv
load_dotenv()
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from pydantic import ConfigDict

_cached_cfg = None


class Config(BaseSettings):
    """Central configuration loader for all AI backends."""

    model_config = ConfigDict(extra="allow", env_file=".env", env_file_encoding="utf-8")

    # Provider selection
    provider: str = Field(
        default_factory=lambda: os.getenv(
            "HOSPITAL_AI_PROVIDER",
            os.getenv("ACME_AI_PROVIDER", "openai")
        ).lower()
    )

    # OpenAI
    openai_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    openai_default_model: str = Field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4.1-mini"))
    openai_embedding_model: str = Field("text-embedding-3-small", validation_alias="OPENAI_EMBEDDING_MODEL")

    # Gemini (public API)
    google_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("GOOGLE_API_KEY"))
    gemini_default_model: str = Field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-2.0-flash"))

    # Vertex AI
    vertex_project_id: Optional[str] = Field(default_factory=lambda: os.getenv("VERTEX_PROJECT_ID"))
    vertex_location: str = Field(default_factory=lambda: os.getenv("VERTEX_LOCATION", "us-central1"))
    vertex_default_model: str = Field(default_factory=lambda: os.getenv("VERTEX_MODEL", "models/gemini-2.0-flash"))
    vertex_embedding_model: str = Field(
        default_factory=lambda: os.getenv("VERTEX_EMBEDDING_MODEL", "models/text-embedding-004")
    )
    google_application_credentials: Optional[str] = Field(
        default_factory=lambda: os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    )

    # Timeout
    default_timeout: int = Field(
        default_factory=lambda: int(os.getenv("ACME_AI_TIMEOUT", os.getenv("TIMEOUT", "30")))
    )


def get_config(force_reload: bool = False) -> Config:
    global _cached_cfg
    if _cached_cfg is None or force_reload:
        _cached_cfg = Config()
    return _cached_cfg
