#!/usr/bin/env bash
set -euo pipefail

TEXT="${1:-Hola, soy un asistente local corriendo en Raspberry Pi cinco. Esta es una prueba de síntesis de voz en español.}"
REPEAT="${2:-10}"
VOICE="${VOICE:-es}"
SPEED="${SPEED:-170}"
CHARS=${#TEXT}

mkdir -p "$HOME/bench_tts/results"

echo "Voice: $VOICE"
echo "Speed: $SPEED"
echo "Repeat: $REPEAT"
echo "Text chars: $CHARS"

TOTAL=0
LAST_WAV="$HOME/bench_tts/results/espeak_last.wav"

espeak-ng -v "$VOICE" -s "$SPEED" -w /tmp/espeak_warmup.wav "$TEXT" >/dev/null 2>&1

for i in $(seq 1 "$REPEAT"); do
  OUT="$HOME/bench_tts/results/espeak_${i}.wav"
  START=$(date +%s.%N)
  espeak-ng -v "$VOICE" -s "$SPEED" -w "$OUT" "$TEXT"
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
