import subprocess
from pathlib import Path


def _run(repo: Path, remote: str) -> str:
    script = Path(__file__).resolve().parents[1] / "scripts" / "setup_remote_repo.sh"
    subprocess.run(["bash", str(script), "origin", remote], cwd=repo, check=True, capture_output=True, text=True)
    got = subprocess.run(["git", "remote", "get-url", "origin"], cwd=repo, check=True, capture_output=True, text=True)
    return got.stdout.strip()


def test_setup_remote_repo_script_sets_ssh_remote(tmp_path):
    repo = tmp_path / "repo_ssh"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    assert _run(repo, "git@github.com:matverse-acoa/papers.git") == "git@github.com:matverse-acoa/papers.git"


def test_setup_remote_repo_script_normalizes_https_repo_url(tmp_path):
    repo = tmp_path / "repo_https"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    assert _run(repo, "https://github.com/matverse-acoa/papers") == "https://github.com/matverse-acoa/papers.git"
