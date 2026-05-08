#!/usr/bin/env bash
set -euo pipefail

AUDIO="${1:-$HOME/bench_audio/test_16k_mono.wav}"
MODEL_DIR="${2:-$HOME/models/sherpa-onnx/sherpa-onnx-whisper-tiny}"
REPEAT="${3:-5}"
THREADS="${THREADS:-4}"

SHERPA_DIR="${SHERPA_DIR:-$(find "$HOME/apps/sherpa-onnx" -maxdepth 1 -type d -name 'sherpa-onnx-*linux-aarch64-shared' | head -n 1)}"
BIN="$SHERPA_DIR/bin/sherpa-onnx-offline"

if [[ ! -x "$BIN" ]]; then
  echo "No encuentro sherpa-onnx-offline en: $BIN" >&2
  exit 1
fi

if [[ ! -f "$AUDIO" ]]; then
  echo "No existe audio: $AUDIO" >&2
  exit 1
fi

DUR=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$AUDIO")

echo "Audio: $AUDIO"
echo "Duración audio: ${DUR}s"
echo "Modelo: $MODEL_DIR"
echo "Threads: $THREADS"

ENC="$MODEL_DIR/tiny-encoder.int8.onnx"
DEC="$MODEL_DIR/tiny-decoder.int8.onnx"
TOK="$MODEL_DIR/tiny-tokens.txt"

echo "Warm-up..."
"$BIN" --num-threads="$THREADS" --whisper-encoder="$ENC" --whisper-decoder="$DEC" --tokens="$TOK" "$AUDIO" >/tmp/sherpa_warmup.txt

echo "Benchmark..."
TOTAL=0

for i in $(seq 1 "$REPEAT"); do
  START=$(date +%s.%N)
  "$BIN" --num-threads="$THREADS" --whisper-encoder="$ENC" --whisper-decoder="$DEC" --tokens="$TOK" "$AUDIO" > "/tmp/sherpa_run_${i}.txt"
  END=$(date +%s.%N)

  ELAPSED=$(python3 - <<PY
print($END - $START)
PY
)
  TOTAL=$(python3 - <<PY
print($TOTAL + $ELAPSED)
PY
)
  RTF=$(python3 - <<PY
print($ELAPSED / $DUR)
PY
)
  echo "run=$i elapsed=${ELAPSED}s RTF=${RTF}"
done

MEAN=$(python3 - <<PY
print($TOTAL / $REPEAT)
PY
)

RTF_MEAN=$(python3 - <<PY
print($MEAN / $DUR)
PY
)

echo
echo "=== Resultado ==="
echo "mean_elapsed_s=$MEAN"
echo "audio_s=$DUR"
echo "RTF_mean=$RTF_MEAN"
echo "Última salida:"
cat "/tmp/sherpa_run_${REPEAT}.txt"
