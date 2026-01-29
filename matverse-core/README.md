# MatVerse Core - Infraestrutura Científica Soberana

## Visão Geral
MatVerse é uma infraestrutura científica soberana que integra governança matemática verificável, identidade criptográfica, economia descentralizada e publicação autônoma.

## Arquitetura
- **Governança**: Ω-GATE com métricas Ψ, Θ, CVaR
- **Identidade**: OHASH + ORCID + DNA criptográfico
- **Segurança**: CERBEROS + BTC2 + PQC (Dilithium/Kyber)
- **Economia**: Paper-SBT + Captals + Research Credits
- **Publicação**: Zenodo/ArXiv + Crossref + DOI automático
- **Cientometria**: PageRank científico + h-index + impacto
- **Pipeline**: Autônomo end-to-end

## Instalação
```bash
git clone https://github.com/matverse-acoa/matverse-core
cd matverse-core
pip install -r requirements.txt
cp .env.example .env
# Configure seu .env com tokens
python scripts/setup.py
```

## Uso Rápido
```python
from core.governance.omega_gate import OmegaGate
from core.identity.ohash import generate_ohash
from pipelines.autonomous_pipeline import run_pipeline

# Gerar identidade científica
orcid = "0009-0008-2973-4047"
paper_hash = "abc123..."
ohash, payload = generate_ohash(orcid, paper_hash)

# Executar pipeline
result = run_pipeline(
    orcid=orcid,
    paper_content="Conteúdo do paper...",
    title="Paper Title"
)
```

## Módulos Principais
1. **Ω-GATE**: Filtro matemático de decisão científica
2. **OHASH**: DNA criptográfico de autoria
3. **CERBEROS**: Antifraude contextual
4. **Paper-SBT**: NFTs científicos soulbound
5. **Scientometrics**: Impacto e ranking
6. **Pipeline Autônomo**: Commit → Publish → DOI

## Roadmap
- Fase 1: MVP com Zenodo + ORCID
- Fase 2: Economia Captals + Paper-SBT
- Fase 3: Rede Sci-Net distribuída
- Fase 4: Governança global Ω-Council

## Contribuição
Veja [CONTRIBUTING.md](docs/CONTRIBUTING.md) para guidelines.

## Licença
CC-BY-4.0
