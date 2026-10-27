#!/bin/bash
# Quita «Semitonos DTF» del menú de aplicaciones (borra el lanzador y el icono que creó crear_acceso_directo.sh).
# No toca el programa ni tus ajustes (están en ~/.config/semitonos-dtf: bórralos a mano si quieres empezar de cero).
ID="semitonos-dtf"
rm -f "$HOME/.local/share/applications/$ID.desktop" "$HOME/.local/share/icons/hicolor/256x256/apps/$ID.png"
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
echo "Listo: «Semitonos DTF» ya no sale en el menú de aplicaciones."
