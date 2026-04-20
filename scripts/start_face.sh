#!/bin/bash
# 1. Configuración de entorno para entorno gráfico
export DISPLAY=:0
export XAUTHORITY=/home/ubuntu/.Xauthority

# 2. Limpieza total de procesos y bloqueos previos
echo "🔄 Limpiando instancias de Chromium..."
pkill -f chromium
sleep 1

# Eliminar archivos de bloqueo que impiden que Chromium abra si hubo un crash
rm -rf ~/.config/chromium/Singleton*
rm -rf /tmp/chromium_kiosk/Singleton*

echo "🚀 Abriendo cara del robot en modo Kiosco..."
# 3. Lanzamiento de Chromium con todas las optimizaciones
/snap/bin/chromium \
  --kiosk \
  --start-fullscreen \
  --app="http://localhost:3000" \
  --window-position=0,0 \
  --window-size=480,320 \
  --user-data-dir=/tmp/chromium_kiosk \
  --no-first-run \
  --disable-infobars \
  --no-sandbox \
  --disable-session-crashed-bubble \
  --check-for-update-interval=31536000 \
  --disable-features=Translate,TranslateUI,TranslateSettings,LanguageDetection \
  --disable-translate \
  --accept-lang=es-PE,es \
  --lang=es \
  --disable-gpu \
  --no-errdialogs \
  --incognito > /dev/null 2>&1 &

# 4. Ajustes de Energía y Pantalla (Evitar que se apague)
echo "⚡ Desactivando gestión de energía de la pantalla..."
xset s off
xset dpms 0 0 0
xset -dpms