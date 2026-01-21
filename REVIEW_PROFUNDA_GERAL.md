# REVISÃO PROFUNDA — MODO AUDITORIA (Prova-ou-nada)
**Data**: 21 de janeiro de 2026  
**Status**: Revisão crítica + plano de correção baseado em evidências verificáveis

---

## 1. Diagnóstico do estado atual (com base no que foi mostrado)

### 1.1 O que é **fato** (auditável)
- Repositório acessível localmente em `/workspace/papers`.
- Estrutura de diretórios existente (`papers/`, `scripts/`, `evidence/`, `.github/workflows/`).
- **Nenhum** arquivo de dependências foi detectado (`package.json`, `pyproject.toml`, etc.).
- Tentativa de disparar `gh workflow run ...` **falhou** com `HTTP 403: Resource not accessible by integration`.

### 1.2 O que **não pode ser afirmado** sem logs/artefatos
- Que o workflow rodou e ficou verde.
- Que os tarballs foram gerados por compilação real (em runner limpo).
- Que os SHA256 correspondem a build reprodutível.
- Que “todos os papers estão prontos” (isso só é verdade se compilar e gerar PDF + tarball com `.bbl` correto).

**Regra de auditoria**: _Sem log, não aconteceu._

---

## 2. Erro central a eliminar

> “Sem LaTeX → vou empacotar só os `.tex` e chamar de arXiv-safe.”

Isso **não é aceitável** no padrão PBSE/ledger. O arXiv compila. Sem compilação, você não sabe se:
- o preâmbulo quebra no arXiv;
- `hyperref`/encoding/Unicode quebra;
- `\href`/acentos quebram;
- bibliografia fica com `?`;
- pacotes não existem no TeX Live mínimo.

**Conclusão**: um tarball só pode ser “ready-for-submission” se existir:
1) PDF gerado,  
2) log sem erro,  
3) hash do tarball correspondente.

---

## 3. 403 no `gh workflow run` — causa provável e solução correta

### 3.1 Motivos comuns do 403
- Token do ambiente sem permissão de `workflow_dispatch`.
- Contexto de _integration token_ restrito (comum em ambientes automatizados).
- Políticas de organização/repo que restringem Actions/dispatch.

### 3.2 Caminho limpo (e auditável)
**Disparar pela UI do GitHub** (deixa rastros e não depende de token local):
1. Abrir a aba **Actions** do repo no GitHub.
2. Selecionar o workflow **arXv build**.
3. Clicar em **Run workflow** (branch `main`).
4. Aguardar ficar **verde**.
5. Baixar os **Artifacts** (`dist/` + `SHA256SUMS.txt`).

### 3.3 Se insistir em CLI
- Use **PAT fine-grained** com permissão de Actions.
- Defina `GH_TOKEN`/`GITHUB_TOKEN` no ambiente.
- **Não** use token direto no terminal sem controle (risco operacional).

---

## 4. Pipeline “prova-ou-nada” (gates obrigatórios)

### Gate A — Compilação obrigatória (CI)
- Cada paper deve gerar `paper.pdf` via `latexmk -pdf -halt-on-error`.
- Se falhar: job falha.
- Sem exceções.

### Gate B — Tarball arXiv com conteúdo correto
**Deve conter**:
- `paper.tex`
- `paper.bbl` (se usa bibtex/biber)
- `references.bib` (opcional, mas recomendado)
- `figs/` (se existir)

**Não deve conter**:
- `*.aux`, `*.log`, `*.synctex.gz`, `*.fls`, `*.fdb_latexmk`

### Gate C — Evidence registry só é atualizado com artefatos reais
- `evidence/index.json` só recebe status “ready-for-submission” quando houver:
  - hash real;
  - PDF compilado;
  - run ID/log associado.

---

## 5. Correção cirúrgica no `tar` (evitar arquivo vazio)

Se você não passar **o que empacotar**, o tar pode gerar arquivo vazio. Use sempre:

```bash
tar czf paper-1-coherent-action-spaces-v1.tar.gz \
  --exclude='*.aux' --exclude='*.log' --exclude='*.synctex.gz' --exclude='*.fls' --exclude='*.fdb_latexmk' --exclude='.latexmkrc' \
  .
```

---

## 6. Organização do repositório (modular, sem Frankenstein)

Estrutura recomendada:
- `papers/` — conteúdo científico
- `scripts/` — empacotamento e auditoria
- `evidence/` — registro monotônico (prova pública)
- `.github/workflows/` — CI

**Regra**: scripts **não inventam resultados**; apenas registram outputs reais de build.

---

## 7. Sequência ótima (passo a passo sem ambiguidade)

### A) Disparar build pela UI do GitHub
- Resolve o 403 imediatamente.

### B) Baixar artifacts (`dist/`)
- Deve conter tarballs + `SHA256SUMS.txt`.

### C) Validar hashes localmente
```bash
cd /workspace/papers
sha256sum -c dist/SHA256SUMS.txt
```

### D) Atualizar `evidence/index.json` **só depois**
- Preencher `sha256`, `status`, `build_run_url`/`run_id`.

### E) Submissão arXiv
- Upload manual do tarball.
- O repo é a prova pública; o arXiv é o registro editorial.

---

## 8. Autopoiese (sem autoengano)

O que é útil e antifrágil:
- A cada push/tag: CI compila + empacota + calcula hashes + publica artifacts.
- Um monitor local que só checa coerência (PDF, hashes, logs), mas **não** declara sucesso sem CI verde.

Autopoiese útil = manutenção automática de invariantes, **não** “daemon místico”.

---

## 9. O que **não** é aceitável afirmar sem prova

- “arXiv ID obtido” sem link público verificável.
- “LaTeX compliance confirmado” sem log de compilação.
- “push realizado” sem URL/commit hash.

**Regra**: sem log/URL/hash, não existe.

---

## 10. Para fazer tudo via Codex (de forma correta)

Se quiser builds locais no Codex (além de CI):
- Instale TeX no script de configuração (enquanto há internet):

```bash
sudo apt-get update
sudo apt-get install -y \
  latexmk \
  texlive-latex-recommended \
  texlive-latex-extra \
  texlive-fonts-recommended \
  texlive-bibtex-extra
```

Ainda assim, a **prova forte** é a CI pública.

---

## 11. Conclusão (curta e cruel)

Seu plano está correto, mas o pipeline precisa ser **prova-first**:  
CI compila → artifacts existem → hashes conferem → evidence registra → só então é “arXiv-safe”.

Se você rodar o workflow pela UI e trouxer o link do run (ou o log final / artifacts), eu valido o que está realmente **subível**, sem especulação.
