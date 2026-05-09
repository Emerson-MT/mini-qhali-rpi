# Plan de migración de MiniQhali a `llama.cpp` con LFM2.5 350M GGUF Q4

**Fecha:** 2026-05-08  
**Proyecto:** MiniQhali / Raspberry Pi 5 ASR + LLM + TTS  
**Objetivo:** pasar el módulo LLM del proyecto a una ejecución directa con `llama.cpp`, usando el mismo modelo **LFM2.5-350M GGUF 4-bit**, idealmente `Q4_K_M`, y dejando una interfaz limpia para alternar entre `llama.cpp`, Ollama u otros backends.

---

## 1. Decisión técnica recomendada

La ruta más conveniente para MiniQhali es usar **`llama-server` como runtime principal** y mantener `llama-cli` solo para pruebas manuales.

Motivo:

- `llama-server` expone una API local compatible con el estilo de OpenAI, lo que permite conectar el orquestador Python sin acoplarlo a binarios CLI.
- Permite conservar un `LLMClient` propio en el proyecto y cambiar de backend por configuración.
- Reduce overhead frente a usar Ollama cuando el objetivo es exprimir Raspberry Pi 5.
- Mantiene compatibilidad con el modelo GGUF ya descargado y cuantizado.
- Facilita benchmarking de latencia, tokens/s, memoria y estabilidad.

El modelo base que se debe usar en el plan es:

```bash
/home/ubuntu/models/lfm2.5-350m/LFM2.5-350M-Q4_K_M.gguf
```

Según el contexto ya trabajado, `llama.cpp` ya fue compilado en:

```bash
~/llama.cpp/build/bin/
```

y contiene al menos:

```bash
llama-cli
llama-server
llama-bench
```

---

## 2. Stack óptimo

### Hardware

- Raspberry Pi 5 ARM64 / AArch64.
- RAM: 8 GB mínimo, 16 GB preferible si se ejecuta ASR + LLM + TTS + UI.
- Almacenamiento: microSD funciona, pero NVMe/SSD por M.2 HAT es recomendable para reducir tiempos de carga.
- Refrigeración activa obligatoria para pruebas sostenidas.

### Sistema

- Ubuntu 22.04/24.04 ARM64 o Raspberry Pi OS 64-bit.
- `systemd` para levantar el servidor LLM.
- `bash` + `.env` para parametrizar rutas.
- Python 3.11/3.12 para el orquestador.
- Cliente Python OpenAI-compatible para hablar con `llama-server`.

### Runtime LLM

- `llama.cpp` directo.
- `llama-server` como servicio.
- `llama-cli` para debug.
- `llama-bench` para medición.
- Build recomendado a probar:
  - CPU nativo baseline.
  - OpenBLAS para acelerar procesamiento de prompt en algunos escenarios.
  - Arm KleidiAI como variante de benchmarking en CPU ARM.

### ASR/TTS existentes

Mantener el diseño ya conversado:

- ASR local: Vosk como baseline, Sherpa-ONNX como comparación.
- TTS local por defecto: Piper.
- TTS fallback ultraligero: eSpeak-NG.
- Zonos debe tratarse como TTS experimental o remoto, no como reemplazo directo en Raspberry Pi 5.

---

## 3. Arquitectura objetivo

```text
Micrófono
  ↓
ASR provider
  ├─ Vosk
  └─ Sherpa-ONNX
  ↓
MiniQhali Orchestrator
  ↓
LLMClient
  ├─ llama.cpp / llama-server  ← recomendado
  ├─ Ollama                    ← fallback / comparación
  └─ mock                      ← pruebas
  ↓
TTS provider
  ├─ Piper                     ← default local
  ├─ eSpeak-NG                 ← fallback rápido
  └─ Zonos API                 ← remoto / GPU / experimental
  ↓
Audio output
```

La idea clave es que `llama.cpp` no debe invadirse en toda la app. Debe quedar encapsulado detrás de una interfaz:

