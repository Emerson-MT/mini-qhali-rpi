import sys
import os

# Agregamos la carpeta 'src' al sistema de rutas
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from miniqhali_lib import MiniQhaliRobot

# --- Configuración ---
GOOGLE_API_KEY = "AIzaSyBaconophlskoUCOuV2Q3iTjUQvXMQnlP8"
VOSK_MODEL_PATH = "src/miniqhali_lib/models/vosk-model-small-es-0.42" 
PDF_PATH = "src/miniqhali_lib/files/protocolo_miniqhali.pdf"
POSES_PATH = "src/miniqhali_lib/files/poses.json"


def main():
    # Inicializamos el robot
    robot = MiniQhaliRobot(
        google_api_key=GOOGLE_API_KEY, 
        vosk_model_path=VOSK_MODEL_PATH,
        device_name="ReSpeaker",
        pdf_path = PDF_PATH,
        poses_path = POSES_PATH
    )

    try:
        # Iniciamos el bucle infinito de escucha y respuesta
        robot.run()
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")

if __name__ == "__main__":
    main()