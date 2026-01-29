from __future__ import annotations

import os
from typing import Any, Dict, Iterable
from pathlib import Path


class GitHubPublisher:
    name = "github"

    def publish(self, files: Iterable[Path], manifest: Dict[str, Any]) -> Dict[str, Any]:
        token = os.getenv("MATVERSE_GITHUB_TOKEN")
        repo = os.getenv("MATVERSE_GITHUB_REPO")
        if not token or not repo:
            return {
                "ok": False,
                "error": "Missing MATVERSE_GITHUB_TOKEN or MATVERSE_GITHUB_REPO",
            }

        return {"ok": True, "message": "Placeholder GitHub publisher"}
