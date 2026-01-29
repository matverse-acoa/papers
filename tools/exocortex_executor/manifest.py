from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable


class ManifestBuilder:
    def __init__(self, trace_id: str) -> None:
        self.trace_id = trace_id

    def build(self, files: Iterable[Path]) -> Dict[str, Any]:
        file_entries = []
        for path in sorted(files, key=lambda p: str(p)):
            digest = self._hash_file(path)
            file_entries.append({"path": str(path), "sha256": digest})

        root_hash = self._hash_root(file_entries)
        manifest = {
            "trace_id": self.trace_id,
            "generated_at": self._now(),
            "root_hash": root_hash,
            "files": file_entries,
        }
        manifest["signature"] = self._sign_manifest(manifest)

        out_path = Path(os.getenv("MATVERSE_MANIFEST_PATH", Path.cwd() / "manifest.json"))
        with out_path.open("w", encoding="utf-8") as handle:
            json.dump(manifest, handle, indent=2)

        manifest["path"] = out_path
        return manifest

    def _hash_file(self, path: Path) -> str:
        hasher = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _hash_root(self, file_entries) -> str:
        payload = json.dumps(file_entries, sort_keys=True).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def _sign_manifest(self, manifest: Dict[str, Any]) -> str:
        key = self._load_signing_key()
        payload = json.dumps(
            {"root_hash": manifest["root_hash"], "trace_id": manifest["trace_id"]},
            sort_keys=True,
        ).encode("utf-8")
        return hashlib.sha256(key + payload).hexdigest()

    def _load_signing_key(self) -> bytes:
        key = os.getenv("MATVERSE_MANIFEST_SIGNING_KEY")
        if key:
            return key.encode("utf-8")

        key_path = os.getenv("MATVERSE_MANIFEST_KEY_PATH")
        if key_path:
            return Path(key_path).read_bytes()

        raise RuntimeError("Missing manifest signing key")

    def _now(self) -> str:
        return os.getenv("MATVERSE_TIMESTAMP") or self._utc_now()

    def _utc_now(self) -> str:
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()
