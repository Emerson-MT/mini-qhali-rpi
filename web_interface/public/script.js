// script.js

// --- Control de parpadeo ---
// Regla: blinkFlag = 0 -> parpadeo natural (animaciones ON)
//        blinkFlag = 1 -> parpadeo pausado (animaciones OFF)
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
    // limpia clases previas
    cls.forEach(c => root.classList.remove(c));
    if (f >= 1 && f <= 3) root.classList.add(`face-${f}`);
    console.log("[CLIENT] setFace ->", f);
  };
})();

// --- Control de Sensores (HUD) ---
(function () {
  const elTemp = document.getElementById("show-temp");
  const elSpo2 = document.getElementById("show-spo2");
  const elHr   = document.getElementById("show-hr");

  // Escuchamos el evento que crearemos en el servidor
  // Asumimos que socket ya está definido globalmente o accedemos a él
  // Nota: Si socket está en el HTML, mejor mueve esta lógica al bloque script del HTML
  // O expón una función global:
  
  window.updateSensors = function(data) {
    if(!data) return;
    
    // Actualizamos el texto
    if(elTemp) elTemp.innerText = parseFloat(data.tempObject).toFixed(1);
    if(elSpo2) elSpo2.innerText = Math.round(data.spo2);
    if(elHr)   elHr.innerText   = Math.round(data.heartRate);
    
    console.log("[CLIENT] Sensores actualizados:", data);
  };
})();
