# hospital_ai/backends/gemini_backend.py
import json
from typing import List, Dict, Any, Optional

_model_instance = None


def _get_model(cfg):
    global _model_instance
    if _model_instance:
        return _model_instance
    import google.generativeai as genai
    genai.configure(api_key=cfg.google_api_key)
    _model_instance = genai.GenerativeModel(cfg.gemini_default_model)
    return _model_instance


class GeminiBackend:
    def __init__(self, cfg):
        self.cfg = cfg
        self.model = _get_model(cfg)

    def chat(self, messages, model=None, timeout=None):
        contents = []
        for m in messages:
            role = "user" if m["role"] in ("user", "system") else "model"
            contents.append({"role": role, "parts": [{"text": m["content"]}]})
        resp = self.model.generate_content(contents)
        return {"text": resp.text, "raw": resp}

    def embed(self, texts, model=None, timeout=None):
        import google.generativeai as genai
        model_name = model or "models/text-embedding-004"
        result = genai.embed_content(model=model_name, content=texts)
        return result["embedding"] if isinstance(texts, str) else result["embedding"]


def _convert_tools_to_gemini(tools):
    """Convert OpenAI-format tool schemas to Gemini function declarations."""
    declarations = []
    for t in tools:
        fn = t.get("function", {})
        params = fn.get("parameters", {})
        # Remove unsupported keys for Gemini
        clean_params = {
            "type": params.get("type", "object"),
            "properties": params.get("properties", {}),
        }
        if "required" in params and params["required"]:
            clean_params["required"] = params["required"]
        declarations.append({
            "name": fn["name"],
            "description": fn.get("description", ""),
            "parameters": clean_params,
        })
    return declarations


def chat_with_tools(messages, tools, model=None, timeout=None):
    import google.generativeai as genai
    from hospital_ai.config import get_config
    cfg = get_config()

    genai.configure(api_key=cfg.google_api_key)

    fn_declarations = _convert_tools_to_gemini(tools)

    gemini_tools = [genai.types.Tool(function_declarations=[
        genai.types.FunctionDeclaration(**fd) for fd in fn_declarations
    ])]

    model_name = model or cfg.gemini_default_model
    gemini_model = genai.GenerativeModel(model_name, tools=gemini_tools)

    contents = []
    for m in messages:
        role = "user" if m["role"] in ("user", "system") else "model"
        if m["role"] == "tool":
            contents.append({
                "role": "user",
                "parts": [{"text": f"Tool result: {m['content']}"}]
            })
        else:
            contents.append({"role": role, "parts": [{"text": m["content"]}]})

    resp = gemini_model.generate_content(contents)

    text = ""
    tool_calls = None

    for part in resp.parts:
        if hasattr(part, "text") and part.text:
            text += part.text
        if hasattr(part, "function_call") and part.function_call:
            if tool_calls is None:
                tool_calls = []
            fc = part.function_call
            tool_calls.append({
                "name": fc.name,
                "arguments": dict(fc.args) if fc.args else {},
            })

    return {"text": text, "tool_calls": tool_calls, "raw": resp}
