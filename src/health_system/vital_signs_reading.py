import serial
import json
import os
import time
from pathlib import Path

# --- CONFIGURACIÓN ---
# En Raspberry Pi, el ESP32 suele ser /dev/ttyUSB0 o /dev/ttyACM0
# Ejecuta 'ls /dev/tty*' en la terminal sin el ESP32 y luego con él para ver cuál aparece.
SERIAL_PORT = '/dev/ttyUSB0' 
BAUD_RATE = 115200

# --- RUTAS GLOBALES CON PATHLIB ---
BASE_DIR = Path(__file__).resolve().parent
JSON_FILE = BASE_DIR / "datos_medicos.json"  # Ruta absoluta segura

def guardar_json(nuevo_dato):
    """
    Lee el archivo existente, agrega el nuevo dato y guarda todo.
    Mantiene el formato de lista de objetos JSON [{}, {}, ...]
    """
    lista_datos = []

    # 1. Si el archivo existe y no está vacío, cargamos su contenido
    if os.path.exists(JSON_FILE) and os.path.getsize(JSON_FILE) > 0:
        try:
            with open(JSON_FILE, 'r') as f:
                lista_datos = json.load(f)
        except json.JSONDecodeError:
            print("Advertencia: El archivo JSON estaba corrupto. Se creará uno nuevo.")
            lista_datos = []

    # 2. Agregamos el nuevo registro
    lista_datos.append(nuevo_dato)

    # 3. Guardamos de nuevo el archivo actualizado
    with open(JSON_FILE, 'w') as f:
        json.dump(lista_datos, f, indent=4)
        print(f"Dato guardado. Total registros: {len(lista_datos)}")

def main():
    print(f"Conectando al puerto {SERIAL_PORT} a {BAUD_RATE} baudios...")
    
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        ser.flush() # Limpiar buffer
        print("Conexión exitosa. Esperando datos...")
        
    except serial.SerialException as e:
        print(f"Error abriendo el puerto serial: {e}")
        print("CONSEJO: Verifica que el puerto sea correcto (ls /dev/tty*) y tengas permisos.")
        return

    while True:
        try:
            if ser.in_waiting > 0:
                # Leer línea del puerto serial y decodificar bytes a string
                linea = ser.readline().decode('utf-8', errors='ignore').strip()
                
                # Intentar parsear como JSON
                # Esto filtrará mensajes de texto plano del ESP32 (ej. "Sistema iniciado")
                if linea.startswith('{') and linea.endswith('}'):
                    try:
                        dato_json = json.loads(linea)
                        
                        # (Opcional) Filtrar si no hay dedo para no llenar el disco de ceros
                        # Descomenta las siguientes 2 líneas si solo quieres guardar lecturas reales
                        # if dato_json.get("finger_detected") == False:
                        #    continue 

                        print(f"Recibido: {dato_json}")
                        guardar_json(dato_json)
                        
                    except json.JSONDecodeError:
                        # Si llega una línea incompleta o ruido
                        pass
                else:
                    # Imprimir mensajes de debug del ESP32 que no sean JSON
                    if linea:
                        print(f"[ESP32 LOG]: {linea}")
                        
        except KeyboardInterrupt:
            print("\nDeteniendo script...")
            if ser.is_open:
                ser.close()
            break
        except Exception as e:
            print(f"Error inesperado: {e}")

if __name__ == '__main__':
    main()
