"""
Cálculo de los semitonos para DTF.

Orden: escalar al tamaño de impresión → degradado del borde (hacia dentro o hacia fuera) →
quitar el color de la camiseta → semitono de la transparencia.

El color de cada punto se conserva; lo que se trama es la transparencia: el PNG final solo
tiene píxeles totalmente opacos o totalmente transparentes, que es lo que necesita la tinta
blanca del DTF.
"""
import math
import os
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageOps

Image.MAX_IMAGE_PIXELS = None

FORMAS = ["Redondo", "Euclídeo", "Cuadrado", "Líneas"]
BORDES = ["Sin degradado", "Hacia dentro", "Hacia fuera"]
FORMAS_BORDE = ["Sigue el diseño", "Ovalado", "Redondo"]
EXTENSIONES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp", ".bmp", ".gif"}
MAX_LADO = 20000       # píxeles por lado del resultado


@dataclass
class Opciones:
    ancho_cm: float = 25.0
    ppp: int = 300
    camiseta: str = "#000000"
    quitar: bool = True
    tolerancia: float = 8.0      # % de diferencia con el color de la camiseta que desaparece del todo
    opaco: float = 60.0          # % de diferencia a partir del cual el color queda opaco
    borde: str = "Sin degradado"
    borde_mm: float = 15.0
    forma_borde: str = "Sigue el diseño"
    semitono: bool = True
    lpi: float = 20.0
    angulo: float = 45.0
    forma: str = "Redondo"
    punto_min: float = 8.0       # % : los puntos más pequeños se quitan
    punto_max: float = 95.0      # % : por encima se rellena del todo


def hex_a_rgb(color):
    color = color.lstrip("#")
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


# ---------------------------------------------------------------------------
# Abrir y escalar
# ---------------------------------------------------------------------------
def abrir(ruta):
    """Devuelve (imagen RGBA, ppp del archivo o None)."""
    with Image.open(ruta) as im:
        im.load()
        dpi = im.info.get("dpi")
        im = ImageOps.exif_transpose(im)
        if im.mode in ("CMYK", "I;16", "I", "F"):
            im = im.convert("RGB")
        im = im.convert("RGBA")
    ppp = None
    if dpi:
        try:
            ppp = float(dpi[0])
        except (TypeError, ValueError, IndexError):
            ppp = None
    return im, (ppp if ppp and ppp >= 1 else None)


def ancho_inicial(im, ppp):
    """Ancho en cm a su tamaño real (si el archivo lo trae con 150 ppp o más) o a 300 ppp."""
    if not ppp or ppp < 150:
        ppp = 300
    return im.width / ppp * 2.54


def medidas_px(im, op):
    w = max(1, round(op.ancho_cm / 2.54 * op.ppp))
    h = max(1, round(w * im.height / im.width))
    return w, h


def escalar(im, op):
    """Imagen al tamaño de impresión, como matriz float32 (alto, ancho, 4) en 0..1."""
    w, h = medidas_px(im, op)
    if max(w, h) > MAX_LADO:
        raise ValueError(f"Demasiado grande: {w} × {h} px (máximo {MAX_LADO} px por lado). "
                         "Baja el ancho o la resolución.")
    if (w, h) != im.size:
        im = im.resize((w, h), Image.LANCZOS)
    return np.asarray(im, dtype=np.float32) / 255.0


# ---------------------------------------------------------------------------
# Quitar el color de la camiseta
# ---------------------------------------------------------------------------
def quitar_color(rgba, color, tolerancia, opaco):
    """Como «color a transparencia»: cada píxel se separa en (color, opacidad) de modo que,
    puesto sobre la camiseta, se vea igual que antes. El negro sobre camiseta negra
    desaparece; un gris oscuro pasa a ser blanco poco opaco (puntos blancos pequeños)."""
    c = np.array(hex_a_rgb(color), dtype=np.float32) / 255.0
    p = rgba[..., :3]
    arriba = np.where(c < 1, 1 - c, 1).astype(np.float32)
    abajo = np.where(c > 0, c, 1).astype(np.float32)
    a = np.where(p > c, (p - c) / arriba, (c - p) / abajo).max(axis=2)
    t0 = max(0.0, tolerancia / 100.0)
    t1 = max(t0 + 0.01, opaco / 100.0)
    a = np.clip((a - t0) / (t1 - t0), 0, 1)
    with np.errstate(divide="ignore", invalid="ignore"):
        fg = c + (p - c) / np.maximum(a, 1e-4)[..., None]
    rgba[..., :3] = np.clip(fg, 0, 1)
    rgba[..., 3] *= a
    return rgba


