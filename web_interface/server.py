# server.py
from flask import Flask, send_from_directory, request, jsonify
from flask_socketio import SocketIO
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
STATIC_DIR = BASE_DIR / "public"

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# --- ESTADOS (MEMORIA DEL ROBOT) ---
blinkFlag = 0
faceFlag = 0
# NUEVO: Guardamos el último dato de sensores recibido
last_sensor_data = {
    "tempObject": 0,
    "spo2": 0,
    "heartRate": 0
}

# --- Ruta principal ---
@app.route("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")

# --- Rutas Blink ---
@app.route("/blink/<int:flag>")
def set_blink(flag):
    global blinkFlag
    blinkFlag = 1 if flag == 1 else 0
    socketio.emit("blinkFlag", blinkFlag)
    return jsonify({"ok": True, "blinkFlag": blinkFlag})

@app.route("/blink", methods=["GET", "POST"])
def blink():
    global blinkFlag
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        flag = data.get("flag", 0)
        blinkFlag = 1 if int(flag) == 1 else 0
        socketio.emit("blinkFlag", blinkFlag)
    return jsonify({"blinkFlag": blinkFlag})

# --- Rutas Face ---
@app.route("/face/<int:flag>")
def set_face(flag):
    global faceFlag
    faceFlag = flag if flag in [0, 1, 2, 3] else 0
    socketio.emit("faceFlag", faceFlag)
    return jsonify({"ok": True, "faceFlag": faceFlag})

@app.route("/face", methods=["GET", "POST"])
def face():
    global faceFlag
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        flag = int(data.get("flag", 0))
        faceFlag = flag if flag in [0, 1, 2, 3] else 0
        socketio.emit("faceFlag", faceFlag)
    return jsonify({"faceFlag": faceFlag})

# --- NUEVA RUTA: Recibir Datos del Sensor ---
@app.route("/api/telemetria", methods=["POST"])
def recibir_telemetria():
    global faceFlag, last_sensor_data # Usamos la variable global
    
    # 1. Recibir el JSON completo (la lista de objetos)
    datos_lista = request.get_json(silent=True) or []
    
    # Validamos que sea una lista y tenga datos
    if not isinstance(datos_lista, list) or len(datos_lista) == 0:
        return jsonify({"error": "Formato incorrecto, se espera una lista"}), 400

    # 2. Tomamos solo el ÚLTIMO dato (el más reciente)
    ultimo_dato = datos_lista[-1]

    # ACTUALIZAMOS LA MEMORIA DEL SERVIDOR
    last_sensor_data = ultimo_dato
    
    # Extraemos los valores usando las llaves de TU json
    temp_obj = ultimo_dato.get("tempObject", 0.0)
    spo2 = ultimo_dato.get("spo2", 0)
    bpm = ultimo_dato.get("heartRate", 0)
    finger = ultimo_dato.get("finger_detected", False)

    print(f"📩 Dato recibido: Temp={temp_obj}, SpO2={spo2}, Dedo={finger}")

    # 3. Lógica de Colores (Temperatura)
    # Rango normal humano: 36.0 a 37.5 aprox.
    nuevo_estado = 0 # Normal
    
    if finger: # Solo cambiamos la cara si hay un dedo detectado
        if temp_obj > 37.5:
            nuevo_estado = 1 # Fiebre -> ROJO
        elif temp_obj < 35.0:
            nuevo_estado = 2 # Hipotermia -> AZUL
        elif spo2 < 90 and spo2 > 0:
            nuevo_estado = 3 # Falta aire -> VERDE 
        else:
            nuevo_estado = 0
    
    # Actualizamos la cara si cambió
    if faceFlag != nuevo_estado:
        faceFlag = nuevo_estado
        socketio.emit("faceFlag", faceFlag)

    # 4. ENVIAMOS LOS NÚMEROS A LA PANTALLA
    # Esto activará el javascript que escribimos en el paso 2
    socketio.emit("sensorData", last_sensor_data)

    return jsonify({"status": "ok", "face": faceFlag})

# --- Eventos Socket.IO ---
@socketio.on("connect")
def handle_connect():
    print("✅ Cliente conectado")
    socketio.emit("blinkFlag", blinkFlag)
    socketio.emit("faceFlag", faceFlag)
    if last_sensor_data:
        print(f"   -> Enviando memoria al nuevo cliente: {last_sensor_data}")
        socketio.emit("sensorData", last_sensor_data)

@socketio.on("disconnect")
def handle_disconnect():
    print("❌ Cliente desconectado")

if __name__ == "__main__":
    print("🚀 Servidor listo en http://localhost:3000")
    print(f"📁 STATIC_DIR = {STATIC_DIR}")
    print("👉 Blink: GET /blink/0 (natural) | /blink/1 (pausar) | GET/POST /blink")
    print("👉 Face:  GET /face/0 (normal) | /face/1 (rojo) | /face/2 (azul) | /face/3 (verde) | GET/POST /face")
    socketio.run(app, host="0.0.0.0", port=3000, allow_unsafe_werkzeug=True)
