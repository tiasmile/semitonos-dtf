# PyInstaller: un único ejecutable portable. Lo usa compilar_linux.sh.
datas = [("recursos", "recursos")]

a = Analysis(
    ["semitonos.py"],
    pathex=["."],
    datas=datas,
    excludes=["PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.QtQuick", "PySide6.QtQml",
              "PySide6.Qt3DCore", "PySide6.QtMultimedia", "PySide6.QtCharts", "PySide6.QtDataVisualization",
              "PySide6.QtSql", "PySide6.QtNetwork", "PySide6.QtPdf", "PySide6.QtSvg", "tkinter", "matplotlib",
              "scipy", "pandas"],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name="Semitonos DTF",
    console=False,
    upx=False,
)
