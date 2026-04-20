import os
import json
import random
import time
from pathlib import Path

from serial_comm import SerialConnection
from server_comm import ServerComm
from user_comm import LargeLanguageModel, SpeechToText, TextToSpeech

class MiniQhaliRobot:
    def __init__(self, google_api_key, vosk_model_path, device_name, pdf_path, poses_path):
        # 1. Configuración de Rutas y Archivos
        self.base_dir = Path(__file__).resolve().parent.parent
        self.json_file = self.base_dir / "datos_medicos.json"
        self.poses = self._load_poses(poses_path)

        # 2. Variables de estado del proceso
        self.is_measuring = None
        self.measuring_state = 'data' 
        
        # 3. Inicialización de Componentes Modulares
        
        # Configuración de conexión Serial
        self.serial = SerialConnection(port='/dev/ttyUSB0', baud_rate=115200)
        
        # Configuración de conexión con servidor
        self.server = ServerComm(url_servidor="http://localhost:3000")
        # Definimos qué canales escuchar
        my_channels = ['cambiar_modo_sensores', 'reset_face', 'finalizar_chequeo']
        self.server.setup_sockets(my_channels)

        # Mapeamos los canales a funciones (Callbacks) de MiniQhali
        self.server.callbacks['cambiar_modo_sensores'] = self.manejar_modo
        self.server.callbacks['reset_face'] = self.reiniciar_robot
        # Se establece la conexión
        self.server.connect_socket()
        
        # Configuración de Speech to Text
        self.stt = SpeechToText(model_path=vosk_model_path, device_name=device_name)

        # Configuración de Text to Speech
        self.tts = TextToSpeech(volume_boost="1.0")
        
        # 3. Configuración del Cerebro (LLM) con sus Tools
        my_tools = [
            self.execute_pose
        ]
        self.brain = LargeLanguageModel(google_api_key=google_api_key, tools=my_tools)
        self.brain.upload_pdf(pdf_path)
    

    def manejar_modo(self, data):
        # 1. Extraemos los datos del evento
        nuevo_estado = data.get('activo', False)
        nuevo_tipo = data.get('tipo', 'data')

        # 2. Actualizamos la memoria interna del robot
        self.is_measuring = nuevo_estado
        self.measuring_state = nuevo_tipo

        print(f"📡 [Socket] Modo: {'ACTIVADO' if self.is_measuring else 'DESACTIVADO'} | Tipo: {self.measuring_state}")

        # 3. Lógica de reacción inmediata (HRI)
        if self.is_measuring:
            if self.measuring_state == 'bpm':
                self.tts.speak("Por favor, coloca tu dedo en el sensor de pulso.")
                self.execute_pose("medicion_atenta")
            elif self.measuring_state == 'spo2':
                self.tts.speak("Por favor coloca tu dedo en mi mano para medir el oxígeno")
            elif self.measuring_state == 'temp':
                self.tts.speak("Acércate al sensor de temperatura por favor.")
        else:
            # Si acabamos de terminar una medición (is_measuring pasó a False)
            # El robot puede dar un feedback de "descanso"
            self.execute_pose("explicacion") 
            if self.measuring_state != 'data': # Evitamos que hable en el primer paso de datos
                self.tts.speak(f"He terminado de capturar los datos de {self.measuring_state}. ¡Muy bien!")

    def reiniciar_robot(self, data):
        print("Robot reiniciando posición...")
        # Lógica para resetear poses

    def _load_poses(self, poses_path):
        """Carga el archivo de poses JSON."""
        try:
            with open(poses_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error cargando poses: {e}")
            # Fallback en caso de error
            return {"explicacion": [[90, 90, 90, 90, 180, 90, 90]], "feedback": [[90, 90, 90, 90, 180, 90, 90]]}
        
    # --- Métodos de Integración de Datos (Serial -> JSON -> Server) ---

    def read_sensors(self):
        """Lee el puerto serial y guarda en el archivo JSON local."""
        if self.serial.connection and self.serial.connection.in_waiting > 0:
            try:
                linea = self.serial.connection.readline().decode('utf-8', errors='ignore').strip()
                if linea.startswith('{') and linea.endswith('}'):
                    dato_json = json.loads(linea)
                    print(f"📥 Dato recibido del ESP32: {dato_json}")
                    self._save_in_json(dato_json)
                    return dato_json
                elif linea:
                    print(f"[ESP32 LOG]: {linea}")
            except Exception as e:
                print(f"⚠️ Error sincronizando serial: {e}")
        return None

    def _save_in_json(self, nuevo_dato):
        """Implementación de persistencia local en lista JSON."""
        lista_datos = []
        if self.json_file.exists() and self.json_file.stat().st_size > 0:
            try:
                with open(self.json_file, 'r') as f:
                    lista_datos = json.load(f)
            except:
                lista_datos = []
        
        lista_datos.append(nuevo_dato)
        with open(self.json_file, 'w') as f:
            json.dump(lista_datos, f, indent=4)

    def update_server(self):
        """Lee el archivo JSON y envía la actualización al servidor Flask."""
        try:
            if self.json_file.exists():
                with open(self.json_file, 'r') as f:
                    datos_lista = json.load(f)
                
                if datos_lista:
                    # El componente ServerComm gestiona el control de duplicados vía timestamp
                    self.server.send_to_server(datos_lista)
        except Exception as e:
            print(f"⚠️ Error al actualizar servidor: {e}")

    # --- Tools del Robot (Mapeadas al LLM) ---

    def execute_pose(self, tipo_pose: str):
        """
        Tool: Mueve los servos según la intención del LLM enviando un JSON al ESP32.
        """

        if self.is_measuring:
            print("⚠️ Intento de pose bloqueado: El robot está midiendo.")
            return "Movimiento omitido por seguridad durante la medición."
        
        if tipo_pose not in self.poses:
            tipo_pose = "explicacion"
        
        # Seleccionar un set de ángulos aleatorio del tipo de pose
        angulos = random.choice(self.poses[tipo_pose])
        
        # Formato corregido: enviar JSON puro {"angles": [...]}
        paquete_movimiento = {"angles": angulos}
        json_comando = json.dumps(paquete_movimiento) + "\n"
        
        self.serial.send(json_comando)
        return f"Ejecutada pose de tipo: {tipo_pose}"

    def begin_measurements(self):
        """
        Tool: Envía la orden al ESP32 para cambiar al estado de medición.
        """
        comando_medicion = {"action": "measure"}
        json_comando = json.dumps(comando_medicion) + "\n"
        
        self.serial.send(json_comando)
        return "Iniciando toma de signos vitales. Los resultados aparecerán en la pantalla."

    # --- Bucle de Ejecución ---

    def run(self):
        print("\n🚀 MiniQhali (Modo Guía de Formulario) iniciado.")
        # Pose y saludo inicial
        self.execute_pose("explicacion")
        self.tts.speak("¡Hola! Soy MiniQhali. Por favor, usa el formulario en mi pantalla para iniciar.")

        try:
            while True:
                # --- 1. TAREAS DE FONDO: LECTURA DE SENSORES ---
                # Solo leemos y mandamos si el Socket nos activó la bandera
                if self.is_measuring:
                    dato_nuevo = self.read_sensors()
                    if dato_nuevo:
                        self.update_server()

                # --- 2. INTERACCIÓN POR VOZ: PROCESAMIENTO LLM ---
                user_input = self.stt.listen()
                if not user_input or user_input.strip() == "":
                    time.sleep(0.01) # Evitar consumo excesivo de CPU
                    continue
                
                print(f"👤 Usuario: {user_input}")

                # Dentro del run()
                estado_actual_texto = f"Contexto actual: El robot {'ESTÁ' if self.is_measuring else 'NO está'} midiendo signos vitales ahora mismo."

                # PROMPT DE INTEGRACIÓN: Guía por PDF + Pensamiento Motor
                prompt_contents = [
                    self.brain.pdf_context, # Contexto principal del PDF
                    estado_actual_texto,
                    f"""
                    Eres MiniQhali, una robot enfermera de la PUCP que ayuda a pacientes con sus signos vitales.
                    
                    INSTRUCCIÓN DE PENSAMIENTO MOTOR:
                    Antes de responder, sigue este proceso mental interno:
                    1. Determina la respuesta basándote en el input: '{user_input}' y el protocolo del PDF. Esta respuesta debe basarse
                    siempre primero en el protocolo del PDF y, de no encontrar respuesta ahí, puedes responder buscando en internet.
                    2. Siempre debes analizar el contenido de lo que dices para elegir el tipo de movimiento a ejecutar mientras hablas:
                       - Informativo/Guía -> tipo_pose='explicacion'.
                       - Éxito/Resultado/Cierre -> tipo_pose='feedback'.
                    3. Siempre que el robot no esté midiendo signos vitales, debes ejecutar el tool 'execute_pose' con el tipo_pose 
                    que hayas elegido previamente.
                    
                    FORMATO DE RESPUESTA OBLIGATORIO (Orden estricto):
                    - Parte 1: Llamada a 'execute_pose' con tipo_pose como parámetro.
                    - Parte 2: Texto de respuesta para el usuario.
    
                    """
                ]

                # Generamos la respuesta usando el método del LLM que configuramos
                response = self.brain.client.models.generate_content(
                    model=self.brain.model_name,
                    contents=prompt_contents,
                    config={"tools": self.brain.tools}
                )

                if not response.candidates or not response.candidates[0].content.parts:
                    continue

                # --- 3. EJECUCIÓN DE PARTES (Secuencia de Hardware) ---
                for part in response.candidates[0].content.parts:
                    if part.function_call:
                        fn = part.function_call
                        if fn.name == "execute_pose":
                            # Ejecuta el movimiento físico inmediatamente
                            self.execute_pose(**fn.args)
                    elif part.text:
                        # El texto se habla al final para que el robot ya esté en la pose correcta
                        self.tts.speak(part.text)

        except KeyboardInterrupt:
            self.serial.disconnect()
            self.server.sio.disconnect()
            print("\n🛑 Programa finalizado por el usuario.")