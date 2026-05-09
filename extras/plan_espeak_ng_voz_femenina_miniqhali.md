# Plan para obtener la mejor voz femenina posible con eSpeak NG en MiniQhali

## 1. Objetivo

Configurar una voz femenina local, liviana y estable para Raspberry Pi 5 usando `eSpeak NG`, priorizando:

- baja latencia;
- funcionamiento offline;
- consumo mínimo de CPU/RAM;
- claridad en español latino;
- integración simple con el proyecto MiniQhali;
- una voz femenina más amable y menos robótica dentro de los límites de eSpeak NG.

Este plan no busca competir con TTS neural como Piper, Zonos, XTTS o ElevenLabs. eSpeak NG usa síntesis por formantes: es muy liviano y claro, pero menos natural que motores basados en grabaciones humanas o redes neuronales. Por tanto, la estrategia óptima es mejorar **inteligibilidad, prosodia aparente, volumen, pausas y suavizado**, no prometer naturalidad humana.

---

## 2. Decisión técnica recomendada

### Stack recomendado

```text
MiniQhali App / backend
        ↓
TTS adapter interno
        ↓
eSpeak NG CLI
        ↓
WAV crudo
        ↓
sox o ffmpeg para limpieza ligera
        ↓
aplay / salida ALSA / archivo cacheado
```

### Motor base

Usar `eSpeak NG` como motor local por defecto para respuestas cortas, confirmaciones, errores y mensajes del asistente.

### Voz base sugerida

Probar en este orden:

```bash
es-la+f3
es-la+f2
es+f3
es+f2
es-419+f3
es-419+f2
```

La razón es práctica: según la versión instalada, el español latino puede aparecer como `es-la`, `es-419` o solo `es`. La forma correcta no es asumirlo, sino listar las voces disponibles en la Raspberry Pi.

---

## 3. Auditoría inicial de voces disponibles

Ejecutar:

```bash
espeak-ng --version
espeak-ng --voices
espeak-ng --voices=es
espeak-ng --voices=es-la || true
espeak-ng --voices=es-419 || true
espeak-ng --voices=variant
espeak-ng --voices=mbrola || true
```

Guardar el resultado:

```bash
mkdir -p ~/mini_qhali_tts_tests
{
  echo "# eSpeak NG version"
  espeak-ng --version
  echo
  echo "# Spanish voices"
  espeak-ng --voices=es
  echo
  echo "# Voice variants"
  espeak-ng --voices=variant
  echo
  echo "# MBROLA voices"
  espeak-ng --voices=mbrola || true
} > ~/mini_qhali_tts_tests/espeak_voice_audit.txt
```

Criterio de decisión:

- Si `es-la` existe, usar `es-la` como español latino.
- Si no existe, usar `es`.
- Si `es-419` existe en tu build, probarlo también.
- Si aparecen variantes femeninas `+f1`, `+f2`, `+f3`, `+f4`, generar muestras comparativas.
- Si aparece `mb-es3`, considerarlo solo como experimento adicional, no como dependencia principal.

---

## 4. Presets recomendados para voz femenina

### Preset A: voz femenina clara y adulta

Recomendado como baseline.

```bash
espeak-ng -v es-la+f3 -s 150 -p 63 -a 135 -g 4 \
  -w /tmp/miniqhali_espeak_raw.wav \
  "Hola, soy Mini Qhali. Estoy lista para ayudarte."
```

### Preset B: voz femenina más suave

```bash
espeak-ng -v es-la+f2 -s 145 -p 60 -a 130 -g 5 \
  -w /tmp/miniqhali_espeak_raw.wav \
  "Hola, soy Mini Qhali. Estoy lista para ayudarte."
```

### Preset C: voz femenina más energética

```bash
espeak-ng -v es-la+f4 -s 158 -p 68 -a 135 -g 3 \
  -w /tmp/miniqhali_espeak_raw.wav \
  "Hola, soy Mini Qhali. Estoy lista para ayudarte."
```

### Preset D: fallback si `es-la` no existe

```bash
espeak-ng -v es+f3 -s 150 -p 63 -a 135 -g 4 \
  -w /tmp/miniqhali_espeak_raw.wav \
  "Hola, soy Mini Qhali. Estoy lista para ayudarte."
```

