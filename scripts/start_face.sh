#!/bin/bash
# 1. Ubicación de la llave que ya encontramos
# Sincronizamos la autoridad
# 1. Variables de entorno con la llave que ya conocemos
export DISPLAY=:0
export XAUTHORITY=/home/ubuntu/.Xauthority

# 2. Asegurar que la cookie esté registrada
# (Esto evita el error de MIT-MAGIC-COOKIE-1 si el archivo se borra)
xauth add ubuntu-desktop/unix:0 MIT-MAGIC-COOKIE-1 a079edf5b8e74edbd0382111452e2f3f

# 3. Desbloquear el acceso al display
xhost +local:ubuntu > /dev/null 2>&1

# 4. Limpieza de procesos
pkill -f chromium
sleep 1
rm -rf /tmp/chromium_kiosk

echo "🚀 Lanzando rostro en Waveshare 3.5..."
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