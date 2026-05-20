#!/bin/bash
MAC_ADDR="F5:4E:FD:5C:CF:12"
VENV_PATH="$HOME/venvs/miniqhali_venv/bin/activate"
PYTHON_MAIN="main.py"

echo "🔗 Conectando al parlante Tronsmart..."
bluetoothctl power on
sleep 1
bluetoothctl connect $MAC_ADDR
sleep 5

# Redirigir audio a Bluetooth
BLUEZ_SINK=$(pactl list short sinks | grep "bluez" | cut -f2)
if [ ! -z "$BLUEZ_SINK" ]; then
    pactl set-default-sink "$BLUEZ_SINK"
    echo "🔊 Audio redirigido a Bluetooth."
fi
pactl set-sink-volume @DEFAULT_SINK@ 85%

# Lanzar Python
if [ -f "$VENV_PATH" ]; then
    source "$VENV_PATH"
    python3 "$PYTHON_MAIN"
else
    echo "❌ Error: Venv no encontrado."
fi
