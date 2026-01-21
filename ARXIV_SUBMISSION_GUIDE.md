# MatVerse arXiv Submission Instructions

All 4 papers are ready for submission to arXiv. Follow these steps:

## 📋 Papers Ready for Submission

| # | Paper | SHA-256 | Size | Status |
|---|-------|---------|------|--------|
| 0 | Foundations of Coherent Action Spaces | `197a26ff...` | 4.0K | Ready |
| 1 | Coherent Action Spaces (Tensorial Model) | `b8d43b81...` | 4.0K | Ready |
| 2 | ACOA: Autopoiesis Without Control | `2fa5e4ec...` | 4.0K | Ready |
| 3 | Ω-GATE Kernel: Reference Implementation | `92c230d0...` | 4.0K | Ready |

## ✅ Pre-flight Checklist

- [x] All papers compiled and packaged
- [x] SHA-256 hashes calculated and logged
- [x] Evidence registry updated
- [x] Tarballs contain only `.tex`, `.bib`, `.bbl`
- [x] Metadata in evidence/index.json
- [x] arXiv account verified (Mateus Arêas, Independent Researcher)
- [x] ORCID linked: https://orcid.org/0009-0008-2973-4047

## 📤 How to Submit to arXiv

### For each paper (in order: 0 → 1 → 2 → 3):

1. Go to https://arxiv.org/submit
2. Log in with your arXiv account (MATVERSE)
3. Click "Start New Submission"
4. Select category: **cs.AI** (primary)
5. Upload tarball from `dist/`:
   - `dist/paper-0-foundations-v1.tar.gz` (for Paper 0)
   - etc.
6. Fill metadata:
   - **Title**: Copy from \title{} in paper.tex
   - **Authors**: Mateus Alves Arêas
   - **Abstract**: Copy from \begin{abstract}
   - **Comments**: 
     - Paper 0: "Foundational work defining Ψ, CVaR, and admissibility"
     - Paper 1: "Extends arXiv:XXXX with tensorial invariant model"
     - Paper 2: "Extends arXiv:XXXX and arXiv:YYYY with ACOA framework"
     - Paper 3: "Extends arXiv:XXXX, YYYY, ZZZZ with Ω-GATE kernel"
7. Review PDF preview
8. Submit

## 🔐 Evidence & Auditability

All builds are reproducible:

```bash
cd /workspaces/papers
./build_tarballs.sh
# Generates identical SHA-256 hashes
```

## 📊 arXiv IDs (to fill in after submission)

| Paper | arXiv ID | Status |
|-------|----------|--------|
| 0 | ` ` | Pending |
| 1 | ` ` (cites: 0) | Pending |
| 2 | ` ` (cites: 0, 1) | Pending |
| 3 | ` ` (cites: 0, 1, 2) | Pending |

After getting real arXiv IDs, update `evidence/index.json` and push.

## 🤖 CI/CD Automation

Each time you `git push`:
1. GitHub Actions compiles papers
2. Generates tarballs
3. Calculates SHA-256
4. Updates evidence/index.json
5. Creates GitHub Release (optional)

## 📝 References

- MatVerse GitHub: https://github.com/matverse-acoa/papers
- ORCID: https://orcid.org/0009-0008-2973-4047
- arXiv Account: https://arxiv.org (login: MATVERSE)
