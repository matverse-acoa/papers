# SPEC-1-Execução-e-Integração-Motor

## Objetivo
Executar localmente o stack v11 (publish fortificado + telemetria segura) e integrar o pipeline ao motor de produção de artefatos sem depender de serviços externos.

## Escopo MVP
- **Must**: ambiente local em venv, health-check, publicação de teste, integração com produtor de artefatos.
- **Should**: telemetria habilitável via env e geração de evidências/certificados em disco.
- **Could**: tokens reais + release via `gh`.
- **Won’t**: integrações físicas (CAN/PLC/etc.) neste MVP.

## Passo a passo

### 1) Ambiente
```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install pyyaml pytest
```

### 2) Testes
```bash
pytest -q tests/test_publish_fortified.py tests/test_matverse_telemetry_secrets.py tests/test_matverse_fortified_publisher.py
```

### 3) Execução da CLI
```bash
python matverse_fortified_publisher.py
```
Use opções **2** (criar paper) e **4** (publicar).

### 4) Hook no motor (software)
Arquivo de referência: `motor_hook.py`.

```bash
python motor_hook.py
```

### 5) Telemetria e segredos por ENV
```bash
export MATVERSE_TELEMETRY_ENABLED=true
export MATVERSE_TELEMETRY_SECURE=true
export MATVERSE_TELEMETRY_ENDPOINT="https://telemetry.matverse.science/secure-ingest"
export MATVERSE_SECRETS_ROTATION=3600
export MATVERSE_SECRETS_ALLOWED="api_key,auth_token,session_token"
```

### 6) Deploy de fumaça
```bash
chmod +x ./deploy_fortified_publisher.sh
./deploy_fortified_publisher.sh
```

### 7) Release opcional
```bash
scripts/manage_release.sh v11.0.0 "MatVerse v11.0.0"
```

## Resultados esperados
- `health_check()` retornando `ok=true`.
- Publicação com `success=true`.
- `doi_ready_artifact` presente no resultado do pipeline.
- Evidências contendo `ohash`, `merkle_root` e `ledger_entry_id`.
- Artefato local em `published_artifacts/*.json`.
- Telemetria sem segredo bruto (apenas hash/redação).
