# MiniQhali - Robot Social de Asistencia Médica 🤖🏥

Este proyecto integra un sistema de **sensores biomédicos (IoT)** con una **interfaz robótica web (Flask)**. El robot "MiniQhali" visualiza el estado de salud del paciente mediante expresiones faciales animadas y métricas en tiempo real.

## 📂 Estructura del Proyecto

El proyecto está organizado de manera modular:

```text
/MiniQhali_Project
│
├── /web_interface           # SERVIDOR FLASK (Frontend y Backend Web)
│   ├── /public              # Archivos estáticos (HTML, CSS, JS)
│   ├── server.py            # Cerebro principal: Recibe datos y controla la cara
│   └── requirements.txt     # Dependencias de Python
│
├── /src                     # LÓGICA DE SENSORES (Hardware)
│   └── /health_system
│       ├── vital_signs_reading.py  # Lee sensores físicos y guarda en JSON
│       ├── send_data_http.py       # Lee el JSON y envía los datos a Flask (POST)
│       ├── datos_medicos.json      # Archivo temporal de intercambio de datos
│       └── /legacy
│           └── iot_publisher.py    # (Opcional) Envío vía MQTT/Mosquitto
│
├── run_miniqhali.sh         # Script de arranque automático (Bash)
└── README.md
```

## ⚙️ Instalación y Requisitos

Asegúrate de tener Python 3 instalado en tu sistema. Antes de iniciar, instala las librerías necesarias ejecutando:
```
install flask flask-socketio requests paho-mqtt
```
## 🚀 Guía de Ejecución Rápida

Para facilitar el despliegue, el proyecto incluye un script de automatización que levanta el servidor web, la lectura de sensores y el envío de datos simultáneamente.

1. Dar permisos de ejecución (Solo la primera vez)Debes autorizar al sistema para ejecutar el script de arranque. Abre una terminal en la raíz del proyecto y escribe:
```
chmod +x run_miniqhali.sh
```
2. Iniciar el SistemaEjecuta el script maestro:
```
./run_miniqhali.sh
```
Lo que sucederá:

Se iniciará el Servidor Flask en segundo plano.
Arrancará la Lectura de Sensores (generación de datos).
Se activará el Puente HTTP para enviar los datos a la web.

    Visualización: Una vez corriendo, abre tu navegador en: http://localhost:3000🛑 

Detener el sistema

Para apagar todos los procesos de forma segura, simplemente presiona Ctrl + C en la terminal donde corre el script.

## 📡 Módulos Opcionales (Legacy)

### Envío por MQTT (Node-RED / Mosquitto)

Si necesitas integración con sistemas antiguos o dashboards en Node-RED, puedes usar el publicador MQTT que se encuentra en la carpeta legacy.
    Requisito: Tener un broker MQTT (como Mosquitto) corriendo en localhost.
    ```
    cd src/health_system/legacy
    python iot_publisher.py
    ```
## 🧠 Lógica de Expresiones (Estados)El servidor analiza la temperatura y la saturación de oxígeno para cambiar la "emoción" del robot automáticamente.

Estado (Flag),Color Cara,Condición Médica,Descripción
0,⚫ Normal,Signos estables,Paciente en rango saludable (36.0°C - 37.5°C).
1,🔴 Rojo,Fiebre,Temperatura corporal > 37.5°C.
2,🔵 Azul,Hipotermia,Temperatura corporal < 36.0°C.
3,🟢 Verde,Hipoxia / Mareo,Saturación de oxígeno (SpO2) < 90%.

