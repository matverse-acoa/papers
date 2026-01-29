from __future__ import annotations

import os
import subprocess
from pathlib import Path


class SBOMBuilder:
    def generate(self, repo_path: Path) -> Path:
        output_path = Path(os.getenv("MATVERSE_SBOM_PATH", repo_path / "sbom.json"))
        command = os.getenv(
            "MATVERSE_SBOM_COMMAND",
            f"cyclonedx-py --format json --output {output_path}",
        )
        result = subprocess.run(command, cwd=repo_path, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(
                f"SBOM generation failed: {result.stderr.strip() or result.stdout.strip()}"
            )
        return output_path
