# hospital_ai/ai_client.py
import os
from typing import List, Dict, Any, Optional
from hospital_ai.config import get_config

_cfg = get_config()
_backend = None


def _load_backend():
    global _backend, _cfg
    if _backend:
        return _backend

    provider = _cfg.provider.lower()
    if provider == "openai":
        try:
            from hospital_ai.backends.openai_backend import OpenAIBackend
            _backend = OpenAIBackend(_cfg)
        except Exception as e:
            _backend = None
            return {"error": f"OpenAI backend init failed: {e}"}
    elif provider == "gemini":
        try:
            from hospital_ai.backends.gemini_backend import GeminiBackend
            _backend = GeminiBackend(_cfg)
        except Exception as e:
            _backend = None
            return {"error": f"Gemini backend init failed: {e}"}
    elif provider == "vertex":
        try:
            from hospital_ai.backends.vertex_backend import VertexBackend
            _backend = VertexBackend(_cfg)
        except Exception as e:
            _backend = None
            return {"error": f"Vertex backend init failed: {e}"}
    elif provider == "mock":
        from hospital_ai.backends.mock_backend import MockBackend
        _backend = MockBackend(_cfg)
    else:
        return {"error": f"Unknown provider: {provider}"}

    return _backend


def ai_chat(messages: List[Dict[str, str]], model: Optional[str] = None, timeout: Optional[int] = None) -> Optional[Dict[str, Any]]:
    backend = _load_backend()
    if isinstance(backend, dict) and backend.get("error"):
        return backend
    if not backend:
        return {"error": "No AI backend available"}
    try:
        return backend.chat(messages=messages, model=model, timeout=timeout)
    except Exception as e:
        return {"error": str(e)}


def ai_embed(texts: List[str], model: Optional[str] = None, timeout: Optional[int] = None) -> List[List[float]]:
    backend = _load_backend()
    if isinstance(backend, dict) and backend.get("error"):
        raise RuntimeError(backend.get("error"))
    if not backend:
        raise RuntimeError("No AI backend available for embeddings")
    try:
        return backend.embed(texts=texts, model=model, timeout=timeout)
    except Exception as e:
        raise


def ai_chat_with_tools(
    messages: List[Dict[str, str]],
    tools: List[Dict[str, Any]],
    model: Optional[str] = None,
    timeout: Optional[int] = None,
) -> Dict[str, Any]:
    provider = _cfg.provider.lower()
    if provider == "openai":
        import hospital_ai.backends.openai_backend as openai_backend
        return openai_backend.chat_with_tools(messages=messages, tools=tools, model=model, timeout=timeout)
    if provider == "gemini":
        import hospital_ai.backends.gemini_backend as gemini_backend
        return gemini_backend.chat_with_tools(messages=messages, tools=tools, model=model, timeout=timeout)
    if provider == "vertex":
        import hospital_ai.backends.vertex_backend as vertex_backend
        return vertex_backend.chat_with_tools(messages=messages, tools=tools, model=model, timeout=timeout)
    if provider == "mock":
        import hospital_ai.backends.mock_backend as mock_backend
        import importlib
        importlib.reload(mock_backend)
        return mock_backend.chat_with_tools(messages=messages, tools=tools, model=model, timeout=timeout)
    return {"error": f"Unknown provider for tools: {provider}"}
