#!/bin/bash
# Package paper for arXiv submission
# Usage: ./package_arxiv.sh paper-1-coherent-action-spaces v1

set -e

PAPER_DIR="${1:?Erro: especifique o diretório do paper (ex: paper-1-coherent-action-spaces)}"
VERSION="${2:-v1}"
PAPER_PATH="papers/$PAPER_DIR"
OUTPUT_DIR="releases"
TIMESTAMP=$(date -u +%Y%m%d-%H%M%S)

if [ ! -d "$PAPER_PATH" ]; then
    echo "❌ Erro: diretório '$PAPER_PATH' não encontrado"
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

# Nome do arquivo
PACKAGE_NAME="${PAPER_DIR}-${VERSION}"
TARBALL="${OUTPUT_DIR}/${PACKAGE_NAME}.tar.gz"

echo "📦 Empacotando: $PACKAGE_NAME"

# Criar tarball (sem metadados desnecessários)
cd "$PAPER_PATH"
tar --exclude='.git' \
    --exclude='.DS_Store' \
    --exclude='*.log' \
    --exclude='*.aux' \
    --exclude='*.fls' \
    --exclude='*.fdb_latexmk' \
    --exclude='build' \
    --exclude='.vscode' \
    -czf "../../${TARBALL}" \
    .

cd ../..

# Calcular SHA256
SHA256=$(sha256sum "$TARBALL" | awk '{print $1}')

echo "✅ Tarball criado: $TARBALL"
echo "🔐 SHA256: $SHA256"
echo ""
echo "Metadados:"
echo "  Timestamp: $TIMESTAMP"
echo "  Tamanho: $(du -h "$TARBALL" | cut -f1)"
echo ""
echo "📋 Adicionar ao evidence/index.json:"
echo ""
cat << EOF
{
  "package": "$PACKAGE_NAME",
  "tarball": "$TARBALL",
  "sha256": "$SHA256",
  "timestamp": "$TIMESTAMP",
  "arxiv_submission_link": "https://arxiv.org/submit"
}
EOF
