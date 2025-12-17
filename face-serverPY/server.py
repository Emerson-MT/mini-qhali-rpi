# server.py
from flask import Flask, send_from_directory, request, jsonify
from flask_socketio import SocketIO
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
STATIC_DIR = BASE_DIR / "public"

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# --- ESTADOS ---
blinkFlag = 0  # 0 = ON natural ; 1 = OFF pausado
faceFlag = 0   # 0 = normal ; 1=rojo ; 2=azul ; 3=verde

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

# --- Eventos Socket.IO ---
@socketio.on("connect")
def handle_connect():
    print("✅ Cliente conectado")
    socketio.emit("blinkFlag", blinkFlag)
    socketio.emit("faceFlag", faceFlag)

@socketio.on("disconnect")
def handle_disconnect():
    print("❌ Cliente desconectado")

if __name__ == "__main__":
    print("🚀 Servidor listo en http://localhost:3000")
    print(f"📁 STATIC_DIR = {STATIC_DIR}")
    print("👉 Blink: GET /blink/0 (natural) | /blink/1 (pausar) | GET/POST /blink")
    print("👉 Face:  GET /face/0 (normal) | /face/1 (rojo) | /face/2 (azul) | /face/3 (verde) | GET/POST /face")
    socketio.run(app, host="0.0.0.0", port=3000)
