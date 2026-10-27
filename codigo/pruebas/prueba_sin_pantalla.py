"""
Prueba sin pantalla: ejecuta el cálculo con varias combinaciones de ajustes (comprobando que el resultado solo
tiene píxeles opacos o transparentes), lo compara con el tramado.py original de Windows (si está en ../../Windows)
y hace capturas de la ventana con una imagen abierta, en claro y oscuro.
Uso:  cd codigo && QT_QPA_PLATFORM=offscreen .venv/bin/python pruebas/prueba_sin_pantalla.py
"""
import importlib.util
import os
import sys
import time

import numpy as np
from PIL import Image, ImageDraw

AQUI = os.path.dirname(os.path.abspath(__file__))
import tempfile
os.environ["XDG_CONFIG_HOME"] = tempfile.mkdtemp()     # los ajustes de la prueba no tocan ~/.config
sys.path.insert(0, os.path.dirname(AQUI))
import tramado as T

SALIDA = os.path.join(AQUI, "salida")
os.makedirs(SALIDA, exist_ok=True)


def imagen_prueba(ruta):
    """Un degradado con formas de colores sobre fondo negro, 600 × 450 px."""
    w, h = 600, 450
    x = np.linspace(0, 1, w)[None, :].repeat(h, 0)
    y = np.linspace(0, 1, h)[:, None].repeat(w, 1)
    a = np.zeros((h, w, 3), dtype=np.uint8)
    a[..., 0] = (x * 255)
    a[..., 1] = (y * 255)
    a[..., 2] = 160
    im = Image.fromarray(a, "RGB")
    d = ImageDraw.Draw(im)
    d.ellipse((120, 60, 480, 390), fill=(240, 190, 40))
    d.rectangle((250, 160, 350, 300), fill=(20, 20, 20))
    im.save(ruta, dpi=(150, 150))


def original():
    ruta = os.path.join(AQUI, "..", "..", "..", "Windows", "Semitonos DTF", "codigo", "tramado.py")
    if not os.path.isfile(ruta):
        return None
    esp = importlib.util.spec_from_file_location("tramado_windows", ruta)
    m = importlib.util.module_from_spec(esp)
    esp.loader.exec_module(m)
    return m


def main():
    fallos = 0
    ruta = os.path.join(SALIDA, "prueba.png")
    imagen_prueba(ruta)
    im, ppp = T.abrir(ruta)
    print("abierta:", im.size, "ppp:", ppp, "ancho inicial cm:", round(T.ancho_inicial(im, ppp), 2))
    orig = original()
    variantes = [
        dict(),
        dict(camiseta="#ffffff"),
        dict(borde="Hacia dentro", borde_mm=5),
        dict(borde="Hacia fuera", borde_mm=5, forma_borde="Ovalado"),
        dict(borde="Hacia dentro", borde_mm=6, forma_borde="Redondo"),
        dict(forma="Euclídeo", lpi=25, angulo=22.5),
        dict(forma="Líneas", lpi=15),
        dict(forma="Cuadrado", quitar=False),
        dict(semitono=False, quitar=True),
    ]
    for extra in variantes:
        op = T.Opciones(ancho_cm=10, ppp=300, **extra)
        t0 = time.time()
        res = T.procesar(im, op)
        a = np.asarray(res)[..., 3]
        binario = op.semitono is False or set(np.unique(a)) <= {0, 255}
        igual = True
        if orig:
            op2 = orig.Opciones(ancho_cm=10, ppp=300, **extra)
            igual = np.array_equal(np.asarray(orig.procesar(im, op2)), np.asarray(res))
        fallos += (not binario) + (not igual)
        print(f"{str(extra):75} {res.size} binario={binario} igual_que_windows={igual} {time.time() - t0:.1f}s")

    # ventana
    from PySide6.QtWidgets import QApplication
    import semitonos
    app = QApplication([])
    v = semitonos.Semitonos()
    v._listo = False                                  # no escribir ajustes.json en la prueba
    v.resize(1360, 900)
    v.show()
    v._listo = True
    v._guardar = lambda: None
    v._abrir(ruta)

    def esperar(seg=8):
        fin = time.time() + seg
        while time.time() < fin:
            app.processEvents()
            time.sleep(0.05)
            if v.resultado is not None and not v.l_calculo.text() and not v._temporizador.isActive():
                break
        app.processEvents()

    esperar()
    for tema in ("claro", "oscuro"):
        if v.tema != tema:
            v._cambiar_tema()
        v.lienzo.update()
        esperar(1)
        v.grab().save(os.path.join(SALIDA, f"ventana_{tema}.png"))
        print("ventana", tema, "| resultado listo:", v.resultado is not None, "| error:", v._error)
    fallos += v.resultado is None
    # fondo de la vista: blanco, negro o el color elegido (la camiseta)
    v._cambio("camiseta", "#1c2541")
    for fondo, esperado in (("Blanco", "#ffffff"), ("Negro", "#000000"), ("Color elegido", "#1c2541")):
        v.radios_fondo[fondo].setChecked(True)
        esperar(1)
        pix = v.lienzo.grab().toImage().pixelColor(3, 3).name()
        print("fondo de la vista", fondo, "->", pix, "OK" if pix == esperado else "MAL (esperado " + esperado + ")")
        fallos += pix != esperado
    v.radios_fondo["Blanco"].setChecked(True)
    esperar(1)
    v.grab().save(os.path.join(SALIDA, "ventana_fondo_blanco.png"))
    # guardar PNG de verdad
    v._guardar_png()
    esperar(10)
    guardados = [f for f in os.listdir(SALIDA) if "DTF semitono" in f]
    print("PNG guardado:", guardados, "| estado:", v._texto_estado)
    fallos += not guardados
    if guardados:
        r = Image.open(os.path.join(SALIDA, guardados[0]))
        print("   dpi:", r.info.get("dpi"), "tamaño:", r.size)
    print("FALLOS:", fallos)
    sys.exit(1 if fallos else 0)


main()
