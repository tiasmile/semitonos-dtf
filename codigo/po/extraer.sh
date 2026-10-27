#!/bin/bash
# Extrae los textos traducibles del código a la plantilla po/semitonos-dtf.pot y actualiza los .po existentes.
cd "$(dirname "$0")/.."
xgettext --language=Python --from-code=UTF-8 --sort-by-file --no-wrap --add-comments=TRADUCTORES \
  --keyword=tr --keyword=trc:1c,2 --keyword=N_ \
  --package-name=semitonos-dtf --package-version=1.0.0 --msgid-bugs-address=contacto@tiasmile.com \
  --copyright-holder="Tiasmile" -o po/semitonos-dtf.pot semitonos.py tramado.py
for po in po/*.po; do [ -e "$po" ] && msgmerge --update --backup=none --no-wrap -q "$po" po/semitonos-dtf.pot; done
echo "Plantilla: $(grep -c '^msgid ' po/semitonos-dtf.pot) textos (el primero es la cabecera)"
