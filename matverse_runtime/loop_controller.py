from __future__ import annotations

import json
import threading
from collections import deque
from datetime import datetime, timedelta, timezone
from pathlib import Path
from queue import Empty, Queue
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
LEDGER_PATH = BASE_DIR / "ledger.jsonl"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(ts: datetime | None = None) -> str:
    return (ts or _utcnow()).isoformat().replace("+00:00", "Z")


class LoopController:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._events: deque[dict[str, Any]] = deque(maxlen=2000)
        self._realtime_log: deque[str] = deque(maxlen=200)
        self._queue: Queue[dict[str, Any]] = Queue()
        self.loop_id = "matverse-loop-001"
        self.state = "running"
        self.last_tx: str | None = None
        self.last_doi: str | None = None
        self.last_trigger: str | None = None
        self.total_loops = 0
        self.omega_spent = 0.0
        self.psi = 0.71
        self.replay_interval_seconds = 6 * 60 * 60

    def _ledger_head(self) -> str | None:
        if not LEDGER_PATH.exists():
            return None
        last: str | None = None
        for line in LEDGER_PATH.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            last = row.get("hash")
        return last

    def _append_event(self, event: dict[str, Any]) -> None:
        self._events.append(event)
        log_line = f"[{event['ts'][11:19]}] trigger={event['trigger']} tx_id={event.get('tx_id')} doi={event.get('doi')}"
        self._realtime_log.append(log_line)
        self._queue.put(event)

    def status(self) -> dict[str, Any]:
        with self._lock:
            next_replay = _utcnow() + timedelta(seconds=self.replay_interval_seconds)
            return {
                "loop_id": self.loop_id,
                "state": self.state,
                "last_tx": self.last_tx,
                "last_doi": self.last_doi,
                "last_trigger": self.last_trigger,
                "next_replay": _iso(next_replay),
                "total_loops": self.total_loops,
                "omega_spent": round(self.omega_spent, 2),
                "psi": self.psi,
                "ledger_head": self._ledger_head(),
                "realtime_log": list(self._realtime_log)[-20:],
            }

    def audit(self, limit: int) -> list[dict[str, Any]]:
        with self._lock:
            items = list(self._events)
            if limit > 0:
                items = items[-limit:]
            return items[::-1]

    def pause(self) -> dict[str, Any]:
        with self._lock:
            self.state = "paused"
            return {"status": "paused", "loop_id": self.loop_id}

    def start(self) -> dict[str, Any]:
        with self._lock:
            self.state = "running"
            return {"status": "running", "loop_id": self.loop_id}

    def destroy(self) -> dict[str, Any]:
        with self._lock:
            self.state = "destroyed"
            return {"status": "destroyed", "loop_id": self.loop_id}

    def accelerate(self, factor: int) -> dict[str, Any]:
        with self._lock:
            self.replay_interval_seconds = max(1, int((6 * 60 * 60) / factor))
            return {
                "status": "accelerated",
                "factor": factor,
                "replay_interval_seconds": self.replay_interval_seconds,
            }

    def trigger(self, trigger_type: str, tx_id: str | None, doi: str | None) -> dict[str, Any]:
        with self._lock:
            if self.state != "running":
                return {"triggered": False, "reason": f"loop_{self.state}"}

            self.last_trigger = trigger_type
            self.last_tx = tx_id or self.last_tx
            self.last_doi = doi or self.last_doi
            self.total_loops += 1
            self.omega_spent += 3.06
            event = {
                "ts": _iso(),
                "trigger": trigger_type,
                "doi": doi,
                "tx_id": tx_id,
                "evidence_hash": None,
                "commit": None,
            }
            self._append_event(event)
            return {"triggered": True, "type": trigger_type, "tx_id": tx_id}

    def register_publish(self, tx_id: str, doi: str | None, evidence_hash: str | None, commit: str | None) -> None:
        with self._lock:
            self.last_tx = tx_id
            self.last_doi = doi
            self.last_trigger = "publish"
            self.total_loops += 1
            event = {
                "ts": _iso(),
                "trigger": "publish",
                "doi": doi,
                "tx_id": tx_id,
                "evidence_hash": evidence_hash,
                "commit": commit,
            }
            self._append_event(event)

    def stream_next(self, timeout: float = 15.0) -> dict[str, Any] | None:
        try:
            return self._queue.get(timeout=timeout)
        except Empty:
            return None


loop_controller = LoopController()
