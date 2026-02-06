import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from matverse_v11 import MatVerseIntegratedSystemV11
from publish_fortified import FortifiedPublisher, LocalJSONPublisher, MAVKThresholds


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
    result = publisher.publish({"id": "artifact-pass", "content": "ok"}, metadata={"title": "T"})
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
    result = publisher.publish({"id": "artifact-fail", "content": "bad"})
    assert result["published"] is False
    assert result["reason"] == "validation_failed"
    assert len(result["problems"]) > 0


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