# ---------------------------------------------------------------------------
# Distancias y degradado del borde
# ---------------------------------------------------------------------------
def distancia(dentro, alcance, fuera_es_dentro=False):
    """Distancia en píxeles de cada píxel `dentro` al píxel que no lo es más cercano
    (hasta `alcance`). Lo que queda fuera de la imagen cuenta como `fuera_es_dentro`.
    Se calcula a escala reducida: el degradado es suave y así es rápido."""
    h, w = dentro.shape
    s = max(1.0, alcance / 24.0, math.sqrt(h * w / 3e6))
    if s > 1:
        pw, ph = max(1, round(w / s)), max(1, round(h / s))
        m = np.asarray(Image.fromarray(dentro.astype(np.uint8) * 255).resize((pw, ph), Image.BOX)) >= 128
    else:
        m = dentro
    r = int(math.ceil(alcance / s)) + 1
    m = np.pad(m, r, constant_values=fuera_es_dentro)
    cero = ~m
    grande = np.float32(r + 1)
    g = np.where(m, grande, np.float32(0))
    for k in range(1, r + 1):          # en vertical
        g[:-k] = np.minimum(g[:-k], np.where(cero[k:], np.float32(k), grande))
        g[k:] = np.minimum(g[k:], np.where(cero[:-k], np.float32(k), grande))
    g2 = g * g
    d2 = g2.copy()
    for k in range(1, r + 1):          # en horizontal
        d2[:, :-k] = np.minimum(d2[:, :-k], g2[:, k:] + k * k)
        d2[:, k:] = np.minimum(d2[:, k:], g2[:, :-k] + k * k)
    d = np.sqrt(d2[r:-r, r:-r]) * s
    if s > 1:
        d = np.asarray(Image.fromarray(d.astype(np.float32), "F").resize((w, h), Image.BILINEAR))
    return np.minimum(d, alcance + s)


def suave(t):
    """Curva en S: el degradado empieza y termina sin escalón."""
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def _caja(dentro):
    """Rectángulo (x0, y0, x1, y1) que ocupa el diseño; la imagen entera si está vacía."""
    filas, cols = np.flatnonzero(dentro.any(axis=1)), np.flatnonzero(dentro.any(axis=0))
    if not len(filas):
        return 0, 0, dentro.shape[1], dentro.shape[0]
    return cols[0], filas[0], cols[-1] + 1, filas[-1] + 1


def _ejes(caja, forma, fuera):
    """Centro y semiejes de la elipse (o círculo). Hacia dentro, la que cabe en el diseño;
    hacia fuera, la que lo rodea entero (pasa por las esquinas)."""
    x0, y0, x1, y1 = caja
    a, b = (x1 - x0) / 2, (y1 - y0) / 2
    if forma == "Redondo":
        a = b = math.hypot(a, b) if fuera else min(a, b)
    elif fuera:
        a, b = a * math.sqrt(2), b * math.sqrt(2)
    return (x0 + x1) / 2, (y0 + y1) / 2, max(a, 1.0), max(b, 1.0)


def _dist_elipse(h, w, cx, cy, a, b):
    """Distancia aproximada (px) al borde de la elipse: positiva dentro, negativa fuera
    (medida en la dirección del centro)."""
    dx = (np.arange(w, dtype=np.float32) + 0.5 - cx)[None, :]
    dy = (np.arange(h, dtype=np.float32) + 0.5 - cy)[:, None]
    r = np.sqrt((dx / a) ** 2 + (dy / b) ** 2)
    rho = np.sqrt(dx * dx + dy * dy)
    with np.errstate(divide="ignore", invalid="ignore"):
        d = rho * (1 / r - 1)
    return np.where(r > 1e-6, d, np.float32(1e9)).astype(np.float32)


