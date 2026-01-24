// mobile.js - VERSIÓN FINAL INTEGRADA

const socket = io();

// --- CONFIGURACIÓN ---
const MUESTRAS_OBJETIVO = 20; 

// --- BASE DE CONOCIMIENTO MÉDICO ---
const RANGOS_MEDICOS = {
    BPM: [
        { edadMax: 1, min: 100, max: 180 }, 
        { edadMax: 3, min: 98, max: 140 },  
        { edadMax: 5, min: 80, max: 120 },  
        { edadMax: 12, min: 75, max: 118 }, 
        { edadMax: 18, min: 60, max: 100 }, 
        { edadMax: 120, min: 60, max: 100 } 
    ],
    TEMP: { hipotermia: 36.0, normalMax: 37.4, fiebreLeve: 38.0 },
    SPO2: { normal: 95, hipoxiaLeve: 90 }
};

// --- ESTADO GLOBAL ---
let patient = { name: "", lastname: "", age: "", sex_id: "", weight: "", height: "" , bmi: "", heart_rate: "", historyBPM: [], spo2: "", historySpO2: [], tempObject: ""};
let historyTemp = [];

let currentStep = 0;
let isMeasuring = false;
let muestrasActuales = 0;

// --- BARRA DE PROGRESO: LÓGICA DE INPUTS (PASO 1) ---
document.addEventListener("DOMContentLoaded", () => {
    // Agregamos 'p-lastname' a la lista de inputs a vigilar
    const inputs = ['p-name', 'p-lastname', 'p-age', 'p-weight', 'p-height'];
    inputs.forEach(id => {
        const el = document.getElementById(id);
        if(el) el.addEventListener('input', actualizarProgresoDatos);
    });
});

function actualizarProgresoDatos() {
    if (currentStep !== 1) return;

    let camposLlenos = 0;
    if(document.getElementById('p-name').value.trim() !== "") camposLlenos++;
    if(document.getElementById('p-lastname').value.trim() !== "") camposLlenos++;
    if(document.getElementById('p-age').value !== "") camposLlenos++;
    if(document.getElementById('p-weight').value !== "") camposLlenos++;
    if(document.getElementById('p-height').value !== "") camposLlenos++;

    // Ahora son 5 campos. El paso 1 cubre del 0% al 25%.
    // Cada campo vale 5% (5 * 5 = 25).
    const porcentaje = camposLlenos * 5; 
    setProgressBar(porcentaje);
}

function setProgressBar(percent) {
    const finalPercent = Math.round(percent);
    
    // 1. Actualizar el ancho de la barra verde (Esto ya funcionaba)
    document.querySelectorAll('.progress-fill').forEach(el => {
        el.style.width = finalPercent + "%";
    });

    // 2. CORRECCIÓN: Actualizar el número usando la NUEVA CLASE
    // Antes buscaba '.progress-text', ahora busca '.progress-text-overlay'
    document.querySelectorAll('.progress-text-overlay').forEach(el => {
        el.innerText = finalPercent + "%";
    });
}
// --- FUNCIONES DE NAVEGACIÓN ---

function nextStep(targetStep) {
    if(currentStep === 1 && targetStep === 2) {
        const name = document.getElementById('p-name').value;
        const lastname = document.getElementById('p-lastname').value;
        const age = document.getElementById('p-age').value;
        const weight = document.getElementById('p-weight').value;
        const height = document.getElementById('p-height').value;
        const sex_id = document.getElementById('p-sex').value; // <--- NUEVO

        if(name.trim() === "" || lastname.trim() === "" || age === "" || weight === "" || height === "" || sex_id === "") {
            return alert("Por favor complete todos los datos, incluyendo el sexo.");
        }

        // Guardamos los datos separados para la BD
        patient.name = name;
        patient.lastname = lastname;
        patient.sex_id = sex_id;
        patient.age = parseInt(age);
        patient.weight = parseFloat(weight);
        patient.height = parseFloat(height);
        
        setProgressBar(25);
    }
    // ... resto de la función igual ...
    document.querySelectorAll('.step').forEach(el => el.classList.remove('active'));
    document.getElementById(`step-${targetStep}`).classList.add('active');
    currentStep = targetStep;
    resetMeasurement(); 
}

function resetMeasurement() {
    isMeasuring = false;
    muestrasActuales = 0;
    const ids = ['timer-bpm', 'timer-spo2', 'timer-temp'];
    ids.forEach(id => {
        if(document.getElementById(id)) document.getElementById(id).innerText = "Esperando señal estable...";
    });

    // Si estamos volviendo al paso 1 o iniciando, avisamos a la cara que se despierte
    if (currentStep === 1) { 
        socket.emit('reset_face'); 
    }
}

