#!/bin/bash
# Compila los .po en codigo/locale/<idioma>/LC_MESSAGES/semitonos-dtf.mo (los que lee el programa).
cd "$(dirname "$0")/.."
for po in po/*.po; do
  idioma="$(basename "$po" .po)"
  mkdir -p "locale/$idioma/LC_MESSAGES"
  msgfmt --check-format -o "locale/$idioma/LC_MESSAGES/semitonos-dtf.mo" "$po" || exit 1
done
echo "Compilados: $(ls locale | tr '\n' ' ')"
