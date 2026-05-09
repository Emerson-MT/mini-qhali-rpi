#!/usr/bin/env bash
set -euo pipefail

LLAMA_SERVER_BIN="${LLAMA_SERVER_BIN:-$HOME/llama.cpp/build/bin/llama-server}"
LLAMA_MODEL_PATH="${LLAMA_MODEL_PATH:-$HOME/models/lfm2.5-350m/LFM2.5-350M-Q4_K_M.gguf}"
LLAMA_HOST="${LLAMA_HOST:-127.0.0.1}"
LLAMA_PORT="${LLAMA_PORT:-8080}"
LLAMA_API_KEY="${LLAMA_API_KEY:-local-key}"
LLAMA_THREADS="${LLAMA_THREADS:-4}"
LLAMA_CTX="${LLAMA_CTX:-2048}"
LLAMA_PARALLEL="${LLAMA_PARALLEL:-1}"
LLAMA_MODEL_ALIAS="${LLAMA_MODEL_ALIAS:-LFM2.5-350M-Q4_K_M.gguf}"
LLAMA_LOG_FILE="${LLAMA_LOG_FILE:-/tmp/miniqhali/llama-server.log}"

mkdir -p "$(dirname "$LLAMA_LOG_FILE")"

if [ ! -x "$LLAMA_SERVER_BIN" ]; then
  echo "Error: no se encontro llama-server ejecutable en $LLAMA_SERVER_BIN" >&2
  exit 1
fi

if [ ! -f "$LLAMA_MODEL_PATH" ]; then
  echo "Error: no se encontro el modelo GGUF en $LLAMA_MODEL_PATH" >&2
  exit 1
fi

exec "$LLAMA_SERVER_BIN" \
  -m "$LLAMA_MODEL_PATH" \
  --host "$LLAMA_HOST" \
  --port "$LLAMA_PORT" \
  -t "$LLAMA_THREADS" \
  -c "$LLAMA_CTX" \
  -np "$LLAMA_PARALLEL" \
  -a "$LLAMA_MODEL_ALIAS" \
  --api-key "$LLAMA_API_KEY" \
  --log-file "$LLAMA_LOG_FILE"