// --- LÓGICA DE RECOLECCIÓN Y PROGRESO DINÁMICO ---

function iniciarRecoleccion(type) {
    if(isMeasuring) return; 
    isMeasuring = true;
    console.log(`[SISTEMA] Iniciando recolección para ${type}`);

    // --- AGREGAR ESTO PARA EVITAR MEZCLAR DATOS VIEJOS ---
    if (type === 'bpm') patient.historyBPM = [];
    if (type === 'spo2') patient.historySpO2 = [];
    if (type === 'temp') historyTemp = [];
}

function actualizarProgreso(type) {
    const timerElement = document.getElementById(`timer-${type}`);
    timerElement.innerText = `Midiendo: ${muestrasActuales} / ${MUESTRAS_OBJETIVO} muestras`;
    timerElement.style.color = "#e67e22";

    // CÁLCULO DE LA BARRA VERDE
    const avanceEtapa = muestrasActuales / MUESTRAS_OBJETIVO; 
    let porcentajeTotal = 0;

    if (type === 'bpm') {
        // Etapa 2: Avanza del 25% al 50%
        porcentajeTotal = 25 + (avanceEtapa * 25);
    } else if (type === 'spo2') {
        // Etapa 3: Avanza del 50% al 75%
        porcentajeTotal = 50 + (avanceEtapa * 25);
    } else if (type === 'temp') {
        // Etapa 4: Avanza del 75% al 100%
        porcentajeTotal = 75 + (avanceEtapa * 25);
    }

    setProgressBar(porcentajeTotal);
}

function finalizarRecoleccion(type) {
    isMeasuring = false;
    const timerElement = document.getElementById(`timer-${type}`);
    const btnElement = document.getElementById(`btn-${type}`);

    timerElement.innerText = "✅ Medición completada";
    timerElement.style.color = "green";
    btnElement.innerText = "Siguiente >";
    
    // 1. Habilitar el botón (funcionalidad)
    btnElement.disabled = false;
    
    // 2. NUEVO: Quitar la clase gris para que se vea verde (estilo)
    btnElement.classList.remove('btn-disabled');
    
    // Asegurar hitos exactos
    if(type === 'bpm') setProgressBar(50);
    if(type === 'spo2') setProgressBar(75);
    if(type === 'temp') setProgressBar(100);
}

// --- RECEPCIÓN DE DATOS (SOCKET) ---

socket.on('sensorData', (data) => {
    const rawBPM = Math.round(data.heartRate || 0);
    const rawSpO2 = Math.round(data.spo2 || 0);
    const rawTemp = parseFloat(data.tempObject || 0).toFixed(1);
    const fingerDetected = data.finger_detected === true || data.finger_detected === "True";

    const elBpm = document.getElementById('val-bpm');
    const elSpo2 = document.getElementById('val-spo2');
    const elTemp = document.getElementById('val-temp');
    
    if(elBpm) elBpm.innerText = (fingerDetected && rawBPM > 0) ? rawBPM : "--";
    if(elSpo2) elSpo2.innerText = (fingerDetected && rawSpO2 > 0) ? rawSpO2 : "--";
    if(elTemp) elTemp.innerText = rawTemp;

    if (!isMeasuring && muestrasActuales >= MUESTRAS_OBJETIVO) return;

    // BPM
    if(currentStep === 2) { 
        let esValido = fingerDetected && (rawBPM > 40 && rawBPM < 220);
        if (esValido) {
            if (!isMeasuring) iniciarRecoleccion('bpm');
            patient.historyBPM.push(rawBPM);
            muestrasActuales++;
            actualizarProgreso('bpm');
            if (muestrasActuales >= MUESTRAS_OBJETIVO) finalizarRecoleccion('bpm');
        }
    }
    // SpO2
    if(currentStep === 3) { 
        let esValido = fingerDetected && (rawSpO2 > 85 && rawSpO2 <= 100);
        if (esValido) {
            if (!isMeasuring) iniciarRecoleccion('spo2');
            patient.historySpO2.push(rawSpO2 - 5);
            muestrasActuales++;
            actualizarProgreso('spo2');
            if (muestrasActuales >= MUESTRAS_OBJETIVO) finalizarRecoleccion('spo2');
        }
    }
    // Temp
    if(currentStep === 4) { 
        let esValido = (rawTemp > 32.0 && rawTemp < 45.0);
        if (esValido) {
            if (!isMeasuring) iniciarRecoleccion('temp');
            historyTemp.push(parseFloat(rawTemp));
            muestrasActuales++;
            actualizarProgreso('temp');
            if (muestrasActuales >= MUESTRAS_OBJETIVO) finalizarRecoleccion('temp');
        }
    }
});