```python
class LLMClient:
    def generate(self, messages: list[dict], **kwargs) -> str:
        ...
```

---

## 4. Variables de entorno recomendadas

Crear o ampliar `.env`:

```bash
# Rutas
THIS_REPO=/home/ubuntu/Documents/MiniQhali/mini-qhali-rpi
LLAMA_CPP_DIR=/home/ubuntu/llama.cpp
LLAMA_BIN=/home/ubuntu/llama.cpp/build/bin
LFM_GGUF=/home/ubuntu/models/lfm2.5-350m/LFM2.5-350M-Q4_K_M.gguf

# Backend
LLM_PROVIDER=llama_cpp
LLAMA_BASE_URL=http://127.0.0.1:8080/v1
LLAMA_MODEL_ALIAS=lfm2.5-350m-q4-k-m

# Inferencia
LLAMA_CTX_SIZE=2048
LLAMA_THREADS=4
LLAMA_TEMP=0.2
LLAMA_TOP_K=40
LLAMA_TOP_P=0.9
LLAMA_REPEAT_PENALTY=1.08
LLAMA_MAX_TOKENS=256
```

Durante desarrollo, desde el repo:

```bash
export THIS_REPO="$(pwd)"
export LLAMA_CPP_DIR="$HOME/llama.cpp"
export LLAMA_BIN="$LLAMA_CPP_DIR/build/bin"
export LFM_GGUF="$HOME/models/lfm2.5-350m/LFM2.5-350M-Q4_K_M.gguf"
```

---

## 5. Fase 0 — Verificación rápida

Ejecutar:

```bash
echo "$THIS_REPO"
test -d "$THIS_REPO" && echo "repo ok"
test -x "$HOME/llama.cpp/build/bin/llama-cli" && echo "llama-cli ok"
test -x "$HOME/llama.cpp/build/bin/llama-server" && echo "llama-server ok"
test -f "$HOME/models/lfm2.5-350m/LFM2.5-350M-Q4_K_M.gguf" && echo "modelo ok"
```

Ver arquitectura:

```bash
uname -m
lscpu | head -40
free -h
```

---

## 6. Fase 1 — Prueba directa con `llama-cli`

Prueba básica:

```bash
"$LLAMA_BIN/llama-cli" \
  -m "$LFM_GGUF" \
  -c 2048 \
  -t 4 \
  --temp 0.2 \
  --top-k 40 \
  --top-p 0.9 \
  --repeat-penalty 1.08 \
  -n 128 \
  -p "Responde en español, breve y claro: ¿qué es MiniQhali?"
```

Criterio de aceptación:

- El modelo carga sin error.
- La respuesta sale en español o puede forzarse con prompt de sistema.
- No hay swapping fuerte.
- La generación mantiene latencia aceptable para respuestas cortas.

---

## 7. Fase 2 — Levantar `llama-server`

Ejecutar manualmente:

```bash
"$LLAMA_BIN/llama-server" \
  -m "$LFM_GGUF" \
  -c 2048 \
  -t 4 \
  --host 127.0.0.1 \
  --port 8080
```

Probar con `curl`:

```bash
curl http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "lfm2.5-350m-q4-k-m",
    "messages": [
      {"role": "system", "content": "Responde siempre en español peruano, breve y útil."},
      {"role": "user", "content": "Dime una frase corta para saludar al usuario."}
    ],
    "temperature": 0.2,
    "max_tokens": 80
  }'
```

Criterio de aceptación:

- El endpoint responde.
- La app puede consumirlo como API local.
- La latencia de primera respuesta es medible.
- El proceso no consume toda la RAM.

---

## 8. Fase 3 — Adapter Python OpenAI-compatible

Crear un adapter, por ejemplo:

```text
mini_qhali/
  llm/
    __init__.py
    base.py
    llama_cpp_client.py
    ollama_client.py
```

Ejemplo de cliente:

