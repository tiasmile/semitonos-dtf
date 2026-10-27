"""Aspecto de la aplicación: minimalista, tema claro y oscuro, sin depender del tema del sistema."""

import os
import sys


def _check():
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "recursos", "check.png").replace("\\", "/")


TEMAS = {
    "claro": {
        "fondo": "#fafafb", "tarjeta": "#ffffff", "texto": "#2e2e32", "suave": "#77767b",
        "titulo": "#2e2e32", "campo": "#f0f0f2", "campo_texto": "#2e2e32", "borde": "#dcdce0",
        "seleccion": "#d0e1f7", "seleccion_texto": "#2e2e32", "boton": "#ebebed",
        "boton_hover": "#e0e0e3", "linea": "#e3e3e6", "zona": "#ffffff",
        "acento": "#3584e4", "acento_hover": "#4a93ea", "cuadros": ("#ffffff", "#e9ebee"),
        "vista": "#ebebed", "ok": "#26a269", "aviso": "#b5790a", "error": "#c01c28",
    },
    "oscuro": {
        "fondo": "#242424", "tarjeta": "#303030", "texto": "#f2f2f2", "suave": "#9a9996",
        "titulo": "#f2f2f2", "campo": "#3a3a3a", "campo_texto": "#f2f2f2", "borde": "#454545",
        "seleccion": "#2b4a73", "seleccion_texto": "#ffffff", "boton": "#3d3d3d",
        "boton_hover": "#4a4a4a", "linea": "#3a3a3a", "zona": "#2b2b2b",
        "acento": "#3584e4", "acento_hover": "#4a93ea", "cuadros": ("#f1f2f4", "#dfe1e5"),
        "vista": "#1c1c1c", "ok": "#57e389", "aviso": "#e5a50a", "error": "#ff7b63",
    },
}


def aplicar(app, nombre):
    """Fusion + paleta + hoja de estilo propias (en Linux el tema del sistema puede dejar textos ilegibles)."""
    from PySide6.QtGui import QColor, QPalette
    t = TEMAS[nombre]
    app.setStyle("Fusion")
    p = QPalette()
    for rol, clave in ((QPalette.Window, "fondo"), (QPalette.Base, "campo"), (QPalette.AlternateBase, "tarjeta"),
                       (QPalette.Button, "boton"), (QPalette.ToolTipBase, "campo"), (QPalette.Highlight, "seleccion"),
                       (QPalette.Text, "campo_texto"), (QPalette.WindowText, "texto"), (QPalette.ButtonText, "texto"),
                       (QPalette.ToolTipText, "texto"), (QPalette.HighlightedText, "seleccion_texto"),
                       (QPalette.PlaceholderText, "suave")):
        p.setColor(rol, QColor(t[clave]))
    for rol in (QPalette.Text, QPalette.WindowText, QPalette.ButtonText):
        p.setColor(QPalette.Disabled, rol, QColor(t["suave"]))
    app.setPalette(p)
    app.setStyleSheet(qss(nombre))


