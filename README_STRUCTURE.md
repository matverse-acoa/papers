# matverse-acoa-papers

**Monorepo para papers do Matverse com auditabilidade automática via CI/CD.**

## 📁 Estrutura

```
matverse-acoa-papers/
├── papers/
│   ├── paper-0-foundations/           # Foundations
│   ├── paper-1-coherent-action-spaces/    # CAS
│   ├── paper-2-acoa/                  # ACOA
│   └── paper-3-omega-gate/            # Omega Gate
├── evidence/
│   └── index.json                     # Registry com SHA256 de todos os releases
├── scripts/
│   ├── build_paper.sh                 # Compile TeX → PDF
│   ├── package_arxiv.sh               # Package limpo para arXiv
│   └── sha256_update.py               # Atualizar registry
├── .github/workflows/
│   └── arxiv-pack.yml                 # CI/CD pipeline
└── README.md
```

## 🚀 Como usar

### 1. Setup de um novo paper

```bash
# Crie paper.tex em um diretório
mkdir papers/paper-X-name
cd papers/paper-X-name
touch paper.tex references.bib
```

**Estrutura mínima esperada:**
- `paper.tex` (obrigatório)
- `references.bib` (se usará bibtex)
- `figs/` (figuras, opcional)

### 2. Compilar localmente

```bash
./scripts/build_paper.sh paper-1-coherent-action-spaces
```

Gera `papers/paper-1-coherent-action-spaces/paper.pdf`

### 3. Empacotar para arXiv

```bash
./scripts/package_arxiv.sh paper-1-coherent-action-spaces v1
```

Cria:
- `releases/paper-1-coherent-action-spaces-v1.tar.gz` (limpo, sem lixo)
- Atualiza `evidence/index.json` com SHA256

### 4. Pipeline automático (GitHub Actions)

Quando você faz `git push`:
1. ✅ Detecta mudanças em `papers/`
2. ✅ Compila com `latexmk`
3. ✅ Empacota para arXiv
4. ✅ Calcula SHA256
5. ✅ Atualiza `evidence/index.json`
6. ✅ Cria GitHub Release com tarball anexado

**Resultado:** você pode fazer download do tarball do Release e fazer upload direto no arXiv.

## 🔐 Auditabilidade

Cada release gera uma entrada em `evidence/index.json`:

```json
{
  "package": "paper-1-coherent-action-spaces-v1",
  "tarball": "releases/paper-1-coherent-action-spaces-v1.tar.gz",
  "sha256": "abcd1234...",
  "timestamp": "2025-01-21T10:30:00Z",
  "size_bytes": 1048576
}
```

**Benefícios:**
- ✅ Rastreabilidade completa
- ✅ Repetibilidade (CI/CD garante build idêntico)
- ✅ Prova de versão (GitHub Release + git tags)
- ✅ arXiv-safe (tarball sem metadados desnecessários)

## 📋 Workflow recomendado

1. **Editar paper.tex** (via Codex ou local)
2. **Testar localmente:** `./scripts/build_paper.sh paper-1-...`
3. **Fazer commit:** `git add papers/paper-1-...; git commit -m "..."`
4. **Push:** `git push origin main`
5. **CI roda automaticamente** (build + package + release)
6. **Download tarball do GitHub Release**
7. **Upload no arXiv** (formulário web)

## 🛠 Dependências

- `latexmk` (LaTeX compilation)
- `texlive-full` (LaTeX packages)
- `python3` (scripts de auditoria)
- `git` (versionamento)

Setup em Ubuntu:
```bash
apt-get install -y latexmk texlive-full python3
```

## 📝 Notas

- Cada `paper-X-*/` é **independente** — pode ter seu próprio `.bbl`, figuras, etc.
- O CI **exclui automaticamente** logs, arquivos temporários, `.git`, etc.
- `evidence/index.json` é o **single source of truth** para auditoria
- GitHub Releases funcionam como **backup + distribuição**

---

**Criado para:** auditabilidade desde o início, repetibilidade garantida, submission simples.
