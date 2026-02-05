import argparse
import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
LEDGER_PATH = BASE_DIR / "ledger.jsonl"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_ledger(path: Path = LEDGER_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def latest_block(path: Path = LEDGER_PATH) -> dict[str, Any]:
    rows = read_ledger(path)
    if not rows:
        return {}
    return rows[-1]


def ledger_head(path: Path = LEDGER_PATH) -> dict[str, Any]:
    block = latest_block(path)
    if not block:
        return {
            "height": -1,
            "hash": None,
            "timestamp": None,
            "as_of": _iso_now(),
        }
    return {
        "height": block.get("index", -1),
        "hash": block.get("hash"),
        "timestamp": block.get("timestamp"),
        "as_of": _iso_now(),
    }


def psi(path: Path = LEDGER_PATH) -> dict[str, Any]:
    block = latest_block(path)
    value = (block.get("state") or {}).get("psi") if block else None
    return {
        "psi": value,
        "height": block.get("index", -1) if block else -1,
        "as_of": _iso_now(),
    }


def replay_status(path: Path = LEDGER_PATH) -> dict[str, Any]:
    rows = read_ledger(path)
    if len(rows) < 2:
        return {
            "replay_ready": False,
            "blocks_available": len(rows),
            "reason": "need at least genesis + one emitted block",
            "as_of": _iso_now(),
        }
    return {
        "replay_ready": True,
        "blocks_available": len(rows),
        "latest_height": rows[-1].get("index", -1),
        "as_of": _iso_now(),
    }


class PublicStatusHandler(BaseHTTPRequestHandler):
    ledger_path = LEDGER_PATH

    def _json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/latest-block":
            block = latest_block(self.ledger_path)
            self._json(block if block else {"error": "ledger_not_found"}, status=200 if block else 404)
            return
        if self.path == "/ledger-head":
            self._json(ledger_head(self.ledger_path))
            return
        if self.path == "/psi":
            self._json(psi(self.ledger_path))
            return
        if self.path == "/replay-status":
            self._json(replay_status(self.ledger_path))
            return
        self._json({"error": "not_found", "path": self.path}, status=404)

    def log_message(self, format: str, *args: Any) -> None:
        return


def serve(host: str, port: int, ledger_path: Path = LEDGER_PATH) -> None:
    PublicStatusHandler.ledger_path = ledger_path
    server = ThreadingHTTPServer((host, port), PublicStatusHandler)
    print(f"[PUBLIC_API] serving on http://{host}:{port}")
    server.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description="MatVerse runtime read-only status API")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--ledger", default=str(LEDGER_PATH))
    args = parser.parse_args()

    serve(host=args.host, port=args.port, ledger_path=Path(args.ledger))


if __name__ == "__main__":
    main()
