// face/script.js

// ==========================================
// 1. DEFINICIÓN DE FUNCIONES (Visuales)
// ==========================================

// --- Control de parpadeo ---
(function () {
  const root = document.body;
  window.setBlink = function setBlink(flag) {
    const paused = Number(flag) === 1;
    if (paused) {
      root.classList.add("blink-off");
    } else {
      root.classList.remove("blink-off");
    }
  };
})();

// --- Control de rostro (mejillas) ---
// faceFlag: 0=normal, 1=rojo (fiebre), 2=azul (hipotermia), 3=verde (hipoxia)
(function () {
  const root = document.body;
  const cls = ["face-1", "face-2", "face-3"];

  window.setFace = function setFace(flag) {
    const f = Number(flag) || 0;
    // Limpia clases previas
    cls.forEach(c => root.classList.remove(c));
    // Agrega la nueva si corresponde
    if (f >= 1 && f <= 3) root.classList.add(`face-${f}`);
    console.log("[CLIENT] Cara cambiada a estado:", f);
  };
})();

// ==========================================
// 2. LÓGICA DE SOCKETS
// ==========================================

const socket = io();

// ESTADO: Determina si la cara está "bloqueada" mostrando el diagnóstico final
let isShowingResults = false; 

socket.on("connect", () => console.log("[CLIENT] Cara conectada al cerebro"));

// --- A) EVENTOS BÁSICOS ---
socket.on('blinkFlag', (value) => setBlink(value));

// --- B) CAMBIO DE CARA EN VIVO ---
// Este evento lo envía el servidor automáticamente cuando llegan datos del sensor.
socket.on('faceFlag', (value) => {
    // IMPORTANTE: Solo cambiamos la cara si NO estamos mostrando el resultado final.
    // Esto evita que el sensor "interrumpa" la reacción final.
    if (!isShowingResults) {
        setFace(value);
    }
});

// --- C) RESULTADOS FINALES (Evento nuevo) ---
// Este evento llega cuando en el celular se pulsa "Finalizar"
socket.on('show_results', (data) => {
    console.log("🏁 Diagnóstico final recibido:", data);
    
    // 1. Bloqueamos actualizaciones futuras de los sensores
    isShowingResults = true;

    // 2. Forzamos la cara correspondiente al diagnóstico final
    // data.faceColor viene calculado desde mobile.js
    setFace(data.faceColor); 
});

// --- D) RESETEAR (Opcional) ---
// Para desbloquear la cara cuando inicies un nuevo paciente
socket.on('reset_face', () => {
    console.log("🔄 Reseteando cara para nuevo paciente");
    isShowingResults = false;
    setFace(0); // Vuelve a normal
});

// ==========================================
// 3. INICIALIZACIÓN
// ==========================================

// Sincronizar estado inicial al cargar la página
Promise.all([
  fetch('/blink').then(r => r.json()),
  fetch('/face').then(r => r.json())
]).then(([{ blinkFlag }, { faceFlag }]) => {
  setBlink(blinkFlag);
  // Solo aplicamos la cara inicial si no estamos bloqueados (por seguridad)
  if(!isShowingResults) setFace(faceFlag);
}).catch(console.error);