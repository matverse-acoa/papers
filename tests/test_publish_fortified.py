import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from matverse_v11 import MatVerseIntegratedSystemV11
from publish_fortified import (
    FortifiedPublicationPipeline,
    FortifiedPublisher,
    LocalJSONPublisher,
    LocalTelemetrySink,
    MAVKThresholds,
)


class DummyMAVKPass:
    def process_artifact(self, artifact):
        return {
            "psi_score": 0.95,
            "omega_score": 0.90,
            "gaming_resistance": 0.90,
            "hallucination_risk": 0.05,
            "truth_anchoring": 0.85,
        }


class DummyMAVKFail:
    def process_artifact(self, artifact):
        return {
            "psi_score": 0.70,
            "omega_score": 0.70,
            "gaming_resistance": 0.60,
            "hallucination_risk": 0.30,
            "truth_anchoring": 0.40,
        }


def test_fortified_publish_pass(tmp_path):
    publisher = FortifiedPublisher(
        mavk_engine=DummyMAVKPass(),
        publishers=[LocalJSONPublisher(output_dir=str(tmp_path / "published"))],
        evidence_dir=str(tmp_path / "evidence"),
    )
    result = asyncio.run(publisher.publish({"id": "artifact-pass", "content": "ok"}, metadata={"title": "T"}))
    assert result["published"] is True
    assert "local" in result["publication_results"]
    assert Path(result["certificate"]).exists()


def test_fortified_publish_fail(tmp_path):
    publisher = FortifiedPublisher(
        mavk_engine=DummyMAVKFail(),
        publishers=[LocalJSONPublisher(output_dir=str(tmp_path / "published"))],
        thresholds=MAVKThresholds(),
        evidence_dir=str(tmp_path / "evidence"),
    )
    result = asyncio.run(publisher.publish({"id": "artifact-fail", "content": "bad"}))
    assert result["published"] is False
    assert result["reason"] == "validation_failed"
    assert len(result["problems"]) > 0


def test_pipeline_execute_publication(tmp_path):
    pipeline = FortifiedPublicationPipeline(publishers=[LocalJSONPublisher(output_dir=str(tmp_path / "published"))])
    pipeline.mavk_validator.mavk = DummyMAVKPass()
    out = asyncio.run(
        pipeline.execute_publication(
            {
                "id": "artifact-pipeline",
                "title": "Paper",
                "authors": ["A"],
                "abstract": "Resumo",
                "metadata": {"orcid": "0000-0000-0000-0000"},
                "content": {"claims": ["c1"], "evidence": ["e1"]},
            }
        )
    )
    assert out["success"] is True
    assert out["evidence_chain"]["ohash"]


def test_matverse_v11_integration(tmp_path):
    publisher = FortifiedPublisher(
        mavk_engine=DummyMAVKPass(),
        publishers=[LocalJSONPublisher(output_dir=str(tmp_path / "published"))],
        evidence_dir=str(tmp_path / "evidence"),
    )
    system = MatVerseIntegratedSystemV11(fortified_publisher=publisher)
    out = system.process_artifact({"id": "w1", "title": "Paper", "authors": ["A"]})
    assert out["processed"] is True
    assert out["fortified_publication"]["published"] is True

    health = asyncio.run(system.health_check())
    assert health["ok"] is True

    publication = asyncio.run(system.publish_scientific_work({"id": "w2", "title": "P2", "authors": ["B"]}))
    assert "success" in publication


def test_process_artifact_inside_running_loop(tmp_path):
    publisher = FortifiedPublisher(
        mavk_engine=DummyMAVKPass(),
        publishers=[LocalJSONPublisher(output_dir=str(tmp_path / "published"))],
        evidence_dir=str(tmp_path / "evidence"),
    )
    system = MatVerseIntegratedSystemV11(fortified_publisher=publisher)

    async def _run():
        out = system.process_artifact({"id": "w-loop", "title": "Loop", "authors": ["A"]})
        assert out["fortified_publication"]["published"] is True

    asyncio.run(_run())


def test_pipeline_trace_to_doi_ready_artifact(tmp_path):
    telemetry = LocalTelemetrySink()
    pipeline = FortifiedPublicationPipeline(
        publishers=[LocalJSONPublisher(output_dir=str(tmp_path / "published"))],
        telemetry=telemetry,
    )
    pipeline.mavk_validator.mavk = DummyMAVKPass()

    out = asyncio.run(
        pipeline.execute_publication(
            {
                "id": "artifact-doi",
                "title": "DOI Artifact",
                "authors": ["A"],
                "abstract": "Resumo",
                "metadata": {"orcid": "0000-0000-0000-0000"},
                "content": {"claims": ["c1"], "evidence": ["e1"]},
            }
        )
    )

    assert out["success"] is True
    assert out["doi_ready_artifact"]["ready_for_doi"] is True
    stages = [e["stage"] for e in out["pipeline_trace"]]
    assert "telemetry" in stages
    assert "hash" in stages
    assert "ledger" in stages
    assert "evidence" in stages
    assert "doi_ready_artifact" in stages
