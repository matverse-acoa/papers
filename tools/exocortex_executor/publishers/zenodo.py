from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import requests


ZENODO_API_SANDBOX = "https://sandbox.zenodo.org/api"
ZENODO_API_PRODUCTION = "https://zenodo.org/api"


class ZenodoPublisher:
    name = "zenodo"

    def __init__(self) -> None:
        sandbox = os.getenv("MATVERSE_ZENODO_SANDBOX", "true").lower() == "true"
        self.api_url = ZENODO_API_SANDBOX if sandbox else ZENODO_API_PRODUCTION
        self.token = os.getenv("MATVERSE_ZENODO_TOKEN")
        self.headers = (
            {"Authorization": f"Bearer {self.token}"} if self.token else {}
        )

    def publish(self, files: Iterable[Path], manifest: Dict[str, Any]) -> Dict[str, Any]:
        if not self.token:
            return {"ok": False, "error": "Missing MATVERSE_ZENODO_TOKEN"}

        metadata = self._build_metadata(manifest)
        deposition_id = self._create_deposition(metadata)
        if not deposition_id:
            return {"ok": False, "error": "Failed to create deposition"}

        uploaded = self._upload_files(deposition_id, files)
        if not uploaded:
            return {
                "ok": False,
                "error": "One or more uploads failed",
                "deposition_id": deposition_id,
            }

        doi = self._publish(deposition_id)
        if not doi:
            return {
                "ok": False,
                "error": "Failed to publish deposition",
                "deposition_id": deposition_id,
            }

        return {"ok": True, "deposition_id": deposition_id, "doi": doi}

    def _create_deposition(self, metadata: Dict[str, Any]) -> Optional[str]:
        response = requests.post(
            f"{self.api_url}/deposit/depositions",
            json=metadata,
            headers=self.headers,
            timeout=30,
        )
        if response.status_code == 201:
            return str(response.json().get("id"))
        return None

    def _upload_files(self, deposition_id: str, files: Iterable[Path]) -> bool:
        for file_path in files:
            with file_path.open("rb") as handle:
                response = requests.put(
                    f"{self.api_url}/deposit/depositions/{deposition_id}/files",
                    files={"file": handle},
                    headers=self.headers,
                    timeout=120,
                )
            if response.status_code not in {200, 201}:
                return False
        return True

    def _publish(self, deposition_id: str) -> Optional[str]:
        response = requests.post(
            f"{self.api_url}/deposit/depositions/{deposition_id}/actions/publish",
            headers=self.headers,
            timeout=30,
        )
        if response.status_code == 202:
            return response.json().get("doi")
        return None

    def _build_metadata(self, manifest: Dict[str, Any]) -> Dict[str, Any]:
        title = os.getenv(
            "MATVERSE_ZENODO_TITLE",
            f"MatVerse ACOA Papers - {datetime.now(timezone.utc).date()}",
        )
        description = os.getenv(
            "MATVERSE_ZENODO_DESCRIPTION",
            "MatVerse ACOA Papers automated submission bundle.",
        )
        keywords = self._parse_csv_env("MATVERSE_ZENODO_KEYWORDS")
        communities = self._parse_csv_env("MATVERSE_ZENODO_COMMUNITIES")
        creators = self._parse_creators_env()

        metadata: Dict[str, Any] = {
            "metadata": {
                "title": title,
                "description": description,
                "upload_type": "publication",
                "publication_type": "collection",
                "creators": creators,
                "license": os.getenv("MATVERSE_ZENODO_LICENSE", "cc-by-4.0"),
            }
        }

        if keywords:
            metadata["metadata"]["keywords"] = keywords

        if communities:
            metadata["metadata"]["communities"] = [
                {"identifier": community} for community in communities
            ]

        metadata["metadata"]["notes"] = json.dumps(
            {"trace_id": manifest.get("trace_id"), "files": manifest.get("files", {})},
            ensure_ascii=False,
        )

        return metadata

    @staticmethod
    def _parse_csv_env(name: str) -> List[str]:
        value = os.getenv(name, "").strip()
        if not value:
            return []
        return [item.strip() for item in value.split(",") if item.strip()]

    @staticmethod
    def _parse_creators_env() -> List[Dict[str, str]]:
        raw = os.getenv("MATVERSE_ZENODO_CREATORS", "").strip()
        if not raw:
            return [{"name": os.getenv("MATVERSE_ZENODO_AUTHOR", "MatVerse Team")}]
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = []
        creators: List[Dict[str, str]] = []
        if isinstance(parsed, list):
            for entry in parsed:
                if isinstance(entry, dict) and entry.get("name"):
                    creators.append({"name": entry["name"]})
        if not creators:
            creators = [{"name": os.getenv("MATVERSE_ZENODO_AUTHOR", "MatVerse Team")}]
        return creators
