# Translating Semitonos DTF · Cómo traducir

The interface uses **gettext**. Source language: Spanish. Translations live in `codigo/po/<language>.po`
(`en`, `de`, `it`, `fr`, `pt_BR`, `ca`). **All current translations were produced with AI assistance and have not been
reviewed by native speakers: corrections are very welcome.** Please read `codigo/po/GLOSARIO.md` first.

## Fix an existing translation
1. Edit `codigo/po/<language>.po` with any text editor, [Poedit](https://poedit.net/) or [Lokalize](https://apps.kde.org/lokalize/).
   Keep placeholders such as `{ancho}` or `{nombre}` exactly as they are, and keep the line breaks (`\n`).
2. Compile and try it:
   ```
   cd codigo
   po/compilar.sh
   LANGUAGE=de python3 semitonos.py
   ```
3. Run the language test: `QT_QPA_PLATFORM=offscreen python3 pruebas/prueba_idiomas.py` (it checks the `.po` files and that no text is cut off).
4. Send the change as a pull request.

## Add a new language
1. `cd codigo && po/extraer.sh && msginit --no-translator -l xx -i po/semitonos-dtf.pot -o po/xx.po`
2. Add `xx` to `IDIOMAS` and `LOCALE_QT` in `codigo/idioma.py`, and to `IDIOMAS`/`LOCALE` in `codigo/pruebas/prueba_idiomas.py`.
3. Translate the file as above, plus the store texts in `Programas/flatpak/textos_semitonos.py` if you maintain the packaging.

## Cambiar una traducción (castellano)
Edita `codigo/po/<idioma>.po`, ejecuta `po/compilar.sh` y prueba con `LANGUAGE=<idioma> python3 semitonos.py`. El
castellano es el idioma original: se cambia directamente en el código (`semitonos.py`, `tramado.py`) y luego
`po/extraer.sh` actualiza las plantillas de los demás idiomas.
