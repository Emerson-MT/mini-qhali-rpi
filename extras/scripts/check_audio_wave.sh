#!/usr/bin/env bash
set -euo pipefail

DURATION="${1:-10}"
RATE="${RATE:-16000}"
CHANNELS="${CHANNELS:-1}"
AUDIO_DEVICE="${AUDIO_DEVICE:-default}"

OUT_DIR="$HOME/bench_audio"
WAV="$OUT_DIR/test_16k_mono.wav"
WAVE_PNG="$OUT_DIR/test_waveform.png"
STATS_TXT="$OUT_DIR/test_audio_stats.txt"
SILENCE_TXT="$OUT_DIR/test_silence_detect.txt"

mkdir -p "$OUT_DIR"

echo "== Dispositivos de captura detectados =="
arecord -l || true
echo

echo "== Grabando ${DURATION}s =="
echo "Device:   $AUDIO_DEVICE"
echo "Rate:     $RATE Hz"
echo "Channels: $CHANNELS"
echo "Output:   $WAV"
echo

arecord -D "$AUDIO_DEVICE" \
  -f S16_LE \
  -r "$RATE" \
  -c "$CHANNELS" \
  -d "$DURATION" \
  "$WAV"

echo
echo "== Info del WAV =="
ffprobe -hide_banner "$WAV" || true

echo
echo "== Estadísticas de volumen con sox =="
sox "$WAV" -n stats 2>&1 | tee "$STATS_TXT"

echo
echo "== Detectando silencio con ffmpeg =="
ffmpeg -hide_banner -nostats \
  -i "$WAV" \
  -af silencedetect=noise=-45dB:d=0.5 \
  -f null - 2>&1 | tee "$SILENCE_TXT" || true

echo
echo "== Generando imagen de onda =="
ffmpeg -y \
  -i "$WAV" \
  -filter_complex "showwavespic=s=1600x500:split_channels=1" \
  -frames:v 1 \
  "$WAVE_PNG" >/dev/null 2>&1

echo
echo "Archivos generados:"
echo "WAV:       $WAV"
echo "Onda PNG:  $WAVE_PNG"
echo "Stats:     $STATS_TXT"
echo "Silence:   $SILENCE_TXT"

echo
echo "Interpretación rápida:"
echo "- Si la onda PNG se ve casi plana, no está entrando voz."
echo "- Si 'RMS amplitude' está cerca de 0.000000, es silencio."
echo "- Si 'Maximum amplitude' está cerca de 0.000000, no hay señal."
echo "- Si silencedetect marca casi todo el audio como silence, el micrófono no está capturando bien."
