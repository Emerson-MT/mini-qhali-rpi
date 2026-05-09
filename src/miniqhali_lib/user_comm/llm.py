import json
import os
import re
import subprocess

import requests


class OllamaClient:
    def __init__(self, host=None, model_name=None, timeout=120):
        self.host = (host or os.getenv("OLLAMA_HOST") or "http://localhost:11434").rstrip("/")
        self.model_name = model_name or os.getenv("OLLAMA_MODEL") or "hf.co/LiquidAI/LFM2.5-350M-GGUF:Q4_K_M"
        self.timeout = timeout
        self.temperature = float(os.getenv("OLLAMA_TEMPERATURE", "0.1"))
        self.top_k = int(os.getenv("OLLAMA_TOP_K", "50"))
        self.repeat_penalty = float(os.getenv("OLLAMA_REPEAT_PENALTY", "1.05"))
        self.num_ctx = int(os.getenv("OLLAMA_NUM_CTX", "2048"))
        self.num_predict = int(os.getenv("OLLAMA_NUM_PREDICT", "192"))

    def chat(self, messages):
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": self.temperature,
                "top_k": self.top_k,
                "repeat_penalty": self.repeat_penalty,
                "num_ctx": self.num_ctx,
                "num_predict": self.num_predict,
            },
        }

        result = requests.post(
            f"{self.host}/api/chat",
            json=payload,
            timeout=self.timeout,
        )
        result.raise_for_status()
        data = result.json()
        return data.get("message", {}).get("content", "")


class LlamaCppClient:
    def __init__(self, base_url=None, api_key=None, model_alias=None, timeout=120):
        self.base_url = (base_url or os.getenv("LLAMA_BASE_URL") or "http://127.0.0.1:8080/v1").rstrip("/")
        self.api_key = api_key or os.getenv("LLAMA_API_KEY") or "local-key"
        self.model_alias = model_alias or os.getenv("LLAMA_MODEL_ALIAS") or "LFM2.5-350M-Q4_K_M.gguf"
        self.timeout = timeout
        self.temperature = float(os.getenv("LLAMA_TEMP", "0.2"))
        self.top_k = int(os.getenv("LLAMA_TOP_K", "40"))
        self.top_p = float(os.getenv("LLAMA_TOP_P", "0.9"))
        self.repeat_penalty = float(os.getenv("LLAMA_REPEAT_PENALTY", "1.08"))
        self.max_tokens = int(os.getenv("LLAMA_MAX_TOKENS", "192"))

    def chat(self, messages):
        payload = {
            "model": self.model_alias,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "repeat_penalty": self.repeat_penalty,
            "response_format": {"type": "json_object"},
            "stream": False,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        result = requests.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            headers=headers,
            timeout=self.timeout,
        )
        if result.status_code >= 400:
            raise RuntimeError(f"HTTP {result.status_code}: {result.text[:500]}")
        data = result.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not content:
            raise RuntimeError(f"Respuesta vacia de llama-server: {str(data)[:500]}")
        return content


class StaticFallbackClient:
    def chat(self, messages):
        return json.dumps(
            {
                "tipo_pose": "explicacion",
                "respuesta": "Ahora mismo no puedo procesar la respuesta. Por favor intenta nuevamente.",
            },
            ensure_ascii=False,
        )

