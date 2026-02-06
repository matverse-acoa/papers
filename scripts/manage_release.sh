#!/usr/bin/env bash
set -euo pipefail

TAG="${1:-}"
TITLE="${2:-}"
NOTES_FILE="${3:-}"

if [[ -z "$TAG" ]]; then
  echo "Uso: scripts/manage_release.sh <tag> [titulo] [arquivo_notas]"
  exit 1
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI (gh) não encontrado. Instale para gerenciar releases."
  exit 2
fi

if [[ -n "$NOTES_FILE" && -f "$NOTES_FILE" ]]; then
  gh release create "$TAG" --title "${TITLE:-$TAG}" --notes-file "$NOTES_FILE"
else
  gh release create "$TAG" --title "${TITLE:-$TAG}" --generate-notes
fi

echo "✅ Release criada: $TAG"
