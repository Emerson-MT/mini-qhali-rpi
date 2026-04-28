import os
import tempfile
import asyncio
import edge_tts
import subprocess

class TextToSpeech:
    def __init__(self, voice="es-MX-DaliaNeural", rate="+0%", volume_boost="1.0"):
        """
        Clase encargada de la síntesis de voz (TTS) para MiniQhali.
        Utiliza Edge TTS para generar audio de alta calidad y ffplay para la reproducción.
        """
        self.voice = voice
        self.rate = rate
        # volume_boost: factor de ganancia digital (ej. 4.0 para cuadruplicar potencia)
        self.volume_boost = volume_boost 

    async def _generate_and_play(self, text, voice, rate):
        """Método interno asíncrono para generar y reproducir el audio."""
        communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)

        # Crear un archivo temporal para el audio generado
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f_mp3:
            mp3_path = f_mp3.name

        try:
            # Guardar el flujo de audio en el archivo temporal
            await communicate.save(mp3_path)

            print(f"🔊 Generando voz ({voice}) y enviando a parlante...")
            
            # Ejecutar ffplay para reproducir el archivo. 
            # Se usa el filtro 'volume' para compensar la potencia del parlante Bluetooth.
            subprocess.run([
                "ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet",
                "-af", f"volume={self.volume_boost}", mp3_path
            ], stderr=subprocess.DEVNULL)

        except Exception as e:
            print(f"❌ Error al reproducir audio TTS: {e}")
        finally:
            # Asegurar la eliminación del archivo temporal
            if os.path.exists(mp3_path):
                os.remove(mp3_path)

    def speak(self, text, voice=None, rate=None):
        """
        Sintetiza y reproduce el texto proporcionado.
        Permite sobrescribir la voz y la velocidad de forma puntual.
        """
        v = voice or self.voice
        r = rate or self.rate
        
        # Imprimir en consola para seguimiento
        print(f"🤖 MiniQhali: {text}\n")
        
        # Ejecutar la corrutina asíncrona de forma síncrona para el flujo del robot
        asyncio.run(self._generate_and_play(text, v, r))

    def set_voice(self, new_voice):
        """Cambia la voz por defecto (ej. para cambiar de personaje o idioma)."""
        self.voice = new_voice