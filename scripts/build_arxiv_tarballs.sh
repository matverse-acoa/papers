#!/bin/bash
# Build all papers for arXiv (compile + package)
# Usage: ./build_arxiv_tarballs.sh

set -euxo pipefail

ROOT_DIR="$(pwd)"

PAPERS=(
    "paper-0-foundations"
    "paper-1-coherent-action-spaces"
    "paper-2-acoa"
    "paper-3-omega-gate"
)

DIST_DIR="$ROOT_DIR/dist"
mkdir -p "$DIST_DIR"

echo "🚀 Building arXiv tarballs for all papers"
echo ""

# Verificar LaTeX disponível
if ! command -v pdflatex &> /dev/null; then
    echo "⚠️  LaTeX não encontrado."
    if [ "${ALLOW_SOURCE_ONLY:-}" = "1" ]; then
        echo "   ALLOW_SOURCE_ONLY=1 set: criando tarballs apenas com fontes (não verificados)"
    else
        echo "   Para permitir tarballs apenas com fontes exporte: ALLOW_SOURCE_ONLY=1"
        echo "   Abortando para evitar artefatos não verificados."
        exit 2
    fi
fi

# Array para armazenar hashes
declare -a HASHES

for i in "${!PAPERS[@]}"; do
    PAPER_DIR="${PAPERS[$i]}"
    PAPER_PATH="$ROOT_DIR/papers/$PAPER_DIR"
    
    if [ ! -d "$PAPER_PATH" ]; then
        echo "⚠️  Pulando: $PAPER_PATH não encontrado"
        continue
    fi
    
    echo "📦 Processando: $PAPER_DIR"
    
    # Se LaTeX disponível, compilar (falhar se compilação falhar)
    if command -v pdflatex &> /dev/null && [ -f "$PAPER_PATH/paper.tex" ]; then
        pushd "$PAPER_PATH" > /dev/null
        echo "   Compilando TeX (preferindo latexmk)..."
        echo "========== CONTEXT =========="
        pwd
        ls -la
        echo "============================="
        latexmk -C || true

        if command -v latexmk &> /dev/null; then
            if ! latexmk -pdf -file-line-error -interaction=nonstopmode paper.tex; then
                echo ""
                echo "=========== LATEX FAILURE ==========="
                echo ""

                if [ -f paper.log ]; then
                    echo "------ FIRST 120 LINES ------"
                    head -120 paper.log
                    echo ""

                    echo "------ ERROR LINES ------"
                    grep -n "!" paper.log | head -20 || true
                else
                    echo "paper.log not found"
                fi

                exit 1
            fi
        else
            pdflatex -interaction=nonstopmode paper.tex
            # tentar BibTeX se houver .aux/bib
            if [ -f "paper.aux" ]; then
                bibtex paper || true
            fi
            pdflatex -interaction=nonstopmode paper.tex
            pdflatex -interaction=nonstopmode paper.tex
        fi

        if [ ! -f "paper.pdf" ]; then
            echo "   ❌ Compilação falhou para $PAPER_DIR"
            exit 1
        fi
        popd > /dev/null
    fi
    
    # Criar tarball arXiv-safe
    PACKAGE_NAME="$PAPER_DIR-v1"
    TARBALL="$DIST_DIR/$PACKAGE_NAME.tar.gz"
    
    echo "   Empacotando arquivos fonte (excluindo artefatos)..."
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
        -czf "$TARBALL" \
        -C "$PAPER_PATH" .
    
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
