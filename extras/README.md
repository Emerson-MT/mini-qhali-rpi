# Guías de benchmark ASR/TTS para Raspberry Pi 5 + Ubuntu Server ARM64

Estas guías están pensadas para Raspberry Pi 5 con Ubuntu Server `aarch64`.

Incluye:

1. `guides/01_asr_vosk.md`
2. `guides/02_asr_sherpa_onnx.md`
3. `guides/03_tts_espeak_ng.md`
4. `guides/04_tts_piper.md`

Scripts auxiliares:

- `scripts/bench_vosk.py`
- `scripts/bench_sherpa_onnx.sh`
- `scripts/bench_espeak_ng.sh`
- `scripts/bench_piper.sh`

## Métricas

ASR/STT:

```text
RTF = tiempo_de_inferencia / duración_del_audio
```

TTS:

```text
RTF_TTS = tiempo_de_generación / duración_del_audio_generado
```

Interpretación:

```text
RTF < 1.0  => más rápido que tiempo real
RTF = 1.0  => tiempo real justo
RTF > 1.0  => más lento que tiempo real
```

## Preparación común

```bash
sudo apt update

sudo apt install -y   curl wget git unzip bzip2 xz-utils   python3-venv python3-pip python3-full   ffmpeg sox alsa-utils   bc jq time
```

Crear carpetas:

```bash
mkdir -p ~/bench_audio ~/bench_results ~/models ~/venvs ~/apps
```

Grabar una muestra de voz de 10 segundos:

```bash
arecord -l

arecord -f S16_LE -r 16000 -c 1 -d 10   ~/bench_audio/test_16k_mono.wav
```

Normalizar cualquier audio externo:

```bash
ffmpeg -y -i entrada.wav   -ac 1 -ar 16000 -sample_fmt s16   ~/bench_audio/test_16k_mono.wav
```

Ver duración:

```bash
ffprobe -v error -show_entries format=duration   -of default=noprint_wrappers=1:nokey=1   ~/bench_audio/test_16k_mono.wav
```