### Rango recomendado de parámetros

| Parámetro | Rango recomendado | Comentario |
|---|---:|---|
| `-s` velocidad | `145–165` | Menos robótico que el default si se mantiene moderado. |
| `-p` pitch | `58–70` | Voz más femenina sin sonar caricaturesca. |
| `-a` amplitud | `120–150` | Evitar saturación; normalizar después. |
| `-g` pausa entre palabras | `3–6` | Mejora claridad en prompts cortos. |
| variante | `+f2`, `+f3`, `+f4` | Seleccionar por prueba auditiva real. |

Recomendación inicial para producción:

```bash
VOICE="es-la+f3"
SPEED="150"
PITCH="63"
AMP="135"
GAP="4"
```

---

## 5. Posprocesado recomendado con sox

Instalar:

```bash
sudo apt update
sudo apt install -y espeak-ng alsa-utils sox libsox-fmt-all ffmpeg
```

Generar WAV y limpiar:

```bash
TEXT="Hola, soy Mini Qhali. Estoy lista para ayudarte."
RAW="/tmp/miniqhali_espeak_raw.wav"
OUT="/tmp/miniqhali_espeak_clean.wav"

espeak-ng -v es-la+f3 -s 150 -p 63 -a 135 -g 4 -w "$RAW" "$TEXT"

sox "$RAW" -r 22050 -c 1 "$OUT" \
  gain -n -3 \
  highpass 80 \
  lowpass 7600

aplay "$OUT"
```

Por qué este posprocesado:

- `gain -n -3`: normaliza y deja margen para evitar clipping.
- `highpass 80`: limpia ruido o energía grave innecesaria.
- `lowpass 7600`: suaviza agudos ásperos de síntesis.
- `22050 Hz mono`: suficiente para voz, más liviano para Raspberry Pi.

Variante con compresión ligera:

```bash
sox "$RAW" -r 22050 -c 1 "$OUT" \
  gain -n -3 \
  highpass 80 \
  lowpass 7600 \
  compand 0.03,0.20 -60,-60,-30,-20,-12,-9,-3,-3 -3
```

Usar compresión solo si la voz queda con sílabas muy desiguales.

---

## 6. Script de pruebas comparativas

Crear:

```bash
mkdir -p scripts
nano scripts/test_espeak_female_grid.sh
```

Contenido:

```bash
#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="${1:-$HOME/mini_qhali_tts_tests/espeak_female_grid}"
TEXT="${2:-Hola, soy Mini Qhali. Estoy lista para ayudarte. Por favor, habla después del sonido.}"
mkdir -p "$OUT_DIR"

VOICES=("es-la+f2" "es-la+f3" "es-la+f4" "es+f2" "es+f3" "es+f4" "es-419+f2" "es-419+f3" "es-419+f4")
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

      sox "$raw" -r 22050 -c 1 "$clean" \
        gain -n -3 \
        highpass 80 \
        lowpass 7600

      rm -f "$raw"
      echo "Generado: $clean"
    done
  done
done

printf '\nEscucha muestras con:\n  aplay %s/*.wav\n' "$OUT_DIR"
```

Permisos:

```bash
chmod +x scripts/test_espeak_female_grid.sh
```

Ejecutar:

```bash
./scripts/test_espeak_female_grid.sh
```

Escuchar:

```bash
aplay ~/mini_qhali_tts_tests/espeak_female_grid/*.wav
```

---

## 7. Script de producción recomendado

Crear:

```bash
nano scripts/tts_espeak_female.sh
```

Contenido:

