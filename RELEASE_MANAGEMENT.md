# Gerenciamento de Versões (Releases)

Este repositório inclui um fluxo simples para versionamento de entregas do MatVerse.

## Pré-requisitos

- GitHub CLI autenticado (`gh auth status`)
- Tag semântica (ex.: `v11.0.0`)

## Criar release

```bash
scripts/manage_release.sh v11.0.0 "MatVerse v11.0.0"
```

Com notas customizadas:

```bash
scripts/manage_release.sh v11.0.0 "MatVerse v11.0.0" docs/release_notes/v11.0.0.md
```

## Boas práticas

- Criar primeiro como draft no GitHub quando houver ativos binários.
- Publicar após anexar certificado/artefatos da pipeline fortificada.
- Referenciar hashes de evidência (OHASH/Merkle) nas notas da release.
