from collections import defaultdict, deque

class SessionState:
    def __init__(self):
        self.tools_used = []
        self.resources_accessed = set()
        self.records_returned = 0
        self.risk_score = 0.0

SESSION_MEMORY = defaultdict(lambda: deque(maxlen=10))
SESSION_STATE = {}
