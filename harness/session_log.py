"""
Session log — the "temporal composability" half of the design. Every
cycle writes an append-only JSONL trace: the system prompt, every model
call, every tool call/result, and the final narrative. Nothing is
overwritten. That gives you three things DeepSeek Harness treats as
first-class:

- Inspect: read exactly what the agent saw and decided, after the fact.
- Replay: re-render a past session without re-running the LLM or hitting
  the market/broker again.
- Fork: cut a session at step N and continue from there (e.g. re-run just
  the entry-model step with a tweaked instruction, keeping the same HTF
  bias evidence).
"""
import json
import os
import uuid
from datetime import datetime, timezone

SESSIONS_DIR = "sessions"


class SessionLog:
    def __init__(self, path: str, session_id: str):
        self.path = path
        self.session_id = session_id

    @classmethod
    def start(cls, symbol: str, sessions_dir: str = SESSIONS_DIR) -> "SessionLog":
        os.makedirs(sessions_dir, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        session_id = f"{symbol.replace('=', '_')}_{stamp}_{uuid.uuid4().hex[:6]}"
        path = os.path.join(sessions_dir, f"{session_id}.jsonl")
        log = cls(path, session_id)
        log.append("session_start", {"symbol": symbol})
        return log

    def append(self, event_type: str, data) -> dict:
        event = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "type": event_type,
            "data": data,
        }
        with open(self.path, "a") as f:
            f.write(json.dumps(event, default=str) + "\n")
        return event

    @staticmethod
    def replay(path: str):
        """Yields every event in a session log, in order."""
        # Accept bare filenames (from list_sessions) or full/relative paths
        if not os.path.isabs(path) and not os.path.exists(path):
            path = os.path.join(SESSIONS_DIR, path)
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)

    @staticmethod
    def fork(path: str, upto_index: int, sessions_dir: str = SESSIONS_DIR) -> str:
        """Copies events [0, upto_index) into a new session file and
        returns its path — continue a run from that point with a fresh
        SessionLog(new_path, new_id) if you want to keep appending."""
        events = list(SessionLog.replay(path))[:upto_index]
        base = os.path.splitext(os.path.basename(path))[0]
        new_path = os.path.join(sessions_dir, f"{base}_fork{uuid.uuid4().hex[:4]}.jsonl")
        with open(new_path, "w") as f:
            for e in events:
                f.write(json.dumps(e) + "\n")
        return new_path

    @staticmethod
    def list_sessions(sessions_dir: str = SESSIONS_DIR) -> list:
        if not os.path.isdir(sessions_dir):
            return []
        return sorted(f for f in os.listdir(sessions_dir) if f.endswith(".jsonl"))
