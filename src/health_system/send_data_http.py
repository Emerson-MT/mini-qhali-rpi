import json
import time
import os
import requests  
from pathlib import Path

# --- CONFIGURACIÓN ---
# Si el script corre en la misma PC que Flask, usa localhost.
# Si está en una Raspberry Pi y Flask corre en un dispositivo diferente, usar la ip de este en lugar de localhost
URL_SERVIDOR = "http://localhost:3000/api/telemetria"

# --- RUTAS GLOBALES CON PATHLIB ---
BASE_DIR = Path(__file__).resolve().parent
JSON_FILE = BASE_DIR / "datos_medicos.json"  # Ruta absoluta segura

def obtener_ultimo_dato():
    """Lee el archivo JSON y retorna el último elemento de la lista."""
    try:
        if os.path.exists(JSON_FILE):
            with open(JSON_FILE, 'r') as f:
                # Intentamos leer el archivo. A veces puede estar vacío si se está escribiendo justo ahora.
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    return None
                
                # Si es una lista, devolvemos toda la lista (Flask elegirá el último)
                # O podemos enviar solo el último desde aquí.
                # Para seguir la lógica de tu server.py, enviamos TODO el contenido.
                if isinstance(data, list):
                    return data
    except Exception as e:
        print(f"Error leyendo archivo: {e}")
    return None

# --- BUCLE PRINCIPAL ---
ultimo_timestamp = 0
print(f"🚀 Iniciando agente de envío a {URL_SERVIDOR}...")

try:
    while True:
        # 1. Leemos el archivo
        datos_lista = obtener_ultimo_dato()
        
        if datos_lista and len(datos_lista) > 0:
            # Tomamos el último para comparar el timestamp y no enviar repetidos
            dato_mas_nuevo = datos_lista[-1]
            ts_actual = dato_mas_nuevo.get("timestamp", 0)
            
            # 2. Si el timestamp es diferente al último enviado, ¡hay novedad!
            if ts_actual != ultimo_timestamp:
                try:
                    # Enviamos la lista completa o solo el objeto, según espere tu server.
                    # Tu server.py espera una lista: "datos_lista = request.get_json... or []"
                    print(f"📤 Enviando actualización (TS: {ts_actual})...")
                    
                    respuesta = requests.post(URL_SERVIDOR, json=datos_lista)
                    
                    if respuesta.status_code == 200:
                        print(f"✅ Recibido por Flask: {respuesta.json()}")
                        ultimo_timestamp = ts_actual
                    else:
                        print(f"⚠️ El servidor rechazó el dato: {respuesta.status_code}")
                        
                except requests.exceptions.ConnectionError:
                    print("❌ Error: No se puede conectar a Flask. ¿Está corriendo server.py?")
        
        # Esperamos un poco antes de volver a leer
        time.sleep(1)

except KeyboardInterrupt:
    print("\n🛑 Deteniendo el envío...")