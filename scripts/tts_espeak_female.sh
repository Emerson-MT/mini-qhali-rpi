#!/usr/bin/env bash
set -euo pipefail

TEXT="${1:-Hola, soy Mini Qhali.}"
OUT="${2:-/tmp/miniqhali_tts.wav}"

VOICE="${ESPEAK_VOICE:-es-la+f4}"
FALLBACK_VOICE="${ESPEAK_FALLBACK_VOICE:-es+f3}"
SPEED="${ESPEAK_SPEED:-128}"
PITCH="${ESPEAK_PITCH:-82}"
AMP="${ESPEAK_AMP:-145}"
GAP="${ESPEAK_GAP:-4}"
SAMPLE_RATE="${TTS_SAMPLE_RATE:-22050}"
SOX_PITCH_CENTS="${TTS_SOX_PITCH_CENTS:-350}"
SOX_TEMPO="${TTS_SOX_TEMPO:-0.94}"

RAW="$(mktemp /tmp/miniqhali_espeak_raw_XXXXXX.wav)"

cleanup() {
  rm -f "$RAW"
}
trap cleanup EXIT

if ! espeak-ng -v "$VOICE" -q "test" 2>/dev/null; then
  echo "Advertencia: voz $VOICE no disponible. Usando $FALLBACK_VOICE." >&2
  VOICE="$FALLBACK_VOICE"
fi

espeak-ng \
  -v "$VOICE" \
  -s "$SPEED" \
  -p "$PITCH" \
  -a "$AMP" \
  -g "$GAP" \
  -k 18 \
  -w "$RAW" \
  "$TEXT"

if command -v sox >/dev/null 2>&1; then
  sox "$RAW" -r "$SAMPLE_RATE" -c 1 "$OUT" \
    gain -n -3 \
    pitch "$SOX_PITCH_CENTS" \
    tempo "$SOX_TEMPO" \
    highpass 80 \
    lowpass 7600
else
  cp "$RAW" "$OUT"
fi

echo "$OUT"