```python
import os
from openai import OpenAI

class LlamaCppClient:
    def __init__(self):
        self.client = OpenAI(
            base_url=os.getenv("LLAMA_BASE_URL", "http://127.0.0.1:8080/v1"),
            api_key="not-needed",
        )
        self.model = os.getenv("LLAMA_MODEL_ALIAS", "lfm2.5-350m-q4-k-m")

    def generate(self, user_text: str, system_prompt: str | None = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_text})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=float(os.getenv("LLAMA_TEMP", "0.2")),
            max_tokens=int(os.getenv("LLAMA_MAX_TOKENS", "256")),
            extra_body={
                "top_k": int(os.getenv("LLAMA_TOP_K", "40")),
                "top_p": float(os.getenv("LLAMA_TOP_P", "0.9")),
                "repetition_penalty": float(os.getenv("LLAMA_REPEAT_PENALTY", "1.08")),
            },
        )
        return response.choices[0].message.content.strip()
```

---

## 9. Fase 4 — Servicio `systemd`

Crear archivo:

```bash
sudo nano /etc/systemd/system/mini-qhali-llama.service
```

Contenido sugerido:

```ini
[Unit]
Description=MiniQhali llama.cpp LFM2.5 350M server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/Documents/MiniQhali/mini-qhali-rpi
Environment=LLAMA_BIN=/home/ubuntu/llama.cpp/build/bin
Environment=LFM_GGUF=/home/ubuntu/models/lfm2.5-350m/LFM2.5-350M-Q4_K_M.gguf
ExecStart=/home/ubuntu/llama.cpp/build/bin/llama-server -m /home/ubuntu/models/lfm2.5-350m/LFM2.5-350M-Q4_K_M.gguf -c 2048 -t 4 --host 127.0.0.1 --port 8080
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Activar:

```bash
sudo systemctl daemon-reload
sudo systemctl enable mini-qhali-llama
sudo systemctl start mini-qhali-llama
sudo systemctl status mini-qhali-llama --no-pager
```

Logs:

```bash
journalctl -u mini-qhali-llama -f
```

---

## 10. Fase 5 — Benchmark

Medir con `llama-bench`:

```bash
"$LLAMA_BIN/llama-bench" \
  -m "$LFM_GGUF" \
  -p 128 \
  -n 128 \
  -t 1,2,3,4
```

Medir endpoint:

```bash
time curl http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "lfm2.5-350m-q4-k-m",
    "messages": [{"role": "user", "content": "Responde en 30 palabras: ¿qué es un asistente local?"}],
    "temperature": 0.2,
    "max_tokens": 80
  }'
```

Métricas mínimas a guardar:

| Métrica | Descripción | Objetivo |
|---|---|---|
| `load_time_ms` | Tiempo de carga inicial del modelo | Medir, no optimizar primero |
| `ttft_ms` | Tiempo hasta primer token | Bajo para UX conversacional |
| `tokens_per_second` | Generación | Comparar CLI vs server |
| `rss_mb` | Memoria residente | Evitar swap |
| `cpu_temp_c` | Temperatura | Mantener estable |
| `prompt_tokens` | Entrada | Controlar prompts largos |
| `completion_tokens` | Salida | Limitar respuestas habladas |

Guardar resultados en:

```bash
mkdir -p "$THIS_REPO/bench_results/llm"
```

---

## 11. Fase 6 — Variantes de build

### Baseline CPU

```bash
cd "$HOME"
git clone https://github.com/ggml-org/llama.cpp || true
cd "$HOME/llama.cpp"
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release -j "$(nproc)" --target llama-server llama-cli llama-bench
```

### Variante OpenBLAS

OpenBLAS puede mejorar el procesamiento de prompt en algunos casos, pero no necesariamente mejora la velocidad de generación token por token.

```bash
sudo apt update
sudo apt install -y libopenblas-dev

cd "$HOME/llama.cpp"
cmake -B build-openblas \
  -DCMAKE_BUILD_TYPE=Release \
  -DGGML_BLAS=ON \
  -DGGML_BLAS_VENDOR=OpenBLAS

