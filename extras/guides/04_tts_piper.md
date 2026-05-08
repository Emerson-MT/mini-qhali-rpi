# Guía 04 — TTS con Piper en Raspberry Pi 5

## Objetivo

Probar Piper TTS local, descargar una voz española y medir latencia/RTF.

Piper es el candidato principal para voz local más natural en pocos recursos.

## 1. Instalar dependencias

```bash
sudo apt update

sudo apt install -y   curl wget jq ffmpeg sox python3-venv python3-pip python3-full   libsndfile1 espeak-ng time
```

## 2. Método A — Instalar con pip

```bash
python3 -m venv ~/venvs/piper
source ~/venvs/piper/bin/activate

python -m pip install -U pip
python -m pip install piper-tts
```

Verificar:

```bash
piper --help
```

Si funciona, sigue al paso 4.

## 3. Método B — Binario ARM64 si pip falla

```bash
mkdir -p ~/apps/piper
cd ~/apps/piper

PIPER_URL=$(
  curl -s https://api.github.com/repos/OHF-Voice/piper1-gpl/releases/latest   | grep browser_download_url   | grep -Ei 'linux.*aarch64|linux.*arm64'   | grep -E 'tar.gz|tar.bz2|zip'   | head -n 1   | cut -d '"' -f 4
)

echo "$PIPER_URL"

wget -O piper-arm64-release "$PIPER_URL"
file piper-arm64-release
```

Extraer según el tipo:

```bash
tar xvf piper-arm64-release
# Si fuera zip:
# unzip piper-arm64-release
```

Buscar binario:

```bash
find ~/apps/piper -type f -name "piper" -perm -111 -print

PIPER_BIN=$(find ~/apps/piper -type f -name "piper" -perm -111 | head -n 1)
"$PIPER_BIN" --help
```

## 4. Descargar voz española

Usaremos `es_ES-davefx-medium`:

```bash
mkdir -p ~/models/piper/es_ES-davefx-medium
cd ~/models/piper/es_ES-davefx-medium

wget -O es_ES-davefx-medium.onnx   https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx

wget -O es_ES-davefx-medium.onnx.json   https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx.json

ls -lh
```

## 5. Probar síntesis

Si usaste pip:

```bash
source ~/venvs/piper/bin/activate
PIPER_BIN=$(which piper)
```

Si usaste binario:

```bash
PIPER_BIN=$(find ~/apps/piper -type f -name "piper" -perm -111 | head -n 1)
```

Generar audio:

```bash
mkdir -p ~/bench_tts

echo "Hola, estoy funcionando con Piper en una Raspberry Pi cinco."   | "$PIPER_BIN"       --model ~/models/piper/es_ES-davefx-medium/es_ES-davefx-medium.onnx       --config ~/models/piper/es_ES-davefx-medium/es_ES-davefx-medium.onnx.json       --output_file ~/bench_tts/piper_test.wav
```

Reproducir:

```bash
aplay ~/bench_tts/piper_test.wav
```

## 6. Copiar script de benchmark

Desde el ZIP:

```bash
cp scripts/bench_piper.sh ~/bench_piper.sh
chmod +x ~/bench_piper.sh
```

Ejecutar:

```bash
source ~/venvs/piper/bin/activate 2>/dev/null || true

~/bench_piper.sh   "Hola, soy un asistente local. Estoy probando Piper TTS en español en Raspberry Pi cinco."   5
```

## 7. Interpretación

```text
RTF_TTS < 1.0 => genera más rápido que reproducción
RTF_TTS 0.2-0.8 => viable para asistente local
RTF_TTS > 1.0 => puede sentirse lento
```

Piper debería ser más lento que eSpeak-NG, pero mucho más natural.

## 8. Recomendación

```text
TTS por defecto: Piper
Fallback rápido: eSpeak-NG
```

## Fuentes

- https://github.com/OHF-Voice/piper1-gpl
- https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/CLI.md
- https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/VOICES.md
- https://huggingface.co/rhasspy/piper-voices
- https://rhasspy.github.io/piper-samples/