```bash
#!/usr/bin/env bash
set -euo pipefail

TEXT="${1:-Hola, soy Mini Qhali.}"
OUT="${2:-/tmp/miniqhali_tts.wav}"

VOICE="${ESPEAK_VOICE:-es-la+f3}"
SPEED="${ESPEAK_SPEED:-150}"
PITCH="${ESPEAK_PITCH:-63}"
AMP="${ESPEAK_AMP:-135}"
GAP="${ESPEAK_GAP:-4}"
SAMPLE_RATE="${TTS_SAMPLE_RATE:-22050}"

RAW="$(mktemp /tmp/miniqhali_espeak_raw_XXXXXX.wav)"

cleanup() {
  rm -f "$RAW"
}
trap cleanup EXIT

# Fallback si la voz elegida no existe.
if ! espeak-ng -v "$VOICE" -q "test" 2>/dev/null; then
  echo "Advertencia: voz $VOICE no disponible. Usando es+f3." >&2
  VOICE="es+f3"
fi

espeak-ng \
  -v "$VOICE" \
  -s "$SPEED" \
  -p "$PITCH" \
  -a "$AMP" \
  -g "$GAP" \
  -w "$RAW" \
  "$TEXT"

sox "$RAW" -r "$SAMPLE_RATE" -c 1 "$OUT" \
  gain -n -3 \
  highpass 80 \
  lowpass 7600

echo "$OUT"
```

Permisos:

```bash
chmod +x scripts/tts_espeak_female.sh
```

Uso:

```bash
./scripts/tts_espeak_female.sh "Hola, soy Mini Qhali. Estoy lista para ayudarte." /tmp/voz.wav
aplay /tmp/voz.wav
```

Con variables:

```bash
ESPEAK_VOICE="es-la+f2" ESPEAK_SPEED=145 ESPEAK_PITCH=61 \
./scripts/tts_espeak_female.sh "Prueba de voz femenina suave." /tmp/suave.wav
```

---

## 8. Normalización de texto antes de sintetizar

eSpeak mejora mucho cuando recibe texto limpio. Agregar un preprocesador antes del TTS.

### Reglas recomendadas

| Entrada | Salida recomendada |
|---|---|
| `MiniQhali` | `Mini Cuali` o `Mini Kuali` |
| `ASR` | `A ese erre` o `reconocimiento de voz` |
| `TTS` | `texto a voz` |
| `API` | `A P I` o `interfaz de programación` |
| `OK` | `De acuerdo` |
| `repo` | `repositorio` |
| URLs | `enlace` o dominio simplificado |
| números largos | agrupar o escribir con palabras |

### Ejemplo de preprocesador mínimo

```bash
normalize_tts_text() {
  local text="$1"
  text="${text//MiniQhali/Mini Cuali}"
  text="${text//mini-qhali/Mini Cuali}"
  text="${text//ASR/reconocimiento de voz}"
  text="${text//TTS/texto a voz}"
  text="${text//API/A P I}"
  text="${text//OK/De acuerdo}"
  printf '%s' "$text"
}
```

Recomendación: mantener esta normalización en Python si el backend principal está en Python/FastAPI, porque será más fácil manejar regex, abreviaturas, números y cache.

---

## 9. Integración con MiniQhali

### Configuración `.env`

```env
TTS_ENGINE=espeak-ng
ESPEAK_VOICE=es-la+f3
ESPEAK_SPEED=150
ESPEAK_PITCH=63
ESPEAK_AMP=135
ESPEAK_GAP=4
TTS_SAMPLE_RATE=22050
TTS_CACHE_ENABLED=true
TTS_OUTPUT_FORMAT=wav
```

### Interfaz interna sugerida

```text
POST /tts/synthesize
{
  "text": "Hola, soy Mini Qhali.",
  "voice_profile": "female_default",
  "play": true
}
```

Respuesta:

```json
{
  "engine": "espeak-ng",
  "voice": "es-la+f3",
  "sample_rate": 22050,
  "audio_path": "/tmp/miniqhali/cache/tts/<hash>.wav",
  "duration_ms": 1234,
  "cached": false
}
```

### Cache recomendado

Calcular hash por:

```text
engine + voice + speed + pitch + amp + gap + normalized_text
```

Ruta sugerida:

```text
/tmp/miniqhali/cache/tts/espeak-ng/<hash>.wav
```

Para respuestas frecuentes, pre-generar:

- “Hola, soy Mini Qhali.”
- “No entendí bien. ¿Puedes repetirlo?”
- “Estoy procesando tu consulta.”
- “Listo.”
- “Hubo un problema con el audio.”
- “Por favor, habla después del sonido.”

---

## 10. Evaluación de calidad

Crear una tabla manual de evaluación con escala 1–5.

