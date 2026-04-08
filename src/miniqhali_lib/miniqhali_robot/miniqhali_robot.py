import os
import json
import queue
import asyncio
import subprocess
import tempfile
import numpy as np
import pyaudio
import serial
from vosk import Model, KaldiRecognizer
import edge_tts
from google import genai
from langsmith import wrappers
from ctypes import CFUNCTYPE, c_char_p, c_int, cdll
import random

# --- Truco para silenciar ALSA ---
def py_error_handler(filename, line, function, err, fmt):
    None

ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)
c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)

def silence_alsa():
    try:
        asound = cdll.LoadLibrary('libasound.so.2')
        asound.snd_lib_error_set_handler(c_error_handler)
    except:
        pass # Si falla, simplemente sigue normal
# --------------------------------

class MiniQhaliRobot:
    def __init__(self, google_api_key, vosk_model_path, device_name, pdf_path, poses_path):
        # --- Configuración de LangSmith (Extraído de tu código) ---
        os.environ["LANGSMITH_API_KEY"] = "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"
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGSMITH_PROJECT"] = "MiniQhali-Motor-Control"
        os.environ["GOOGLE_API_KEY"] = google_api_key
        
        # --- Configuración Serial (ESP32) ---
        try:
            self.ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
        except Exception:
            print("⚠️ Advertencia: ESP32 no detectado. Modo simulación activo.")
            self.ser = None

        # --- Audio & STT ---
        self.rate = 16000
        self.channels = 6
        self.chunk = 1024
        self.device_index = self._find_device(device_name)
        self.stt_model = Model(vosk_model_path)
        self.rec = KaldiRecognizer(self.stt_model, self.rate)

        # --- LLM Gemini con Wrapper de LangSmith ---
        gemini_client = genai.Client()
        # PRIMERO: Definir el cliente
        self.client = wrappers.wrap_gemini(gemini_client)
        self.model_name = "gemini-2.5-flash" 

        # SEGUNDO: Subir el PDF (ahora que self.client existe)
        self.pdf_file = self._upload_context_pdf(pdf_path)

        # TERCERO: Definir las herramientas
        self.tools = [
            self.iniciar_mediciones_signos_vitales,
            self.ejecutar_pose_robot
        ]

        # --- TTS ---
        self.voice = "es-MX-DaliaNeural" 
        
        # --- Poses ---
        self.poses = self._load_poses(poses_path)

    def _find_device(self, name_hint):
        p = pyaudio.PyAudio()
        target_idx = None
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if name_hint.lower() in info['name'].lower():
                target_idx = i
                break
        p.terminate()
        return target_idx
    
    def _upload_context_pdf(self, pdf_path):
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"No se encontró el PDF en: {pdf_path}")
            
        print(f"📄 Subiendo protocolo {pdf_path} a Gemini...")
        
        # Añadimos el mime_type explícitamente
        pdf_file = self.client.files.upload(
            file=pdf_path,
            config={'mime_type': 'application/pdf'} # <-- Esto ayuda a Gemini a saber cómo procesarlo
        )
        
        import time
        while pdf_file.state.name == "PROCESSING":
            print("Esperando procesamiento de PDF...", end="\r", flush=True)
            time.sleep(2)
            pdf_file = self.client.files.get(name=pdf_file.name)
        
        # Si el archivo llega aquí y da error de páginas, es el archivo físico
        if pdf_file.state.name == "FAILED":
             raise Exception(f"Fallo en servidor: {pdf_file.error.message}")

        print(f"\n✅ Contexto PDF listo.")
        return pdf_file
    
    def _load_poses(self, poses_path):
        try:
            with open(poses_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error cargando poses.json: {e}")
            return {"explicacion": [[90]*6], "feedback": [[90]*6]}

    def ejecutar_pose_robot(self, tipo_pose: str):
        """
        Mueve los 6 servos del robot según la intención del mensaje.
        tipo_pose: Puede ser 'explicacion' (si está respondiendo dudas o guiando) 
                   o 'feedback' (si está dando resultados o confirmando éxito).
        """
        if tipo_pose not in self.poses:
            tipo_pose = "explicacion" # Default
        
        # Selección aleatoria de uno de los arreglos (listas de 6 ángulos)
        angulos = random.choice(self.poses[tipo_pose])
        
        # Formatear comando para ESP32: P:ang1,ang2,ang3,ang4,ang5,ang6\n
        str_angulos = ",".join(map(str, angulos))
        comando = f"P:{str_angulos}\n"
        
        if self.ser:
            self.ser.write(comando.encode())
            print(f"📤 Enviando Pose ({tipo_pose}): {comando.strip()}")
            return f"Movimiento de {tipo_pose} ejecutado con ángulos: {angulos}"
        
        return f"[Simulado] Pose de {tipo_pose}: {angulos}"

    async def _speak_async(self, text):
        communicate = edge_tts.Communicate(text, self.voice)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            await communicate.save(f.name)
            subprocess.run([
                "ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", 
                "-af", "volume=4.0", f.name
            ], stderr=subprocess.DEVNULL)
        if os.path.exists(f.name): os.remove(f.name)

    def speak(self, text):
        print(f"🤖 MiniQhali: {text}")
        asyncio.run(self._speak_async(text))

    def listen(self):
        q = queue.Queue()
        def callback(in_data, frame_count, time_info, status):
            samples = np.frombuffer(in_data, dtype=np.int16).reshape(-1, self.channels)
            q.put(samples[:, 0].tobytes())
            return (None, pyaudio.paContinue)

        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=self.channels, rate=self.rate,
                        input=True, input_device_index=self.device_index,
                        frames_per_buffer=self.chunk, stream_callback=callback)
        stream.start_stream()
        print("🎤 Escuchando...")
        try:
            while True:
                data = q.get()
                if self.rec.AcceptWaveform(data):
                    res = json.loads(self.rec.Result())
                    if res["text"]:
                        stream.stop_stream()
                        return res["text"]
        finally:
            stream.close()
            p.terminate()

    def iniciar_mediciones_signos_vitales(self):
        """Activa la secuencia de sensores sincronizada con el formulario del celular."""
        print("\n[TOOL] Sincronizando con formulario móvil...")
        # Aquí se enviará la señal al ESP32 para que los sensores empiecen a leer
        # se levante habilite el formilario en la pantalla del celular.
        return "Sensores activados. Por favor, sigue las instrucciones en la pantalla del celular para ver tus resultados de BPM, SpO2 y Temperatura."

    def run(self):
        print("\n🚀 MiniQhali (Modo Guía de Formulario) iniciado.")
        self.ejecutar_pose_robot("explicacion")
        self.speak("¡Hola! Soy MiniQhali. Por favor, usa el formulario en el celular que sostengo para iniciar tu registro y mediciones.")

        try:
            while True:
                user_input = self.listen()
                if not user_input or user_input.strip() == "": continue
                
                print(f"👤 Usuario: {user_input}")

                # PROMPT ACTUALIZADO: Instrucciones de no pedir datos uno por uno
                prompt_contents = [
                    self.pdf_file,
                    f"""
                    Eres MiniQhali, una robot enfermera que ayuda a los pacientes a tomar mediciones de signos vitales antes de
                    que pasen a su cita con el doctor.
                    INSTRUCCIÓN DE PENSAMIENTO MOTOR:
                    Antes de responder, sigue este proceso mental interno:
                    1. Determina el contenido del texto de respuesta basándote en el input del usuario: '{user_input}'.
                    2. Analiza el tono de ese texto resultante:
                    - Si es informativo, de guía o instructivo -> Elige tipo_pose='explicacion'.
                    - Si es de cierre, éxito, alegría o resultado -> Elige tipo_pose='feedback'.
                    3. Identifica si la situación requiere activar sensores (iniciar_mediciones_signos_vitales).

                    FORMATO DE RESPUESTA OBLIGATORIO (Secuencia de Partes):
                    Tu respuesta final DEBE enviar las partes en este orden estricto para la ejecución del hardware:
                    - Parte 1: Llamada a 'ejecutar_pose_robot' (con el tipo_pose decidido en el paso 2).
                    - Parte 2: (Si aplica) Llamada a 'iniciar_mediciones_signos_vitales'.
                    - Parte 3: El texto de respuesta para el usuario.
                    """
                ]

                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt_contents,
                    config={"tools": self.tools}
                )

                if not response.candidates or not response.candidates[0].content.parts:
                    print("⚠️ Gemini no devolvió partes en la respuesta.")
                    continue

                # Procesamiento de múltiples partes (Gemini puede querer mover y hablar a la vez)
                for part in response.candidates[0].content.parts:
                    if part.function_call:
                        fn = part.function_call
                        if fn.name == "ejecutar_pose_robot":
                            self.ejecutar_pose_robot(**fn.args)
                        elif fn.name == "iniciar_mediciones_signos_vitales":
                            res = self.iniciar_mediciones_signos_vitales()
                            # Al terminar mediciones, forzamos una pose de feedback
                            self.ejecutar_pose_robot("feedback")
                            self.speak(res)
                    elif part.text:
                        self.speak(part.text)

        except KeyboardInterrupt:
            print("\nPrograma finalizado.")