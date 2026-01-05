#!/bin/bash
# Script para ejecutar la aplicación

echo "🚗 Iniciando Paseos - App de Gastos Compartidos..."
echo ""

# Verificar si existe el archivo de secrets
if [ ! -f ".streamlit/secrets.toml" ]; then
    echo "⚠️  Advertencia: No se encontró .streamlit/secrets.toml"
    echo "   Asegúrate de configurar tu API key de OpenAI"
fi

# Crear carpeta de uploads si no existe
mkdir -p uploads

# Ejecutar Streamlit
streamlit run app.py

