"""
Semitonos para DTF (versión Linux).

Prepara una imagen para estampar en DTF: lo que se trama es la transparencia, y el PNG final solo
tiene píxeles totalmente opacos o totalmente transparentes (lo que necesita la tinta blanca).
Los ajustes se guardan en ~/.config/semitonos-dtf/ajustes.json.
"""
import copy
import json
import os
import queue
import sys
import threading
from dataclasses import asdict, fields

from PIL import Image
from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, QUrl
from PySide6.QtGui import (QColor, QDesktopServices, QFont, QIcon, QImage, QKeySequence, QPainter, QPen, QShortcut)
from PySide6.QtWidgets import (QApplication, QButtonGroup, QCheckBox, QColorDialog, QComboBox, QFileDialog, QFrame,
                               QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton,
                               QRadioButton, QScrollArea, QSlider, QVBoxLayout, QWidget)

import estilo
import idioma
import tramado as T
from idioma import N_, tr, trc

APP_NOMBRE = tr("Semitonos para DTF")
ARCHIVO_AJUSTES = "ajustes.json"
# Los textos de estas listas son CLAVES (se guardan en ajustes.json y el código las compara): siguen en castellano en
# cualquier idioma. N_() solo las marca para extraerlas; se traducen al mostrarlas, con tr().
CAMISETAS = [(N_("Blanca"), "#ffffff"), (N_("Negra"), "#000000"), (N_("Gris"), "#9a9a9a"),
             (N_("Azul marino"), "#1c2541"), (N_("Roja"), "#b3141f"), (N_("Verde botella"), "#1d4d34")]
VISTAS = [N_("Comparar"), N_("Resultado"), N_("Original")]
ZOOMS = [N_("Ajustar"), "100 %", "200 %"]
FONDOS = [N_("Blanco"), N_("Negro"), N_("Color elegido")]   # fondo de la vista previa; «Color elegido» = el de la camiseta
AJUSTES_POR_DEFECTO = {"interfaz": "claro", "ultima_carpeta": "", "fondo_vista": "Color elegido", "opciones": asdict(T.Opciones())}
AYUDA_VISTA = tr("Barra: arrastrar para comparar · rueda: acercar o alejar · botón derecho: mover la imagen · "
                 "doble clic: ver entera")
MARCA = "#ffc72c"        # barra de comparar (aviso visual, sobre cualquier color de camiseta)


# ---------------------------------------------------------------------------
def carpeta_ajustes():
    """Donde se guardan los ajustes: ~/.config/semitonos-dtf (o $XDG_CONFIG_HOME). Se crea si no existe."""
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    ruta = os.path.join(base, "semitonos-dtf")
    try:
        os.makedirs(ruta, exist_ok=True)
    except OSError:
        pass
    return ruta


def recurso(nombre):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "recursos", nombre)


def cargar_ajustes():
    datos = copy.deepcopy(AJUSTES_POR_DEFECTO)
    try:
        with open(os.path.join(carpeta_ajustes(), ARCHIVO_AJUSTES), encoding="utf-8") as f:
            leidos = json.load(f)
        datos.update({k: v for k, v in leidos.items() if k != "opciones"})
        datos["opciones"].update(leidos.get("opciones", {}))
    except (OSError, ValueError):
        pass
    return datos


