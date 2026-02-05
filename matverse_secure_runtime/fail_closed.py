from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

FORENSIC_LOG = "FAILURE_FORENSIC.log"


def civilizational_fail(message: str, log_file: str | Path = FORENSIC_LOG, exit_code: int = 255) -> None:
    """Fail-closed handler: persist forensic event then terminate process."""
    path = Path(log_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    with path.open("a", encoding="utf-8") as file:
        file.write(f"{timestamp} — {message}\n")
    raise SystemExit(exit_code)