def qss(nombre):
    t = TEMAS[nombre]
    return f"""
* {{ font-family: "Adwaita Sans", "Cantarell", "Noto Sans", "Segoe UI", sans-serif; font-size: 13px; color: {t['texto']}; }}
QMainWindow {{ background: {t['fondo']}; }}
QWidget#raiz {{ background: {t['fondo']}; }}
QLabel {{ background: transparent; }}
QLabel#titulo {{ color: {t['suave']}; font-size: 12px; font-weight: 600; }}
QLabel#cabecera {{ color: {t['titulo']}; font-size: 20px; font-weight: 700; }}
QLabel#ok {{ color: {t['ok']}; font-weight: 600; }}
QLabel#aviso {{ color: {t['aviso']}; font-weight: 600; }}
QLabel#error {{ color: {t['error']}; font-weight: 600; }}
QLabel#vista {{ background: {t['vista']}; border-radius: 12px; }}
QLabel#suave, QLabel#ayuda {{ color: {t['suave']}; font-size: 12px; }}
QFrame#tarjeta {{ background: {t['tarjeta']}; border: 1px solid {t['linea']}; border-radius: 12px; }}
QFrame#tarjeta QLabel, QFrame#tarjeta QCheckBox {{ background: transparent; }}
QFrame#zona {{ background: {t['zona']}; border: 1px dashed {t['suave']}; border-radius: 12px; }}
QFrame#linea {{ background: {t['linea']}; }}
QFrame#fila {{ background: {t['tarjeta']}; border: 1px solid {t['linea']}; border-radius: 12px; }}
QFrame#fila QLabel {{ background: transparent; }}
QLabel#codigo {{ font-weight: 600; }}
QLabel#codigo:hover {{ color: {t['acento']}; }}
QPushButton {{ background: {t['boton']}; border: 1px solid {t['boton']}; border-radius: 8px; padding: 7px 16px; }}
QPushButton:hover {{ background: {t['boton_hover']}; }}
QPushButton:disabled {{ color: {t['suave']}; background: {t['fondo']}; }}
QPushButton#accion {{ background: {t['acento']}; border-color: {t['acento']}; color: #ffffff; font-weight: 600; padding: 9px 24px; border-radius: 20px; }}
QPushButton#accion:hover {{ background: {t['acento_hover']}; border-color: {t['acento_hover']}; }}
QPushButton#accion:disabled {{ background: {t['boton']}; border-color: {t['borde']}; color: {t['suave']}; }}
QLineEdit, QComboBox {{ background: {t['campo']}; color: {t['campo_texto']}; border: 1px solid {t['campo']};
                       border-radius: 8px; padding: 6px 8px; }}
QLineEdit:focus, QComboBox:focus {{ border-color: {t['acento']}; }}
QComboBox QAbstractItemView {{ background: {t['campo']}; color: {t['campo_texto']};
                               selection-background-color: {t['seleccion']}; selection-color: {t['seleccion_texto']}; }}
QCheckBox {{ spacing: 8px; }}
QCheckBox::indicator {{ width: 16px; height: 16px; border: 1px solid {t['suave']}; border-radius: 4px; background: {t['campo']}; }}
QCheckBox::indicator:checked {{ background: {t['acento']}; border-color: {t['acento']}; image: url({_check()}); }}
QRadioButton {{ spacing: 6px; }}
QRadioButton::indicator {{ width: 12px; height: 12px; border: 1px solid {t['suave']}; border-radius: 7px; background: {t['campo']}; }}
QRadioButton::indicator:checked {{ border: 1px solid {t['acento']}; border-radius: 7px; background: qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5, stop:0 #ffffff, stop:0.4 #ffffff, stop:0.45 {t['acento']}, stop:1 {t['acento']}); }}
QSlider::groove:horizontal {{ height: 4px; background: {t['borde']}; border-radius: 2px; }}
QSlider::sub-page:horizontal {{ background: {t['acento']}; border-radius: 2px; }}
QSlider::handle:horizontal {{ background: {t['acento']}; width: 14px; height: 14px; margin: -5px 0; border-radius: 7px; }}
QSlider::groove:horizontal:disabled, QSlider::sub-page:horizontal:disabled {{ background: {t['borde']}; }}
QSlider::handle:horizontal:disabled {{ background: {t['suave']}; }}
QPushButton#chico {{ padding: 4px 10px; }}
QPushButton#muestra {{ border: 1px solid {t['suave']}; border-radius: 4px; padding: 0; }}
QScrollArea {{ background: transparent; border: none; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
QScrollBar:vertical {{ background: {t['fondo']}; width: 12px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {t['boton']}; border: 1px solid {t['borde']}; border-radius: 5px; min-height: 30px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QToolTip {{ background: {t['campo']}; color: {t['campo_texto']}; border: 1px solid {t['borde']}; }}
QMessageBox, QFileDialog {{ background: {t['fondo']}; }}
"""
