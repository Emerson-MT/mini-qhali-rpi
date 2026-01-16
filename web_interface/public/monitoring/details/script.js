// monitoring/details/detail.js

const pathSegments = window.location.pathname.split('/');
const patientId = pathSegments[pathSegments.length - 1];

// Variables globales para los gráficos (para poder destruirlos si recargamos)
let chartBPMInstance = null;
let chartSpO2Instance = null;

document.addEventListener("DOMContentLoaded", () => {
    fetchPatientDetails(patientId);
    startClock();
});

async function fetchPatientDetails(id) {
    try {
        const response = await fetch(`/api/pacientes/${id}`);
        const result = await response.json();

        if(result.status === "success") {
            const p = result.data;
            
            // 1. Llenar Textos (Igual que antes)
            const dateObj = new Date(p.date_register);
            const timeStr = dateObj.toLocaleTimeString('es-PE', {hour: '2-digit', minute:'2-digit', hour12:true});

            document.getElementById('d-name').innerText = `${p.lastname}, ${p.name}`;
            document.getElementById('d-age').innerText = p.age;
            document.getElementById('d-sex').innerText = p.sex_id;
            document.getElementById('d-time').innerText = timeStr;
            document.getElementById('d-val-temp').innerText = p.tempObject + "°C";
            document.getElementById('d-val-spo2').innerText = p.spo2 + "%";
            document.getElementById('d-val-bpm').innerText = p.heart_rate + " bpm";

            // 2. Generar Notas (Igual que antes)
            const notesList = document.getElementById('d-notes');
            notesList.innerHTML = "";
            if(p.tempObject > 37.5) notesList.innerHTML += "<li>• Temperatura corporal elevada.</li>";
            if(p.spo2 < 95) notesList.innerHTML += "<li>• Saturación de oxígeno baja.</li>";
            if(p.heart_rate > 100) notesList.innerHTML += "<li>• Frecuencia cardiaca elevada.</li>";
            if(notesList.innerHTML === "") notesList.innerHTML = "<li>Valores dentro de rangos normales.</li>";

            // 3. PROCESAR DATOS DE GRÁFICOS (NUEVO)
            // Convertimos el texto de la DB a Arreglo real.
            // Si viene null o vacío, usamos "[]" para evitar errores.
            const arrayBPM = JSON.parse(p.history_bpm || "[]");
            const arraySpO2 = JSON.parse(p.history_spo2 || "[]");

            // Dibujar los gráficos
            renderMedicalChart('chartBPM', 'BPM', arrayBPM, '#32CD32'); // Verde Lima
            renderMedicalChart('chartSpO2', 'SpO2', arraySpO2, '#00FFFF'); // Cyan/Celeste

        } else {
            alert("Error: Paciente no encontrado");
        }
    } catch(e) {
        console.error(e);
        // alert("Error de conexión"); // Comentado para no molestar si hay error silencioso
    }
}

// Función Reutilizable para dibujar gráficos estilo "Monitor Médico"
function renderMedicalChart(canvasId, label, dataArray, lineColor) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    // Generar etiquetas simples (1, 2, 3...) según la cantidad de datos
    const labels = dataArray.map((_, i) => i + 1);

    // Crear el gráfico
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: dataArray,
                borderColor: lineColor,
                backgroundColor: lineColor, // Color de fondo del punto (si se viera)
                borderWidth: 2,
                pointRadius: 0,       // Sin puntos, solo línea limpia
                pointHoverRadius: 4,  // Punto aparece al pasar el mouse
                tension: 0.4,         // Curvas suaves (Bézier)
                fill: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }, // Ocultar leyenda para más realismo
                tooltip: {
                    mode: 'index',
                    intersect: false,
                }
            },
            scales: {
                x: {
                    display: false, // Ocultar eje X (tiempo) para limpieza
                    grid: { display: false }
                },
                y: {
                    display: true,
                    grid: {
                        color: '#333', // Grilla muy sutil gris oscuro
                        borderDash: [5, 5]
                    },
                    ticks: {
                        color: '#888', // Números del eje Y en gris
                        font: { size: 10 }
                    }
                    // Opcional: forzar rangos si quieres que se vea estático
                    // min: 40, max: 140 
                }
            },
            animation: {
                duration: 1500, // Animación de entrada suave
                easing: 'easeOutQuart'
            }
        }
    });
}

function startClock() {
    const clock = document.getElementById('clock');
    if(clock) {
        setInterval(() => {
            const now = new Date();
            clock.innerText = now.toLocaleTimeString('es-PE', { hour12: true });
        }, 1000);
    }
}