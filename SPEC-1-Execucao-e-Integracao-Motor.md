# SPEC-1-Execução-e-Integração-Motor

## Background

Este repositório contém os módulos v11 para publicação fortificada (MAVK + evidências), telemetria segura e integração com motor:

- CLI de publicação de papers (`matverse_fortified_publisher.py`)
- Pipeline fortificada (`publish_fortified.py`) e integração v11 (`matverse_v11.py`)
- Telemetria/segredos (`matverse_telemetry_secrets.py`)
- Deploy de fumaça (`deploy_fortified_publisher.sh`)
- Gestão de releases (`scripts/manage_release.sh`)

## Requirements

### Must
- Rodar localmente com Python 3.10+ em venv.
- Executar `health_check()` e um publish de teste.
- Integrar pipeline ao motor (`ThreeBodyMotorWithSecrets`) ou outro produtor via função.

### Should
- Telemetria local habilitável/desabilitável por env.
- Gerar certificado/evidências em disco.

### Could
- Configurar tokens para publicação real em plataformas.
- Criar release via `gh`.

### Won’t (MVP)
- Integração com motor físico (ex.: CAN-bus).

## Implementation — Execução local (MVP)

### 1) Pré-requisitos

```bash
python3 -V
pip install --upgrade pip virtualenv
```

### 2) Ambiente

```bash
python -m venv .venv
source .venv/bin/activate
pip install pyyaml pytest
```

### 3) Teste rápido da suíte

```bash
pytest -q
```

### 4) Executar CLI de publicação

```bash
python matverse_fortified_publisher.py
```

Menu interativo: criar paper (opção 2) e publicar (opção 4).

### 5) Deploy de fumaça (one-shot)

```bash
export ZENODO_TOKEN="..."; export GITHUB_TOKEN="..."; export HF_TOKEN="..."
chmod +x ./deploy_fortified_publisher.sh
./deploy_fortified_publisher.sh
```

### 6) Ligar no motor (software)

Arquivo `motor_hook.py`:

```bash
python motor_hook.py
```

### 7) Telemetria e segredos (opcional)

```bash
export MATVERSE_TELEMETRY_ENABLED=true
export MATVERSE_TELEMETRY_SECURE=true
export MATVERSE_TELEMETRY_ENDPOINT="https://telemetry.matverse.science/secure-ingest"
export MATVERSE_SECRETS_ROTATION=3600
export MATVERSE_SECRETS_ALLOWED="api_key,auth_token,session_token"
```

### 8) Ajustes de pipeline

Revisar `pipeline_config.yaml`. Sem tokens reais, a publicação cai para `LocalJSONPublisher`.

### 9) Criar release (opcional)

```bash
scripts/manage_release.sh v11.0.0 "MatVerse v11.0.0"
```

## Integração com repo remoto (papers.git)

Destino: `git@github.com:matverse-acoa/papers.git`


### Passo A0 — configurar remoto automaticamente

```bash
scripts/setup_remote_repo.sh origin git@github.com:matverse-acoa/papers.git
```

### Passo A — clonar e preparar

```bash
ssh -T git@github.com
cd ~
git clone git@github.com:matverse-acoa/papers.git matverse-papers
cd matverse-papers
python -m venv .venv
source .venv/bin/activate
pip install pyyaml pytest
```

### Passo B — estrutura no repo

- Opção 1: usar CLI normalmente (subpasta `./papers/`).
- Opção 2: usar `repo_path='.'` para gravar direto no root do repo.

### Passo C — publicar direto no repo (sem subpasta)

Use `init_here.py`:

```bash
python init_here.py --repo-path . --title "Primeiro Paper"
git add .
git commit -m "chore(papers): estrutura + primeiro certificado"
git push origin main
```

### Passo D — ligar o motor v11 e versionar saídas

Use `motor_to_repo.py`:

```bash
python motor_to_repo.py --output-dir published
git add published/ evidence/ drafts/ published/
git commit -m "feat(pub): engine-002 publicado + evidências"
git push origin main
```

### Passo E — `.gitignore` sugerido

```gitignore
.venv/
__pycache__/
*.pyc
# published_artifacts/
```

## Milestones

- M1: Ambiente e testes passando
- M2: CLI publicando paper de exemplo
- M3: `motor_hook.py` publica com certificado/evidências
- M4: telemetria habilitada e sem vazamento de segredo
- M5: release criada (opcional)

## Gathering Results

- Certificado JSON presente e válido
- Evidências contendo `ohash`, `merkle_root`, `ledger_entry_id`
- `published_artifacts/engine-001.json` criado
- Telemetria contendo somente hashes/redações (sem segredos)
