import serial
import time

class SerialConnection:
     
    def __init__(self, port='/dev/ttyACM0', baud_rate=115200, timeout=1):
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.connection = None
        self.connect()

    def connect(self):
        try:
            self.connection = serial.Serial(self.port, self.baud_rate, timeout=self.timeout)
            time.sleep(2)  # Dar tiempo para que se establezca la conexión
            print(f"[Serial] Conectado a {self.port}")
        except serial.SerialException as e:
            print(f"[Serial Error] {e}")
    
    def disconnect(self):
        if self.connection:
            self.connection.close()
            print("[Serial] Conexión cerrada.")

    def send(self, data: str):
        if self.connection and self.connection.is_open:
            print(f"📤 Enviando: {data.strip()}")
            self.connection.write(data.encode())
        else:
            print("[Serial Warning] Intento de enviar sin conexión activa.")