import os
import shutil
import sys
import tempfile
import subprocess
import hashlib
import re

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
        Usa eSpeak-NG local por defecto y Piper como fallback de voz neural.
        """
        self.backend = backend or os.getenv("TTS_BACKEND", "espeak")
        self.voice = voice or os.getenv("ESPEAK_VOICE", "es-la+f4")
        self.rate = rate or os.getenv("ESPEAK_SPEED", "145")
        self.espeak_pitch = os.getenv("ESPEAK_PITCH", "95")
        self.espeak_amp = os.getenv("ESPEAK_AMP", "145")
        self.espeak_gap = os.getenv("ESPEAK_GAP", "4")
        self.sample_rate = os.getenv("TTS_SAMPLE_RATE", "22050")
        self.cache_enabled = os.getenv("TTS_CACHE_ENABLED", "true").lower() == "true"
        self.cache_dir = os.getenv("TTS_CACHE_DIR", "/tmp/miniqhali/cache/tts")
        self.sox_enabled = os.getenv("TTS_SOX_ENABLED", "true").lower() == "true"
        self.sox_pitch_cents = os.getenv("TTS_SOX_PITCH_CENTS", "650")
        self.sox_tempo = os.getenv("TTS_SOX_TEMPO", "1.30")
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
        v = voice or self.voice
        if not self._espeak_voice_available(v):
            fallback = os.getenv("ESPEAK_FALLBACK_VOICE", "es+f3")
            print(f"⚠️ Voz eSpeak {v} no disponible. Usando {fallback}.")
            v = fallback

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as raw_wav:
            raw_path = raw_wav.name

        try:
            self._run_espeak(text, raw_path, v, rate)
            if self.sox_enabled and shutil.which("sox"):
                subprocess.run(
                    [
                        "sox",
                        raw_path,
                        "-r",
                        str(self.sample_rate),
                        "-c",
                        "1",
                        wav_path,
                        "gain",
                        "-n",
                        "-3",
                        "pitch",
                        str(self.sox_pitch_cents),
                        "tempo",
                        str(self.sox_tempo),
                        "highpass",
                        "80",
                        "lowpass",
                        "7600",
                    ],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=self.max_generation_seconds,
                )
            else:
                shutil.copyfile(raw_path, wav_path)
        finally:
            if os.path.exists(raw_path):
                os.remove(raw_path)

    @staticmethod
    def _espeak_voice_available(voice):
        return subprocess.run(
            ["espeak-ng", "-v", voice, "-q", "test"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode == 0

    def _run_espeak(self, text, wav_path, voice, rate=None):
        subprocess.run(
            [
                "espeak-ng",
                "-v",
                voice,
                "-s",
                str(rate or self.rate),
                "-p",
                str(self.espeak_pitch),
                "-a",
                str(self.espeak_amp),
                "-g",
                str(self.espeak_gap),
                "-k",
                "18",
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

    def _normalize_text(self, text):
        replacements = {
            "MiniQhali": "Mini Qhali",
            "mini-qhali": "Mini Qhali",
            "ASR": "reconocimiento de voz",
            "TTS": "texto a voz",
            "API": "A P I",
            "OK": "De acuerdo",
            "repo": "repositorio",
        }
        normalized = text
        for src, dst in replacements.items():
            normalized = normalized.replace(src, dst)
        normalized = re.sub(r"https?://\S+", "enlace", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    def _cache_path(self, backend, text, voice=None, rate=None):
        key = "|".join(
            [
                backend,
                voice or self.voice,
                str(rate or self.rate),
                str(self.espeak_pitch),
                str(self.espeak_amp),
                str(self.espeak_gap),
                str(self.sox_pitch_cents),
                str(self.sox_tempo),
                text,
            ]
        )
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        cache_dir = os.path.join(self.cache_dir, backend)
        os.makedirs(cache_dir, exist_ok=True)
        return os.path.join(cache_dir, f"{digest}.wav")

    def _generate_cached(self, backend, text, wav_path, voice=None, rate=None):
        if backend == "espeak":
            self._generate_with_espeak(text, wav_path, voice, rate)
        elif backend == "piper":
            self._generate_with_piper(text, wav_path)
        else:
            raise ValueError(f"Backend TTS no soportado: {backend}")

    def _synthesize_to_file(self, backend, text, voice=None, rate=None):
        if self.cache_enabled:
            cached_path = self._cache_path(backend, text, voice, rate)
            if os.path.exists(cached_path) and os.path.getsize(cached_path) > 0:
                return cached_path, True
            self._generate_cached(backend, text, cached_path, voice, rate)
            return cached_path, False

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f_wav:
            wav_path = f_wav.name
        self._generate_cached(backend, text, wav_path, voice, rate)
        return wav_path, False

    def _generate_and_play(self, text, voice=None, rate=None):
        normalized_text = self._normalize_text(text)
        generated_temp = None

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f_wav:
            fallback_path = f_wav.name

        try:
            if self.backend == "espeak":
                try:
                    print(f"🔊 Generando voz local con eSpeak-NG ({voice or self.voice})...")
                    wav_path, cached = self._synthesize_to_file("espeak", normalized_text, voice, rate)
                    print("♻️ Audio TTS cacheado." if cached else "✅ Audio TTS generado.")
                except Exception as espeak_error:
                    print(f"⚠️ eSpeak-NG falló: {espeak_error}")
                    print("🔊 Usando fallback Piper...")
                    wav_path, cached = self._synthesize_to_file("piper", normalized_text)
                    print("♻️ Audio TTS cacheado." if cached else "✅ Audio TTS generado.")
            else:
                try:
                    print("🔊 Generando voz local con Piper...")
                    wav_path, cached = self._synthesize_to_file("piper", normalized_text)
                    print("♻️ Audio TTS cacheado." if cached else "✅ Audio TTS generado.")
                except Exception as piper_error:
                    print(f"⚠️ Piper no disponible o falló: {piper_error}")
                    print(f"🔊 Usando fallback eSpeak-NG ({voice or self.voice})...")
                    wav_path, cached = self._synthesize_to_file("espeak", normalized_text, voice, rate)
                    print("♻️ Audio TTS cacheado." if cached else "✅ Audio TTS generado.")

            generated_temp = wav_path if not self.cache_enabled else None

            self._play_audio(wav_path)
        except Exception as e:
            print(f"❌ Error al reproducir audio TTS: {e}")
        finally:
            if os.path.exists(fallback_path):
                os.remove(fallback_path)
            if generated_temp and os.path.exists(generated_temp):
                os.remove(generated_temp)

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
