# hospital_ai/backends/vertex_backend.py
import json
import os
from typing import List, Dict, Any, Optional

_vertex_model = None


def _get_model(cfg):
    global _vertex_model
    if _vertex_model:
        return _vertex_model

    creds_path = cfg.google_application_credentials
    if creds_path:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path

    import vertexai
    from vertexai.generative_models import GenerativeModel

    vertexai.init(project=cfg.vertex_project_id, location=cfg.vertex_location)
    _vertex_model = GenerativeModel(cfg.vertex_default_model)
    return _vertex_model


class VertexBackend:
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
        from vertexai.language_models import TextEmbeddingModel
        embed_model = TextEmbeddingModel.from_pretrained(
            model or self.cfg.vertex_embedding_model
        )
        embeddings = embed_model.get_embeddings(texts)
        return [e.values for e in embeddings]


def _convert_tools_to_vertex(tools):
    """Convert OpenAI-format tool schemas to Vertex/Gemini function declarations."""
    from vertexai.generative_models import FunctionDeclaration, Tool

    declarations = []
    for t in tools:
        fn = t.get("function", {})
        params = fn.get("parameters", {})
        clean_params = {
            "type": params.get("type", "object"),
            "properties": params.get("properties", {}),
        }
        if "required" in params and params["required"]:
            clean_params["required"] = params["required"]
        declarations.append(
            FunctionDeclaration(
                name=fn["name"],
                description=fn.get("description", ""),
                parameters=clean_params,
            )
        )
    return Tool(function_declarations=declarations)


def chat_with_tools(messages, tools, model=None, timeout=None):
    from hospital_ai.config import get_config
    from vertexai.generative_models import GenerativeModel

    cfg = get_config()

    creds_path = cfg.google_application_credentials
    if creds_path:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path

    import vertexai
    vertexai.init(project=cfg.vertex_project_id, location=cfg.vertex_location)

    vertex_tool = _convert_tools_to_vertex(tools)
    model_name = model or cfg.vertex_default_model
    vertex_model = GenerativeModel(model_name, tools=[vertex_tool])

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

    resp = vertex_model.generate_content(contents)

    text = ""
    tool_calls = None

    for part in resp.candidates[0].content.parts:
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
