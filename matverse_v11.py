"""MatVerse v11: integração do fluxo v10 com publicação fortificada e telemetria segura."""

from __future__ import annotations

import asyncio
import threading
from typing import Any, Dict, Optional

from publish_fortified import FortifiedPublicationPipeline, FortifiedPublisher

try:
    from matverse_telemetry_secrets import SecureTelemetryWithSecrets, SecretsVault, ThreeBodyMotorWithTelemetry
except Exception:  # pragma: no cover
    SecureTelemetryWithSecrets = None  # type: ignore
    SecretsVault = None  # type: ignore
    ThreeBodyMotorWithTelemetry = None  # type: ignore


class _MatVerseIntegratedSystemV10Fallback:
    def process_artifact(self, artifact: Dict[str, Any]) -> Dict[str, Any]:
        return {"artifact": artifact, "processed": True, "pipeline": "v10-fallback"}


try:
    from matverse_v10 import MatVerseIntegratedSystemV10 as _BaseV10  # type: ignore
except Exception:  # pragma: no cover
    _BaseV10 = _MatVerseIntegratedSystemV10Fallback


class _MAVKWithTelemetryFallback:
    def validate_with_telemetry(self, artifact: Dict[str, Any]) -> Dict[str, Any]:
        return {"ok": True, "artifact_id": artifact.get("id")}


def _run_coroutine_sync(coro: Any) -> Any:
    """Executa coroutine de forma segura em contexto sync (com/sem loop ativo)."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    result: Dict[str, Any] = {}
    error: Dict[str, BaseException] = {}

    def _runner() -> None:
        try:
            result["value"] = asyncio.run(coro)
        except BaseException as exc:  # pragma: no cover
            error["exc"] = exc

    t = threading.Thread(target=_runner, daemon=True)
    t.start()
    t.join()

    if "exc" in error:
        raise error["exc"]
    return result.get("value")


class MatVerseIntegratedSystemV11(_BaseV10):
    """Extensão da v10 com publish fortificado (MAVK gate) e telemetria segura."""

    def __init__(
        self,
        fortified_publisher: Optional[FortifiedPublisher] = None,
        publication_pipeline: Optional[FortifiedPublicationPipeline] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.fortified_publisher = fortified_publisher or FortifiedPublisher()
        self.publication_pipeline = publication_pipeline or FortifiedPublicationPipeline()

        self.telemetry = None
        if SecureTelemetryWithSecrets and SecretsVault:
            self.telemetry = SecureTelemetryWithSecrets(SecretsVault())

        self.three_body_motor = ThreeBodyMotorWithTelemetry(self.telemetry) if ThreeBodyMotorWithTelemetry else None
        self.mavk_validator = _MAVKWithTelemetryFallback()

    async def health_check(self) -> Dict[str, Any]:
        return {
            "ok": True,
            "pipeline_ready": self.publication_pipeline is not None,
            "telemetry_enabled": self.telemetry is not None,
        }

    def process_artifact(self, artifact: Dict[str, Any]) -> Dict[str, Any]:
        result = super().process_artifact(artifact)
        publication = _run_coroutine_sync(
            self.fortified_publisher.publish(
                artifact=result,
                metadata={
                    "title": artifact.get("title", "MatVerse Artifact"),
                    "authors": artifact.get("authors", []),
                    "description": artifact.get("abstract", ""),
                },
            )
        )
        result["fortified_publication"] = publication
        if self.telemetry:
            self.telemetry.record_metric(
                "fortified_publication",
                {
                    "artifact_id": artifact.get("id", "anon"),
                    "published": publication.get("published", False),
                    "certificate": publication.get("certificate"),
                },
            )
        return result

    async def publish_scientific_work(self, work: Dict[str, Any]) -> Dict[str, Any]:
        motor_result = self.three_body_motor.process_artifact(work) if self.three_body_motor else {"processed": True}
        mavk_result = self.mavk_validator.validate_with_telemetry(work)
        publication_result = await self.publication_pipeline.execute_publication(
            {**work, "motor_processing": motor_result, "mavk_validation": mavk_result}
        )
        if self.telemetry:
            self.telemetry.record_metric(
                "fortified_publication",
                {
                    "work_id": work.get("id"),
                    "publication_success": publication_result.get("success", False),
                    "platforms_published": len([p for p, r in publication_result.get("publication_results", {}).items() if r.get("success")]),
                    "mavk_scores": publication_result.get("mavk_validation", {}).get("mavk_result", {}),
                },
            )
        return publication_result


__all__ = ["MatVerseIntegratedSystemV11"]