// --- DIAGNÓSTICOS ---

function calcularPromedio(arr) {
    if(arr.length === 0) return 0;
    const sum = arr.reduce((a, b) => a + b, 0);
    return (sum / arr.length).toFixed(1);
}

function obtenerDiagnosticoIMC(peso, tallaCm) {
    let tallaM = (tallaCm > 3.0) ? tallaCm / 100 : tallaCm; 
    if (tallaM === 0) return { valor: 0, texto: "Error", color: "black" };
    const imc = (peso / (tallaM * tallaM)).toFixed(1);
    let diag = "", color = "";
    if (imc < 18.5) { diag = "Bajo Peso"; color = "#e74c3c"; } 
    else if (imc < 25) { diag = "Normal"; color = "#27ae60"; } 
    else if (imc < 30) { diag = "Sobrepeso"; color = "#f39c12"; } 
    else { diag = "Obesidad"; color = "#c0392b"; } 
    return { valor: imc, texto: diag, color: color };
}

function obtenerDiagnosticoBPM(bpm, edad) {
    const rango = RANGOS_MEDICOS.BPM.find(r => edad <= r.edadMax) || RANGOS_MEDICOS.BPM[RANGOS_MEDICOS.BPM.length - 1];
    let diag = "", color = "";
    if (bpm < rango.min) { diag = "Bradicardia"; color = "#f39c12"; } 
    else if (bpm > rango.max) { diag = "Taquicardia"; color = "#c0392b"; } 
    else { diag = "Normal"; color = "#27ae60"; }
    return { valor: bpm, texto: diag, color: color, rango: `${rango.min}-${rango.max}` };
}

function obtenerDiagnosticoTemp(temp) {
    let diag = "", color = "";
    const r = RANGOS_MEDICOS.TEMP;
    if (temp < r.hipotermia) { diag = "Hipotermia"; color = "#3498db"; } 
    else if (temp <= r.normalMax) { diag = "Normal"; color = "#27ae60"; } 
    else if (temp <= r.fiebreLeve) { diag = "Febrícula"; color = "#f39c12"; } 
    else { diag = "Fiebre"; color = "#c0392b"; }
    return { valor: temp, texto: diag, color: color };
}

function obtenerDiagnosticoSpO2(spo2) {
    let diag = "", color = "";
    const r = RANGOS_MEDICOS.SPO2;
    if (spo2 >= r.normal) { diag = "Normal"; color = "#27ae60"; } 
    else if (spo2 >= r.hipoxiaLeve) { diag = "Hipoxia Leve"; color = "#f39c12"; } 
    else { diag = "Hipoxia Sev."; color = "#c0392b"; }
    return { valor: spo2 + "%", texto: diag, color: color };
}

// --- FINALIZACIÓN ---

