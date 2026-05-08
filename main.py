import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# 1. Configuración de Rutas del Proyecto
# Determinamos la ruta base para que los archivos siempre se encuentren
BASE_DIR = Path(__file__).resolve().parent
SRC_PATH = BASE_DIR / "src"
sys.path.append(str(SRC_PATH))

from miniqhali_lib import MiniQhaliRobot

# --- Configuración de Parámetros ---

# Carga el archivo .env
load_dotenv()

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "hf.co/LiquidAI/LFM2.5-350M-GGUF:Q4_K_M")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Rutas relativas a la carpeta del proyecto
VOSK_MODEL_PATH = SRC_PATH / "miniqhali_lib/models/vosk-model-small-es-0.42" 
PDF_PATH = SRC_PATH / "miniqhali_lib/files/protocolo_miniqhali.pdf"
POSES_PATH = SRC_PATH / "miniqhali_lib/files/poses.json"

def main():
    print("--- 🤖 Iniciando Sistema de Control MiniQhali ---")
    
    archivos_criticos = [VOSK_MODEL_PATH, PDF_PATH, POSES_PATH]
    for ruta in archivos_criticos:
        if not ruta.exists():
            print(f"❌ Error: No se encontró el recurso crítico en: {ruta}")
            return

    # 2. Inicialización del Robot
    # Aquí se disparan los hilos de Socket.IO, Serial y carga de PDF
    try:
        robot = MiniQhaliRobot(
            vosk_model_path=str(VOSK_MODEL_PATH),
            device_name="ReSpeaker", # Revisa que el nombre coincida en tu SO
            pdf_path=str(PDF_PATH),
            poses_path=str(POSES_PATH),
            ollama_model=OLLAMA_MODEL,
            ollama_host=OLLAMA_HOST,
        )

        print("✅ MiniQhali inicializada y conectada al Servidor.")
        print("💡 El robot reaccionará automáticamente a los pasos del formulario.")
        
        # 3. Ejecución del Bucle Principal
        # Gestiona la lectura de sensores (si is_measuring es True) e interacción LLM
        robot.run()

    except ConnectionError as ce:
        print(f"❌ Error de conexión (Servidor/Socket): {ce}")
    except Exception as e:
        print(f"⚠️ Ocurrió un error inesperado: {e}")
    finally:
        print("\n👋 Sistema MiniQhali apagado.")

if __name__ == "__main__":
    main()
