# Guía 02 — ASR con Sherpa-ONNX en Raspberry Pi 5

## Objetivo

Probar Sherpa-ONNX como ASR/STT offline y medir RTF.

Sherpa-ONNX corre local, usa ONNX Runtime, tiene binarios Linux ARM64, soporta ASR streaming/no streaming, VAD, TTS y modelos INT8.

Para baseline usaremos `sherpa-onnx-whisper-tiny`, modelo Whisper multilingüe exportado a ONNX.

## 1. Instalar dependencias

```bash
sudo apt update

sudo apt install -y   curl wget bzip2 tar ffmpeg sox jq time alsa-utils
```

## 2. Descargar binario ARM64

```bash
mkdir -p ~/apps/sherpa-onnx
cd ~/apps/sherpa-onnx

ASSET_URL=$(
  curl -s https://api.github.com/repos/k2-fsa/sherpa-onnx/releases/latest   | grep browser_download_url   | grep 'linux-aarch64-shared.tar.bz2'   | head -n 1   | cut -d '"' -f 4
)

echo "$ASSET_URL"

wget -O sherpa-onnx-linux-aarch64-shared.tar.bz2 "$ASSET_URL"
tar xvf sherpa-onnx-linux-aarch64-shared.tar.bz2
rm sherpa-onnx-linux-aarch64-shared.tar.bz2

SHERPA_DIR=$(find ~/apps/sherpa-onnx -maxdepth 1 -type d -name 'sherpa-onnx-*linux-aarch64-shared' | head -n 1)
"$SHERPA_DIR/bin/sherpa-onnx-version"
```

Activar PATH:

```bash
export SHERPA_DIR=$(find ~/apps/sherpa-onnx -maxdepth 1 -type d -name 'sherpa-onnx-*linux-aarch64-shared' | head -n 1)
export PATH="$SHERPA_DIR/bin:$PATH"

which sherpa-onnx-offline
```

## 3. Descargar modelo Whisper tiny ONNX

```bash
mkdir -p ~/models/sherpa-onnx
cd ~/models/sherpa-onnx

wget https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-tiny.tar.bz2

tar xvf sherpa-onnx-whisper-tiny.tar.bz2
rm sherpa-onnx-whisper-tiny.tar.bz2

ls -lh ~/models/sherpa-onnx/sherpa-onnx-whisper-tiny
```

## 4. Preparar audio

```bash
mkdir -p ~/bench_audio

arecord -f S16_LE -r 16000 -c 1 -d 10   ~/bench_audio/test_16k_mono.wav
```

O normaliza:

```bash
ffmpeg -y -i entrada.wav   -ac 1 -ar 16000 -sample_fmt s16   ~/bench_audio/test_16k_mono.wav
```

## 5. Prueba simple

```bash
export SHERPA_DIR=$(find ~/apps/sherpa-onnx -maxdepth 1 -type d -name 'sherpa-onnx-*linux-aarch64-shared' | head -n 1)
export PATH="$SHERPA_DIR/bin:$PATH"

MODEL_DIR=~/models/sherpa-onnx/sherpa-onnx-whisper-tiny
AUDIO=~/bench_audio/test_16k_mono.wav

sherpa-onnx-offline   --num-threads=4   --whisper-encoder="$MODEL_DIR/tiny-encoder.int8.onnx"   --whisper-decoder="$MODEL_DIR/tiny-decoder.int8.onnx"   --tokens="$MODEL_DIR/tiny-tokens.txt"   "$AUDIO"
```

## 6. Copiar script de benchmark

Desde el ZIP:

```bash
cp scripts/bench_sherpa_onnx.sh ~/bench_sherpa_onnx.sh
chmod +x ~/bench_sherpa_onnx.sh
```

Ejecutar:

```bash
THREADS=4 ~/bench_sherpa_onnx.sh   ~/bench_audio/test_16k_mono.wav   ~/models/sherpa-onnx/sherpa-onnx-whisper-tiny   5
```

Probar hilos:

```bash
for t in 1 2 3 4; do
  echo "==== THREADS=$t ===="
  THREADS=$t ~/bench_sherpa_onnx.sh     ~/bench_audio/test_16k_mono.wav     ~/models/sherpa-onnx/sherpa-onnx-whisper-tiny     3
done
```

## 7. Prueba con micrófono + VAD

```bash
cd ~/models/sherpa-onnx

wget -O silero_vad.onnx   https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/silero_vad.onnx
```

```bash
MODEL_DIR=~/models/sherpa-onnx/sherpa-onnx-whisper-tiny

sherpa-onnx-vad-microphone-offline-asr   --silero-vad-model=~/models/sherpa-onnx/silero_vad.onnx   --num-threads=4   --whisper-encoder="$MODEL_DIR/tiny-encoder.int8.onnx"   --whisper-decoder="$MODEL_DIR/tiny-decoder.int8.onnx"   --tokens="$MODEL_DIR/tiny-tokens.txt"
```

## 8. Interpretación

```text
RTF < 1.0 => viable realtime
RTF 0.3-0.7 => bueno para asistente local
RTF > 1.0 => usar Vosk, VAD, modelo más pequeño o fallback a Jetson/PC
```

## Fuentes

- https://k2-fsa.github.io/sherpa/onnx/
- https://k2-fsa.github.io/sherpa/onnx/pretrained_models/index.html
- https://k2-fsa.github.io/sherpa/onnx/pretrained_models/whisper/tiny.en.html
- https://github.com/k2-fsa/sherpa-onnx
