import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from matverse_v11 import MatVerseIntegratedSystemV11
from publish_fortified import FortifiedPublicationPipeline, LocalJSONPublisher


def test_spec1_publish_scientific_work_creates_doi_ready(tmp_path):
    pipeline = FortifiedPublicationPipeline(
        publishers=[LocalJSONPublisher(output_dir=str(tmp_path / "published_artifacts"))]
    )
    system = MatVerseIntegratedSystemV11(publication_pipeline=pipeline)

    async def _run():
        health = await system.health_check()
        assert health["ok"] is True

        out = await system.publish_scientific_work(
            {
                "id": "engine-001",
                "title": "Teste do Motor",
                "authors": [{"name": "Equipe"}],
                "abstract": "Artefato produzido pelo motor.",
                "content": {"demo": True, "references": ["r1"]},
                "evidence": {"dataset": "local"},
                "metadata": {"orcid": "0000-0000-0000-0000"},
            }
        )
        assert out["success"] is True
        assert out["doi_ready_artifact"]["ready_for_doi"] is True
        assert out["evidence_chain"]["ohash"]

    asyncio.run(_run())
