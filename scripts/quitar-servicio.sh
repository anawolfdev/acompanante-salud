#!/bin/bash
# Para el Acompanante de salud y quita el arranque automático (macOS).
#
# Uso:
#   ./scripts/quitar-servicio.sh
#
# No borra tus citas (datos/salud.db) ni el archivo .env.

set -euo pipefail

ETIQUETA="com.anawolfdev.acompanante"
DESTINO="$HOME/Library/LaunchAgents/$ETIQUETA.plist"
USUARIO="$(id -u)"
DOMINIO="gui/$USUARIO"

# Descarga el servicio. Si no estaba cargado, no pasa nada.
launchctl bootout "$DOMINIO/$ETIQUETA" >/dev/null 2>&1 \
    || launchctl unload -w "$DESTINO" >/dev/null 2>&1 \
    || true

if [ -f "$DESTINO" ]; then
    rm "$DESTINO"
    echo "Servicio parado y archivo borrado:"
    echo "  $DESTINO"
else
    echo "El servicio no estaba instalado."
fi

echo
echo "Ya no arrancará solo al encender el Mac."
echo "Los logs siguen en ~/Library/Logs (no los borro por si los necesitas)."
echo "Tus citas y tus claves siguen donde estaban."
