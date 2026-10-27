"""
Idioma de la interfaz (gettext).

Los textos originales del código están en castellano: ese es el idioma «sin traducir». Los demás idiomas
salen de codigo/locale/<idioma>/LC_MESSAGES/semitonos-dtf.mo (se compilan desde codigo/po/<idioma>.po).
Se sigue el idioma del sistema; si no es uno de los admitidos se usa inglés.

    tr("texto")          traduce un texto
    trc("contexto", "t") traduce un texto que se escribe igual pero significa otra cosa según el contexto
    N_("texto")          solo marca un texto para extraerlo (lo traduce más tarde quien lo muestre)
"""
import gettext
import os

DOMINIO = "semitonos-dtf"
IDIOMAS = ("es", "en", "de", "it", "fr", "pt_BR", "ca")
POR_DEFECTO = "en"
# configuración regional de Qt para cada idioma (números, diálogos estándar)
LOCALE_QT = {"es": "es_ES", "en": "en_US", "de": "de_DE", "it": "it_IT", "fr": "fr_FR", "pt_BR": "pt_BR", "ca": "ca_ES"}
CARPETA_LOCALE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "locale")


def _normalizar(codigo):
    """'pt_BR.UTF-8' → 'pt_BR'; 'ca_ES@valencia' → 'ca'; 'de-AT' → 'de'. None si no es uno de los admitidos."""
    codigo = codigo.split(".")[0].split("@")[0].replace("-", "_").strip()
    if not codigo or codigo in ("C", "POSIX"):
        return None
    if codigo in IDIOMAS:
        return codigo
    base = codigo.split("_")[0]
    if base == "pt":                       # portugués de Portugal y demás → el que tenemos (pt_BR)
        return "pt_BR"
    return base if base in IDIOMAS else None


def detectar():
    """El primer idioma admitido de los que pide el sistema (LANGUAGE, LC_ALL, LC_MESSAGES, LANG); si no, inglés."""
    candidatos = os.environ.get("LANGUAGE", "").split(":")
    candidatos += [os.environ.get(v, "") for v in ("LC_ALL", "LC_MESSAGES", "LANG")]
    for c in candidatos:
        c = c.split(".")[0].strip()
        if c in ("", "C", "POSIX"):       # «C» no dice nada del idioma: se sigue mirando
            continue
        return _normalizar(c) or POR_DEFECTO   # un idioma que no tenemos → inglés, no castellano
    return POR_DEFECTO


IDIOMA = detectar()
DECIMAL = "." if IDIOMA == "en" else ","

if IDIOMA == "es":
    _catalogo = gettext.NullTranslations()
else:
    _catalogo = gettext.translation(DOMINIO, CARPETA_LOCALE, languages=[IDIOMA], fallback=True)

tr = _catalogo.gettext


def trc(contexto, texto):
    return _catalogo.pgettext(contexto, texto)


def N_(texto):
    return texto


def instalar_qt(app):
    """Traducciones de Qt (botones de los diálogos estándar) y configuración regional. Llamar tras crear QApplication."""
    from PySide6.QtCore import QLibraryInfo, QLocale, QTranslator
    local = QLocale(LOCALE_QT[IDIOMA])
    QLocale.setDefault(local)
    ruta = QLibraryInfo.path(QLibraryInfo.TranslationsPath)
    for nombre in ("qtbase", "qt"):
        t = QTranslator(app)
        if t.load(local, nombre, "_", ruta):
            app.installTranslator(t)
