#!/bin/bash
# Instala el Acompanante de salud para que arranque solo con el Mac (macOS).
#
# Uso:
#   ./scripts/instalar-servicio.sh
#   PYTHON=/ruta/a/python3 ./scripts/instalar-servicio.sh
#
# Hace tres cosas:
#   1. Rellena la plantilla deploy/com.anawolfdev.acompanante.plist.
#   2. La copia en ~/Library/LaunchAgents.
#   3. La carga con launchctl para que empiece a funcionar ya.

set -euo pipefail

ETIQUETA="com.anawolfdev.acompanante"
CARPETA_SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROYECTO="$(cd "$CARPETA_SCRIPT/.." && pwd)"
PLANTILLA="$PROYECTO/deploy/$ETIQUETA.plist"
DESTINO="$HOME/Library/LaunchAgents/$ETIQUETA.plist"
CARPETA_LOGS="$HOME/Library/Logs"
LOG="$CARPETA_LOGS/acompanante.log"
LOG_ERROR="$CARPETA_LOGS/acompanante-error.log"

if [ ! -f "$PLANTILLA" ]; then
    echo "No encuentro la plantilla: $PLANTILLA"
    echo "¿Está el script dentro de la carpeta del proyecto?"
    exit 1
fi

PYTHON="${PYTHON:-$(command -v python3 || true)}"
if [ -z "$PYTHON" ]; then
    echo "No encuentro python3."
    echo "Instala Python 3.10 o más nuevo y vuelve a intentarlo."
    exit 1
fi
if [ ! -x "$PYTHON" ]; then
    echo "El python no se puede ejecutar: $PYTHON"
    exit 1
fi
if ! "$PYTHON" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)'; then
    echo "El python es demasiado antiguo: $PYTHON"
    echo "Hace falta Python 3.10 o más nuevo."
    exit 1
fi

if [ ! -f "$PROYECTO/.env" ]; then
    echo "Aviso: no hay archivo .env en $PROYECTO."
    echo "El bot puede arrancar, pero no tendrá las claves de Telegram."
    echo "Puedes seguir: el servicio se instala igual."
    echo
fi

mkdir -p "$HOME/Library/LaunchAgents" "$CARPETA_LOGS"
touch "$LOG" "$LOG_ERROR"

# Rellena la plantilla con las rutas de este Mac.
# Se usa plistlib, que viene con Python: no hace falta instalar nada.
"$PYTHON" - "$PLANTILLA" "$DESTINO" "$PYTHON" "$PROYECTO" "$LOG" "$LOG_ERROR" <<'FIN'
import plistlib
import sys

plantilla, destino, python, proyecto, log, log_error = sys.argv[1:7]

with open(plantilla, "rb") as archivo:
    datos = plistlib.load(archivo)

datos["ProgramArguments"][0] = python
datos["WorkingDirectory"] = proyecto
datos["StandardOutPath"] = log
datos["StandardErrorPath"] = log_error

with open(destino, "wb") as archivo:
    plistlib.dump(datos, archivo)
FIN

if command -v plutil >/dev/null 2>&1; then
    plutil -lint "$DESTINO" >/dev/null
fi

USUARIO="$(id -u)"
DOMINIO="gui/$USUARIO"

# Si ya estaba cargado, se descarga primero para coger los cambios.
launchctl bootout "$DOMINIO/$ETIQUETA" >/dev/null 2>&1 || true
launchctl enable "$DOMINIO/$ETIQUETA" >/dev/null 2>&1 || true

if ! launchctl bootstrap "$DOMINIO" "$DESTINO"; then
    echo "No se ha podido cargar de la forma nueva. Probando la forma antigua..."
    launchctl load -w "$DESTINO"
fi

echo
echo "Servicio instalado y arrancado."
echo "Usa este python: $PYTHON"
echo "Carpeta del proyecto: $PROYECTO"
echo
echo "Para ver si está funcionando:"
echo "  launchctl list | grep acompanante"
echo
echo "Para ver los mensajes:"
echo "  tail -f \"$LOG\""
echo
echo "Para ver los errores:"
echo "  tail -f \"$LOG_ERROR\""
echo
echo "Para pararlo y quitarlo:"
echo "  ./scripts/quitar-servicio.sh"
