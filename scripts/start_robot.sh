#!/bin/bash
MAC_ADDR="F5:4E:FD:30:F8:61"
VENV_PATH="$HOME/venvs/miniqhali_venv/bin/activate"
PYTHON_MAIN="main.py"
LLM_PROVIDER="${LLM_PROVIDER:-llama_cpp}"
LLAMA_BASE_URL="${LLAMA_BASE_URL:-http://127.0.0.1:8080/v1}"
LLAMA_HEALTH_URL="${LLAMA_BASE_URL%/v1}/health"
LLAMA_LOG_FILE="${LLAMA_LOG_FILE:-/tmp/miniqhali/llama-server.log}"
OLLAMA_MODEL="${OLLAMA_MODEL:-hf.co/LiquidAI/LFM2.5-350M-GGUF:Q4_K_M}"
TTS_BACKEND="${TTS_BACKEND:-espeak}"
PIPER_MODEL="${PIPER_MODEL:-$HOME/models/piper/es_ES-davefx-medium/es_ES-davefx-medium.onnx}"
PIPER_CONFIG="${PIPER_CONFIG:-$HOME/models/piper/es_ES-davefx-medium/es_ES-davefx-medium.onnx.json}"
ESPEAK_VOICE="${ESPEAK_VOICE:-es-la+f4}"

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

echo "🧠 Verificando LLM local..."
if [ "$LLM_PROVIDER" = "llama_cpp" ]; then
    if curl -fsS "$LLAMA_BASE_URL/models" >/dev/null 2>&1; then
        echo "✅ llama-server disponible en $LLAMA_BASE_URL"
    else
        echo "⚠️ llama-server no responde en $LLAMA_BASE_URL; iniciándolo en segundo plano..."
        mkdir -p /tmp/miniqhali
        nohup bash scripts/start_llama_server.sh >/tmp/miniqhali/llama-server.stdout.log 2>&1 &
        LLAMA_PID=$!
        echo "   PID llama-server: $LLAMA_PID"
        for _ in $(seq 1 45); do
            if curl -fsS "$LLAMA_BASE_URL/models" >/dev/null 2>&1; then
                echo "✅ llama-server disponible en $LLAMA_BASE_URL"
                break
            fi
            if ! kill -0 "$LLAMA_PID" 2>/dev/null; then
                echo "❌ llama-server terminó durante el arranque. Revisa: $LLAMA_LOG_FILE"
                break
            fi
            sleep 1
        done
        if ! curl -fsS "$LLAMA_BASE_URL/models" >/dev/null 2>&1; then
            echo "⚠️ llama-server sigue sin responder; MiniQhali intentará fallback Ollama."
        fi
    fi
fi
if command -v ollama >/dev/null 2>&1; then
    if ! ollama list | grep -Fq "$OLLAMA_MODEL"; then
        echo "⚠️ No se encontró el modelo Ollama fallback: $OLLAMA_MODEL"
        echo "   Ejecuta si lo necesitas: ollama pull $OLLAMA_MODEL"
    fi
else
    echo "⚠️ Ollama no está en PATH; no habrá fallback Ollama."
fi

echo "🗣️ Verificando TTS local..."
if ! command -v espeak-ng >/dev/null 2>&1; then
    echo "❌ Error: No se encontró espeak-ng, requerido como TTS principal."
    exit 1
fi
if ! espeak-ng -v "$ESPEAK_VOICE" -q "test" 2>/dev/null; then
    echo "⚠️ Voz eSpeak $ESPEAK_VOICE no disponible; se usará fallback desde Python."
fi
if ! command -v sox >/dev/null 2>&1; then
    echo "⚠️ sox no está en PATH; eSpeak funcionará sin posprocesado."
fi
if ! command -v piper >/dev/null 2>&1 && [ -z "$PIPER_BIN" ]; then
    echo "⚠️ No se encontró piper en PATH; no habrá fallback Piper."
fi
if [ ! -f "$PIPER_MODEL" ] || [ ! -f "$PIPER_CONFIG" ]; then
    echo "⚠️ No se encontró el modelo Piper completo; fallback Piper no estará disponible."
fi

# Lanzar Python
python3 "$PYTHON_MAIN"
