import json
import os
import subprocess

import requests

class LargeLanguageModel:
    def __init__(
        self,
        model_name=None,
        ollama_host=None,
        timeout=120,
        max_protocol_chars=None,
        tools=None,
    ):
        """
        Cliente LLM local para MiniQhali usando Ollama.

        El modelo por defecto es pequeño para Raspberry Pi 5 y se puede cambiar
        con OLLAMA_MODEL sin tocar el codigo.
        """
        self.ollama_host = (ollama_host or os.getenv("OLLAMA_HOST") or "http://localhost:11434").rstrip("/")
        self.model_name = model_name or os.getenv("OLLAMA_MODEL") or "hf.co/LiquidAI/LFM2.5-350M-GGUF:Q4_K_M"
        self.timeout = timeout
        self.max_protocol_chars = max_protocol_chars or int(os.getenv("OLLAMA_MAX_PROTOCOL_CHARS", "8000"))
        self.tools = tools or []
        self.pdf_context = ""

        self.temperature = float(os.getenv("OLLAMA_TEMPERATURE", "0.1"))
        self.top_k = int(os.getenv("OLLAMA_TOP_K", "50"))
        self.repeat_penalty = float(os.getenv("OLLAMA_REPEAT_PENALTY", "1.05"))
        self.num_ctx = int(os.getenv("OLLAMA_NUM_CTX", "2048"))
        self.num_predict = int(os.getenv("OLLAMA_NUM_PREDICT", "192"))

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
            f"{self.ollama_host}/api/chat",
            json=payload,
            timeout=self.timeout,
        )
        result.raise_for_status()
        data = result.json()
        return data.get("message", {}).get("content", "")

    def _parse_robot_reply(self, content):
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            data = self._load_json_object(content)

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

    def generate_response(self, user_input, system_instruction):
        """Metodo de compatibilidad para llamadas antiguas."""
        return self._chat(
            [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_input},
            ]
        )
