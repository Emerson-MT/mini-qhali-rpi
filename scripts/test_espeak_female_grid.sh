#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="${1:-$HOME/mini_qhali_tts_tests/espeak_female_grid}"
TEXT="${2:-Hola, soy Mini Qhali. Estoy lista para ayudarte. Por favor, habla despues del sonido.}"
mkdir -p "$OUT_DIR"

VOICES=("es-la+f2" "es-la+f3" "es-la+f4" "es-419+f2" "es-419+f3" "es-419+f4" "es+f2" "es+f3" "es+f4")
SPEEDS=(145 150 155)
PITCHES=(60 63 66 69)

for voice in "${VOICES[@]}"; do
  if ! espeak-ng -v "$voice" -q "test" 2>/dev/null; then
    echo "Saltando voz no disponible: $voice"
    continue
  fi

  safe_voice="${voice//[^a-zA-Z0-9]/_}"

  for speed in "${SPEEDS[@]}"; do
    for pitch in "${PITCHES[@]}"; do
      raw="$OUT_DIR/${safe_voice}_s${speed}_p${pitch}_raw.wav"
      clean="$OUT_DIR/${safe_voice}_s${speed}_p${pitch}_clean.wav"

      espeak-ng -v "$voice" -s "$speed" -p "$pitch" -a 135 -g 4 -w "$raw" "$TEXT"

      if command -v sox >/dev/null 2>&1; then
        sox "$raw" -r 22050 -c 1 "$clean" \
          gain -n -3 \
          highpass 80 \
          lowpass 7600
        rm -f "$raw"
      else
        mv "$raw" "$clean"
      fi

      echo "Generado: $clean"
    done
  done
done

printf '\nEscucha muestras con:\n  aplay %s/*.wav\n' "$OUT_DIR"
