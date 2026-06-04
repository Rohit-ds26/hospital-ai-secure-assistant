from hospital_ai.ai_client import ai_chat_with_tools
from services.tool_router import execute_tool
from security.prompt_filter import check_prompt
from prompts.system_prompt import SYSTEM_PROMPT

from collections import defaultdict, deque
import json
import re


# ---------------------------
# Conversation memory
# ---------------------------

CONVERSATION_MEMORY = defaultdict(lambda: deque(maxlen=10))
ENTITY_MEMORY = defaultdict(dict)


# ---------------------------
# Utility
# ---------------------------

def strip_role_prefixes(text: str) -> str:

    if not text:
        return text

    prefixes = ["assistant:", "Assistant:", "user:", "User:", "system:", "System:"]

    lines = []
    for line in text.splitlines():
        line = line.strip()
        for p in prefixes:
            if line.startswith(p):
                line = line[len(p):].strip()
        lines.append(line)

    return "\n".join(lines).strip()


# ---------------------------
# Main agent
# ---------------------------

def run_chat_agent(db, actor, prompt, conversation_id, tools, patient_id=None, chatbot_name=None, chatbot_instructions=None):

    # ----------------------------------
    # Prompt filtering
    # ----------------------------------

    if check_prompt(prompt):
        return "Request blocked by security policy."

    history = CONVERSATION_MEMORY[conversation_id]

    role_context = f"""
Current chatbot surface: {chatbot_name or "Role-Aware Clinical Assistant"}
Current actor role: {actor.role}

Possible roles:
SUPER_ADMIN
HOSPITAL_SUPERVISOR
DOCTOR
NURSE
LAB_TECH
RECEPTIONIST
BILLING_INSURANCE
PATIENT

The role determines what tools can be used.
"""

    system_prompt = SYSTEM_PROMPT + role_context

    if chatbot_instructions:
        system_prompt += "\n" + chatbot_instructions.strip() + "\n"

    if patient_id:
        system_prompt += f"\nAuthenticated patient_id: {patient_id}"

    messages = [
        {"role": "system", "content": system_prompt}
    ]

    messages.extend(history)

    messages.append({
        "role": "user",
        "content": prompt
    })

    history.append({"role": "user", "content": prompt})

    # ----------------------------------
    # Model tool planning
    # ----------------------------------

    result = ai_chat_with_tools(
        messages=messages,
        tools=tools
    )

    if not result:
        return "Sorry, I couldn't process your request."

    model_text = strip_role_prefixes(result.get("text") or "")
    tool_calls = result.get("tool_calls")

    # ------------------------------------------------
    # Robust tool call extraction
    # ------------------------------------------------

    if not tool_calls and model_text:

        # ---------- try full JSON parse ----------
        try:
            parsed = json.loads(model_text)

            if isinstance(parsed, dict) and "tool_calls" in parsed:
                tool_calls = parsed["tool_calls"]

            if isinstance(parsed, dict) and "text" in parsed:
                model_text = parsed["text"]

        except Exception:
            pass

        # ---------- extract JSON from markdown ----------
        if not tool_calls:

            json_blocks = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", model_text, re.DOTALL)

            for block in json_blocks:

                try:
                    parsed = json.loads(block)

                    if "tool_calls" in parsed:
                        tool_calls = parsed["tool_calls"]

                    if "text" in parsed:
                        model_text = parsed["text"]

                    break

                except Exception:
                    continue

    # ----------------------------------
    # No tool required
    # ----------------------------------

    if not tool_calls:

        history.append({
            "role": "assistant",
            "content": model_text
        })

        return model_text

    # ----------------------------------
    # Execute tools
    # ----------------------------------

    MAX_TOOL_ITERATIONS = 5
    iteration = 0

    VALID_TOOL_NAMES = {t["function"]["name"] for t in tools}

    while tool_calls and iteration < MAX_TOOL_ITERATIONS:

        iteration += 1

        for call in tool_calls:

            name = call.get("name")
            tool_call_id = call.get("id")

            if name not in VALID_TOOL_NAMES:
                messages.append({
                    "role": "tool",
                    "name": name,
                    "content": json.dumps({"error": "Unknown tool"})
                })
                continue

            args = call.get("arguments", {})

            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    args = {}

            if not isinstance(args, dict):
                args = {}

            try:

                tool_result = execute_tool(
                    tool_name=name,
                    db=db,
                    args=args,
                    actor=actor
                )

                tool_msg = {
                    "role": "tool",
                    "name": name,
                    "content": json.dumps(tool_result, default=str),
                }
                if tool_call_id:
                    tool_msg["tool_call_id"] = tool_call_id

                messages.append(tool_msg)

                history.append({
                    "role": "tool",
                    "content": json.dumps(tool_result, default=str)
                })

            except Exception as e:

                messages.append({
                    "role": "tool",
                    "name": name,
                    "content": json.dumps({"error": str(e)})
                })

        followup = ai_chat_with_tools(messages=messages, tools=tools)

        if not followup:
            return "Sorry, something went wrong while processing your request."

        model_text = strip_role_prefixes(followup.get("text") or "")
        tool_calls = followup.get("tool_calls")

        if not tool_calls:

            history.append({
                "role": "assistant",
                "content": model_text
            })

            return model_text

    return "Sorry, I couldn't complete the request due to an internal processing issue."
