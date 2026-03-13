#!/bin/bash
# start.sh — Limpa cache e inicia a aplicação Streamlit

echo "🧹 Limpando cache..."

# Apaga __pycache__ em todo o projeto
find . -type d -name "__pycache__" -not -path "./venv/*" -exec rm -rf {} + 2>/dev/null

# Apaga cache do Streamlit
rm -rf ~/.streamlit/cache 2>/dev/null

echo "✅ Cache limpo."
echo ""
echo "🚀 Iniciando Streamlit..."

# Ativa o ambiente virtual e roda o app
source venv/Scripts/activate
streamlit run app.py --server.port 8510
