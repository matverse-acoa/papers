from __future__ import annotations

from datetime import datetime, timezone
import os
import socket
from typing import Any


def evidence_note(state_hash: str, ohash: str) -> dict[str, Any]:
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "hostname": socket.gethostname(),
        "pid": os.getpid(),
        "runtime": "MatVerse Constitutional Runtime",
        "evidence_hash": state_hash,
        "ohash": ohash,
    }
