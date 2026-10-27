# AI assistance / Uso de IA

This project was developed with the assistance of **Claude** (Anthropic), through Claude Code. In the interest of
transparency, this is what the assistant generated or helped with, as far as the project history shows:

- The port of the program from Windows (Python + tkinter) to Linux (Python + PySide6), including its interface.
- The translation system (`codigo/idioma.py`, `codigo/po/*`) and **all translations** (English, German, Italian, French,
  Brazilian Portuguese, Catalan). They have **not** been reviewed by native speakers yet.
- The Flatpak packaging (`flatpak/`), the AppStream and desktop metadata and their translations, the screenshots script and
  the example artwork (`flatpak/capturas/`, drawn by a script), the tests (`codigo/pruebas/`) and the documentation.
- **100% of the programming and source code**, generated through continuous iterative prompting.

**Author's note:** As a graphic designer, this tool was born from a direct need in my daily workflow to automate the tedious manual process of preparing DTF prints in Photoshop (copying layers, converting to black and white, adjusting contrast, and bitmap conversion). While the AI handled all the coding, the core concept, the feature design and the interface design and workflow are my own; the AI implemented them. I explicitly directed the AI to implement the specific toolset required for practical DTF printing: dynamic output resizing, color knockout for ink saving, gradient borders to soften edges, semi-transparency halftone conversion, and the custom background preview system to simulate the final garment. This note was polished with Gemini.

The program and its test suites were run to check the results; the translations were checked only for completeness, placeholders and layout, not for linguistic quality.

---

Este proyecto se ha desarrollado con la ayuda de **Claude** (Anthropic), mediante Claude Code: el port a Linux, el sistema
de traducción y **todas las traducciones** (sin revisar aún por hablantes nativos), el empaquetado Flatpak, los
metadatos, las capturas, las pruebas y la documentación. También se ha encargado de redactar el **100% del código fuente** bajo mis indicaciones.

**Nota del autor:** Como diseñador gráfico, esta herramienta nace de una necesidad en mi flujo de trabajo para automatizar el tedioso proceso manual de preparar impresiones DTF en Photoshop (copiar capas, pasar a blanco y negro, ajustar contraste y convertir a mapa de bits). Aunque la IA se ha encargado íntegramente de picar código, la idea original, la lógica del flujo de trabajo y el diseño de la interfaz son de creación propia (la IA los ha implementado). He guiado a la IA paso a paso para implementar las herramientas que realmente se necesitan al estampar: el ajuste de tamaño final de impresión, la eliminación de colores para ahorrar tinta, la creación de bordes degradados, la conversión de semitransparencias a semitonos y la previsualización sobre fondos neutros o del color exacto de la camiseta. Esta nota se ha pulido con Gemini.
