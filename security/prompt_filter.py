# =====================================================================
# Prompt Injection Filter — Hospital-specific blocked patterns
# =====================================================================

BLOCKED_PATTERNS = [
    "dump all patients",
    "export database",
    "show all patient records",
    "show all hiv",
    "list all mental health",
    "reveal system prompt",
    "ignore previous instructions",
    "override security",
    "bypass rbac",
    "show all insurance claims",
    "dump all prescriptions",
    "show all lab reports for all patients",
    "export all billing",
    "reveal all passwords",
    "enumerate all users",
    "show all staff credentials",
]


def check_prompt(prompt):
    """Return True if the prompt matches a blocked pattern."""

    lower = prompt.lower()

    for p in BLOCKED_PATTERNS:
        if p in lower:
            return True

    return False
