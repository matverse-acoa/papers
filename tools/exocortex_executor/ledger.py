from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict


class LedgerWriter:
    def __init__(self) -> None:
        self.ledger_path = Path(
            os.getenv("MATVERSE_LEDGER_PATH", Path.cwd() / "deploy_reports" / "ledger.jsonl")
        )

    def write(self, record: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
            with self.ledger_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record) + "\n")
            return {"ok": True, "path": str(self.ledger_path)}
        except Exception as exc:  # pragma: no cover
            return {"ok": False, "error": str(exc)}
