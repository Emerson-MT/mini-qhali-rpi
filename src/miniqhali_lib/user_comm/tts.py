import os
import shutil
import sys
import tempfile
import subprocess

class TextToSpeech:
    def __init__(
        self,
        backend=None,
        voice=None,
        rate=None,
        volume_boost="1.0",
        piper_model=None,
        piper_config=None,
        piper_bin=None,
        max_generation_seconds=12,
    ):
        """
        Clase encargada de la síntesis de voz (TTS) para MiniQhali.
        Usa Piper local por defecto y eSpeak-NG como fallback ultrarrapido.
        """
        self.backend = backend or os.getenv("TTS_BACKEND", "piper")
        self.voice = voice or os.getenv("ESPEAK_VOICE", "es-la")
        self.rate = rate or os.getenv("ESPEAK_SPEED", "170")
        self.piper_model = piper_model or os.getenv(
            "PIPER_MODEL",
            os.path.expanduser("~/models/piper/es_ES-davefx-medium/es_ES-davefx-medium.onnx"),
        )
        self.piper_config = piper_config or os.getenv(
            "PIPER_CONFIG",
            os.path.expanduser("~/models/piper/es_ES-davefx-medium/es_ES-davefx-medium.onnx.json"),
        )
        self.piper_bin = piper_bin or os.getenv("PIPER_BIN") or shutil.which("piper") or self._venv_piper_bin()
        self.max_generation_seconds = max_generation_seconds
        # volume_boost: factor de ganancia digital (ej. 4.0 para cuadruplicar potencia)
        self.volume_boost = volume_boost 

    @staticmethod
    def _venv_piper_bin():
        piper_path = os.path.join(os.path.dirname(sys.executable), "piper")
        if os.path.exists(piper_path) and os.access(piper_path, os.X_OK):
            return piper_path
        return None

    def _generate_with_piper(self, text, wav_path):
        if not self.piper_bin:
            raise FileNotFoundError("No se encontro el binario piper. Define PIPER_BIN o activa el venv.")
        if not os.path.exists(self.piper_model):
            raise FileNotFoundError(f"No se encontro el modelo Piper: {self.piper_model}")
        if not os.path.exists(self.piper_config):
            raise FileNotFoundError(f"No se encontro la config Piper: {self.piper_config}")

        subprocess.run(
            [
                self.piper_bin,
                "--model",
                self.piper_model,
                "--config",
                self.piper_config,
                "--output_file",
                wav_path,
            ],
            input=text,
            text=True,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=self.max_generation_seconds,
        )

    def _generate_with_espeak(self, text, wav_path, voice=None, rate=None):
        subprocess.run(
            [
                "espeak-ng",
                "-v",
                voice or self.voice,
                "-s",
                str(rate or self.rate),
                "-w",
                wav_path,
                text,
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=self.max_generation_seconds,
        )

    def _play_audio(self, wav_path):
        subprocess.run(
            [
                "ffplay",
                "-nodisp",
                "-autoexit",
                "-loglevel",
                "quiet",
                "-af",
                f"volume={self.volume_boost}",
                wav_path,
            ],
            stderr=subprocess.DEVNULL,
        )

    def _generate_and_play(self, text, voice=None, rate=None):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f_wav:
            wav_path = f_wav.name

        try:
            if self.backend == "espeak":
                print(f"🔊 Generando voz local con eSpeak-NG ({voice or self.voice})...")
                self._generate_with_espeak(text, wav_path, voice, rate)
            else:
                try:
                    print("🔊 Generando voz local con Piper...")
                    self._generate_with_piper(text, wav_path)
                except Exception as piper_error:
                    print(f"⚠️ Piper no disponible o falló: {piper_error}")
                    print(f"🔊 Usando fallback eSpeak-NG ({voice or self.voice})...")
                    self._generate_with_espeak(text, wav_path, voice, rate)

            self._play_audio(wav_path)
        except Exception as e:
            print(f"❌ Error al reproducir audio TTS: {e}")
        finally:
            if os.path.exists(wav_path):
                os.remove(wav_path)

    def speak(self, text, voice=None, rate=None):
        """
        Sintetiza y reproduce el texto proporcionado.
        Permite sobrescribir la voz y la velocidad de forma puntual.
        """
        v = voice or self.voice
        r = rate or self.rate
        
        # Imprimir en consola para seguimiento
        print(f"🤖 MiniQhali: {text}\n")
        self._generate_and_play(text, v, r)

    def set_voice(self, new_voice):
        """Cambia la voz por defecto (ej. para cambiar de personaje o idioma)."""
        self.voice = new_voice
