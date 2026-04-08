#!/bin/bash

# --- CONFIGURACIÓN ---
# La MAC del Tronsmart sigue siendo la misma (F5:4E:FD:30:F8:61)
MAC_ADDR="F5:4E:FD:30:F8:61"
PYTHON_MAIN="main.py" 
VENV_PATH="$HOME/venvs/miniqhali_venv/bin/activate"

echo "---------------------------------------"
echo "🤖 Iniciando sistema de audio MiniQhali"
echo "---------------------------------------"

# 1. Limpieza y Reintento de Bluetooth
echo "🔄 Preparando adaptador Bluetooth..."
# Intentar desconectar por si quedó una sesión colgada
bluetoothctl disconnect $MAC_ADDR > /dev/null 2>&1
sleep 1
bluetoothctl power off
sleep 1
bluetoothctl power on
sleep 2

# 2. Conexión al parlante
echo "🔗 Conectando al Tronsmart T7 Mini..."
# 'trust' es vital para que se reconecte solo en el futuro
bluetoothctl trust $MAC_ADDR > /dev/null 2>&1
bluetoothctl connect $MAC_ADDR

# Esperamos un poco más para que PulseAudio/Pipewire reconozca el dispositivo
sleep 5

# 3. Verificación y Ajuste de Audio
if bluetoothctl info $MAC_ADDR | grep -q "Connected: yes"; then
    echo "✅ Conexión establecida con éxito."
    
    # Intentar forzar el Sink de audio al Bluetooth
    # Esto evita que el sonido salga por el Jack o HDMI de la Raspberry
    BLUEZ_SINK=$(pactl list short sinks | grep "bluez" | cut -f2)
    if [ ! -z "$BLUEZ_SINK" ]; then
        pactl set-default-sink "$BLUEZ_SINK"
        echo "🔊 Salida de audio redirigida al parlante BT."
    fi

    # Volumen al 80% (ajustar si la voz de Dalia suena muy fuerte)
    pactl set-sink-volume @DEFAULT_SINK@ 80%
    
    # 4. Ejecución del Robot
    if [ -f "$VENV_PATH" ]; then
        echo "🐍 Activando entorno: miniqhali_venv"
        source "$VENV_PATH"
        
        echo "🚀 Lanzando MiniQhali..."
        # Ejecutamos con python3 para asegurar el uso del venv
        python3 "$PYTHON_MAIN"
    else
        echo "❌ Error: No se encontró el venv en $VENV_PATH"
    fi
else
    echo "❌ Error: No se pudo conectar al parlante."
    echo "💡 Tip: Verifica que el parlante esté en modo emparejamiento o no esté unido a tu móvil."
fi