| Criterio | Peso | Qué medir |
|---|---:|---|
| Inteligibilidad | 40% | Se entiende sin mirar texto. |
| Amabilidad | 20% | No suena agresiva ni chillona. |
| Naturalidad | 15% | Menos robótica dentro de eSpeak. |
| Volumen estable | 10% | No hay sílabas saturadas o bajas. |
| Latencia | 10% | Respuesta rápida en Pi 5. |
| Pronunciación de marca | 5% | “Mini Qhali” se entiende. |

Frases de prueba:

```text
Hola, soy Mini Qhali. Estoy lista para ayudarte.
No entendí bien. ¿Puedes repetirlo, por favor?
Estoy procesando tu consulta.
La grabación se completó correctamente.
Hubo un problema con el micrófono.
Por favor, habla después del sonido.
El sistema está funcionando en modo local.
```

Comando para generar una frase:

```bash
./scripts/tts_espeak_female.sh "No entendí bien. ¿Puedes repetirlo, por favor?" /tmp/repetir.wav
aplay /tmp/repetir.wav
```

---

## 11. Opción avanzada: MBROLA

MBROLA puede mejorar el timbre frente al eSpeak puro, pero tiene restricciones prácticas:

- sus voces son gratuitas para uso no comercial, pero no son open source;
- no siempre están empaquetadas en Ubuntu/Raspberry Pi OS;
- algunas voces españolas femeninas pueden requerir instalación manual;
- añade complejidad al despliegue.

Probar solo como rama experimental:

```bash
sudo apt update
sudo apt install -y mbrola
apt-cache search mbrola | grep -E 'es|mx|vz'
```

Si está disponible:

```bash
sudo apt install -y mbrola-es1 mbrola-es2 || true
```

Para la voz española femenina documentada por eSpeak NG:

```bash
espeak-ng -v mb-es3 "Hola, soy Mini Qhali."
```

Si no existe el paquete, revisar instalación manual de voces MBROLA. No convertirlo en dependencia de producción salvo que el licenciamiento y el empaquetado estén claros.

---

## 12. Recomendación final

### Para producción local en Raspberry Pi 5

Usar:

```bash
espeak-ng + sox + cache WAV
```

Preset inicial:

```bash
ESPEAK_VOICE=es-la+f3
ESPEAK_SPEED=150
ESPEAK_PITCH=63
ESPEAK_AMP=135
ESPEAK_GAP=4
TTS_SAMPLE_RATE=22050
```

### Para mejor experiencia de usuario

No intentar que eSpeak NG suene humano. Hacer que suene:

- clara;
- femenina;
- calmada;
- consistente;
- rápida;
- sin clipping;
- con pausas adecuadas;
- con frases cortas.

### Regla de arquitectura

En MiniQhali, eSpeak NG debe quedar como:

```text
TTS local mínimo garantizado
```

Y no como único camino futuro. La arquitectura debería permitir cambiar entre:

```text
eSpeak NG → Piper → Zonos remoto/GPU
```

sin cambiar la lógica de negocio.

---

## 13. Checklist de implementación

- [ ] Instalar `espeak-ng`, `sox`, `ffmpeg`, `alsa-utils`.
- [ ] Auditar voces disponibles.
- [ ] Generar grilla de pruebas con variantes femeninas.
- [ ] Elegir preset ganador por escucha real.
- [ ] Agregar normalización de texto.
- [ ] Crear script `tts_espeak_female.sh`.
- [ ] Añadir `.env` con parámetros TTS.
- [ ] Añadir cache por hash.
- [ ] Pre-generar frases frecuentes.
- [ ] Medir latencia en Raspberry Pi 5.
- [ ] Documentar voz final elegida.
- [ ] Mantener Piper/Zonos como rutas de mejora futura.

---

## 14. Fuentes consultadas

- eSpeak NG GitHub / documentación oficial: https://github.com/espeak-ng/espeak-ng
- Manual de `espeak-ng`: https://www.mankier.com/1/espeak-ng
- Documentación de voces de eSpeak NG: https://github.com/espeak-ng/espeak-ng/blob/master/docs/voices.md
- Documentación de MBROLA en eSpeak NG: https://github.com/espeak-ng/espeak-ng/blob/master/docs/mbrola.md
