#!/bin/bash
# Build paper PDF from TeX source
# Usage: ./build_paper.sh paper-1-coherent-action-spaces

set -e

PAPER_DIR="${1:?Erro: especifique o diretório do paper (ex: paper-1-coherent-action-spaces)}"
PAPER_PATH="papers/$PAPER_DIR"

if [ ! -d "$PAPER_PATH" ]; then
    echo "❌ Erro: diretório '$PAPER_PATH' não encontrado"
    exit 1
fi

if [ ! -f "$PAPER_PATH/paper.tex" ]; then
    echo "❌ Erro: '$PAPER_PATH/paper.tex' não encontrado"
    exit 1
fi

cd "$PAPER_PATH"

echo "🔨 Compilando: $PAPER_DIR"

# Verificar se latexmk está disponível
if ! command -v latexmk &> /dev/null; then
    echo "❌ latexmk não instalado. Execute: apt-get install -y latexmk texlive-full"
    exit 1
fi

# Compilar com latexmk
latexmk -pdf -interaction=nonstopmode paper.tex

# Verificar saída
if [ -f "paper.pdf" ]; then
    echo "✅ PDF gerado: paper.pdf"
    echo "📊 Tamanho: $(du -h paper.pdf | cut -f1)"
else
    echo "❌ Erro: falha na compilação"
    exit 1
fi

cd ../..
