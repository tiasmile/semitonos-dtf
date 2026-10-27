#!/bin/bash
# Compila el ejecutable portable en ../Portable/
cd "$(dirname "$0")"
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt
.venv/bin/pyinstaller --noconfirm --clean semitonos.spec --distpath ../Portable --workpath .build
rm -rf .build
echo "Listo: ../Portable/Semitonos DTF"
