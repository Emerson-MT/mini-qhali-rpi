#!/bin/bash

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

VENV_PATH="$HOME/venvs/miniqhali_venv/bin/activate"
SERVER_PATH="src/web_interface/server.py"

# --- 1. FUNCIÓN DE LIMPIEZA ROBUSTA ---
cleanup() {
    echo -e "\n🛑 Deteniendo ecosistema MiniQhali..."
    
    # Matar el grupo de procesos para no dejar hijos huérfanos
    if [ ! -z "$SERVER_PID" ]; then
        kill -TERM $SERVER_PID 2>/dev/null
    fi
    
    # Limpieza forzosa de procesos por nombre
    pkill -f "$SERVER_PATH"
    pkill -f "main.py"
    
    # LIBERACIÓN DE PUERTO (El salvavidas de la Raspberry Pi)
    # Mata cualquier proceso que siga usando el puerto 3000
    fuser -k 3000/tcp 2>/dev/null
    
    echo "✅ Ecosistema cerrado correctamente."
    exit
}

# Trap al inicio (captura Ctrl+C, cierre de terminal y errores)
trap cleanup SIGINT SIGTERM EXIT

echo "------------------------------------------------"
echo "🤖 INICIANDO ECOSISTEMA MINIQHALI"
echo "------------------------------------------------"

# --- 2. LIMPIEZA PREVENTIVA ---
# Nos aseguramos de que el puerto esté libre antes de empezar
fuser -k 3000/tcp 2>/dev/null

# --- 3. INICIAR BACKEND ---
if [ -f "$VENV_PATH" ]; then
    source "$VENV_PATH"
else
    echo "❌ Error: No se encontró el venv en $VENV_PATH"
    exit 1
fi

# Ejecutamos con 'unbuffered' para que los logs salgan en tiempo real
python3 -u "$SERVER_PATH" > server.log 2>&1 &
SERVER_PID=$!
echo "🌐 1/3 Servidor Flask en PID: $SERVER_PID"

sleep 5

# --- 4. INICIAR INTERFAZ ---
echo "🖥️ 2/3 Lanzando Interfaz Visual..."
# Usamos & para que no bloquee la ejecución
bash scripts/start_face.sh & 

# --- 5. INICIAR LÓGICA Y AUDIO ---
echo "🎙️ 3/3 Iniciando Audio y Cerebro..."
# Al ser el último proceso, NO usamos &, así el script se queda "viviendo" aquí
# y cualquier Ctrl+C activará el trap de arriba.
bash scripts/start_robot.sh