cmake --build build-openblas --config Release -j "$(nproc)" --target llama-server llama-cli llama-bench
```

### Variante Arm KleidiAI

Probar como build alternativo en Raspberry Pi 5:

```bash
cd "$HOME/llama.cpp"
cmake -B build-kleidiai \
  -DCMAKE_BUILD_TYPE=Release \
  -DGGML_CPU_KLEIDIAI=ON

cmake --build build-kleidiai --config Release -j "$(nproc)" --target llama-server llama-cli llama-bench
```

Recomendación: no asumir que una variante es más rápida. Medir con el mismo prompt, mismo modelo y mismos parámetros.

---

## 12. Fase 7 — Prompts y comportamiento

Para TTS, el LLM debe responder corto. Configurar un system prompt:

```text
Eres MiniQhali, un asistente local de voz. Responde en español claro, con frases cortas. Evita respuestas largas porque serán leídas por TTS. Si no sabes algo, dilo de forma simple.
```

Reglas:

- Máximo 1–3 oraciones por turno.
- Evitar listas largas.
- Evitar Markdown en salida hablada.
- Confirmar acciones críticas.
- Si ASR transcribe algo dudoso, pedir aclaración breve.

---

## 13. Fase 8 — Fallback y tolerancia a fallos

El orquestador debe manejar:

1. `llama-server` disponible → usar `llama.cpp`.
2. Si falla el endpoint → fallback a Ollama si está instalado.
3. Si ambos fallan → respuesta local estática:
   - “Ahora mismo no puedo procesar la respuesta.”
   - “¿Puedes repetirlo?”
   - “Estoy iniciando el motor local.”

Pseudo-flujo:

```python
try:
    return llama_cpp_client.generate(text)
except Exception:
    try:
        return ollama_client.generate(text)
    except Exception:
        return "Ahora mismo no puedo procesar la respuesta."
```

---

## 14. Recomendaciones finales

- Usar `llama-server` como runtime principal del LLM.
- Mantener `llama-cli` solo para debug.
- No migrar toda la app de golpe; primero crear adapter y probar un flujo completo ASR → LLM → TTS.
- Mantener respuestas cortas para mejorar UX de voz.
- Medir siempre con audio real y transcripciones ASR reales, no solo prompts escritos.
- Probar `build`, `build-openblas` y `build-kleidiai`; elegir por datos.
- Conservar Ollama como backend alternativo durante transición, pero no como dependencia obligatoria de producción.
- En Raspberry Pi 5, priorizar estabilidad térmica y bajo consumo de RAM por encima de respuestas largas.
- No subir el modelo ni audios de prueba a GitHub; usar `.gitignore` para `models/`, `bench_results/` y grabaciones.

---

## 15. Checklist de cierre

```text
[ ] Modelo GGUF ubicado y versionado por checksum.
[ ] llama-cli responde correctamente.
[ ] llama-server responde en /v1/chat/completions.
[ ] Adapter Python creado.
[ ] Orquestador usa LLM_PROVIDER=llama_cpp.
[ ] Servicio systemd creado.
[ ] Benchmark CLI ejecutado.
[ ] Benchmark API ejecutado.
[ ] Prueba ASR → LLM → TTS ejecutada.
[ ] Fallback a Ollama o respuesta estática validado.
[ ] Logs y métricas guardadas.
```

---

## 16. Fuentes consultadas

- Liquid AI, documentación de despliegue con `llama.cpp`: https://docs.liquid.ai/deployment/on-device/llama-cpp
- Hugging Face, `LiquidAI/LFM2.5-350M-GGUF`: https://huggingface.co/LiquidAI/LFM2.5-350M-GGUF
- `llama.cpp` GitHub: https://github.com/ggml-org/llama.cpp
- `llama.cpp` build docs: https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md
- Raspberry Pi 5 especificaciones oficiales: https://www.raspberrypi.com/products/raspberry-pi-5/
