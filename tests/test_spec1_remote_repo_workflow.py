import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import init_here
import motor_to_repo


def test_motor_to_repo_runs(tmp_path):
    asyncio.run(motor_to_repo._run(str(tmp_path / "published")))
    assert any((tmp_path / "published").glob("*.json"))


def test_init_here_runs(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["init_here.py", "--repo-path", str(tmp_path), "--title", "X"])
    init_here.main()
    assert (tmp_path / "drafts").exists()
