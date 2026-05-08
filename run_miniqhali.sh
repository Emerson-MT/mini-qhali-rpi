#!/bin/bash

# --- 1. CONFIGURACIÓN DE RUTAS DINÁMICAS ---
# Esta línea detecta dónde está el script y entra a esa carpeta
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Definimos las rutas relativas a la raíz del proyecto
VENV_PATH="$HOME/venvs/miniqhali_venv/bin/activate"
SERVER_PATH="src/web_interface/server.py"

echo "------------------------------------------------"
echo "🤖 INICIANDO ECOSISTEMA MINIQHALI"
echo "📍 Directorio: $PROJECT_DIR"
echo "------------------------------------------------"

# --- 2. INICIAR BACKEND (SERVER) ---
echo "🌐 1/3 Lanzando Servidor Flask..."
if [ -f "$VENV_PATH" ]; then
    source "$VENV_PATH"
else
    echo "❌ Error: No se encontró el venv en $VENV_PATH"
    exit 1
fi

# Ejecutamos el servidor en segundo plano
python3 "$SERVER_PATH" > server.log 2>&1 &
SERVER_PID=$!

# Espera crucial para que el puerto 3000 esté listo antes de abrir la cara
echo "⏳ Esperando a que el servidor levante..."
sleep 5

# --- 3. INICIAR INTERFAZ (CARA) ---
echo "🖥️ 2/3 Lanzando Interfaz Visual..."
bash scripts/start_face.sh

# --- 4. INICIAR LÓGICA Y AUDIO (CEREBRO) ---
echo "🎙️ 3/3 Iniciando Audio y Cerebro..."
# Este script bloquea la terminal; cuando lo cierres con Ctrl+C, seguirá el trap
bash scripts/start_robot.sh

# --- 5. LIMPIEZA AL SALIR ---
# Si cierras el proceso principal, matamos el servidor Flask para liberar el puerto
trap "echo '🛑 Deteniendo servidor...'; kill $SERVER_PID" EXIT
