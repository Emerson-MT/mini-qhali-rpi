import os
import json
import queue
import asyncio
import subprocess
import tempfile
import numpy as np
import pyaudio
from vosk import Model, KaldiRecognizer
import edge_tts

# --- Importaciones de LangChain ---
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain

class MiniQhaliRobot:
    def __init__(self, google_api_key, vosk_model_path, device_name="ReSpeaker"):
        # --- Configuración de Trazado (LangSmith) ---
        os.environ["LANGSMITH_API_KEY"] = "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"
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGSMITH_PROJECT"] = "MiniQhali-LangChain-Chat"
        
        # --- Configuración de LangChain con Gemini ---
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=google_api_key,
            temperature=0.7
        )
        
        # Memoria de LangChain para recordar la conversación
        self.memory = ConversationBufferMemory()
        
        # La cadena (Chain) que une el modelo con la memoria
        self.conversation = ConversationChain(
            llm=self.llm,
            memory=self.memory,
            verbose=False # Puedes ponerlo en True para ver el prompt interno en consola
        )

        # --- Audio & STT (ReSpeaker + Vosk) ---
        self.rate = 16000
        self.channels = 6
        self.chunk = 1024
        self.device_index = self._find_device(device_name)
        self.stt_model = Model(vosk_model_path)
        self.rec = KaldiRecognizer(self.stt_model, self.rate)

        # --- TTS (EdgeTTS) ---
        self.voice = "es-PE-AlexNeural"

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

    async def _speak_async(self, text):
        communicate = edge_tts.Communicate(text, self.voice)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            await communicate.save(f.name)
            subprocess.run([
                "ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", 
                "-af", "volume=2.0", f.name
            ], stderr=subprocess.DEVNULL)
        if os.path.exists(f.name): os.remove(f.name)

    def speak(self, text):
        print(f"🤖 MiniQhali: {text}")
        asyncio.run(self._speak_async(text))

    def listen(self):
        q = queue.Queue()
        def callback(in_data, frame_count, time_info, status):
            samples = np.frombuffer(in_data, dtype=np.int16).reshape(-1, self.channels)
            q.put(samples[:, 0].tobytes()) # Canal 0 procesado
            return (None, pyaudio.paContinue)

        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=self.channels, rate=self.rate,
                        input=True, input_device_index=self.device_index,
                        frames_per_buffer=self.chunk, stream_callback=callback)
        stream.start_stream()
        print("\n🎤 Escuchando...")
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

    def run(self):
        print("🚀 MiniQhali con LangChain activo. (Ctrl+C para salir)")
        # Mensaje inicial de sistema opcional
        self.memory.chat_memory.add_message(SystemMessage(content="Eres MiniQhali, un asistente robótico de salud amable y servicial."))
        
        try:
            while True:
                user_input = self.listen()
                print(f"👤 Usuario: {user_input}")

                # LangChain procesa el input, revisa la memoria y genera la respuesta
                response = self.conversation.predict(input=user_input)
                
                self.speak(response)
        except KeyboardInterrupt:
            print("\nCerrando sesión de MiniQhali...")