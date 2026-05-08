# Guía 03 — TTS con eSpeak-NG en Raspberry Pi 5

## Objetivo

Probar eSpeak-NG como TTS ultraligero, generar WAV y medir velocidad.

eSpeak-NG es ideal para latencia mínima, bajo consumo, alertas, robots y fallback. Su voz es más robótica que Piper.

## 1. Instalar

```bash
sudo apt update
sudo apt install -y espeak-ng ffmpeg sox bc time
```

Verificar:

```bash
espeak-ng --version
espeak-ng --voices=es
```

## 2. Probar voz

Reproducir directo:

```bash
espeak-ng -v es "Hola, estoy funcionando en la Raspberry Pi cinco."
```

Guardar WAV:

```bash
mkdir -p ~/bench_tts

espeak-ng -v es -s 170   -w ~/bench_tts/espeak_test.wav   "Hola, estoy funcionando en la Raspberry Pi cinco."
```

Reproducir:

```bash
aplay ~/bench_tts/espeak_test.wav
```

## 3. Copiar script de benchmark

Desde el ZIP:

```bash
cp scripts/bench_espeak_ng.sh ~/bench_espeak_ng.sh
chmod +x ~/bench_espeak_ng.sh
```

Ejecutar:

```bash
~/bench_espeak_ng.sh   "Hola, soy un asistente local. Estoy probando síntesis de voz en español en una Raspberry Pi cinco."   10
```

Probar voces:

```bash
for v in es es-la es-mx; do
  echo "==== VOICE=$v ===="
  VOICE=$v ~/bench_espeak_ng.sh     "Hola, esta es una prueba de voz local en español."     5
done
```

## 4. Interpretación

```text
RTF_TTS < 1.0 => genera más rápido que reproducción
RTF_TTS 0.05 => extremadamente rápido
RTF_TTS 0.5  => todavía usable
RTF_TTS > 1  => no realtime
```

eSpeak-NG debería ser extremadamente rápido en Raspberry Pi 5.

## Fuentes

- https://github.com/espeak-ng/espeak-ng
- https://github.com/espeak-ng/espeak-ng/blob/master/docs/guide.md
