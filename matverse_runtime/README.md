# MatVerse Runtime (Constitutional Minimal Core)

## Continuous mode (7+ days)

Run the runtime as a long-lived process with deterministic replay checks and periodic ledger snapshots:

```bash
python runtime.py \
  --tick 60 \
  --replay-every 10 \
  --backup-every 60 \
  --backup-dir ./snapshots
```

What this guarantees:

- append-only ledger growth (`ledger.jsonl`)
- ProjectionGate hard-fail on invalid state
- OHASH + EvidenceNote for each emitted block
- deterministic replay health checks every `--replay-every` blocks
- immutable-by-practice snapshot exports every `--backup-every` blocks

## Operational minimum

- Keep process alive continuously (systemd/tmux/supervisor)
- Persist `ledger.jsonl` and `organism.key`
- Replicate `snapshots/` to external storage
- Run `python replay.py` after restarts or during audits


## Public read-only status API

Expose a minimal observer surface for external verifiers:

```bash
python public_status_api.py --host 0.0.0.0 --port 8787
```

Endpoints:

- `/latest-block` → full latest block payload
- `/ledger-head` → current height + hash + timestamp
- `/psi` → latest psi signal
- `/replay-status` → whether replay checks are ready to run
