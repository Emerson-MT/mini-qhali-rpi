import json
import os
import time
from pathlib import Path
import paho.mqtt.client as mqtt

# --- CONFIGURACIÓN MQTT ---
MQTT_BROKER = "localhost"  # Como este script corre en la misma Pi que Mosquitto
MQTT_PORT = 1883
MQTT_TOPIC = "miniqhali/data"

# --- RUTAS GLOBALES ---
BASE_DIR = Path(__file__).resolve().parent
JSON_FILE = BASE_DIR / "datos_medicos.json"

def guardar_json(nuevo_dato):
    """
    Lee el archivo existente, agrega el nuevo dato y guarda todo.
    (Misma lógica que tu código original)
    """
    lista_datos = []
    
    if os.path.exists(JSON_FILE) and os.path.getsize(JSON_FILE) > 0:
        try:
            with open(JSON_FILE, 'r') as f:
                lista_datos = json.load(f)
        except json.JSONDecodeError:
            print("Advertencia: JSON corrupto, iniciando uno nuevo.")
            lista_datos = []

    lista_datos.append(nuevo_dato)

    with open(JSON_FILE, 'w') as f:
        json.dump(lista_datos, f, indent=4)
        # Feedback visual simple
        print(f"[{time.strftime('%H:%M:%S')}] Dato guardado. SpO2: {nuevo_dato.get('spo2')}% | Temp: {nuevo_dato.get('tempObject')}°C")

# --- CALLBACKS MQTT ---

def on_connect(client, userdata, flags, rc):
    """ Se ejecuta cuando nos conectamos al Broker """
    if rc == 0:
        print("Conectado al Broker MQTT exitosamente.")
        # Nos suscribimos al tópico donde el ESP32 publica
        client.subscribe(MQTT_TOPIC)
        print(f"Suscrito a: {MQTT_TOPIC}")
    else:
        print(f"Fallo en la conexión. Código: {rc}")

def on_message(client, userdata, msg):
    """ Se ejecuta CADA VEZ que llega un mensaje nuevo """
    try:
        payload = msg.payload.decode('utf-8')
        # print(f"Raw recibido: {payload}") # Descomentar para debug
        
        dato_json = json.loads(payload)
        
        # Opcional: Filtrar si 'finger_detected' es falso para ahorrar espacio
        # if not dato_json.get("finger_detected", False):
        #     return

        guardar_json(dato_json)

    except json.JSONDecodeError:
        print("Error: El mensaje recibido no es un JSON válido.")
    except Exception as e:
        print(f"Error procesando mensaje: {e}")

def main():
    # Crear instancia del cliente
    client = mqtt.Client()

    # Asignar funciones callback
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"Conectando a {MQTT_BROKER}...")
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        # loop_forever bloquea el script y maneja reconexiones automáticamente
        # Es perfecto para scripts que corren en background (daemons)
        client.loop_forever()
        
    except KeyboardInterrupt:
        print("\nDesconectando...")
        client.disconnect()
    except Exception as e:
        print(f"Error crítico: {e}")

if __name__ == '__main__':
    main()