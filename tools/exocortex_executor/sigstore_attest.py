from __future__ import annotations

import os
import subprocess
from typing import Any, Dict


class SigstoreAttestor:
    def attest(self, manifest: Dict[str, Any]) -> Dict[str, Any]:
        if os.getenv("EXECUTOR_MODE", "dry-run") != "production":
            return {"ok": True, "skipped": True, "reason": "dry-run"}

        predicate = os.getenv("MATVERSE_SIGSTORE_PREDICATE", str(manifest["path"]))
        command = os.getenv(
            "MATVERSE_SIGSTORE_COMMAND",
            f"cosign attest --predicate {predicate} --type matverse",
        )
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            return {
                "ok": False,
                "error": result.stderr.strip() or result.stdout.strip(),
            }
        return {"ok": True}
