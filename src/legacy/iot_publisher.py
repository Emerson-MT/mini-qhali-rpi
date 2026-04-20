import json
import time
import os
import paho.mqtt.client as mqtt

# --- CONFIGURACIÓN ---
BROKER = "localhost"
TOPIC = "salud/signos"
RUTA_ARCHIVO = "datos_medicos.json"

# --- CORRECCIÓN 1: Actualizar versión del API para quitar el Warning ---
# Usamos CallbackAPIVersion.VERSION2 para evitar el mensaje de error "DeprecationWarning"
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

try:
    client.connect(BROKER, 1883, 60)
    
    # --- CORRECCIÓN 2: ¡ESTO FALTABA! ---
    # Inicia el hilo en segundo plano que gestiona el envío y recepción de red
    client.loop_start()
    
    print("✅ Conectado al Broker MQTT y Loop iniciado")
except Exception as e:
    print(f"❌ Error conectando al Broker: {e}")
    exit()

def obtener_ultimo_dato():
    try:
        if os.path.exists(RUTA_ARCHIVO):
            with open(RUTA_ARCHIVO, 'r') as f:
                data = json.load(f)
                if data and isinstance(data, list):
                    return data[-1]
    except Exception as e:
        print(f"Error leyendo archivo: {e}")
    return None

# Bucle principal
ultimo_timestamp = 0

print("🚀 Iniciando publicación de datos...")

try:
    while True:
        dato_actual = obtener_ultimo_dato()
        
        if dato_actual:
            ts_actual = dato_actual.get("timestamp", 0)
            
            if ts_actual != ultimo_timestamp:
                mensaje = json.dumps(dato_actual)
                
                # Al tener loop_start(), este publish ahora sí saldrá de la Raspberry
                info = client.publish(TOPIC, mensaje)
                
                # Opcional: Verificar si se puso en cola correctamente
                if info.rc == mqtt.MQTT_ERR_SUCCESS:
                    print(f"📡 Enviado: {mensaje}")
                else:
                    print("⚠️ Fallo al poner en cola el mensaje")

                ultimo_timestamp = ts_actual
            
        time.sleep(1)

except KeyboardInterrupt:
    print("Deteniendo...")
    client.loop_stop() # Detenemos el hilo de red limpiamente
    client.disconnect()
