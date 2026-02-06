import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from matverse_fortified_publisher import FortifiedPublisher, PaperRepository


def test_create_and_get_paper(tmp_path):
    repo = PaperRepository(str(tmp_path / "papers"))
    created = repo.create_paper(
        title="Teste",
        authors=[{"name": "Autor"}],
        abstract="Resumo",
        category="draft",
    )
    loaded = repo.get_paper(created["paper_id"])
    assert loaded is not None
    assert loaded["title"] == "Teste"
    assert loaded["status"] == "draft"


def test_publish_pipeline(tmp_path):
    publisher = FortifiedPublisher(str(tmp_path / "papers"))
    created = publisher.repo.create_paper(
        title="Paper robusto",
        authors=[{"name": "Autor"}],
        abstract="Resumo",
        category="draft",
    )
    paper_id = created["paper_id"]
    p = publisher.repo.get_paper(paper_id)
    assert p is not None
    content = p["content"] + "\n[1][2][3][4][5]\nLimitações\n"
    (tmp_path / "papers" / "drafts" / paper_id / f"{paper_id}.md").write_text(content, encoding="utf-8")

    result = asyncio.run(publisher.publish_paper(paper_id, ["zenodo", "github"]))
    assert result["success"] is True
    assert "zenodo" in result["publication_results"]
