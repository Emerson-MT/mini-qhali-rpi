#!/bin/bash
MAC_ADDR="F5:4E:FD:30:F8:61"
VENV_PATH="$HOME/venvs/miniqhali_venv/bin/activate"
PYTHON_MAIN="main.py"
OLLAMA_MODEL="${OLLAMA_MODEL:-hf.co/LiquidAI/LFM2.5-350M-GGUF:Q4_K_M}"
TTS_BACKEND="${TTS_BACKEND:-piper}"
PIPER_MODEL="${PIPER_MODEL:-$HOME/models/piper/es_ES-davefx-medium/es_ES-davefx-medium.onnx}"
PIPER_CONFIG="${PIPER_CONFIG:-$HOME/models/piper/es_ES-davefx-medium/es_ES-davefx-medium.onnx.json}"

if [ -f "$VENV_PATH" ]; then
    source "$VENV_PATH"
else
    echo "❌ Error: Venv no encontrado."
    exit 1
fi

echo "🔗 Conectando al parlante Tronsmart..."
bluetoothctl power on
sleep 1
bluetoothctl connect $MAC_ADDR
sleep 5

# Redirigir audio a Bluetooth
BLUEZ_SINK=$(pactl list short sinks | grep "bluez" | cut -f2)
if [ ! -z "$BLUEZ_SINK" ]; then
    pactl set-default-sink "$BLUEZ_SINK"
    pactl set-sink-mute "$BLUEZ_SINK" 0
    pactl set-sink-volume "$BLUEZ_SINK" 85%
    echo "🔊 Audio redirigido a Bluetooth."
fi
pactl set-sink-mute @DEFAULT_SINK@ 0
pactl set-sink-volume @DEFAULT_SINK@ 85%
pactl get-sink-volume @DEFAULT_SINK@

echo "🧠 Verificando Ollama local..."
if ! command -v ollama >/dev/null 2>&1; then
    echo "❌ Error: No se encontró ollama en PATH."
    exit 1
fi
if ! ollama list | grep -Fq "$OLLAMA_MODEL"; then
    echo "❌ Error: No se encontró el modelo Ollama: $OLLAMA_MODEL"
    echo "   Ejecuta: ollama pull $OLLAMA_MODEL"
    exit 1
fi

echo "🗣️ Verificando TTS local..."
if [ "$TTS_BACKEND" = "piper" ]; then
    if ! command -v piper >/dev/null 2>&1 && [ -z "$PIPER_BIN" ]; then
        echo "⚠️ No se encontró piper en PATH; el robot intentará fallback eSpeak-NG."
    fi
    if [ ! -f "$PIPER_MODEL" ] || [ ! -f "$PIPER_CONFIG" ]; then
        echo "⚠️ No se encontró el modelo Piper completo; el robot intentará fallback eSpeak-NG."
    fi
fi
if ! command -v espeak-ng >/dev/null 2>&1; then
    echo "❌ Error: No se encontró espeak-ng, requerido como fallback TTS."
    exit 1
fi

# Lanzar Python
python3 "$PYTHON_MAIN"
