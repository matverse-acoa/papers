"""MatVerse v11: integração de publicação fortificada com fluxo principal."""

from __future__ import annotations

from typing import Any, Dict, Optional

from publish_fortified import FortifiedPublisher

try:
    from matverse_telemetry_secrets import SecureTelemetryWithSecrets, SecretsVault
except Exception:  # pragma: no cover
    SecureTelemetryWithSecrets = None  # type: ignore
    SecretsVault = None  # type: ignore


class _MatVerseIntegratedSystemV10Fallback:
    """Fallback mínimo quando v10 não está disponível no ambiente."""

    def process_artifact(self, artifact: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "artifact": artifact,
            "processed": True,
            "pipeline": "v10-fallback",
        }


try:
    from matverse_v10 import MatVerseIntegratedSystemV10 as _BaseV10  # type: ignore
except Exception:  # pragma: no cover
    _BaseV10 = _MatVerseIntegratedSystemV10Fallback


class MatVerseIntegratedSystemV11(_BaseV10):
    """Extensão da v10 que exige validação MAVK fortificada antes de publicar."""

    def __init__(self, fortified_publisher: Optional[FortifiedPublisher] = None, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fortified_publisher = fortified_publisher or FortifiedPublisher()
        self.telemetry = None
        if SecureTelemetryWithSecrets and SecretsVault:
            self.telemetry = SecureTelemetryWithSecrets(SecretsVault())

    def process_artifact(self, artifact: Dict[str, Any]) -> Dict[str, Any]:
        result = super().process_artifact(artifact)
        publication = self.fortified_publisher.publish(
            artifact=result,
            metadata={
                "title": artifact.get("title", "MatVerse Artifact"),
                "authors": artifact.get("authors", []),
                "description": artifact.get("abstract", ""),
            },
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


__all__ = ["MatVerseIntegratedSystemV11"]
