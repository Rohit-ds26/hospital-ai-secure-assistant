# hospital_ai/backends/openai_backend.py
import json
from typing import List, Dict, Any, Optional

_client = None


def _get_client(cfg):
    global _client
    if _client:
        return _client
    from openai import OpenAI
    _client = OpenAI(api_key=cfg.openai_api_key)
    return _client


class OpenAIBackend:
    def __init__(self, cfg):
        self.cfg = cfg
        self.client = _get_client(cfg)

    def chat(self, messages, model=None, timeout=None):
        model = model or self.cfg.openai_default_model
        timeout = timeout or self.cfg.default_timeout
        resp = self.client.chat.completions.create(
            model=model,
            messages=messages,
            timeout=timeout,
        )
        choice = resp.choices[0]
        return {"text": choice.message.content or "", "raw": resp}

    def embed(self, texts, model=None, timeout=None):
        model = model or self.cfg.openai_embedding_model
        resp = self.client.embeddings.create(model=model, input=texts)
        return [d.embedding for d in resp.data]


def chat_with_tools(messages, tools, model=None, timeout=None):
    from hospital_ai.config import get_config
    cfg = get_config()
    client = _get_client(cfg)
    model = model or cfg.openai_default_model
    timeout = timeout or cfg.default_timeout

    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=tools,
        timeout=timeout,
    )

    choice = resp.choices[0]
    text = choice.message.content or ""
    tool_calls = None

    if choice.message.tool_calls:
        tool_calls = []
        for tc in choice.message.tool_calls:
            try:
                args = json.loads(tc.function.arguments)
            except Exception:
                args = {}
            tool_calls.append({
                "id": tc.id,
                "name": tc.function.name,
                "arguments": args,
            })

    return {"text": text, "tool_calls": tool_calls, "raw": resp}
