# src/miniqhali_lib/user_comm/silence_alsa.py
import ctypes

# Definimos el prototipo de la función callback para el manejador de errores de ALSA
# void alsa_error_handler(const char *file, int line, const char *function, int err, const char *fmt, ...)
ERROR_HANDLER_FUNC = ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p)

def silent_alsa_handler(file, line, function, err, fmt, *args):
    # Dejar completamente vacío para ignorar el mensaje de error
    pass

# Mantener la referencia global para evitar que el Garbage Collector lo elimine
_c_error_handler = ERROR_HANDLER_FUNC(silent_alsa_handler)

def silence_alsa():
    """Sobreescribe el manejador de errores de ALSA para silenciar la consola."""
    try:
        # Cargamos la librería dinámica de ALSA en Linux
        asound = ctypes.cdll.LoadLibrary('libasound.so.2')
        # Buscamos la función nativa que configura el manejador de errores
        asound.snd_lib_error_set_handler(_c_error_handler)
        print("🔇 Logs nativos de ALSA silenciados exitosamente.")
    except Exception as e:
        # Fallback silencioso si no se encuentra la librería o estás en otro OS
        print(f"⚠️ No se pudo silenciar ALSA nativo: {e}")