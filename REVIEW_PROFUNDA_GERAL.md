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

## 9. Sistema inteligente, eficaz e antifrágil (o que falta para ficar real)

### 9.1 Loop de feedback fechado (autopoiese real)
Um sistema autopoietico não “se declara pronto”; ele **se autocorrige** com base em sinais reais:
- **Sensor**: resultados do CI (logs + artifacts + hashes).
- **Memória**: `evidence/index.json` com links rastreáveis (run URL / IDs).
- **Ação**: scripts que atualizam o registry **só** quando há prova.
- **Regra dura**: se qualquer gate falha, o estado não avança.

### 9.2 Invariantes obrigatórios (antifragilidade)
Defina invariantes que **sempre** precisam permanecer verdadeiras:
- Cada tarball publicado tem hash verificável e run associado.
- Cada paper “ready” tem PDF compilado **sem erro**.
- `evidence/index.json` é monotônico (não regride status).
- Artefatos são reproduzíveis (mesma entrada → mesmo hash, quando o runner é equivalente).

### 9.3 Estratégia de “falha útil”
Antifragilidade exige que a falha gere valor:
- Quando o build falha, registre o motivo (log) e **aprenda**: crie um ticket local com causa.
- Se o runner muda (ex.: TeX Live), registre a versão do ambiente em `evidence/`.
- Se o arXiv rejeitar, capture o relatório e ajuste o pipeline (é uma prova, não um erro escondido).

---

## 10. Controles objetivos (o mínimo para ser auditável)

### 10.1 Evidências mínimas por paper
Para declarar “ready-for-submission”, cada paper precisa ter:
- `paper.pdf` gerado em CI;
- `paper.bbl` presente no tarball (se houver bibliografia);
- `SHA256SUMS.txt` contendo o hash do tarball;
- URL do run do workflow (ou run ID) associada ao hash.

Recomendação prática: registre também o **link do run** e o **nome do artifact** (ex.: “arXiv build #N”) junto do hash no `evidence/index.json`.

### 10.2 Registros que nunca devem ser “manual-only”
- Hashes (`SHA256SUMS.txt`) devem vir do build.
- Status “ready-for-submission” deve vir de gate automático.
- Logs de compilação devem ser preservados como artifacts.

---

## 11. Plano direto (sem rodeios)

1. Abra: `https://github.com/matverse-acoa/papers/actions/workflows/arxiv-build.yml`  
   ► **Run workflow** → branch `main` → **Run**.

2. Aguarde o run completar e confirme **status** e **commit** (o run deve corresponder ao commit que gerou o artifact).  
   - Se **vermelho**, abra o log final e corrija a causa antes de repetir.  
   - Se **verde**, continue.

3. Baixe o artifact `dist.zip` do run concluído e **descompacte** em pasta limpa.

4. Valide os hashes:
```bash
sha256sum -c SHA256SUMS.txt
```
Saída deve ser tudo **OK**.

5. Submeta os tarballs ao arXiv (um por vez, `cs.AI`).  
   Use os metadatas exatos já definidos (título, abstract, comments).

6. Quando cada ID sair (`arxiv.org/abs/2406.xxxxx`), cole aqui.  
   Atualizo `evidence/index.json` **ou fecho o ledger final de submissão**.

7. Registre no `evidence/index.json` o **link do run**, o **nome do artifact** e o **hash** correspondente.

8. (Opcional, recomendado) Se for versionar um lote pronto, crie **tag assinada** após CI verde:
```bash
git tag -s v1.0.0
git tag -v v1.0.0
```

9. Execute o monitor autopoietico local para validar integridade e dependências:
```bash
python3 scripts/autopoietic_monitor.py
```

Qualquer erro no CI, envie o link do run que eu debugo em < 1 min.

Isso transforma o repositório em um **sistema inteligente, eficaz, autopoietico e antifrágil real**, porque:
- só avança com prova;
- registra a origem dos fatos;
- melhora com falhas documentadas;
- evita autoengano.

---

## 12. Submissões arXiv (estado e correção imediata)

Se houver uma submissão **incompleta** no painel do arXiv (ex.: `submit/6985500`), trate como **estado pendente**:
- **Não** declare “submitted” até que o upload finalize e o arXiv gere o ID público (`arxiv.org/abs/…`).
- Complete o upload com **source TeX** e todos os arquivos requeridos (evite PDF-only). O arXiv **requer TeX quando possível** e pode recusar PDFs gerados a partir de TeX se o source não for enviado.  
  Referência: https://arxiv.org/help/submit_tex
- Depois de concluir, copie o ID público e registre no `evidence/index.json`.

Checklist de saneamento antes de finalizar:
- Todas as referências resolvidas (sem `?` no PDF).
- `paper.bbl` presente no tarball, se houver bibliografia.
- Tarball sem arquivos auxiliares (`*.aux`, `*.log`, `*.synctex.gz`, etc.).

---

## 13. O que **não** é aceitável afirmar sem prova

- “arXiv ID obtido” sem link público verificável.
- “LaTeX compliance confirmado” sem log de compilação.
- “push realizado” sem URL/commit hash.

**Regra**: sem log/URL/hash, não existe.

---

## 14. Referências úteis (submissão e TeX)

- Guia arXiv sobre envio de TeX: https://arxiv.org/help/submit_tex
- Exemplos e repositórios em TeX (GitHub Search): https://github.com/search?q=LaTeX+language%3ATeX&type=repositories&l=TeX

---

## 15. Para fazer tudo via Codex (de forma correta)

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

## 16. Conclusão (curta e cruel)

Seu plano está correto, mas o pipeline precisa ser **prova-first**:  
CI compila → artifacts existem → hashes conferem → evidence registra → só então é “arXiv-safe”.

Se você rodar o workflow pela UI e trouxer o link do run (ou o log final / artifacts), eu valido o que está realmente **subível**, sem especulação.

**Regra operacional**: qualquer declaração de prontidão, conformidade ou submissão é **inválida** se não estiver vinculada a um run de CI bem-sucedido com logs e artifacts anexos.

**Fonte da verdade**: texto **não** valida estado. Logs + artifacts validam estado. Sem logs/artifacts, o estado é **desconhecido**.
