# Guía 01 — ASR con Vosk en Raspberry Pi 5

## Objetivo

Probar Vosk como ASR/STT offline y medir si corre más rápido que tiempo real en Raspberry Pi 5.

Vosk es buena opción para baja latencia, uso offline, CPU puro, comandos, frases cortas, formularios y control local.

## 1. Instalar

```bash
sudo apt update

sudo apt install -y   python3-venv python3-pip python3-full   ffmpeg sox unzip curl alsa-utils
```

```bash
python3 -m venv ~/venvs/vosk
source ~/venvs/vosk/bin/activate

python -m pip install -U pip
python -m pip install vosk soundfile
```

Verificar:

```bash
python - <<'PY'
import vosk
print("Vosk import OK")
PY
```

## 2. Descargar modelo español pequeño

```bash
mkdir -p ~/models/vosk
cd ~/models/vosk

curl -L -o vosk-model-small-es-0.42.zip   https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip

unzip vosk-model-small-es-0.42.zip
rm vosk-model-small-es-0.42.zip

ls -lh ~/models/vosk/vosk-model-small-es-0.42
```

## 3. Preparar audio

```bash
mkdir -p ~/bench_audio

arecord -f S16_LE -r 16000 -c 1 -d 10   ~/bench_audio/test_16k_mono.wav
```

O normaliza un archivo:

```bash
ffmpeg -y -i entrada.wav   -ac 1 -ar 16000 -sample_fmt s16   ~/bench_audio/test_16k_mono.wav
```

## 4. Copiar script de benchmark

Desde el ZIP, copia:

```bash
cp scripts/bench_vosk.py ~/bench_vosk.py
chmod +x ~/bench_vosk.py
```

O crea el script pegando el contenido de `scripts/bench_vosk.py`.

## 5. Ejecutar benchmark

```bash
source ~/venvs/vosk/bin/activate

python ~/bench_vosk.py   ~/bench_audio/test_16k_mono.wav   ~/models/vosk/vosk-model-small-es-0.42   --repeat 5
```

## 6. Interpretación

```text
RTF 0.10 => procesa 10 s de audio en 1 s
RTF 0.50 => procesa 10 s de audio en 5 s
RTF 1.00 => tiempo real justo
RTF 2.00 => tarda 20 s para 10 s de audio
```

Vosk debería ser de los más rápidos en Raspberry Pi 5.

## Fuentes

- https://alphacephei.com/vosk/
- https://alphacephei.com/vosk/models
- https://github.com/alphacep/vosk-api
