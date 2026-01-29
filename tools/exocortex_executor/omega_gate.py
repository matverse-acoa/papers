from __future__ import annotations

import json
import os
import urllib.request
from typing import Any, Dict


class OmegaGateClient:
    def __init__(self) -> None:
        self.url = os.getenv("MATVERSE_OMEGA_GATE_URL")

    def validate(self, manifest: Dict[str, Any], provenance: Dict[str, Any]) -> Dict[str, Any]:
        if not self.url:
            return {"ok": True, "skipped": True, "reason": "offline"}

        payload = json.dumps({"manifest": manifest, "provenance": provenance}).encode("utf-8")
        request = urllib.request.Request(
            self.url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                data = response.read().decode("utf-8")
                result = json.loads(data)
        except Exception as exc:  # pragma: no cover - network dependent
            return {"ok": False, "error": str(exc)}

        if not isinstance(result, dict):
            return {"ok": False, "error": "Invalid response"}

        return {"ok": bool(result.get("pass")), "response": result}
