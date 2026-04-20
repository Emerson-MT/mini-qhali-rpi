import os
import time
from google import genai
from langsmith import wrappers

class LargeLanguageModel:
    def __init__(self, google_api_key, langsmith_api_key, model_name="gemini-2.0-flash", tools=None):
        # Configuración de entorno para LangSmith
        os.environ["GOOGLE_API_KEY"] = google_api_key
        os.environ["LANGSMITH_API_KEY"] = langsmith_api_key
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGSMITH_PROJECT"] = "MiniQhali"

        # Inicialización del cliente con Wrapper
        client_genai = genai.Client()
        self.client = wrappers.wrap_gemini(client_genai)
        self.model_name = model_name
        
        # Herramientas pasadas como arreglo de funciones
        self.tools = tools if tools else []
        self.pdf_context = None

    def upload_pdf(self, pdf_path):
        """Sube un archivo PDF para darle contexto al modelo."""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"No se encontró el PDF en: {pdf_path}")
            
        print(f"📄 Subiendo protocolo {pdf_path} a Gemini...")
        
        file_uploaded = self.client.files.upload(
            file=pdf_path,
            config={'mime_type': 'application/pdf'}
        )
        
        while file_uploaded.state.name == "PROCESSING":
            print("Esperando procesamiento de PDF...", end="\r", flush=True)
            time.sleep(2)
            file_uploaded = self.client.files.get(name=file_uploaded.name)
        
        if file_uploaded.state.name == "FAILED":
             raise Exception(f"Fallo en servidor: {file_uploaded.error.message}")

        print(f"\n✅ Contexto PDF listo.")
        self.pdf_context = file_uploaded
        return file_uploaded

    def generate_response(self, user_input, system_instruction):
        """Genera la respuesta procesando texto y herramientas."""
        prompt_contents = []
        
        # Añadir contexto de archivo si existe
        if self.pdf_context:
            prompt_contents.append(self.pdf_context)
        
        # Añadir instrucción de sistema y entrada del usuario
        prompt_contents.append(f"{system_instruction}\n\nUsuario dice: {user_input}")

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt_contents,
            config={"tools": self.tools}
        )
        
        return response