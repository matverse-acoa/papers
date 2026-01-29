from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict


class ProvenanceBuilder:
    def generate(self, manifest: Dict[str, Any], sbom_path: Path) -> Dict[str, Any]:
        sbom_hash = self._hash_file(sbom_path)
        provenance = {
            "slsa_level": 2,
            "generated_at": self._now(),
            "manifest_hash": manifest["root_hash"],
            "sbom": str(sbom_path),
            "sbom_hash": sbom_hash,
            "materials": manifest.get("files", []),
        }

        out_path = Path(os.getenv("MATVERSE_PROVENANCE_PATH", Path.cwd() / "provenance.json"))
        with out_path.open("w", encoding="utf-8") as handle:
            json.dump(provenance, handle, indent=2)

        provenance["path"] = out_path
        return provenance

    def _hash_file(self, path: Path) -> str:
        hasher = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _now(self) -> str:
        return os.getenv("MATVERSE_TIMESTAMP") or self._utc_now()

    def _utc_now(self) -> str:
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()