def degradar_dentro(rgba, px, forma="Sigue el diseño"):
    """Del 100 % al 0 % de opacidad desde dentro hasta el borde del diseño (o de la imagen).
    Ovalado / Redondo: hasta el borde de la elipse o el círculo que cabe en el diseño."""
    dentro = rgba[..., 3] > 0.5
    if forma in ("Ovalado", "Redondo"):
        h, w = dentro.shape
        d = _dist_elipse(h, w, *_ejes(_caja(dentro), forma, fuera=False))
    else:
        d = distancia(dentro, px, fuera_es_dentro=False)
    rgba[..., 3] *= suave(d / px)
    return rgba


def _rellenar(rgb, peso):
    """Rellena las zonas sin peso con los colores de alrededor (pirámide «push-pull»)."""
    niveles = []
    p, w = rgb * peso[..., None], peso.copy()
    while True:
        niveles.append((p, w))
        h, ww = w.shape
        if max(h, ww) <= 4:
            break
        h2, w2 = (h + 1) // 2, (ww + 1) // 2
        pp = np.pad(p, ((0, h2 * 2 - h), (0, w2 * 2 - ww), (0, 0)), mode="edge")
        wp = np.pad(w, ((0, h2 * 2 - h), (0, w2 * 2 - ww)), mode="edge")
        p = pp.reshape(h2, 2, w2, 2, 3).mean(axis=(1, 3))
        w = wp.reshape(h2, 2, w2, 2).mean(axis=(1, 3))
    color = None
    for p, w in reversed(niveles):
        with np.errstate(divide="ignore", invalid="ignore"):
            c = np.where(w[..., None] > 1e-6, p / np.maximum(w, 1e-6)[..., None], 0)
        if color is not None:
            h, ww = w.shape
            arriba = np.stack([np.asarray(Image.fromarray(color[..., i].astype(np.float32), "F")
                                          .resize((ww, h), Image.BILINEAR)) for i in range(3)], axis=2)
            k = np.clip(w * 4, 0, 1)[..., None]      # donde hay poco peso manda el nivel de arriba
            c = k * c + (1 - k) * arriba
        color = c
    return color.astype(np.float32)


def degradar_fuera(rgba, px, forma="Sigue el diseño"):
    """Añade alrededor del diseño un margen de `px` que pasa del 100 % al 0 % de opacidad,
    alargando los colores del borde. La imagen crece `px` por cada lado.
    Ovalado / Redondo: el degradado empieza en el borde del diseño y termina en una elipse
    (o círculo) que lo rodea entero, a `px` de las esquinas (la imagen crece más)."""
    if forma in ("Ovalado", "Redondo"):
        h, w = rgba.shape[:2]
        cx, cy, a, b = _ejes(_caja(rgba[..., 3] > 0.5), forma, fuera=True)
        mx = int(math.ceil(max(0, a + px - cx, a + px - (w - cx)))) + 2
        my = int(math.ceil(max(0, b + px - cy, b + px - (h - cy)))) + 2
        if max(h + 2 * my, w + 2 * mx) > MAX_LADO:
            raise ValueError("Con el degradado hacia fuera la imagen pasa del tamaño máximo.")
        rgba = np.pad(rgba, ((my, my), (mx, mx), (0, 0)))
        dentro = rgba[..., 3] > 0.5
        exterior = np.maximum(_dist_elipse(rgba.shape[0], rgba.shape[1], cx + mx, cy + my, a + px, b + px), 0)
        cerca = distancia(~dentro, max(mx, my) + px, fuera_es_dentro=True)
        with np.errstate(divide="ignore", invalid="ignore"):
            t = np.where(exterior > 0, cerca / (cerca + exterior), 1)
        relleno = _rellenar(rgba[..., :3], dentro.astype(np.float32))
        rgba[..., :3] = np.where(dentro[..., None], rgba[..., :3], relleno)
        rgba[..., 3] = np.maximum(rgba[..., 3], 1 - suave(t))
        return rgba
    m = int(math.ceil(px)) + 2
    if max(rgba.shape[:2]) + 2 * m > MAX_LADO:
        raise ValueError("Con el degradado hacia fuera la imagen pasa del tamaño máximo.")
    rgba = np.pad(rgba, ((m, m), (m, m), (0, 0)))
    dentro = rgba[..., 3] > 0.5
    d = distancia(~dentro, px, fuera_es_dentro=True)
    relleno = _rellenar(rgba[..., :3], dentro.astype(np.float32))
    rgba[..., :3] = np.where(dentro[..., None], rgba[..., :3], relleno)
    rgba[..., 3] = np.maximum(rgba[..., 3], 1 - suave(d / px))
    return rgba


