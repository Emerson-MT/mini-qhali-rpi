# server.py
from flask import Flask, send_from_directory, render_template, request, jsonify
from flask_socketio import SocketIO
from pathlib import Path
import mysql.connector
import json
from datetime import datetime
import pytz

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
    return send_from_directory(STATIC_DIR, "face/index.html")

@app.route("/mobile")
def mobile_interface():
    # Esta ruta servirá el archivo HTML específico para el celular
    return send_from_directory(STATIC_DIR, "mobile/index.html")

@app.route("/monitoring")
def monitoring_interface():
    return send_from_directory(STATIC_DIR, "monitoring/index.html")

@app.route("/monitoring/details/<int:patient_id>")
def patient_detail_view(patient_id):
    # Servimos un archivo nuevo llamado "detail.html"
    return send_from_directory(STATIC_DIR, "monitoring/details/index.html")

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
    temp_obj = ultimo_dato.get("tempObject", 0.0) or 0.0
    spo2 = ultimo_dato.get("spo2", 0) or 0
    bpm = ultimo_dato.get("heartRate", 0) or 0
    finger = ultimo_dato.get("finger_detected", False) or False

    print(f"📩 Dato recibido: Temp={temp_obj}, SpO2={spo2}, Dedo={finger}")

    # 3. Lógica de Colores (Temperatura)
    # Rango normal humano: 36.0 a 37.5 aprox.
    nuevo_estado = 0 # Normal
    
    if finger: # Solo cambiamos la cara si hay un dedo detectado
        if temp_obj > 37.5:
            nuevo_estado = 1 # Fiebre -> ROJO
        elif temp_obj > 30.0 and temp_obj < 35.0:
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

# --- CONFIGURACIÓN DE BASE DE DATOS ---
db_config = {
    'host': 'sql10.freesqldatabase.com',
    'user': 'sql10815178',       # Cambia esto por tu usuario de MySQL
    'password': '5LNS15uY8G', # Cambia esto por tu contraseña de MySQL
    'database': 'sql10815178'
}

# --- NUEVA RUTA API PARA GUARDAR ---
@app.route('/api/guardar_paciente', methods=['POST'])
def guardar_paciente():
    try:
        data = request.json

        # Obtener la hora actual de Lima
        zona_lima = pytz.timezone('America/Lima')
        fecha_lima = datetime.now(zona_lima).strftime('%Y-%m-%d %H:%M:%S')
        
        # Conexión a la BD
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Si el frontend envía [70, 72, 75], esto lo convierte a "[70, 72, 75]"
        bpm_json = json.dumps(data.get('history_bpm', []))
        spo2_json = json.dumps(data.get('history_spo2', []))

        # Query SQL
        sql = """
            INSERT INTO patients 
            (name, lastname, age, sex_id, weight, height, bmi, heart_rate, history_bpm, spo2, history_spo2, tempObject, date_register)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        valores = (
            data['name'],
            data['lastname'],
            data['age'],
            data['sex_id'],
            data['weight'],
            data['height'],
            data['bmi'],
            data['heart_rate'],
            bpm_json,
            data['spo2'],
            spo2_json,
            data['tempObject'],
            fecha_lima
        )
        
        cursor.execute(sql, valores)
        conn.commit() # Importante para guardar cambios
        new_id = cursor.lastrowid
        
        cursor.close()
        conn.close()
        
        return jsonify({"status": "success", "id": new_id, "message": "Paciente registrado"}), 200

    except mysql.connector.Error as err:
        print(f"Error SQL: {err}")
        return jsonify({"status": "error", "message": str(err)}), 500
    except Exception as e:
        print(f"Error General: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/pacientes", methods=["GET"])
def obtener_pacientes():
    try:
        # 1. Obtener parámetros de la URL (Query Params)
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '', type=str)
        limit = 5  # Cantidad de pacientes por página (como en tu imagen)
        offset = (page - 1) * limit

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True) # dictionary=True es CLAVE para JSON

        # 2. Construir la Query Dinámica (Búsqueda + Paginación)
        query = """
            SELECT id, name, lastname, age, sex_id, date_register 
            FROM patients 
            WHERE name LIKE %s OR lastname LIKE %s 
            ORDER BY date_register DESC 
            LIMIT %s OFFSET %s
        """
        search_pattern = f"%{search}%"
        cursor.execute(query, (search_pattern, search_pattern, limit, offset))
        pacientes = cursor.fetchall()

        # 3. Obtener el total de registros (para saber cuántas páginas hay)
        count_query = "SELECT COUNT(*) as total FROM patients WHERE name LIKE %s OR lastname LIKE %s"
        cursor.execute(count_query, (search_pattern, search_pattern))
        total_records = cursor.fetchone()['total']
        
        cursor.close()
        conn.close()

        # 4. Responder JSON
        return jsonify({
            "status": "success",
            "data": pacientes,
            "page": page,
            "limit": limit,
            "total_records": total_records,
            "total_pages": (total_records + limit - 1) // limit
        })

    except Exception as e:
        print(f"Error API Pacientes: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# 2. API para obtener un paciente específico (Backend)
@app.route("/api/pacientes/<int:id>", methods=["GET"])
def obtener_paciente_id(id):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # Query para buscar por ID
        query = "SELECT * FROM patients WHERE id = %s"
        cursor.execute(query, (id,))
        paciente = cursor.fetchone()
        
        cursor.close()
        conn.close()

        if paciente:
            return jsonify({"status": "success", "data": paciente})
        else:
            return jsonify({"status": "error", "message": "Paciente no encontrado"}), 404

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
# --- Eventos Socket.IO ---
@socketio.on("connect")
def handle_connect():
    print("✅ Cliente conectado")
    socketio.emit("blinkFlag", blinkFlag)
    socketio.emit("faceFlag", faceFlag)
    '''
    if last_sensor_data:
        print(f"   -> Enviando memoria al nuevo cliente: {last_sensor_data}")
        socketio.emit("sensorData", last_sensor_data)
    '''

@socketio.on("disconnect")
def handle_disconnect():
    print("❌ Cliente desconectado")

@socketio.on('finalizar_chequeo')
def handle_final_results(data):
    # data contiene: { temp, spo2, bpm, faceColor }
    print(f"🏁 Chequeo finalizado. Resultados: {data}")
    # Reenviamos esto a la cara con un evento específico
    socketio.emit('show_results', data)

@socketio.on('reset_face')
def handle_reset_face():
    print("🔄 Reiniciando sistema para nuevo paciente")
    # Le avisa a TODOS (incluida la cara) que se reinicien
    socketio.emit('reset_face')


if __name__ == "__main__":
    print("🚀 Servidor listo en http://localhost:3000")
    print(f"📁 STATIC_DIR = {STATIC_DIR}")
    print("👉 Blink: GET /blink/0 (natural) | /blink/1 (pausar) | GET/POST /blink")
    print("👉 Face:  GET /face/0 (normal) | /face/1 (rojo) | /face/2 (azul) | /face/3 (verde) | GET/POST /face")
    socketio.run(app, host="0.0.0.0", port=3000, allow_unsafe_werkzeug=True)
 