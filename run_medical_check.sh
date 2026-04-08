#!/bin/bash

# Función para matar todos los procesos cuando presiones Ctrl+C
trap "kill 0" EXIT

echo "🚀 Iniciando Sistema MiniQhali..."

# 1. Iniciamos el Servidor Web (Flask) en segundo plano (&)
echo "   -> Iniciando Interfaz Web..."
python3 web_interface/server.py &
PID_SERVER=$! # Guardamos el ID del proceso por si acaso
sleep 3 # Esperamos unos segundos a que el servidor arranque bien

# 2. Iniciamos la lectura de sensores
echo "   -> Iniciando Sensores..."
python3 src/health_system/vital_signs_reading_mqtt.py &

# 3. Iniciamos el puente de datos
echo "   -> Iniciando Transmisión HTTP..."
python3 src/health_system/send_data_http.py &

echo "✅ Todo corriendo. Presiona Ctrl+C para detener todo."

# Mantiene el script vivo esperando
wait
