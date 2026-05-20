import requests
import socketio

class ServerComm:
    def __init__(self, base_url="http://localhost:3000"):
        self.base_url = base_url
        self.url_telemetria = f"{base_url}/api/telemetria"
        self.ultimo_timestamp = 0
        
        self.sio = socketio.Client()
        self.callbacks = {}

    def setup_sockets(self, canales):
        """
        Registra dinámicamente los canales y los eventos base.
        """
        # 1. Definimos las funciones de evento
        def handle_connect():
            print("✅ Conectado al servidor de Sockets")

        def handle_disconnect():
            print("❌ Desconectado del servidor de Sockets")

        # 2. Las registramos explícitamente (esto quita el "not accessed")
        self.sio.on('connect', handle_connect)
        self.sio.on('disconnect', handle_disconnect)

        # 3. Registro dinámico de canales con la fábrica
        def crear_manejador(nombre_canal):
            def handler(data=None):  # <-- data ahora es opcional
                print(f"📡 Evento [{nombre_canal}] recibido")
                if nombre_canal in self.callbacks:
                    # Si data es None, enviamos un diccionario vacío seguro
                    payload_y_seguro = data if data is not None else {}
                    self.callbacks[nombre_canal](payload_y_seguro)
            return handler

        for canal in canales:
            self.sio.on(canal, crear_manejador(canal))

    def connect_socket(self):
        try:
            if not self.sio.connected:
                self.sio.connect(self.base_url, wait_timeout=10)
        except Exception as e:
            print(f"❌ Error Socket: {e}")

    def send_to_server(self, datos):
        """
        Envía datos al servidor mediante una petición POST.
        :param datos: Puede ser un diccionario o una lista de diccionarios.
        :return: True si el servidor respondió con éxito, False en caso contrario.
        """
        try:
            # Validación simple de timestamp para evitar envíos redundantes 
            # (si los datos vienen con el formato de tu sistema)
            if isinstance(datos, list) and len(datos) > 0:
                ts_actual = datos[-1].get("timestamp", 0)
            elif isinstance(datos, dict):
                ts_actual = datos.get("timestamp", 0)
            else:
                ts_actual = None

            if ts_actual is not None and ts_actual == self.ultimo_timestamp:
                return False # Ya se envió este dato

            print(f"📤 Enviando datos al servidor: {self.url_telemetria}")
            
            # Tu server.py espera una lista: "datos_lista = request.get_json... or []"
            # Realizar la petición POST
            respuesta = requests.post(self.url_telemetria, json=datos, timeout=3)
            
            if respuesta.status_code == 200:
                print(f"✅ Respuesta del servidor: {respuesta.json()}")
                if ts_actual:
                    self.ultimo_timestamp = ts_actual
                return True
            else:
                print(f"⚠️ Error en servidor: Código {respuesta.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión con el servidor: {e}")
            return False

    def verify_server_state(self):
        """
        Verifica si el servidor está en línea (opcional).
        """
        try:
            # Se asume que una petición GET a la raíz o al endpoint indica estado
            respuesta = requests.get(self.base_url, timeout=2)
            return respuesta.status_code == 200
        except:
            return False