function finalizar() {
    const valBPM = Math.round(calcularPromedio(patient.historyBPM));
    const valSpO2 = Math.round(calcularPromedio(patient.historySpO2));
    const valTemp = calcularPromedio(historyTemp);

    const dIMC = obtenerDiagnosticoIMC(patient.weight, patient.height);
    const dBPM = obtenerDiagnosticoBPM(valBPM, patient.age);
    const dSpO2 = obtenerDiagnosticoSpO2(valSpO2);
    const dTemp = obtenerDiagnosticoTemp(valTemp);

    patient.heart_rate = valBPM;
    patient.spo2 = valSpO2;
    patient.tempObject = valTemp;
    patient.bmi = dIMC.valor;

    guardarEnBaseDeDatos();

    // 1. Determinar qué cara poner basada en el diagnóstico final
    let colorFinal = 0; // Normal
    if (dTemp.color === "#c0392b" || dTemp.color === "#3498db") colorFinal = 1; // Fiebre/Hipotermia (Rojo/Azul - simplificado a Rojo aquí o ajusta lógica)
    if (dSpO2.color === "#c0392b") colorFinal = 3; // Hipoxia (Verde/Mareado)
    
    // Si quieres ser muy preciso con tu lógica de colores de cara:
    // face-1: Rojo (Fiebre), face-2: Azul (Hipotermia), face-3: Verde (SpO2 bajo)
    if (valTemp > 37.5) colorFinal = 1;
    else if (valTemp < 35.0) colorFinal = 2;
    else if (valSpO2 < 90) colorFinal = 3;

    // 2. Enviar evento al servidor para actualizar la cara
    socket.emit('finalizar_chequeo', {
        temp: valTemp,
        spo2: valSpO2,
        bpm: valBPM,
        faceColor: colorFinal
    });

    const resumenHTML = `
        <div style="background: #eef2f3; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
            <p style="margin:5px 0; font-size: 1.2rem;"><strong>👤 ${patient.name}</strong> (${patient.age} años)</p>
            <p style="margin:5px 0; color: #555;">📏 ${patient.height} cm | ⚖️ ${patient.weight} kg</p>
        </div>

        <div style="display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; margin-bottom: 20px;">
            <div style="flex: 1; min-width: 140px; background: white; padding: 10px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); border-top: 4px solid ${dIMC.color};">
                <div style="font-size: 0.8rem; color: #7f8c8d; font-weight: bold;">IMC</div>
                <div style="font-size: 1.8rem; font-weight: bold; color: ${dIMC.color}; margin: 5px 0;">${dIMC.valor}</div>
                <div style="font-size: 0.9rem; font-weight: bold; color: ${dIMC.color}; text-transform: uppercase;">${dIMC.texto}</div>
            </div>
            <div style="flex: 1; min-width: 140px; background: white; padding: 10px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); border-top: 4px solid ${dBPM.color};">
                <div style="font-size: 0.8rem; color: #7f8c8d; font-weight: bold;">RITMO (BPM)</div>
                <div style="font-size: 1.8rem; font-weight: bold; color: ${dBPM.color}; margin: 5px 0;">${dBPM.valor}</div>
                <div style="font-size: 0.9rem; font-weight: bold; color: ${dBPM.color}; text-transform: uppercase;">${dBPM.texto}</div>
                <div style="font-size: 0.7rem; color: #aaa;">Rango: ${dBPM.rango}</div>
            </div>
            <div style="flex: 1; min-width: 140px; background: white; padding: 10px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); border-top: 4px solid ${dSpO2.color};">
                <div style="font-size: 0.8rem; color: #7f8c8d; font-weight: bold;">OXÍGENO</div>
                <div style="font-size: 1.8rem; font-weight: bold; color: ${dSpO2.color}; margin: 5px 0;">${dSpO2.valor}</div>
                <div style="font-size: 0.9rem; font-weight: bold; color: ${dSpO2.color}; text-transform: uppercase;">${dSpO2.texto}</div>
            </div>
            <div style="flex: 1; min-width: 140px; background: white; padding: 10px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); border-top: 4px solid ${dTemp.color};">
                <div style="font-size: 0.8rem; color: #7f8c8d; font-weight: bold;">TEMP (°C)</div>
                <div style="font-size: 1.8rem; font-weight: bold; color: ${dTemp.color}; margin: 5px 0;">${dTemp.valor}</div>
                <div style="font-size: 0.9rem; font-weight: bold; color: ${dTemp.color}; text-transform: uppercase;">${dTemp.texto}</div>
            </div>
        </div>
        <hr>
    `;
    
    document.getElementById('resumen-texto').innerHTML = resumenHTML;

    nextStep(5);

    setTimeout(() => {
        dibujarGrafico('chartBPM', 'BPM', patient.historyBPM, dBPM.color);
        dibujarGrafico('chartSpO2', 'SpO2 %', patient.historySpO2, dSpO2.color);
        // dibujarGrafico('chartTemp', 'Temp °C', historyTemp, dTemp.color); // Oculto
    }, 100);
}

function dibujarGrafico(canvasId, label, dataArray, color) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    const labels = dataArray.map((_, index) => index + 1);

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: dataArray,
                borderColor: color,
                backgroundColor: color,
                borderWidth: 2,
                pointRadius: 2,
                tension: 0.4 
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } }, 
            scales: { x: { display: false }, y: { beginAtZero: false } }
        }
    });
}

async function guardarEnBaseDeDatos() {
    const datospatient = {
        name: patient.name,
        lastname: patient.lastname,
        age: patient.age,
        sex_id: patient.sex_id,
        weight: patient.weight,
        height: patient.height,
        bmi: patient.bmi,
        heart_rate: patient.heart_rate,
        history_bpm: patient.historyBPM,
        spo2: patient.spo2,
        history_spo2: patient.historySpO2,
        tempObject: patient.tempObject
    };

    try {
        const respuesta = await fetch('/api/guardar_paciente', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(datospatient)
        });

        const resultado = await respuesta.json();
        if (resultado.status === 'success') {
            console.log("✅ Datos guardados en MySQL correctamente ID:", resultado.id);
            alert("¡Chequeo guardado en la base de datos!");
        } else {
            console.error("❌ Error guardando datos:", resultado.message);
            alert("Hubo un error al guardar en la base de datos.");
        }
    } catch (error) {
        console.error("❌ Error de red:", error);
    }
}