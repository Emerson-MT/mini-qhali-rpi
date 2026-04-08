// script.js (Cara del Robot)

// ==========================================
// 1. DEFINICIÓN DE FUNCIONES (Herramientas)
// ==========================================

// --- Control de parpadeo ---
// Regla: blinkFlag = 0 -> animaciones ON, 1 -> animaciones OFF
(function () {
  const root = document.body;

  window.setBlink = function setBlink(flag) {
    const paused = Number(flag) === 1;
    if (paused) {
      root.classList.add("blink-off");
      console.log("[CLIENT] Parpadeo: OFF (blinkFlag=1)");
    } else {
      root.classList.remove("blink-off");
      console.log("[CLIENT] Parpadeo: ON  (blinkFlag=0)");
    }
  };
})();

// --- Control de rostro (mejillas) ---
// faceFlag: 0=normal, 1=rojo, 2=azul, 3=verde
(function () {
  const root = document.body;
  const cls = ["face-1", "face-2", "face-3"];

  window.setFace = function setFace(flag) {
    const f = Number(flag) || 0;
    // Limpia clases previas
    cls.forEach(c => root.classList.remove(c));
    // Agrega la nueva si corresponde
    if (f >= 1 && f <= 3) root.classList.add(`face-${f}`);
    console.log("[CLIENT] setFace ->", f);
  };
})();

// --- Control de Sensores (HUD) ---
// (Desactivado visualmente en la cara, pero mantenemos la función vacía para evitar errores)
window.updateSensors = function(data) {
    // Aquí podrias hacer console.log si quieres depurar sin ensuciar la pantalla
    // console.log("[DEBUG] Datos latentes:", data);
};


// ==========================================
// 2. CONEXIÓN Y EVENTOS (Lógica)
// ==========================================

const socket = io();

socket.on("connect", () => console.log("[CLIENT] Cara conectada al cerebro:", socket.id));

// Como las funciones ya están definidas arriba, podemos llamarlas directamente
socket.on('blinkFlag', (value) => setBlink(value));
socket.on('faceFlag', (value)  => setFace(value));
socket.on('sensorData', (data) => updateSensors(data));


// ==========================================
// 3. INICIALIZACIÓN (Estado al cargar)
// ==========================================

// Pedimos al servidor el estado actual por si llegamos tarde a la fiesta
Promise.all([
  fetch('/blink').then(r => r.json()),
  fetch('/face').then(r => r.json())
]).then(([{ blinkFlag }, { faceFlag }]) => {
  setBlink(blinkFlag);
  setFace(faceFlag);
}).catch(console.error);