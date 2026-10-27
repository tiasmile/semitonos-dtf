"""
Prueba de idiomas: comprueba los .po (todo traducido, sin «fuzzy», marcadores {…} correctos), abre la ventana en cada
idioma, comprueba que lo que se guarda sigue siendo la clave en castellano, que la interfaz cabe en su panel, y
hace una captura por idioma en pruebas/salida/idiomas/<idioma>.png.
Uso:  cd codigo && QT_QPA_PLATFORM=offscreen python3 pruebas/prueba_idiomas.py
"""
import os
import subprocess
import sys
import tempfile
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
CODIGO = os.path.dirname(AQUI)
SALIDA = os.path.join(AQUI, "salida", "idiomas")
IDIOMAS = ["es", "en", "de", "it", "fr", "pt_BR", "ca"]
LOCALE = {"es": "es_ES", "en": "en_US", "de": "de_DE", "it": "it_IT", "fr": "fr_FR", "pt_BR": "pt_BR", "ca": "ca_ES"}


def comprobar_po():
    fallos = 0
    for idioma in IDIOMAS[1:]:
        r = subprocess.run(["msgfmt", "--check-format", "--check-header", "--statistics", "-o", os.devnull,
                            os.path.join(CODIGO, "po", idioma + ".po")], capture_output=True, text=True)
        texto = (r.stdout + r.stderr).strip()
        bien = r.returncode == 0 and "fuzzy" not in texto and "untranslated" not in texto
        print(f"{idioma:6} .po: {'OK' if bien else 'MAL'}  ({texto.splitlines()[-1] if texto else ''})")
        fallos += not bien
    return fallos


def hijo(idioma):
    """Se ejecuta en un proceso aparte por idioma (el idioma se fija al importar)."""
    os.environ["XDG_CONFIG_HOME"] = tempfile.mkdtemp()
    sys.path.insert(0, CODIGO)
    import idioma as I
    from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QLabel, QPushButton, QRadioButton, QScrollArea
    import numpy as np
    from PIL import Image, ImageDraw
    import semitonos
    fallos = 0

    def comprobar(nombre, ok, detalle=""):
        nonlocal fallos
        print(f"   {'OK ' if ok else 'MAL'} {nombre} {detalle}")
        fallos += not ok

    comprobar("idioma detectado", I.IDIOMA == idioma, f"({I.IDIOMA})")
    comprobar("separador decimal", semitonos.numero(22.5) == ("22.5" if idioma == "en" else "22,5"), f"({semitonos.numero(22.5)})")
    if idioma != "es":
        comprobar("título traducido", semitonos.APP_NOMBRE != "Semitonos para DTF", f"({semitonos.APP_NOMBRE})")
    app = QApplication([])
    I.instalar_qt(app)
    os.makedirs(SALIDA, exist_ok=True)
    ruta = os.path.join(tempfile.mkdtemp(), "ejemplo.png")
    w, h = 600, 450
    x, y = np.linspace(0, 1, w)[None, :].repeat(h, 0), np.linspace(0, 1, h)[:, None].repeat(w, 1)
    a = np.stack([x * 255, y * 255, np.full((h, w), 160)], axis=2).astype("uint8")
    im = Image.fromarray(a, "RGB")
    d = ImageDraw.Draw(im)
    d.ellipse((120, 60, 480, 390), fill=(240, 190, 40))
    d.rectangle((250, 160, 350, 300), fill=(20, 20, 20))
    im.save(ruta, dpi=(150, 150))
    v = semitonos.Semitonos()
    v.resize(1360, 900)
    v.show()
    v._abrir(ruta)
    fin = time.time() + 10
    while time.time() < fin:
        app.processEvents()
        time.sleep(0.05)
        if v.resultado is not None and not v.l_calculo.text() and not v._temporizador.isActive():
            break
    app.processEvents()
    # lo que se guarda y se compara son las claves en castellano, se vea el idioma que se vea
    v.w["borde"].setCurrentIndex(1)
    v.w["forma"].setCurrentIndex(2)
    comprobar("borde guardado como clave", v.v["borde"] == "Hacia dentro", f"({v.v['borde']})")
    comprobar("forma guardada como clave", v.v["forma"] == "Cuadrado", f"({v.v['forma']})")
    op = v.opciones()
    comprobar("opciones válidas", op.borde == "Hacia dentro" and op.forma == "Cuadrado")
    # que todo quepa
    scroll = v.findChildren(QScrollArea)[0]
    ancho_util = scroll.viewport().width()
    necesario = scroll.widget().minimumSizeHint().width()
    comprobar("panel de ajustes cabe", necesario <= ancho_util, f"(necesita {necesario}px de {ancho_util}px)")
    cortados = []
    for c in v.findChildren(QComboBox):
        if not c.isEditable():
            fm = c.fontMetrics()
            maximo = max(fm.horizontalAdvance(c.itemText(i)) for i in range(c.count()))
            if maximo + 36 > c.width():
                cortados.append(f"{c.itemText(0)}… ({maximo + 36}>{c.width()})")
    for c in v.findChildren(QPushButton) + v.findChildren(QRadioButton) + v.findChildren(QCheckBox) + v.findChildren(QLabel):
        if c.text() and not getattr(c, "wordWrap", lambda: False)() and c.width() < c.minimumSizeHint().width() - 1:
            cortados.append(f"{c.text()[:30]} ({c.width()}<{c.minimumSizeHint().width()})")
    comprobar("ningún texto cortado", not cortados, str(cortados[:5]))
    v.lienzo.update()
    app.processEvents()
    v.grab().save(os.path.join(SALIDA, f"{idioma}.png"))
    print("FALLOS:", fallos)
    sys.exit(1 if fallos else 0)


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--hijo":
        hijo(sys.argv[2])
    fallos = comprobar_po()
    for idioma in IDIOMAS:
        print(f"== {idioma}")
        entorno = dict(os.environ, LANGUAGE=idioma, LANG=LOCALE[idioma] + ".UTF-8", QT_QPA_PLATFORM="offscreen",
                       PYTHONDONTWRITEBYTECODE="1")
        r = subprocess.run([sys.executable, os.path.abspath(__file__), "--hijo", idioma], env=entorno,
                           capture_output=True, text=True)
        sal = (r.stdout + r.stderr).strip().splitlines()
        print("\n".join(l for l in sal if l.startswith("   ") or "Traceback" in l or "Error" in l or "FALLOS" in l))
        fallos += r.returncode != 0
    print("FALLOS TOTALES:", fallos)
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
