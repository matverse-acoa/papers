from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def zenodo_metadata(orcid: str = "0009-0008-2973-4047") -> dict:
    today = date.today().isoformat()
    return {
        "title": f"MatVerse Constitutional Ledger Snapshot {today}",
        "description": "Continuous constitutional runtime snapshot with replay-verifiable evidence.",
        "creators": [{"name": "MatVerse Publisher", "orcid": orcid}],
        "keywords": [
            "constitutional runtime",
            "hash chain",
            "ohash",
            "evidence ledger",
        ],
        "license": "MIT",
        "access_right": "open",
        "upload_type": "dataset",
    }


def build_zenodo_package(files: list[str | Path], zip_path: str | Path, metadata_path: str | Path) -> None:
    with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as zf:
        for file in files:
            p = Path(file)
            if p.exists():
                zf.write(p, arcname=p.name)

    Path(metadata_path).write_text(json.dumps(zenodo_metadata(), indent=2), encoding="utf-8")