# ---------------------------------------------------------------------------
# Semitono
# ---------------------------------------------------------------------------
def _mancha(forma, fu, fv):
    """Función de punto: los valores bajos se encienden antes."""
    if forma == "Euclídeo":
        return -(np.cos(2 * np.pi * fu) + np.cos(2 * np.pi * fv))
    if forma == "Cuadrado":
        return np.maximum(np.abs(fu), np.abs(fv))
    if forma == "Líneas":
        return np.abs(fv) + np.abs(fu) * 1e-3
    return np.hypot(fu, fv) + np.abs(fu * fv) * 1e-3


def _tabla(forma, n=256):
    """Valores de la función de punto ordenados: convierte la mancha en cobertura exacta."""
    t = (np.arange(n, dtype=np.float32) + 0.5) / n - 0.5
    fu, fv = np.meshgrid(t, t)
    return np.sort(_mancha(forma, fu, fv).ravel())


def tramar(alfa, op, franja=512):
    """Convierte la opacidad (0..1) en puntos: devuelve una matriz booleana."""
    a = alfa.copy()
    pmin, pmax = op.punto_min / 100.0, op.punto_max / 100.0
    a[a < pmin] = 0
    if pmax < 1:
        a[a > pmax] = 1
    h, w = a.shape
    celda = max(2.0, op.ppp / max(1.0, op.lpi))
    ang = math.radians(op.angulo)
    co, si = math.cos(ang) / celda, math.sin(ang) / celda
    tabla = _tabla(op.forma)
    n = np.float32(tabla.size)
    x = np.arange(w, dtype=np.float32) + 0.5
    sale = np.zeros((h, w), dtype=bool)
    for y0 in range(0, h, franja):
        y = (np.arange(y0, min(h, y0 + franja), dtype=np.float32) + 0.5)[:, None]
        u = x * co + y * si
        v = y * co - x * si
        fu = u - np.floor(u) - 0.5
        fv = v - np.floor(v) - 0.5
        t = np.searchsorted(tabla, _mancha(op.forma, fu, fv)).astype(np.float32) / n
        sale[y0:y0 + len(y)] = a[y0:y0 + len(y)] > t
    return sale


# ---------------------------------------------------------------------------
# Todo junto
# ---------------------------------------------------------------------------
def procesar(im, op, origen=None):
    """`im`: imagen RGBA original. `origen`: la matriz ya escalada (para no repetirlo).
    Devuelve la imagen RGBA lista para DTF."""
    rgba = (origen if origen is not None else escalar(im, op)).copy()
    px = op.borde_mm / 25.4 * op.ppp
    if op.borde == "Hacia dentro" and px >= 1:
        rgba = degradar_dentro(rgba, px, op.forma_borde)
    elif op.borde == "Hacia fuera" and px >= 1:
        rgba = degradar_fuera(rgba, px, op.forma_borde)
    if op.quitar:
        rgba = quitar_color(rgba, op.camiseta, op.tolerancia, op.opaco)
    if op.semitono:
        puntos = tramar(rgba[..., 3], op)
        rgba[..., 3] = puntos
        rgba[..., :3] *= puntos[..., None]
    out = np.empty(rgba.shape, dtype=np.uint8)
    np.multiply(rgba, 255, out=rgba)
    np.add(rgba, 0.5, out=rgba)
    np.clip(rgba, 0, 255, out=rgba)
    out[...] = rgba
    return Image.fromarray(out, "RGBA")


def guardar(im, ruta, ppp):
    im.save(ruta, "PNG", dpi=(ppp, ppp), optimize=False, compress_level=6)


def ruta_libre(carpeta, nombre, extension):
    ruta = os.path.join(carpeta, nombre + extension)
    n = 2
    while os.path.exists(ruta):
        ruta = os.path.join(carpeta, f"{nombre} ({n}){extension}")
        n += 1
    return ruta
