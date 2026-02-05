# MatVerse Secure Runtime (EvidenceNote + OHASH + Segurança)

Runtime mínimo irreversível com:
- ledger append-only (fsync)
- cadeia causal hashada (SHA3-256)
- ProjectionGate fail-closed
- OHASH encadeado
- assinatura HMAC-SHA3
- Merkle root por bloco
- replay determinístico com validação completa
- guardião de integridade anti-rewrite
- ancoragem Bitcoin (dry-run ou live via Electrum)
- notarização assinada do ledger
- auditoria consolidada e pacote Zenodo

## Rodar runtime
```bash
python -m matverse_secure_runtime.runtime --max-blocks 3
```

## Validar integridade
```bash
python -c "from matverse_secure_runtime.replay import replay_verify; replay_verify('matverse_secure_runtime/ledger.jsonl')"
```

## Pipeline civilizacional (local)
```bash
python -m matverse_secure_runtime.civilizational_submit \
  --ledger matverse_secure_runtime/ledger.jsonl \
  --blocks 16 --tick 0 --output-dir matverse_secure_runtime/artifacts
```

## Anchoring live na Bitcoin
Use `--live-anchor` e configure um endereço real + Electrum CLI disponível.
