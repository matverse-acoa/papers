from __future__ import annotations

import os
from typing import Any, Dict, Iterable
from pathlib import Path


class ZenodoPublisher:
    name = "zenodo"

    def publish(self, files: Iterable[Path], manifest: Dict[str, Any]) -> Dict[str, Any]:
        token = os.getenv("MATVERSE_ZENODO_TOKEN")
        if not token:
            return {"ok": False, "error": "Missing MATVERSE_ZENODO_TOKEN"}

        return {"ok": True, "message": "Placeholder Zenodo publisher"}