class LargeLanguageModel:
    def __init__(
        self,
        model_name=None,
        ollama_host=None,
        provider=None,
        timeout=120,
        max_protocol_chars=None,
        tools=None,
    ):
        """
        Cliente LLM local para MiniQhali.

        Usa llama.cpp via llama-server como proveedor principal y conserva
        Ollama como fallback durante la transicion.
        """
        self.provider = provider or os.getenv("LLM_PROVIDER", "llama_cpp")
        self.timeout = timeout
        self.max_protocol_chars = max_protocol_chars or int(os.getenv("OLLAMA_MAX_PROTOCOL_CHARS", "8000"))
        self.tools = tools or []
        self.pdf_context = ""
        self.ollama_client = OllamaClient(host=ollama_host, model_name=model_name, timeout=timeout)
        self.llama_cpp_client = LlamaCppClient(timeout=timeout)
        self.static_client = StaticFallbackClient()

    def load_pdf(self, pdf_path):
        """Carga texto local del protocolo PDF para usarlo como contexto."""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"No se encontro el PDF en: {pdf_path}")

        print(f"📄 Cargando protocolo local desde: {pdf_path}")
        text = self._extract_pdf_text(pdf_path).strip()
        if not text:
            raise ValueError(f"No se pudo extraer texto del PDF: {pdf_path}")

        if len(text) > self.max_protocol_chars:
            text = text[: self.max_protocol_chars]
            print(f"⚠️ Protocolo truncado a {self.max_protocol_chars} caracteres para mantener baja latencia.")

        self.pdf_context = text
        print("✅ Contexto PDF local listo.")
        return text

    # Compatibilidad con el nombre anterior usado por MiniQhaliRobot.
    upload_pdf = load_pdf

    def _extract_pdf_text(self, pdf_path):
        """
        Usa pdftotext si esta instalado. Si no, intenta una extraccion basica
        con strings para no bloquear el arranque por falta de una dependencia.
        """
        try:
            result = subprocess.run(
                ["pdftotext", "-layout", pdf_path, "-"],
                check=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.stdout
        except (FileNotFoundError, subprocess.SubprocessError):
            pass

        try:
            result = subprocess.run(
                ["strings", pdf_path],
                check=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.stdout
        except (FileNotFoundError, subprocess.SubprocessError):
            return ""

    def generate_robot_reply(self, user_input, measurement_context):
        """Genera una respuesta estructurada para ejecutar pose y TTS localmente."""
        system_prompt = self._build_system_prompt(measurement_context)
        response = self._chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
            ]
        )
        return self._parse_robot_reply(response)

    def _build_system_prompt(self, measurement_context):
        return f"""
Eres MiniQhali, una robot enfermera de la PUCP que ayuda a pacientes con sus signos vitales.
Responde siempre en español, con frases breves, claras y aptas para hablar en voz alta.
Usa primero el protocolo incluido. Si el protocolo no contiene la respuesta, dilo con cautela y da una orientacion general; no inventes datos medicos.
No busques ni menciones internet: estas funcionando localmente.

Contexto actual del robot:
{measurement_context}

Protocolo MiniQhali:
{self.pdf_context}

Debes responder solo JSON valido, sin markdown, con esta forma exacta:
{{"tipo_pose":"explicacion","respuesta":"texto para el usuario"}}

Reglas:
- tipo_pose solo puede ser "explicacion" o "feedback".
- Usa "feedback" para exito, resultado, felicitacion o cierre.
- Usa "explicacion" para guia, informacion, preguntas y aclaraciones.
- La respuesta debe ser corta: maximo 2 oraciones.
""".strip()

    def _chat(self, messages):
        errors = []
        for name, client in self._provider_chain():
            try:
                if name != self.provider:
                    print(f"⚠️ LLM usando fallback: {name}")
                return client.chat(messages)
            except Exception as e:
                errors.append(f"{name}: {e}")
                print(f"⚠️ LLM provider {name} falló: {e}")

        print("❌ Todos los proveedores LLM fallaron: " + " | ".join(errors))
        return self.static_client.chat(messages)

    def _provider_chain(self):
        if self.provider == "llama_cpp":
            return [
                ("llama_cpp", self.llama_cpp_client),
                ("ollama", self.ollama_client),
                ("static", self.static_client),
            ]
        if self.provider == "ollama":
            return [
                ("ollama", self.ollama_client),
                ("static", self.static_client),
            ]
        return [("static", self.static_client)]

    def _parse_robot_reply(self, content):
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            data = self._load_json_object(content)
        if not data:
            data = self._extract_robot_reply_fields(content)

        tipo_pose = data.get("tipo_pose", "explicacion")
        if tipo_pose not in {"explicacion", "feedback"}:
            tipo_pose = "explicacion"

        respuesta = str(data.get("respuesta", "")).strip()
        if not respuesta:
            respuesta = "Perdon, no pude preparar una respuesta clara. Por favor repite tu pregunta."

        return {"tipo_pose": tipo_pose, "respuesta": respuesta}

    @staticmethod
    def _load_json_object(content):
        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return {}
        try:
            return json.loads(content[start : end + 1])
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def _extract_robot_reply_fields(content):
        data = {}
        tipo_match = re.search(r'"tipo_pose"\s*:\s*"([^"]+)"', content)
        respuesta_match = re.search(r'"respuesta"\s*:\s*"(.+?)"\s*"?\s*}', content, re.DOTALL)
        if tipo_match:
            data["tipo_pose"] = tipo_match.group(1)
        if respuesta_match:
            data["respuesta"] = respuesta_match.group(1).strip().rstrip('"')
        return data

    def generate_response(self, user_input, system_instruction):
        """Metodo de compatibilidad para llamadas antiguas."""
        return self._chat(
            [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_input},
            ]
        )
