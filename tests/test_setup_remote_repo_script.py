import subprocess
from pathlib import Path


def test_setup_remote_repo_script_sets_remote(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)

    script = Path(__file__).resolve().parents[1] / "scripts" / "setup_remote_repo.sh"
    remote = "git@github.com:matverse-acoa/papers.git"
    subprocess.run(["bash", str(script), "origin", remote], cwd=repo, check=True, capture_output=True, text=True)

    got = subprocess.run(["git", "remote", "get-url", "origin"], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()
    assert got == remote
