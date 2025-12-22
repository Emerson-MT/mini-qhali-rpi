// mobile.js - Lógica de la interfaz de celular

// ==========================================
// 1. ESTADO GLOBAL (Memoria)
// ==========================================
const socket = io();

// Objeto para guardar el reporte final
let paciente = {
    nombre: "",
    edad: "",
    bpm: 0,
    spo2: 0,
    temp: 0
};

// Variables temporales para la visualización en tiempo real
let currentBPM = 0;
let currentSpO2 = 0;
let currentTemp = 0.0;


// ==========================================
// 2. FUNCIONES DE INTERFAZ (Navegación)
// ==========================================

// Función global para cambiar de paso
function nextStep(stepNumber) {
    
    // VALIDACIÓN: Si estamos saliendo del paso 1, verificamos datos
    if(stepNumber === 2) {
        const nombreInput = document.getElementById('p-name').value;
        const edadInput = document.getElementById('p-age').value;

        if(nombreInput.trim() === "") {
            alert("Por favor, ingrese el nombre del paciente.");
            return; // Detiene la función, no avanza
        }
        
        // Guardamos en memoria
        paciente.nombre = nombreInput;
        paciente.edad = edadInput;
    }

    // Ocultar todos los pasos
    document.querySelectorAll('.step').forEach(el => el.classList.remove('active'));
    // Mostrar el deseado
    document.getElementById(`step-${stepNumber}`).classList.add('active');
}

// Función para congelar el dato actual y avanzar
function guardarDato(tipo, nextStepNum) {
    if(tipo === 'bpm') {
        paciente.bpm = currentBPM;
        console.log(`[MOBILE] BPM guardado: ${currentBPM}`);
    }
    if(tipo === 'spo2') {
        paciente.spo2 = currentSpO2;
        console.log(`[MOBILE] SpO2 guardado: ${currentSpO2}`);
    }
    
    nextStep(nextStepNum);
}

// Función final para generar el resumen
function finalizar() {
    paciente.temp = currentTemp;
    console.log(`[MOBILE] Temp guardada: ${currentTemp}`);
    
    // Generar HTML del resumen
    const resumenHTML = `
        <div style="text-align: left; margin-top: 10px;">
            <p><strong>👤 Paciente:</strong> ${paciente.nombre} (${paciente.edad} años)</p>
            <hr>
            <p>❤️ <strong>Ritmo Cardíaco:</strong> ${paciente.bpm} BPM</p>
            <p>💧 <strong>Saturación:</strong> ${paciente.spo2} %</p>
            <p>🌡️ <strong>Temperatura:</strong> ${paciente.temp} °C</p>
        </div>
    `;
    
    const elResumen = document.getElementById('resumen');
    if(elResumen) elResumen.innerHTML = resumenHTML;
    
    // (Opcional) Aquí podrías enviar 'paciente' al servidor para guardarlo en un Excel/BD
    // socket.emit('guardarReporte', paciente);

    nextStep(5);
}


// ==========================================
// 3. EVENTOS DE SOCKET (Datos en vivo)
// ==========================================

socket.on("connect", () => console.log("[MOBILE] Conectado al servidor"));

socket.on('sensorData', (data) => {
    // Protección: Si data es null o faltan campos, usa 0
    // Esto evita que salga "NaN" en la pantalla
    currentBPM = Math.round(data.heartRate || 0);
    currentSpO2 = Math.round(data.spo2 || 0);
    currentTemp = parseFloat(data.tempObject || 0).toFixed(1);

    // Actualizamos el DOM solo si el elemento existe en pantalla
    const elBpm = document.getElementById('val-bpm');
    const elSpo2 = document.getElementById('val-spo2');
    const elTemp = document.getElementById('val-temp');

    // Usamos innerText para ser más rápidos
    if(elBpm) elBpm.innerText = currentBPM;
    if(elSpo2) elSpo2.innerText = currentSpO2;
    if(elTemp) elTemp.innerText = currentTemp;
});