import queue
import sys
import json
import pyaudio
import numpy as np
from vosk import Model, KaldiRecognizer

class SpeechToText:
    def __init__(self, model_path, device_name="ReSpeaker", rate=16000, channels=6, chunk=1024):
        """
        Clase especializada en el reconocimiento de voz usando Vosk y la matriz de 
        micrófonos ReSpeaker de MiniQhali.
        """
        self.rate = rate
        self.channels = channels
        self.chunk = chunk
        
        # Intentar encontrar el índice del dispositivo de audio
        self.device_index = self.find_device(device_name)
        if self.device_index is None:
            print(f"⚠️ Advertencia: No se encontró '{device_name}'. Usando dispositivo por defecto.")
            # Si no encuentra el ReSpeaker, intentamos con el default para no romper el programa
            self.device_index = None 

        # Atributos para el modelo
        self.stt_model = None
        self.stt_recognizer = None
        self.load_stt_model(model_path)

    def load_stt_model(self, model_path):
        """Carga el modelo de lenguaje de Vosk en memoria."""
        try:
            print(f"⏳ Cargando modelo de Vosk desde: {model_path}...")
            self.stt_model = Model(model_path)
            self.stt_recognizer = KaldiRecognizer(self.stt_model, self.rate)
            print("✅ Modelo STT cargado exitosamente.")
        except Exception as e:
            print(f"❌ Error crítico al cargar el modelo STT: {e}")
            raise

    @staticmethod
    def find_device(name_hint="ReSpeaker"):
        """Busca el índice del hardware de audio basado en un nombre (hint)."""
        p = pyaudio.PyAudio()
        device_index = None

        print("🔍 Buscando hardware de audio...")
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            # Imprimimos para debug en la terminal de la Raspberry Pi
            # print(f"{i}: {info['name']} ({info['maxInputChannels']} canales)") 
            if name_hint.lower() in info['name'].lower():
                device_index = i
                break
        p.terminate()
        return device_index

    def listen(self):
        """
        Inicia el flujo de audio, procesa los canales y retorna el texto reconocido.
        """
        q = queue.Queue()

        def callback(in_data, frame_count, time_info, status):
            if status:
                print(status, file=sys.stderr)

            # Convertir bytes del buffer a array de numpy para manipular canales
            samples = np.frombuffer(in_data, dtype=np.int16)
            
            # El ReSpeaker entrega 6 canales. Redimensionamos el array.
            if self.channels > 1:
                samples = samples.reshape(-1, self.channels)
                # Tomamos solo el canal 0 (donde suele estar la señal procesada/monoaural)
                selected_channel = samples[:, 0]
            else:
                selected_channel = samples

            # Volver a convertir a bytes para que Vosk lo procese (formato mono int16)
            q.put(selected_channel.tobytes())
            return (None, pyaudio.paContinue)

        p = pyaudio.PyAudio()
        
        try:
            # Abrir el stream con el dispositivo indexado
            stream = p.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.chunk,
                stream_callback=callback
            )

            print("🎤 MiniQhali escuchando...")
            stream.start_stream()

            while True:
                try:
                    # Obtenemos los datos del callback mediante la cola (queue)
                    data = q.get(timeout=0.2)
                    if self.stt_recognizer.AcceptWaveform(data):
                        result = self.stt_recognizer.Result()
                        text = json.loads(result).get("text", "")
                        if text:
                            return text
                except queue.Empty:
                    continue

        except KeyboardInterrupt:
            # No retornamos texto, lanzamos la excepción hacia arriba (al Robot)
            raise 
        except Exception as e:
            print(f"❌ Error en audio: {e}")
            return None
        finally:
            # Limpieza profunda
            if stream:
                stream.stop_stream()
                stream.close()
            p.terminate()