#!/bin/bash
# Añade «Semitonos DTF» al menú de aplicaciones de ESTE ordenador (un lanzador y su icono).
# No copia ni instala el programa: el lanzador apunta al ejecutable allí donde esté ahora mismo.
#
# Uso:  ./crear_acceso_directo.sh [ruta/al/ejecutable]
#       (sin ruta usa ../Portable/Semitonos DTF)
# Para quitarlo:  ./eliminar_acceso_directo.sh
set -e
ID="semitonos-dtf"
AQUI="$(cd "$(dirname "$0")" && pwd)"
EJECUTABLE="$(realpath "${1:-$AQUI/../Portable/Semitonos DTF}")"
[ -x "$EJECUTABLE" ] || { echo "No encuentro el ejecutable: $EJECUTABLE"; exit 1; }

ICONO="$HOME/.local/share/icons/hicolor/256x256/apps/$ID.png"
LANZADOR="$HOME/.local/share/applications/$ID.desktop"
mkdir -p "$(dirname "$ICONO")" "$(dirname "$LANZADOR")"
cp "$AQUI/recursos/icono.png" "$ICONO"          # el icono se copia: el menú no depende de esta carpeta
cat > "$LANZADOR" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Semitonos DTF
Comment=Prepara imágenes para estampar en DTF con semitonos
Exec="$EJECUTABLE" %f
Icon=$ICONO
Terminal=false
Categories=Graphics;
MimeType=image/png;image/jpeg;image/webp;image/tiff;
DESKTOP
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
echo "Listo: «Semitonos DTF» ya sale en el menú de aplicaciones (apunta a $EJECUTABLE)."
