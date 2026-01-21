#!/bin/bash
set -e

PAPERS=(
    "paper-0-foundations"
    "paper-1-coherent-action-spaces"
    "paper-2-acoa"
    "paper-3-omega-gate"
)

DIST_DIR="/workspaces/papers/dist"
mkdir -p "$DIST_DIR"

echo "🚀 Gerando tarballs arXiv-safe..."
echo ""

declare -a HASHES

for PAPER_DIR in "${PAPERS[@]}"; do
    PAPER_PATH="/workspaces/papers/papers/$PAPER_DIR"
    
    if [ ! -d "$PAPER_PATH" ]; then
        echo "⚠️  Pulando: $PAPER_PATH não encontrado"
        continue
    fi
    
    echo "📦 Empacotando: $PAPER_DIR"
    
    PACKAGE_NAME="$PAPER_DIR-v1"
    TARBALL="$DIST_DIR/$PACKAGE_NAME.tar.gz"
    
    cd "$PAPER_PATH"
    tar czf "$TARBALL" \
        --exclude='.git' \
        --exclude='.DS_Store' \
        --exclude='*.log' \
        --exclude='*.aux' \
        --exclude='*.fls' \
        --exclude='*.fdb_latexmk' \
        --exclude='*.out' \
        --exclude='*.toc' \
        --exclude='build' \
        --exclude='.vscode' \
        --exclude='__pycache__' \
        .
    
    SHA256=$(sha256sum "$TARBALL" | awk '{print $1}')
    SIZE=$(du -h "$TARBALL" | cut -f1)
    
    HASHES+=("$SHA256  $PACKAGE_NAME.tar.gz")
    
    echo "   ✅ Criado: $TARBALL ($SIZE)"
    echo "   🔐 SHA256: $SHA256"
    echo ""
done

echo "📋 Gerando SHA256SUMS.txt"
{
    printf "%s\n" "${HASHES[@]}"
} > "$DIST_DIR/SHA256SUMS.txt"

echo ""
echo "✅ Tarballs gerados em $DIST_DIR/"
echo ""
cat "$DIST_DIR/SHA256SUMS.txt"
echo ""
echo "📌 Próximos passos:"
echo "   1. Revisar tarballs em dist/"
echo "   2. Atualizar evidence/index.json com hashes"
echo "   3. Git push para GitHub"
echo "   4. Upload dos tarballs no arXiv"
