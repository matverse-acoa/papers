#!/usr/bin/env python3
"""
MatVerse Sovereign Executor v2
PBSE-native • Fail-Closed • SLSA • SBOM • Sigstore • Audit Trail
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from manifest import ManifestBuilder
from observability import MetricsCollector
from omega_gate import OmegaGateClient
from pbse_local import PBSEValidator
from provenance import ProvenanceBuilder
from publishers import load_publishers
from sbom import SBOMBuilder
from sigstore_attest import SigstoreAttestor
from ledger import LedgerWriter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("matverse.executor")

REPO_PATH = Path(os.getenv("MATVERSE_REPO_PATH", Path.cwd()))
MODE = os.getenv("EXECUTOR_MODE", "dry-run")  # dry-run | production


class SovereignExecutor:
    def __init__(self) -> None:
        self.trace_id = self._trace_id()
        self.pbse = PBSEValidator()
        self.metrics = MetricsCollector(self.trace_id)
        self.omega_gate = OmegaGateClient()
        self.ledger = LedgerWriter()

        self.results: Dict[str, Any] = {
            "trace_id": self.trace_id,
            "mode": MODE,
            "start_time": self._now(),
            "steps": {},
        }

    def _trace_id(self) -> str:
        seed = f"{datetime.now(timezone.utc).isoformat()}-{os.urandom(16).hex()}"
        return hashlib.sha3_512(seed.encode()).hexdigest()[:32]

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def run(self) -> Dict[str, Any]:
        try:
            files = self.collect_files()
            manifest = ManifestBuilder(self.trace_id).build(files)
            self.results["steps"]["manifest"] = {"ok": True, "path": str(manifest["path"])}

            tests_ok = self.run_tests()
            if not tests_ok:
                return self.block("Tests failed")

            sbom_path = SBOMBuilder().generate(REPO_PATH)
            self.results["steps"]["sbom"] = {"ok": True, "path": str(sbom_path)}

            prov = ProvenanceBuilder().generate(manifest, sbom_path)
            self.results["steps"]["provenance"] = {"ok": True, "path": str(prov["path"])}

            pbse_ok = self.pbse.validate(manifest, prov)
            self.results["steps"]["pbse_local"] = {"ok": pbse_ok}
            if not pbse_ok:
                return self.block("PBSE BLOCK")

            omega_ok = self.omega_gate.validate(manifest, prov)
            self.results["steps"]["omega_gate"] = omega_ok
            if not omega_ok.get("ok", False):
                return self.block("Omega Gate BLOCK")

            sigstore = SigstoreAttestor().attest(manifest)
            self.results["steps"]["sigstore"] = sigstore
            if not sigstore.get("ok", False):
                return self.block("Sigstore attest failed")

            publishers = load_publishers()
            publish_results = self.publish(publishers, files, manifest)
            self.results["steps"]["publish"] = publish_results
            if publish_results.get("blocked"):
                return self.block("Publish blocked")

            ledger_result = self.ledger.write(self.results)
            self.results["steps"]["ledger"] = ledger_result
            if not ledger_result.get("ok", False):
                return self.block("Ledger write failed")

            self.results["success"] = True
            self.results["end_time"] = self._now()

        except Exception as exc:  # pragma: no cover - emergency catch
            logger.exception("Executor failure")
            self.results["success"] = False
            self.results["error"] = str(exc)
            self.results["end_time"] = self._now()

        self.write_report()
        return self.results

    def collect_files(self) -> List[Path]:
        patterns = ["**/*.tex", "**/*.pdf", "**/*.py", "**/*.json"]
        files: List[Path] = []
        for pattern in patterns:
            files.extend(REPO_PATH.glob(pattern))
        return [path for path in set(files) if path.is_file()]

    def run_tests(self) -> bool:
        logger.info("Running tests...")
        command = os.getenv("MATVERSE_TEST_COMMAND", "pytest -q")
        result = subprocess.run(
            command,
            cwd=REPO_PATH,
            capture_output=True,
            text=True,
            shell=True,
        )
        ok = result.returncode == 0
        self.results["steps"]["tests"] = {
            "ok": ok,
            "command": command,
            "stdout": result.stdout[:2000],
            "stderr": result.stderr[:2000],
        }
        return ok

    def publish(self, publishers, files: List[Path], manifest: Dict[str, Any]) -> Dict[str, Any]:
        if MODE != "production":
            return {"skipped": True, "mode": MODE}

        out: Dict[str, Any] = {}
        for publisher in publishers:
            result = publisher.publish(files, manifest)
            out[publisher.name] = result
            if not result.get("ok", False):
                return {"blocked": True, "details": out}
        return out

    def block(self, reason: str) -> Dict[str, Any]:
        self.results["success"] = False
        self.results["blocked"] = True
        self.results["reason"] = reason
        self.results["end_time"] = self._now()
        self.write_report()
        return self.results

    def write_report(self) -> None:
        out_dir = Path(os.getenv("MATVERSE_OUTPUT_DIR", REPO_PATH / "deploy_reports"))
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"deploy_{self.trace_id}.json"
        with path.open("w", encoding="utf-8") as handle:
            json.dump(self.results, handle, indent=2)
        logger.info("Report saved: %s", path)


if __name__ == "__main__":
    executor = SovereignExecutor()
    executor.run()
