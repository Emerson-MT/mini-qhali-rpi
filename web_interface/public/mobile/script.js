// mobile.js

const socket = io();

// --- CONFIGURACIÓN ---
const TIEMPO_MEDICION = 15; // Segundos que dura cada etapa

// --- ESTADO GLOBAL ---
let paciente = { nombre: "", edad: "" };

// Almacenes de datos (Aquí guardaremos todo lo que llegue en los 15s)
let historyBPM = [];
let historySpO2 = [];
let historyTemp = [];

// Promedios finales
let avgBPM = 0, avgSpO2 = 0, avgTemp = 0;

// Variables de control de medición
let currentStep = 1;
let isMeasuring = false;
let timeLeft = TIEMPO_MEDICION;
let timerInterval = null;

// --- FUNCIONES DE NAVEGACIÓN ---

function nextStep(targetStep) {
    // 1. Validación del Paso 1
    if(currentStep === 1 && targetStep === 2) {
        const nombre = document.getElementById('p-name').value;
        const edad = document.getElementById('p-age').value;
        if(nombre.trim() === "") return alert("Ingrese nombre");
        paciente.nombre = nombre;
        paciente.edad = edad;
    }

    // 2. Transición visual
    document.querySelectorAll('.step').forEach(el => el.classList.remove('active'));
    document.getElementById(`step-${targetStep}`).classList.add('active');
    
    currentStep = targetStep;

    // 3. Preparar la nueva medición según el paso
    resetMeasurement(); // Reiniciamos temporizadores y banderas

    if(targetStep === 2) console.log("Listo para medir BPM...");
    if(targetStep === 3) console.log("Listo para medir SpO2...");
    if(targetStep === 4) console.log("Listo para medir Temp...");
}

function resetMeasurement() {
    isMeasuring = false;
    timeLeft = TIEMPO_MEDICION;
    clearInterval(timerInterval);
    // Actualizamos textos de UI
    if(document.getElementById('timer-bpm')) document.getElementById('timer-bpm').innerText = "Esperando sensor...";
    if(document.getElementById('timer-spo2')) document.getElementById('timer-spo2').innerText = "Esperando sensor...";
    if(document.getElementById('timer-temp')) document.getElementById('timer-temp').innerText = "Esperando sensor...";
}

// --- LÓGICA DEL TEMPORIZADOR ---

function startTimer(type) {
    if(isMeasuring) return; // Si ya está corriendo, no hacer nada
    isMeasuring = true;

    console.log(`[TIMER] Iniciando cuenta regresiva para ${type}`);
    
    const timerElement = document.getElementById(`timer-${type}`);
    const btnElement = document.getElementById(`btn-${type}`);

    // Intervalo de 1 segundo
    timerInterval = setInterval(() => {
        timeLeft--;
        timerElement.innerText = `Midiendo: ${timeLeft}s restantes`;

        if(timeLeft <= 0) {
            stopTimer(type, btnElement, timerElement);
        }
    }, 1000);
}

function stopTimer(type, btnElement, timerElement) {
    clearInterval(timerInterval);
    isMeasuring = false; // Dejamos de aceptar datos nuevos para el historial
    
    timerElement.innerText = "✅ Medición completada";
    timerElement.style.color = "green";
    
    // Habilitar botón de siguiente
    btnElement.innerText = "Siguiente >";
    btnElement.disabled = false;

    // Calcular promedio inmediato para logs (opcional)
    console.log(`[TIMER] Fin de ${type}. Datos recolectados.`);
}

// --- RECEPCIÓN DE DATOS (SOCKET) ---

socket.on('sensorData', (data) => {
    // Valores crudos
    const rawBPM = Math.round(data.heartRate || 0);
    const rawSpO2 = Math.round(data.spo2 || 0);
    const rawTemp = parseFloat(data.tempObject || 0).toFixed(1);

    // 1. Mostrar siempre el valor en vivo (feedback visual)
    const elBpm = document.getElementById('val-bpm');
    const elSpo2 = document.getElementById('val-spo2');
    const elTemp = document.getElementById('val-temp');
    
    if(elBpm) elBpm.innerText = rawBPM;
    if(elSpo2) elSpo2.innerText = rawSpO2;
    if(elTemp) elTemp.innerText = rawTemp;

    // 2. LÓGICA DE CAPTURA SEGÚN EL PASO ACTUAL
    
    // --- PASO 2: BPM ---
    if(currentStep === 2) {
        // Solo empezamos si detectamos un valor válido (> 40 para evitar ruido)
        if(!isMeasuring && rawBPM > 40 && timeLeft === TIEMPO_MEDICION) {
            startTimer('bpm');
        }
        
        // Si el tiempo está corriendo, guardamos el dato
        if(isMeasuring && rawBPM > 40) {
            historyBPM.push(rawBPM);
        }
    }

    // --- PASO 3: SpO2 ---
    if(currentStep === 3) {
        if(!isMeasuring && rawSpO2 > 80 && timeLeft === TIEMPO_MEDICION) {
            startTimer('spo2');
        }
        if(isMeasuring && rawSpO2 > 50) {
            historySpO2.push(rawSpO2);
        }
    }

    // --- PASO 4: Temperatura ---
    if(currentStep === 4) {
        if(!isMeasuring && rawTemp > 30 && timeLeft === TIEMPO_MEDICION) {
            startTimer('temp');
        }
        if(isMeasuring && rawTemp > 30) {
            historyTemp.push(parseFloat(rawTemp));
        }
    }
});

// --- FINALIZACIÓN Y GRÁFICAS ---

function calcularPromedio(arr) {
    if(arr.length === 0) return 0;
    const sum = arr.reduce((a, b) => a + b, 0);
    return (sum / arr.length).toFixed(1);
}

function finalizar() {
    // 1. Calcular promedios finales
    avgBPM = Math.round(calcularPromedio(historyBPM));
    avgSpO2 = Math.round(calcularPromedio(historySpO2));
    avgTemp = calcularPromedio(historyTemp);

    // 2. Mostrar Resumen Texto
    const resumenHTML = `
        <p><strong>👤 Paciente:</strong> ${paciente.nombre} (${paciente.edad} años)</p>
        <hr>
        <p>❤️ <strong>Promedio BPM:</strong> ${avgBPM}</p>
        <p>💧 <strong>Promedio SpO2:</strong> ${avgSpO2}%</p>
        <p>🌡️ <strong>Promedio Temp:</strong> ${avgTemp}°C</p>
    `;
    document.getElementById('resumen-texto').innerHTML = resumenHTML;

    // 3. Ir al paso 5
    nextStep(5);

    // 4. DIBUJAR LAS GRÁFICAS (Chart.js)
    // Pequeño delay para asegurar que el canvas sea visible
    setTimeout(() => {
        dibujarGrafico('chartBPM', 'BPM', historyBPM, 'red');
        dibujarGrafico('chartSpO2', 'SpO2 %', historySpO2, 'blue');
        dibujarGrafico('chartTemp', 'Temp °C', historyTemp, 'orange');
    }, 100);
}

function dibujarGrafico(canvasId, label, dataArray, color) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    // Generamos etiquetas simples (1, 2, 3...) para el eje X
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
                pointRadius: 1,
                tension: 0.4 // Suaviza la curva
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } }, // Ocultar leyenda para ahorrar espacio
            scales: {
                x: { display: false }, // Ocultar eje X
                y: { beginAtZero: false } // Auto-escala eje Y
            }
        }
    });
}