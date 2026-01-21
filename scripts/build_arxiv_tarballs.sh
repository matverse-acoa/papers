#!/bin/bash
# Build all papers for arXiv (compile + package)
# Usage: ./build_arxiv_tarballs.sh

set -e

PAPERS=(
    "paper-0-foundations"
    "paper-1-coherent-action-spaces"
    "paper-2-acoa"
    "paper-3-omega-gate"
)

DIST_DIR="dist"
mkdir -p "$DIST_DIR"

echo "🚀 Building arXiv tarballs for all papers"
echo ""

# Verificar LaTeX disponível
if ! command -v pdflatex &> /dev/null; then
    echo "⚠️  LaTeX não encontrado. Ignorando compilação."
    echo "   (Tarballs serão criados apenas com fontes TeX)"
fi

# Array para armazenar hashes
declare -a HASHES

for i in "${!PAPERS[@]}"; do
    PAPER_DIR="${PAPERS[$i]}"
    PAPER_PATH="papers/$PAPER_DIR"
    
    if [ ! -d "$PAPER_PATH" ]; then
        echo "⚠️  Pulando: $PAPER_PATH não encontrado"
        continue
    fi
    
    echo "📦 Processando: $PAPER_DIR"
    
    # Se LaTeX disponível, compilar
    if command -v pdflatex &> /dev/null && [ -f "$PAPER_PATH/paper.tex" ]; then
        cd "$PAPER_PATH"
        echo "   Compilando TeX..."
        pdflatex -interaction=nonstopmode paper.tex > /dev/null 2>&1 || true
        cd ../../..
    fi
    
    # Criar tarball arXiv-safe
    PACKAGE_NAME="$PAPER_DIR-v1"
    TARBALL="$DIST_DIR/$PACKAGE_NAME.tar.gz"
    
    cd "$PAPER_PATH"
    tar --exclude='.git' \
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
        -czf "../../$TARBALL" \
        paper.tex *.bib 2>/dev/null || true
    
    cd ../../..
    
    # Calcular SHA256
    if [ -f "$TARBALL" ]; then
        SHA256=$(sha256sum "$TARBALL" | awk '{print $1}')
        SIZE=$(du -h "$TARBALL" | cut -f1)
        HASHES+=("$SHA256  $PACKAGE_NAME.tar.gz")
        echo "   ✅ Criado: $TARBALL ($SIZE)"
        echo "   🔐 SHA256: $SHA256"
    else
        echo "   ❌ Erro ao criar tarball"
    fi
    echo ""
done

# Gerar SHA256SUMS.txt
echo "📋 Gerando SHA256SUMS.txt"
{
    printf "%s\n" "${HASHES[@]}"
} > "$DIST_DIR/SHA256SUMS.txt"

echo ""
echo "✅ Tarballs gerados em $DIST_DIR/"
echo ""
cat "$DIST_DIR/SHA256SUMS.txt"
echo ""
echo "📌 Próximo passo:"
echo "   1. Revisar os tarballs em dist/"
echo "   2. Copiar hashes do SHA256SUMS.txt para evidence/index.json"
echo "   3. Fazer git commit + push"
echo "   4. Upload dos tarballs no arXiv"
