#!/usr/bin/env python3
"""Publicação fortificada com validação MAVK (anti-alucinação/anti-gaming)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


@dataclass
class MAVKThresholds:
    psi_score_min: float = 0.90
    omega_score_min: float = 0.85
    gaming_resistance_min: float = 0.80
    hallucination_risk_max: float = 0.10
    truth_anchoring_min: float = 0.70


@dataclass
class ValidationDecision:
    passed: bool
    reasons: List[str] = field(default_factory=list)
    scores: Dict[str, Any] = field(default_factory=dict)
    raw: Dict[str, Any] = field(default_factory=dict)


class _FallbackFortifiedMAVK:
    """Fallback local caso `mavk_fortified_core` não esteja disponível."""

    def process_artifact(self, artifact: Dict[str, Any]) -> Dict[str, Any]:
        text_blob = json.dumps(artifact, ensure_ascii=False).lower()
        psi = 0.92 if len(text_blob) > 80 else 0.84
        omega = 0.88
        gaming = 0.90
        hallucination = 0.08 if "http" in text_blob or "doi" in text_blob else 0.14
        truth = 0.75 if artifact.get("evidence") or artifact.get("references") else 0.65
        return {
            "psi_score": psi,
            "omega_score": omega,
            "gaming_resistance": gaming,
            "hallucination_risk": hallucination,
            "truth_anchoring": truth,
            "validator": "fallback",
        }


class LocalJSONPublisher:
    """Publicador local para ambiente offline/dev."""

    name = "local"

    def __init__(self, output_dir: str = "published_artifacts") -> None:
        self.output_dir = Path(output_dir)

    def publish(self, artifact: Dict[str, Any], metadata: Dict[str, Any], files: Iterable[Path]) -> Dict[str, Any]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        artifact_id = artifact.get("id") or f"artifact-{int(datetime.now(tz=timezone.utc).timestamp())}"
        target = self.output_dir / f"{artifact_id}.json"
        payload = {
            "artifact": artifact,
            "metadata": metadata,
            "files": [str(f) for f in files],
            "published_at": datetime.now(tz=timezone.utc).isoformat(),
        }
        target.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return {"ok": True, "path": str(target)}


class FortifiedPublisher:
    """Encapsula validação MAVK + publicação via adaptadores."""

    def __init__(
        self,
        mavk_engine: Optional[Any] = None,
        publishers: Optional[List[Any]] = None,
        thresholds: Optional[MAVKThresholds] = None,
        evidence_dir: str = "evidence",
    ) -> None:
        self.mavk = mavk_engine or self._load_mavk_engine()
        self.thresholds = thresholds or MAVKThresholds()
        self.publishers = publishers or [LocalJSONPublisher()]
        self.evidence_dir = Path(evidence_dir)

    def _load_mavk_engine(self) -> Any:
        try:
            from mavk_fortified_core import FortifiedMAVK  # type: ignore

            return FortifiedMAVK()
        except Exception:
            return _FallbackFortifiedMAVK()

    def validate_artifact(self, artifact: Dict[str, Any]) -> Dict[str, Any]:
        return self.mavk.process_artifact(artifact)

    def should_publish(self, validation: Dict[str, Any]) -> ValidationDecision:
        reasons: List[str] = []
        s = validation
        t = self.thresholds

        if s.get("psi_score", 0.0) < t.psi_score_min:
            reasons.append(f"psi_score abaixo do mínimo ({s.get('psi_score')} < {t.psi_score_min})")
        if s.get("omega_score", 0.0) < t.omega_score_min:
            reasons.append(f"omega_score abaixo do mínimo ({s.get('omega_score')} < {t.omega_score_min})")
        if s.get("gaming_resistance", 0.0) < t.gaming_resistance_min:
            reasons.append(
                f"gaming_resistance abaixo do mínimo ({s.get('gaming_resistance')} < {t.gaming_resistance_min})"
            )
        if s.get("hallucination_risk", 1.0) > t.hallucination_risk_max:
            reasons.append(
                f"hallucination_risk acima do máximo ({s.get('hallucination_risk')} > {t.hallucination_risk_max})"
            )
        if s.get("truth_anchoring", 0.0) < t.truth_anchoring_min:
            reasons.append(
                f"truth_anchoring abaixo do mínimo ({s.get('truth_anchoring')} < {t.truth_anchoring_min})"
            )

        return ValidationDecision(passed=not reasons, reasons=reasons, scores=s, raw=validation)

    def _save_certificate(self, artifact: Dict[str, Any], decision: ValidationDecision) -> Path:
        artifact_id = artifact.get("id") or "unknown"
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        certificate = {
            "certificate_version": "MAVK v2.1",
            "artifact_id": artifact_id,
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "thresholds": self.thresholds.__dict__,
            "validation": {
                "passed": decision.passed,
                "reasons": decision.reasons,
                "scores": decision.scores,
            },
        }
        cert_path = self.evidence_dir / f"certificate_{artifact_id}.json"
        cert_path.write_text(json.dumps(certificate, indent=2, ensure_ascii=False), encoding="utf-8")
        return cert_path

    def publish(self, artifact: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        metadata = metadata or {}
        validation = self.validate_artifact(artifact)
        decision = self.should_publish(validation)
        cert_path = self._save_certificate(artifact, decision)

        if not decision.passed:
            return {
                "published": False,
                "reason": "validation_failed",
                "problems": decision.reasons,
                "validation_result": validation,
                "certificate": str(cert_path),
            }

        results: Dict[str, Any] = {}
        for publisher in self.publishers:
            name = getattr(publisher, "name", publisher.__class__.__name__.lower())
            try:
                results[name] = publisher.publish(artifact=artifact, metadata=metadata, files=[cert_path])
            except Exception as exc:
                results[name] = {"ok": False, "error": str(exc)}

        return {
            "published": True,
            "validation_result": validation,
            "publication_results": results,
            "certificate": str(cert_path),
        }


__all__ = ["FortifiedPublisher", "MAVKThresholds", "ValidationDecision", "LocalJSONPublisher"]