def guardar_ajustes(datos):
    try:
        with open(os.path.join(carpeta_ajustes(), ARCHIVO_AJUSTES), "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def numero(x, dec=1):
    texto = f"{x:.{dec}f}"
    if "." in texto:
        texto = texto.rstrip("0").rstrip(".")
    return texto.replace(".", idioma.DECIMAL)


def leer_num(texto, defecto):
    try:
        return float(str(texto).replace(",", ".").strip())
    except ValueError:
        return defecto


def sobre(img, color):
    """La imagen RGBA puesta sobre la camiseta (RGB)."""
    fondo = Image.new("RGB", img.size, T.hex_a_rgb(color))
    fondo.paste(img, mask=img.getchannel("A"))
    return fondo


def contraste(color):
    r, g, b = T.hex_a_rgb(color)
    return "#000000" if r * 0.3 + g * 0.59 + b * 0.11 > 140 else "#ffffff"


def a_qimage(im_rgb):
    datos = im_rgb.tobytes("raw", "RGB")
    return QImage(datos, im_rgb.width, im_rgb.height, 3 * im_rgb.width, QImage.Format_RGB888).copy()


# ---------------------------------------------------------------------------
class Lienzo(QWidget):
    """Vista previa: pinta con una función de la ventana (en píxeles reales de pantalla) y le pasa el ratón."""

    def __init__(self, ventana):
        super().__init__()
        self.ventana = ventana
        self.setMinimumSize(400, 300)
        self.setMouseTracking(False)
        self.setFocusPolicy(Qt.StrongFocus)

    def tam(self):
        d = self.devicePixelRatioF()
        return round(self.width() * d), round(self.height() * d)

    def _p(self, e):
        d = self.devicePixelRatioF()
        return e.position().x() * d, e.position().y() * d

    def paintEvent(self, e):
        p = QPainter(self)
        d = self.devicePixelRatioF()
        p.scale(1 / d, 1 / d)                # a partir de aquí, 1 unidad = 1 píxel real
        self.ventana.pintar(p, *self.tam(), d)

    def mousePressEvent(self, e):
        self.setFocus()
        x, y = self._p(e)
        if e.button() == Qt.LeftButton:
            self.ventana.clic(x, y)
        elif e.button() == Qt.RightButton:
            self.ventana.coger(x, y)

    def mouseMoveEvent(self, e):
        x, y = self._p(e)
        if e.buttons() & Qt.LeftButton:
            self.ventana.mover(x, y)
        elif e.buttons() & Qt.RightButton:
            self.ventana.arrastrar(x, y)

    def mouseReleaseEvent(self, e):
        self.ventana.arrastre = None

    def mouseDoubleClickEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.ventana.ajustar()

    def wheelEvent(self, e):
        x, y = self._p(e)
        self.ventana.rueda(x, y, e.angleDelta().y())

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.update()


class Semitonos(QMainWindow):
    def __init__(self, archivo=None):
        super().__init__()
        self.setWindowTitle(APP_NOMBRE)
        self.setWindowIcon(QIcon(recurso("icono.png")))
        self.resize(1360, 900)
        self.setMinimumSize(1150, 720)
        self.setAcceptDrops(True)
        self.aj = cargar_ajustes()
        self.tema = self.aj["interfaz"] if self.aj["interfaz"] in estilo.TEMAS else "claro"
        self.t = estilo.TEMAS[self.tema]

        self.v = {}                 # valor de cada opción (texto, o bool para las casillas)
        for f in fields(T.Opciones):
            valor = self.aj["opciones"].get(f.name, f.default)
            if f.type in (bool, "bool"):
                self.v[f.name] = bool(valor)
            else:
                self.v[f.name] = numero(valor, 2) if isinstance(valor, float) else str(valor)
        self.v_alto = ""
        self.vista, self.zoom_txt = "Comparar", "Ajustar"
        self.fondo_vista = self.aj["fondo_vista"] if self.aj.get("fondo_vista") in FONDOS else FONDOS[-1]
        self._sincronizando = False

        self.ruta = None
        self.im = None              # imagen original RGBA
        self.ppp_archivo = None
        self.escalada = None        # (clave, matriz, imagen PIL) al tamaño de impresión
        self.resultado = None       # (opciones, imagen PIL)
        self._error = None
        self._capas = []            # últimas imágenes ya escaladas para la vista
        self.zoom = None            # None: ajustar a la ventana; si no, píxeles de pantalla por píxel
        self.centro = None          # punto de la imagen (0-1) que queda en el centro de la vista
        self.barra = 0.5            # posición de la barra de comparar (0-1)
        self.arrastre = None
        self.cuentagotas = False
        self._guardando = False
        self._carpeta_resultado = None
        self._texto_estado = ""
        self._listo = False

        self._cerrojo = threading.Lock()
        self._pedido = None         # vista previa pendiente
        self._pedido_guardar = None
        self._hilo = False
        self._gen = 0
        self.cola = queue.Queue()
        self._temporizador = QTimer(self, singleShot=True)
        self._temporizador.timeout.connect(self._calcular)
        self._recogedor = QTimer(self)
        self._recogedor.timeout.connect(self._recoger)
        self._recogedor.start(100)
        QShortcut(QKeySequence("Esc"), self, activated=self._fin_cuentagotas)
        self._construir()
        self._listo = True
        self._actualizar_controles()
        if archivo and os.path.isfile(archivo):
            QTimer.singleShot(300, lambda: self._abrir(archivo))

    # ======================================================================
    # Interfaz
    # ======================================================================
    def _construir(self):
        """(Re)crea toda la ventana; se llama otra vez al cambiar de tema."""
        estilo.aplicar(QApplication.instance(), self.tema)
        raiz = QWidget()
        raiz.setObjectName("raiz")
        self.setCentralWidget(raiz)
        col = QVBoxLayout(raiz)
        col.setContentsMargins(18, 14, 18, 16)
        col.setSpacing(0)
        cab = QHBoxLayout()
        titulo = QLabel(APP_NOMBRE)
        titulo.setObjectName("cabecera")
        cab.addWidget(titulo)
        cab.addStretch()
        b = QPushButton(tr("☀  Modo claro") if self.tema == "oscuro" else tr("☾  Modo oscuro"))
        b.clicked.connect(self._cambiar_tema)
        cab.addWidget(b)
        col.addLayout(cab)
        col.addSpacing(12)
        linea = QFrame()
        linea.setObjectName("linea")
        linea.setFixedHeight(1)
        col.addWidget(linea)
        col.addSpacing(10)
        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(18)
        cuerpo.addLayout(self._panel_vista(), 1)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedWidth(490)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        der = QWidget()
        der.setLayout(self._panel_ajustes())
        scroll.setWidget(der)
        cuerpo.addWidget(scroll)
        col.addLayout(cuerpo, 1)
        self._info()

    def _titulo(self, texto):
        l = QLabel(texto)
        l.setObjectName("titulo")
        return l

    def _ayuda(self, texto):
        l = QLabel(texto)
        l.setObjectName("ayuda")
        l.setWordWrap(True)
        return l

    def _cambiar_tema(self):
        self.tema = "oscuro" if self.tema == "claro" else "claro"
        self.t = estilo.TEMAS[self.tema]
        self._guardar()
        self._listo = False
        self._construir()
        self._listo = True
        self._actualizar_controles()

    # ----- izquierda: imagen y vista previa ---------------------------------
    def _panel_vista(self):
        izq = QVBoxLayout()
        izq.addWidget(self._titulo(tr("1. Imagen")))
        zona = QFrame()
        zona.setObjectName("zona")
        h = QHBoxLayout(zona)
        h.setContentsMargins(14, 8, 10, 8)
        self.l_archivo = QLabel(self._texto_archivo())
        self.l_archivo.setStyleSheet("font-weight: 600;")
        h.addWidget(self.l_archivo, 1)
        b = QPushButton(tr("Abrir imagen…"))
        b.clicked.connect(self._elegir)
        h.addWidget(b)
        izq.addWidget(zona)
        izq.addSpacing(6)

        barra = QHBoxLayout()
        grupo_v, grupo_z = QButtonGroup(self), QButtonGroup(self)
        for valor in VISTAS:
            r = QRadioButton(tr(valor))
            r.setChecked(valor == self.vista)
            r.toggled.connect(lambda on, val=valor: on and self._cambiar_vista(val))
            grupo_v.addButton(r)
            barra.addWidget(r)
        barra.addSpacing(14)
        self.radios_zoom = {}
        for valor in ZOOMS:
            r = QRadioButton(tr(valor))
            r.setChecked(valor == self.zoom_txt)
            r.toggled.connect(lambda on, val=valor: on and self._cambiar_zoom(val))
            grupo_z.addButton(r)
            self.radios_zoom[valor] = r
            barra.addWidget(r)
        barra.addStretch()
        self.l_calculo = QLabel("")
        self.l_calculo.setObjectName("suave")
        barra.addWidget(self.l_calculo)
        izq.addLayout(barra)

        barra2 = QHBoxLayout()
        barra2.addWidget(self._ayuda(tr("Fondo de la vista:")))
        grupo_f = QButtonGroup(self)
        self.radios_fondo = {}
        for valor in FONDOS:
            r = QRadioButton(tr(valor))
            self.radios_fondo[valor] = r
            r.setChecked(valor == self.fondo_vista)
            r.setToolTip(tr("Solo cambia lo que ves: el PNG que se guarda no lleva fondo.") if valor != FONDOS[-1] else
                         tr("El color de la camiseta elegido abajo"))
            r.toggled.connect(lambda on, val=valor: on and self._cambiar_fondo(val))
            grupo_f.addButton(r)
            barra2.addWidget(r)
        barra2.addStretch()
        izq.addLayout(barra2)

        self.lienzo = Lienzo(self)
        izq.addWidget(self.lienzo, 1)
        self.l_info = QLabel("")
        self.l_info.setObjectName("suave")
        self.l_info.setWordWrap(True)
        izq.addWidget(self.l_info)
        return izq

    # ----- derecha: ajustes ---------------------------------------------------
    def _tarjeta(self, lista, titulo):
        lista.addWidget(self._titulo(titulo))
        f = QFrame()
        f.setObjectName("tarjeta")
        g = QGridLayout(f)
        g.setContentsMargins(14, 10, 14, 10)
        g.setVerticalSpacing(6)
        lista.addWidget(f)
        lista.addSpacing(6)
        return g

    def _campo(self, nombre, ancho=70, valores=None, editable=True):
        """QLineEdit, o QComboBox editable si hay lista de valores, ligado a la opción `nombre`."""
        if valores:
            w = QComboBox()
            w.setEditable(editable)
            w.addItems(valores)
            w.setCurrentText(self.v[nombre])
            w.setFixedWidth(ancho + 20)
            w.currentTextChanged.connect(lambda txt, k=nombre: self._cambio(k, txt))
        else:
            w = QLineEdit(self.v[nombre])
            w.setFixedWidth(ancho)
            w.textChanged.connect(lambda txt, k=nombre: self._cambio(k, txt))
        self.w[nombre] = w
        return w

    def _lista(self, nombre, valores, ancho=130):
        w = QComboBox()
        for valor in valores:        # se ve traducido; lo que se guarda y se compara es la clave en castellano
            w.addItem(tr(valor), valor)
        w.setCurrentIndex(max(0, w.findData(self.v[nombre])))
        fm = w.fontMetrics()           # el ancho se ajusta al texto más largo de la lista (cambia según el idioma)
        w.setFixedWidth(max(ancho, max(fm.horizontalAdvance(w.itemText(i)) for i in range(w.count())) + 40))
        w.currentIndexChanged.connect(lambda _i, k=nombre, c=w: self._cambio(k, c.currentData()))
        self.w[nombre] = w
        return w

    def _casilla(self, nombre, texto):
        w = QCheckBox(texto)
        w.setChecked(self.v[nombre])
        w.toggled.connect(lambda x, k=nombre: self._cambio(k, x))
        self.w[nombre] = w
        return w

    def _deslizador(self, g, fila, texto, nombre, desde, hasta):
        g.addWidget(QLabel(texto), fila, 0)
        caja = QHBoxLayout()
        s = QSlider(Qt.Horizontal)
        s.setRange(desde, hasta)
        s.setValue(round(leer_num(self.v[nombre], desde)))
        etiqueta = QLabel(f"{s.value()} %")
        etiqueta.setFixedWidth(46)
        etiqueta.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        def cambia(x):
            etiqueta.setText(f"{x} %")
            self._cambio(nombre, str(x))
        s.valueChanged.connect(cambia)
        caja.addWidget(s, 1)
        caja.addWidget(etiqueta)
        g.addLayout(caja, fila, 1)
        self.w[nombre] = s
        return s

    def _panel_ajustes(self):
        der = QVBoxLayout()
        der.setContentsMargins(0, 0, 8, 0)
        self.w = {}

        # --- Tamaño
        g = self._tarjeta(der, tr("2. Tamaño de impresión"))
        caja = QHBoxLayout()
        caja.addWidget(QLabel(tr("Ancho")))
        caja.addWidget(self._campo("ancho_cm", 64))
        caja.addWidget(QLabel("cm"))
        caja.addSpacing(10)
        caja.addWidget(QLabel(tr("Alto")))
        self.e_alto = QLineEdit(self.v_alto)
        self.e_alto.setFixedWidth(64)
        self.e_alto.textChanged.connect(lambda txt: self._sincronizar("alto", txt))
        caja.addWidget(self.e_alto)
        caja.addWidget(QLabel("cm"))
        caja.addSpacing(10)
        # TRADUCTORES: en «Ancho 25 cm  Alto 20 cm  a 300 ppp», la palabra «a» introduce la resolución
        caja.addWidget(QLabel(trc("tamaño de impresión: «25 cm a 300 ppp»", "a")))
        caja.addWidget(self._campo("ppp", 52, ["300", "360", "400"]))
        # TRADUCTORES: unidad de resolución de impresión (puntos por pulgada), «dpi» en inglés
        caja.addWidget(QLabel(tr("ppp")))
        caja.addStretch()
        g.addLayout(caja, 0, 0, 1, 2)

        # --- Camiseta
        g = self._tarjeta(der, tr("3. Color de la camiseta"))
        caja = QHBoxLayout()
        self.l_color = QFrame()
        self.l_color.setFixedSize(46, 30)
        caja.addWidget(self.l_color)
        caja.addSpacing(6)
        for nombre, color in CAMISETAS:
            m = QPushButton()
            m.setObjectName("muestra")
            m.setFixedSize(24, 24)
            m.setCursor(Qt.PointingHandCursor)
            m.setToolTip(tr(nombre))
            m.setStyleSheet(f"background: {color};")
            m.clicked.connect(lambda _=False, c=color: self._cambio("camiseta", c, actualizar=True))
            caja.addWidget(m)
        otro = QPushButton(tr("Otro…"))
        otro.setObjectName("chico")
        otro.clicked.connect(self._otro_color)
        # TRADUCTORES: herramienta para coger un color pulsando sobre la imagen (eyedropper / pipette)
        self.b_gotas = QPushButton(tr("Cuentagotas"))
        self.b_gotas.setObjectName("chico")
        self.b_gotas.clicked.connect(self._activar_cuentagotas)
        caja.addSpacing(6)
        caja.addWidget(otro)
        caja.addWidget(self.b_gotas)
        caja.addStretch()
        g.addLayout(caja, 0, 0, 1, 2)
        g.addWidget(self._casilla("quitar", tr("Quitar el color de la camiseta de la imagen")), 1, 0, 1, 2)
        # TRADUCTORES: umbral. Los colores más parecidos al de la camiseta que este valor se vuelven transparentes
        self.s_tol = self._deslizador(g, 2, tr("Quitar hasta"), "tolerancia", 0, 50)
        # TRADUCTORES: umbral. Los colores más distintos al de la camiseta que este valor quedan totalmente opacos
        self.s_opaco = self._deslizador(g, 3, tr("Opaco desde"), "opaco", 10, 100)
        g.addWidget(self._ayuda(tr("Más parecido que «Quitar hasta»: desaparece. Más distinto que «Opaco desde»: "
                                   "sólido. Lo de en medio: puntos.")), 4, 0, 1, 2)

        # --- Degradado
        g = self._tarjeta(der, tr("4. Degradado del borde"))
        caja = QHBoxLayout()
        # TRADUCTORES: tipo de degradado del borde del diseño: sin degradado / hacia dentro / hacia fuera
        caja.addWidget(self._lista("borde", T.BORDES, 130))
        caja.addWidget(self._lista("forma_borde", T.FORMAS_BORDE, 130))
        caja.addStretch()
        g.addLayout(caja, 0, 0, 1, 2)
        caja = QHBoxLayout()
        caja.addWidget(QLabel(tr("Ancho")))
        caja.addWidget(self._campo("borde_mm", 60))
        caja.addWidget(QLabel("mm"))
        caja.addStretch()
        g.addLayout(caja, 1, 0, 1, 2)
        g.addWidget(self._ayuda(tr("Del 100 % al 0 % con puntos. Hacia dentro difumina el borde; hacia fuera añade un "
                                   "margen alargando los colores. Ovalado / Redondo: en elipse o círculo, sin esquinas.")),
                    2, 0, 1, 2)

        # --- Semitono
        g = self._tarjeta(der, tr("5. Semitono"))
        g.addWidget(self._casilla("semitono", tr("Convertir la transparencia en puntos")), 0, 0, 1, 2)
        caja = QHBoxLayout()
        # TRADUCTORES: lineatura de la trama (líneas por pulgada, lpi): cuántas filas de puntos caben en una pulgada
        caja.addWidget(QLabel(tr("Lineatura")))
        caja.addWidget(self._campo("lpi", 46, ["10", "15", "20", "25", "35", "45", "55"]))
        caja.addWidget(QLabel("lpi"))
        caja.addSpacing(10)
        caja.addWidget(QLabel(tr("Ángulo")))
        caja.addWidget(self._campo("angulo", 52, ["0", "15", numero(22.5), "45", "75"]))
        caja.addWidget(QLabel("°"))
        caja.addStretch()
        g.addLayout(caja, 1, 0, 1, 2)
        caja = QHBoxLayout()
        caja.addWidget(QLabel(tr("Forma del punto")))
        caja.addWidget(self._lista("forma", T.FORMAS, 120))
        caja.addStretch()
        g.addLayout(caja, 2, 0, 1, 2)
        # TRADUCTORES: tamaño del punto de la trama (en %); por debajo del mínimo el punto se elimina
        self.s_min = self._deslizador(g, 3, tr("Punto mínimo"), "punto_min", 0, 40)
        self.s_max = self._deslizador(g, 4, tr("Punto máximo"), "punto_max", 60, 100)
        # TRADUCTORES: «no agarran» = los puntos demasiado pequeños no se adhieren a la tela al estampar. «Sólido» = totalmente relleno
        g.addWidget(self._ayuda(tr("Lineatura más baja = puntos más grandes. Los puntos más pequeños que el mínimo se "
                                   "quitan (no agarran); por encima del máximo, sólido.")), 5, 0, 1, 2)

        # --- Guardar
        der.addSpacing(6)
        self.b_guardar = QPushButton(tr("Guardar PNG para DTF"))
        self.b_guardar.setObjectName("accion")
        self.b_guardar.clicked.connect(self._guardar_png)
        der.addWidget(self.b_guardar)
        abajo = QHBoxLayout()
        self.l_estado = QLabel(self._texto_estado)
        self.l_estado.setObjectName("suave")
        self.l_estado.setWordWrap(True)
        abajo.addWidget(self.l_estado, 1)
        self.b_abrir = QPushButton(tr("Abrir carpeta"))
        self.b_abrir.setObjectName("chico")
        self.b_abrir.clicked.connect(self._abrir_carpeta)
        self.b_abrir.setVisible(bool(self._carpeta_resultado))
        abajo.addWidget(self.b_abrir)
        der.addLayout(abajo)
        der.addStretch()
        return der

    # ======================================================================
    # Ajustes
    # ======================================================================
    def _cambio(self, nombre, valor, actualizar=False):
        if nombre == "ancho_cm" and not self._sincronizando:
            self.v[nombre] = valor
            self._sincronizar("ancho", valor)
        self.v[nombre] = valor
        if actualizar and nombre in self.w and isinstance(self.w[nombre], QLineEdit):
            self.w[nombre].setText(valor)
        if not self._listo:
            return
        self._actualizar_controles()
        self._guardar()
        self._programar()

    def opciones(self):
        datos = {}
        for f in fields(T.Opciones):
            valor = self.v[f.name]
            if f.type in (int, "int"):
                valor = int(round(leer_num(valor, f.default)))
            elif f.type in (float, "float"):
                valor = leer_num(valor, f.default)
            datos[f.name] = valor
        op = T.Opciones(**datos)
        op.ancho_cm = min(500.0, max(0.5, op.ancho_cm))
        op.ppp = min(1200, max(72, op.ppp))
        op.lpi = min(150.0, max(5.0, op.lpi))
        op.borde_mm = min(200.0, max(0.0, op.borde_mm))
        op.tolerancia = min(100.0, max(0.0, op.tolerancia))
        op.opaco = min(100.0, max(0.0, op.opaco))
        op.punto_min = min(100.0, max(0.0, op.punto_min))
        op.punto_max = min(100.0, max(op.punto_min, op.punto_max))
        if op.forma not in T.FORMAS:
            op.forma = T.FORMAS[0]
        if op.borde not in T.BORDES:
            op.borde = T.BORDES[0]
        if op.forma_borde not in T.FORMAS_BORDE:
            op.forma_borde = T.FORMAS_BORDE[0]
        try:
            T.hex_a_rgb(op.camiseta)
        except ValueError:
            op.camiseta = "#000000"
        return op

    def _guardar(self):
        if not self._listo:
            return
        self.aj["interfaz"] = self.tema
        self.aj["opciones"] = asdict(self.opciones())
        guardar_ajustes(self.aj)

    def _sincronizar(self, cambiado, texto):
        """Ancho y alto van unidos (se mantiene la proporción de la imagen)."""
        if self._sincronizando or self.im is None:
            return
        self._sincronizando = True
        try:
            prop = self.im.height / self.im.width
            if cambiado == "ancho":
                ancho = leer_num(texto, 0)
                if ancho > 0:
                    self.v_alto = numero(ancho * prop, 2)
                    self.e_alto.setText(self.v_alto)
            else:
                alto = leer_num(texto, 0)
                if alto > 0:
                    self.v["ancho_cm"] = numero(alto / prop, 2)
                    self.w["ancho_cm"].setText(self.v["ancho_cm"])
        finally:
            self._sincronizando = False
        if cambiado == "alto" and self._listo:
            self._actualizar_controles()
            self._guardar()
            self._programar()

    def _actualizar_controles(self):
        if not self._listo or not hasattr(self, "b_guardar"):
            return
        v = self.v
        color = self.opciones().camiseta
        self.l_color.setStyleSheet(f"background: {color}; border: 1px solid {self.t['suave']}; border-radius: 4px;")
        for s in (self.s_tol, self.s_opaco):
            s.setEnabled(v["quitar"])
        hay_borde = v["borde"] != "Sin degradado"
        self.w["borde_mm"].setEnabled(hay_borde)
        self.w["forma_borde"].setEnabled(hay_borde)
        for k in ("lpi", "angulo", "forma"):
            self.w[k].setEnabled(v["semitono"])
        for s in (self.s_min, self.s_max):
            s.setEnabled(v["semitono"])
        self.b_guardar.setEnabled(self.im is not None and not self._guardando)
        self.b_gotas.setEnabled(self.im is not None)
        self.lienzo.update()

    # ======================================================================
    # Abrir
    # ======================================================================
    def _texto_archivo(self):
        if not self.ruta:
            return tr("↓   Arrastra aquí la imagen (PNG, JPG, TIFF, WEBP)")
        return f"{os.path.basename(self.ruta)}   ·   {self.im.width} × {self.im.height} px"

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        rutas = [u.toLocalFile() for u in e.mimeData().urls() if u.isLocalFile()]
        for r in rutas:
            if os.path.splitext(r)[1].lower() in T.EXTENSIONES:
                e.acceptProposedAction()
                self._abrir(r)
                return
        QMessageBox.information(self, tr("Formato no admitido"), tr("Arrastra una imagen PNG, JPG, TIFF o WEBP."))

    def _elegir(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self, tr("Elegir imagen"), self.aj.get("ultima_carpeta") or "",
            tr("Imágenes") + " (" + " ".join("*" + e for e in sorted(T.EXTENSIONES)) + ");;" + tr("Todos") + " (*)")
        if ruta:
            self._abrir(ruta)

    def _abrir(self, ruta):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            im, ppp = T.abrir(ruta)
        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, tr("No se puede abrir"), tr("No se puede abrir la imagen:\n{error}").format(error=e))
            return
        QApplication.restoreOverrideCursor()
        self.ruta, self.im, self.ppp_archivo = os.path.normpath(ruta), im, ppp
        self.escalada = self.resultado = self.centro = self.zoom = None
        self._capas = []
        self._carpeta_resultado = None
        self.b_abrir.setVisible(False)
        self._estado("")
        self.aj["ultima_carpeta"] = os.path.dirname(self.ruta)
        self.l_archivo.setText(self._texto_archivo())
        self.zoom_txt = "Ajustar"
        self.radios_zoom["Ajustar"].setChecked(True)
        self.w["ancho_cm"].setText(numero(T.ancho_inicial(im, ppp), 2))   # recalcula el alto y la vista
        self._sincronizar("ancho", self.w["ancho_cm"].text())
        self._actualizar_controles()
        self._programar()

    # ======================================================================
    # Cálculo en segundo plano
    # ======================================================================
    def _programar(self, espera=350):
        self._temporizador.start(espera)
        self._info()

    def _calcular(self):
        if self.im is None:
            return
        self._gen += 1
        self.l_calculo.setText(tr("Calculando…"))
        with self._cerrojo:
            self._pedido = ("vista", self._gen, self.opciones(), self.im)
            self._arrancar_hilo()

    def _arrancar_hilo(self):
        """Con el cerrojo cogido."""
        if not self._hilo:
            self._hilo = True
            threading.Thread(target=self._trabajo, daemon=True).start()

    def _trabajo(self):
        while True:
            with self._cerrojo:
                if self._pedido_guardar:
                    pedido, self._pedido_guardar = self._pedido_guardar, None
                else:
                    pedido, self._pedido = self._pedido, None
                if pedido is None:
                    self._hilo = False
                    return
            tipo, gen, op, im = pedido
            try:
                clave = (id(im), op.ancho_cm, op.ppp)
                escalada = self.escalada
                if escalada is None or escalada[0] != clave:
                    matriz = T.escalar(im, op)
                    escalada = (clave, matriz, Image.fromarray((matriz * 255 + 0.5).astype("uint8"), "RGBA"))
                    self.cola.put(("escalada", gen, escalada))
                if tipo == "guardar":
                    resultado = self.resultado[1] if self.resultado and self.resultado[0] == op else \
                        T.procesar(im, op, escalada[1])
                    T.guardar(resultado, gen, op.ppp)      # en un guardado, `gen` es la ruta
                    self.cola.put(("guardado", gen, (op, resultado)))
                else:
                    self.cola.put(("vista", gen, (op, T.procesar(im, op, escalada[1]))))
            except MemoryError:
                self.cola.put(("error", gen, tr("No hay memoria suficiente para este tamaño. Baja el ancho o la resolución.")))
            except Exception as e:
                self.cola.put(("error", gen, str(e)))

    def _recoger(self):
        try:
            while True:
                tipo, gen, datos = self.cola.get_nowait()
                if tipo == "escalada":
                    if datos[0][0] == id(self.im):
                        self.escalada = datos
                        if self._modo() == "Original" or self.resultado is None:
                            self.lienzo.update()
                elif tipo == "vista" and gen == self._gen:
                    self.resultado = datos
                    self._error = None
                    self.l_calculo.setText("")
                    self.lienzo.update()
                    self._info()
                elif tipo == "guardado":
                    self._guardando = False
                    if datos[0] == self.opciones():
                        self.resultado = datos
                    self._carpeta_resultado = os.path.dirname(gen)
                    self.b_abrir.setVisible(True)
                    self._estado(tr("✔ Guardado: {nombre}").format(nombre=os.path.basename(gen)))
                    self.l_calculo.setText("")
                    self._actualizar_controles()
                    if not self.resultado or self.resultado[0] != self.opciones():
                        self._programar()
                elif tipo == "error" and (isinstance(gen, str) or gen == self._gen):
                    if isinstance(gen, str):
                        self._guardando = False
                        self._actualizar_controles()
                        self._estado("")
                        QMessageBox.critical(self, tr("No se ha podido guardar"), datos)
                    self._error = datos
                    self.l_calculo.setText("")
                    self._info()
        except queue.Empty:
            pass

    # ======================================================================
    # Vista previa
    # ======================================================================
    def _imagenes(self):
        """(ancho y alto de referencia, (original, dx, dy), (resultado, 0, 0) o None).
        Con el degradado hacia fuera el resultado es más grande: el original va centrado en él."""
        if self.escalada is None:
            return None
        orig = self.escalada[2]
        if not self.resultado:
            return orig.size, (orig, 0, 0), None
        res = self.resultado[1]
        return res.size, (orig, (res.width - orig.width) // 2, (res.height - orig.height) // 2), (res, 0, 0)

    def _color_vista(self):
        """El color sobre el que se ve la imagen: blanco, negro o el de la camiseta."""
        return {"Blanco": "#ffffff", "Negro": "#000000"}.get(self.fondo_vista, self.opciones().camiseta)

    def _cambiar_fondo(self, valor):
        self.fondo_vista = valor
        self.aj["fondo_vista"] = valor
        self._guardar()
        self.lienzo.update()

    def _modo(self):
        if self.cuentagotas:
            return "Original"
        return self.vista if self.vista in VISTAS else "Comparar"

    def _geometria(self, tam):
        """(zoom, x e y en pantalla de la esquina de la imagen de referencia)."""
        cw, ch = self.lienzo.tam()
        W, H = tam
        z = self.zoom or min((cw - 24) / W, (ch - 24) / H)
        cx, cy = self.centro or (0.5, 0.5)
        return z, cw / 2 - cx * W * z, ch / 2 - cy * H * z

    def _cambiar_vista(self, valor):
        self.vista = valor
        self.lienzo.update()

    def _cambiar_zoom(self, valor):
        self.zoom_txt = valor
        self.zoom = {"Ajustar": None, "100 %": 1.0, "200 %": 2.0}.get(valor)
        if self.zoom is None:
            self.centro = None
        self.lienzo.update()

    def ajustar(self):
        self.radios_zoom["Ajustar"].setChecked(True)
        self._cambiar_zoom("Ajustar")

    def _capa(self, img, ox, oy, z, x0, y0, cw, ch, color):
        """La imagen (colocada en ox, oy) tal como se ve en pantalla, sobre la camiseta.
        Se guardan las últimas: al mover la barra no hay que volver a escalar nada."""
        clave = (ox, oy, round(z, 6), round(x0), round(y0), cw, ch, color)
        for guardada, k, capa, caja in self._capas:
            if guardada is img and k == clave:
                return capa, caja
        capa = Image.new("RGB", (cw, ch), T.hex_a_rgb(color))
        sx0, sy0 = x0 + ox * z, y0 + oy * z
        caja = (sx0, sy0, sx0 + img.width * z, sy0 + img.height * z)
        vx0, vy0 = max(0, round(caja[0])), max(0, round(caja[1]))
        vx1, vy1 = min(cw, round(caja[2])), min(ch, round(caja[3]))
        if vx1 > vx0 and vy1 > vy0:
            recorte = (max(0.0, (vx0 - sx0) / z), max(0.0, (vy0 - sy0) / z),
                       min(img.width, (vx1 - sx0) / z), min(img.height, (vy1 - sy0) / z))
            trozo = img.resize((vx1 - vx0, vy1 - vy0), Image.NEAREST if z >= 1 else Image.BOX,
                               box=recorte, reducing_gap=3.0 if z < 0.5 else None)
            capa.paste(sobre(trozo, color), (vx0, vy0))
        self._capas = ([(img, clave, capa, caja)] + self._capas)[:4]
        return capa, caja

    def pintar(self, p, cw, ch, dpr):
        """Dibuja la vista en el lienzo (coordenadas en píxeles reales)."""
        color = self._color_vista()
        p.fillRect(0, 0, cw, ch, QColor(color))
        datos = self._imagenes()
        fuente = QFont(self.font())
        fuente.setPixelSize(round(13 * dpr))
        p.setFont(fuente)
        if datos is None or cw < 50 or ch < 50:
            texto = tr("Calculando…") if self.im is not None else tr("Arrastra aquí una imagen para empezar")
            p.setPen(QColor(contraste(color)))
            p.drawText(QRectF(0, 0, cw, ch), Qt.AlignCenter, texto)
            return
        tam, original, resultado = datos
        modo = self._modo()
        if resultado is None:
            modo = "Original"
        z, x0, y0 = self._geometria(tam)
        bx = 0
        if modo == "Comparar":
            izquierda, _ = self._capa(*original, z, x0, y0, cw, ch, color)
            vista, caja = self._capa(*resultado, z, x0, y0, cw, ch, color)
            bx = min(cw, max(0, round(self.barra * cw)))
            vista = vista.copy()
            vista.paste(izquierda.crop((0, 0, bx, ch)), (0, 0))
        else:
            vista, caja = self._capa(*(original if modo == "Original" else resultado), z, x0, y0, cw, ch, color)
        p.drawImage(0, 0, a_qimage(vista))
        if modo == "Original" and resultado is not None:
            caja = (x0, y0, x0 + tam[0] * z, y0 + tam[1] * z)
        lapiz = QPen(QColor(contraste(color)))
        lapiz.setStyle(Qt.DashLine)
        p.setPen(lapiz)
        p.setBrush(Qt.NoBrush)
        p.drawRect(QRectF(caja[0] - 1, caja[1] - 1, caja[2] - caja[0] + 1, caja[3] - caja[1] + 1))
        if modo == "Comparar":
            p.setPen(QPen(QColor(MARCA), 2 * dpr))
            p.drawLine(bx, 0, bx, ch)
            p.setBrush(QColor(MARCA))
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(QRectF(bx - 7 * dpr, ch / 2 - 22 * dpr, 14 * dpr, 44 * dpr), 4 * dpr, 4 * dpr)
            self._etiqueta(p, dpr, 12 * dpr, 10 * dpr, tr("Original"), "nw")
            self._etiqueta(p, dpr, cw - 12 * dpr, 10 * dpr, tr("Resultado"), "ne")
        self._etiqueta(p, dpr, 12 * dpr, ch - 10 * dpr, f"{round(z * 100)} %" + ("" if self.zoom else " " + tr("(ajustado)")), "sw")
        if self.cuentagotas:
            self._etiqueta(p, dpr, cw / 2, 10 * dpr, tr("Haz clic en el color de la camiseta (Esc para cancelar)"), "n")

    def _etiqueta(self, p, dpr, x, y, texto, ancla):
        m = p.fontMetrics()
        w, h = m.horizontalAdvance(texto) + 12 * dpr, m.height() + 4 * dpr
        izq = x if "w" in ancla else (x - w if "e" in ancla else x - w / 2)
        arriba = y if "n" in ancla else y - h
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 190))
        p.drawRoundedRect(QRectF(izq, arriba, w, h), 4 * dpr, 4 * dpr)
        p.setPen(QColor("#ffffff"))
        p.drawText(QRectF(izq, arriba, w, h), Qt.AlignCenter, texto)

    def _comparando(self):
        return self._modo() == "Comparar" and self.resultado is not None

    def clic(self, x, y):
        datos = self._imagenes()
        if datos is None:
            return
        if self.cuentagotas:
            z, x0, y0 = self._geometria(datos[0])
            _, dx, dy = datos[1]
            self._tomar_color(((x - x0) / z - dx, (y - y0) / z - dy))
        elif self._comparando():
            self._mover_barra(x)
        else:
            self.coger(x, y)

    def mover(self, x, y):
        if self.cuentagotas:
            return
        if self._comparando():
            self._mover_barra(x)
        else:
            self.arrastrar(x, y)

    def _mover_barra(self, x):
        self.barra = min(1, max(0, x / max(self.lienzo.tam()[0], 1)))
        self.lienzo.update()

    def coger(self, x, y):
        self.arrastre = (x, y, self.centro or (0.5, 0.5))

    def arrastrar(self, x, y):
        datos = self._imagenes()
        if datos is None or not self.arrastre:
            return
        (W, H), z = datos[0], self._geometria(datos[0])[0]
        x1, y1, (cx, cy) = self.arrastre
        self.centro = (min(1, max(0, cx - (x - x1) / (W * z))), min(1, max(0, cy - (y - y1) / (H * z))))
        self.lienzo.update()

    def rueda(self, x, y, delta):
        """Acercar o alejar dejando quieto el punto que hay bajo el ratón."""
        datos = self._imagenes()
        if datos is None or not delta:
            return
        W, H = datos[0]
        z, x0, y0 = self._geometria(datos[0])
        nuevo = min(8, max(0.02, z * (1.25 if delta > 0 else 0.8)))
        px, py = (x - x0) / (W * z), (y - y0) / (H * z)
        cw, ch = self.lienzo.tam()
        self.zoom = nuevo
        self.centro = (min(1, max(0, px - (x - cw / 2) / (W * nuevo))),
                       min(1, max(0, py - (y - ch / 2) / (H * nuevo))))
        self.lienzo.update()

    # ----- cuentagotas y colores ------------------------------------------
    def _otro_color(self):
        c = QColorDialog.getColor(QColor(self.opciones().camiseta), self, tr("Color de la camiseta"))
        if c.isValid():
            self._cambio("camiseta", c.name().lower())

    def _activar_cuentagotas(self):
        if self.escalada is None:
            return
        self.cuentagotas = True
        self.lienzo.setCursor(Qt.CrossCursor)
        self.lienzo.update()

    def _fin_cuentagotas(self):
        if not self.cuentagotas:
            return
        self.cuentagotas = False
        self.lienzo.unsetCursor()
        self.lienzo.update()

    def _tomar_color(self, punto):
        img = self.escalada[2]
        x, y = int(punto[0]), int(punto[1])
        if 0 <= x < img.width and 0 <= y < img.height:
            # media de 5 × 5 píxeles para no coger ruido de la foto
            trozo = img.crop((max(0, x - 2), max(0, y - 2), min(img.width, x + 3), min(img.height, y + 3)))
            r, g, b = [round(sum(c) / len(c)) for c in zip(*[p[:3] for p in trozo.getdata()])]
            self._cambio("camiseta", f"#{r:02x}{g:02x}{b:02x}")
        self._fin_cuentagotas()

    # ======================================================================
    # Información y guardar
    # ======================================================================
    def _info(self):
        if not hasattr(self, "l_info"):
            return
        if self.im is None:
            self.l_info.setText(AYUDA_VISTA)
            self.l_info.setStyleSheet("")
            return
        if self._error:
            self.l_info.setText(f"✖ {self._error}")
            self.l_info.setStyleSheet(f"color: {self.t['error']};")
            return
        op = self.opciones()
        w, h = T.medidas_px(self.im, op)
        ancho, alto = op.ancho_cm, op.ancho_cm * h / w
        if self.resultado and self.resultado[0] == op:
            rw, rh = self.resultado[1].size
            ancho, alto = rw / op.ppp * 2.54, rh / op.ppp * 2.54
            w, h = rw, rh
        texto = tr("Impresión: {ancho} × {alto} cm a {ppp} ppp ({w} × {h} px)").format(
            ancho=numero(ancho), alto=numero(alto), ppp=op.ppp, w=w, h=h)
        if op.semitono:
            texto += "  ·  " + tr("trama de {mm} mm").format(mm=numero(25.4 / op.lpi, 2))
        real = self.im.width / (op.ancho_cm / 2.54)
        estilo_info = ""
        if real < 150:
            texto += "\n" + tr("⚠ Poca resolución: la imagen original da {ppp} ppp a este tamaño. "
                              "Se verá borrosa (mejor no pasar de {cm} cm).").format(
                ppp=round(real), cm=numero(self.im.width / 150 * 2.54))
            estilo_info = f"color: {self.t['aviso']};"
        texto += "\n" + AYUDA_VISTA
        self.l_info.setText(texto)
        self.l_info.setStyleSheet(estilo_info)

    def _estado(self, texto):
        self._texto_estado = texto
        if hasattr(self, "l_estado"):
            self.l_estado.setText(texto)

    def _guardar_png(self):
        if self.im is None or self._guardando:
            return
        op = self.opciones()
        base = os.path.splitext(os.path.basename(self.ruta))[0]
        ruta = T.ruta_libre(os.path.dirname(self.ruta), f"{base} - DTF semitono", ".png")
        self._guardando = True
        self._actualizar_controles()
        self._estado(tr("Guardando…"))
        self.l_calculo.setText(tr("Guardando…"))
        with self._cerrojo:
            # el pedido de guardar lleva la ruta en el lugar del número de vista
            self._pedido_guardar = ("guardar", ruta, op, self.im)
            self._arrancar_hilo()

    def _abrir_carpeta(self):
        if self._carpeta_resultado and os.path.isdir(self._carpeta_resultado):
            QDesktopServices.openUrl(QUrl.fromLocalFile(self._carpeta_resultado))


def main():
    app = QApplication(sys.argv)
    idioma.instalar_qt(app)
    app.setApplicationName(APP_NOMBRE)
    app.setDesktopFileName(os.environ.get("FLATPAK_ID", "semitonos-dtf"))
    rutas = [a for a in sys.argv[1:] if os.path.isfile(a)]
    ventana = Semitonos(rutas[0] if rutas else None)
    ventana.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
