from __future__ import annotations

import json
import os
import tarfile
from pathlib import Path
from typing import Any, Dict, Iterable


class LocalArchivePublisher:
    name = "local_archive"

    def publish(self, files: Iterable[Path], manifest: Dict[str, Any]) -> Dict[str, Any]:
        archive_dir = Path(os.getenv("MATVERSE_ARCHIVE_DIR", Path.cwd() / "archives"))
        archive_dir.mkdir(parents=True, exist_ok=True)
        archive_path = archive_dir / f"archive_{manifest['trace_id']}.tar.gz"

        with tarfile.open(archive_path, "w:gz") as tar:
            for path in files:
                tar.add(path, arcname=path.name)

        metadata_path = archive_dir / f"archive_{manifest['trace_id']}.json"
        with metadata_path.open("w", encoding="utf-8") as handle:
            json.dump({"manifest": manifest, "archive": str(archive_path)}, handle, indent=2)

        return {"ok": True, "archive": str(archive_path)}
