from __future__ import annotations

from typing import Any, Dict


class PBSEValidator:
    def validate(self, manifest: Dict[str, Any], provenance: Dict[str, Any]) -> bool:
        if not manifest.get("signature"):
            return False
        if provenance.get("slsa_level", 0) < 2:
            return False
        if not provenance.get("materials"):
            return False
        return True
