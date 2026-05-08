#!/usr/bin/env bash
set -euo pipefail

TEXT="${1:-Hola, soy un asistente local corriendo con Piper en Raspberry Pi cinco. Esta es una prueba de síntesis de voz en español.}"
REPEAT="${2:-5}"
CHARS=${#TEXT}

MODEL="${MODEL:-$HOME/models/piper/es_ES-davefx-medium/es_ES-davefx-medium.onnx}"
CONFIG="${CONFIG:-$HOME/models/piper/es_ES-davefx-medium/es_ES-davefx-medium.onnx.json}"

if command -v piper >/dev/null 2>&1; then
  PIPER_BIN="${PIPER_BIN:-$(command -v piper)}"
else
  PIPER_BIN="${PIPER_BIN:-$(find "$HOME/apps/piper" -type f -name "piper" -perm -111 | head -n 1)}"
fi

if [[ ! -x "$PIPER_BIN" ]]; then
  echo "No encuentro binario piper. Activa el venv o define PIPER_BIN." >&2
  exit 1
fi

if [[ ! -f "$MODEL" ]]; then
  echo "No existe modelo: $MODEL" >&2
  exit 1
fi

if [[ ! -f "$CONFIG" ]]; then
  echo "No existe config: $CONFIG" >&2
  exit 1
fi

mkdir -p "$HOME/bench_tts/results"

echo "Piper: $PIPER_BIN"
echo "Modelo: $MODEL"
echo "Config: $CONFIG"
echo "Repeat: $REPEAT"
echo "Text chars: $CHARS"

TOTAL=0
LAST_WAV="$HOME/bench_tts/results/piper_last.wav"

echo "$TEXT" | "$PIPER_BIN" --model "$MODEL" --config "$CONFIG" --output_file /tmp/piper_warmup.wav >/dev/null 2>&1

for i in $(seq 1 "$REPEAT"); do
  OUT="$HOME/bench_tts/results/piper_${i}.wav"
  START=$(date +%s.%N)
  echo "$TEXT" | "$PIPER_BIN" --model "$MODEL" --config "$CONFIG" --output_file "$OUT"
  END=$(date +%s.%N)

  ELAPSED=$(python3 - <<PY
print($END - $START)
PY
)
  TOTAL=$(python3 - <<PY
print($TOTAL + $ELAPSED)
PY
)
  cp "$OUT" "$LAST_WAV"

  DUR=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$OUT")
  RTF=$(python3 - <<PY
print($ELAPSED / $DUR)
PY
)
  CPS=$(python3 - <<PY
print($CHARS / $ELAPSED)
PY
)
  echo "run=$i elapsed=${ELAPSED}s audio_s=${DUR}s RTF_TTS=${RTF} chars_per_s=${CPS}"
done

MEAN=$(python3 - <<PY
print($TOTAL / $REPEAT)
PY
)

DUR_LAST=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$LAST_WAV")

RTF_MEAN=$(python3 - <<PY
print($MEAN / $DUR_LAST)
PY
)

CPS_MEAN=$(python3 - <<PY
print($CHARS / $MEAN)
PY
)

echo
echo "=== Resultado ==="
echo "mean_elapsed_s=$MEAN"
echo "last_audio_s=$DUR_LAST"
echo "RTF_TTS_mean=$RTF_MEAN"
echo "chars_per_s_mean=$CPS_MEAN"
echo "last_wav=$LAST_WAV"
