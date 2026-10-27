"""
Crea las capturas de pantalla de la ficha de la tienda: la ventana REAL del programa (en inglés, 1600 × 900) con un diseño
de ejemplo propio (ejemplo-diseno.png, un sol retro dibujado aquí mismo; sin derechos de nadie).
Uso (dentro del Flatpak, con el código en esta carpeta):
  cd "Semitonos DTF" && LANGUAGE=en QT_QPA_PLATFORM=offscreen flatpak run --command=python3 com.tiasmile.SemitonosDTF flatpak/capturas/hacer_capturas.py
"""
import os
import sys
import tempfile
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
CODIGO = os.path.join(AQUI, "..", "..", "codigo")
os.environ["XDG_CONFIG_HOME"] = tempfile.mkdtemp()       # no toca los ajustes reales
sys.path.insert(0, CODIGO)

import numpy as np
from PIL import Image, ImageDraw
from PySide6.QtWidgets import QApplication

import idioma
import semitonos


def dibujar_ejemplo(ruta):
    """Un sol retro con franjas y montañas sobre fondo transparente (1400 × 1000 px)."""
    w, h = 1400, 1000
    y = np.linspace(0, 1, h)[:, None].repeat(w, 1)
    rgb = np.zeros((h, w, 3), dtype=np.float32)
    arriba, abajo = np.array([255, 214, 10]), np.array([255, 45, 140])
    t = np.clip((y - 0.12) / 0.55, 0, 1)[..., None]
    rgb[:] = arriba * (1 - t) + abajo * t
    sol = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(sol)
    cx, cy, r = 700, 420, 330
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
    for i, (yy, grosor) in enumerate([(470, 10), (520, 16), (570, 24), (620, 32), (668, 40)]):   # franjas que recortan el sol
        d.rectangle((0, yy, w, yy + grosor), fill=0)
    montes = Image.new("L", (w, h), 0)
    m = ImageDraw.Draw(montes)
    m.polygon([(120, 900), (420, 560), (560, 690), (760, 520), (1010, 770), (1180, 640), (1290, 900)], fill=255)
    capa = np.zeros((h, w, 4), dtype=np.uint8)
    capa[..., :3] = rgb.astype(np.uint8)
    capa[..., 3] = np.asarray(sol)
    montes_a = np.asarray(montes) > 0
    capa[montes_a] = (96, 38, 150, 255)
    Image.fromarray(capa, "RGBA").save(ruta, dpi=(150, 150))


def main():
    ejemplo = os.path.join(AQUI, "ejemplo-diseno.png")
    if not os.path.isfile(ejemplo):
        dibujar_ejemplo(ejemplo)
    assert idioma.IDIOMA == "en", "las capturas de la tienda van en inglés (LANGUAGE=en)"
    app = QApplication([])
    idioma.instalar_qt(app)
    v = semitonos.Semitonos()
    v.resize(1600, 900)
    v.show()
    v._abrir(ejemplo)

    def esperar(seg=12):
        fin = time.time() + seg
        while time.time() < fin:
            app.processEvents()
            time.sleep(0.05)
            if v.resultado is not None and not v.l_calculo.text() and not v._temporizador.isActive():
                break
        app.processEvents()

    esperar()
    v.w["ancho_cm"].setText("23")                    # a este ancho la imagen da más de 150 ppp (sin aviso de poca resolución)
    v.w["lpi"].setCurrentText("12")
    v.w["borde"].setCurrentIndex(v.w["borde"].findData("Hacia dentro"))
    v.w["borde_mm"].setText("10")
    v.barra = 0.45
    esperar()
    for tema in ("claro", "oscuro"):
        if v.tema != tema:
            v._cambiar_tema()
        v.resize(1600, 900)
        esperar(3)
        v.lienzo.update()
        app.processEvents()
        v.grab().save(os.path.join(AQUI, f"{tema}.png"))
        print("captura", tema, v.grab().size().width(), "x", v.grab().size().height())


if __name__ == "__main__":
    main()
