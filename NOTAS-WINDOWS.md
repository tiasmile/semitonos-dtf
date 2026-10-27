# Notes for a Windows version · Notas para una versión de Windows

> Written for whoever (a person, or an AI assistant such as Claude Code) picks up the Windows port. The author plans to do it
> from a Windows PC. Nothing here is done yet. Spanish summary at the end.

**Status:** Semitonos DTF 1.0.0 is Linux-only (a Flatpak). The code is Python 3 + PySide6 + Pillow + NumPy and is mostly
portable; the points below are what is Linux-specific. The interface language is Spanish in the source (gettext), with
translations in `codigo/po/`.

## 1. What to change in the code
| Where | Problem on Windows | What to do |
|---|---|---|
| `codigo/idioma.py` → `detectar()` | Reads only `LANGUAGE`, `LC_ALL`, `LC_MESSAGES`, `LANG`. These don't exist on Windows, so the interface would always be English. | When no variable is set, fall back to `QLocale.system().name()` (or `locale.getlocale()`); keep the env variables first (they are used by the tests). |
| `codigo/semitonos.py` → `carpeta_ajustes()` (~line 45) | Settings go to `~/.config/semitonos-dtf` (or `$XDG_CONFIG_HOME`). | On Windows use `%APPDATA%\semitonos-dtf` (e.g. `QStandardPaths.AppConfigLocation`). Keep the XDG path on Linux so existing settings keep working. |
| `codigo/semitonos.py` → `main()` | `app.setDesktopFileName(os.environ.get("FLATPAK_ID", "semitonos-dtf"))` is Linux/Flatpak-only. | Harmless on Windows, but you can skip it there. |
| `codigo/semitonos.py` → `_abrir_carpeta()` | Uses `QDesktopServices.openUrl(QUrl.fromLocalFile(...))`. | Should work as is on Windows; check it opens Explorer. |
| Paths | The code uses `os.path` everywhere, and `recurso()` / `estilo.py` look in `sys._MEIPASS` when frozen. | Check that PyInstaller bundles `recursos/` and `locale/` (see §2). |
| Interface style | `estilo.py` uses the Fusion style with its own palette and fonts. | Check fonts and sizes on Windows (the window has a minimum size of 1150 × 720 px). |

Keep the Spanish keys stored in `ajustes.json` (`"Hacia dentro"`, `"Cuadrado"`, `"Color elegido"`...): they are values, not
display texts. Display texts go through `tr()`; do **not** name anything `_` (the code uses `_` as a throwaway variable).

## 2. Building the `.exe`
- Dependencies: `codigo/requirements.txt` (`PySide6`, `pillow`, `numpy`, `pyinstaller`).
- The old PyInstaller spec was removed from the tree but is in the git history: `git show 849d625^:codigo/semitonos.spec`
  (it bundles `recursos/`; **also add `locale/`**, see below).
- Recommended: a **GitHub Actions** workflow on a `windows-latest` runner that builds the `.exe`/`.zip` when a `v*` tag is
  pushed and attaches it to the same GitHub Release as the Linux `.flatpak`. Public repositories get this for free.
- Without a code-signing certificate Windows SmartScreen will warn ("unknown publisher"); document "More info → Run
  anyway" in the README.

## 3. Translations (`.mo` files are not in git)
`codigo/locale/` is generated and git-ignored. Compile the `.po` files before building:
`po/compilar.sh` uses `msgfmt` (GNU gettext), which Windows doesn't have by default. Options: install gettext tools, or compile
with Python (`Tools/i18n/msgfmt.py` or Babel's `pybabel compile`) — the output must be
`locale/<lang>/LC_MESSAGES/semitonos-dtf.mo` for `en`, `de`, `it`, `fr`, `pt_BR`, `ca`. Without them the program silently
shows Spanish. Never commit the `.mo` files; compile them in the build.

## 4. Tests
- `codigo/pruebas/prueba_sin_pantalla.py` (calculation + window screenshots) and `codigo/pruebas/prueba_idiomas.py` (7
  languages): run with `QT_QPA_PLATFORM=offscreen`. The first sets `XDG_CONFIG_HOME` to a temporary folder; adapt it if you
  change the settings path. `prueba_idiomas.py` skips the `.po` check if `msgfmt` is missing.
- Test the real window by hand on Windows: open an image (button and drag & drop), change the options, save the PNG,
  switch language (set the Windows display language, or `set LANGUAGE=en` in the terminal).

## 5. Release and docs
- Same repository, same Release, more files: `semitonos-dtf-X.Y.Z.flatpak` (Linux) + `semitonos-dtf-X.Y.Z-windows.zip`.
  Supporting Windows changes the code, so it should be version **1.1.0**. See `CHANGELOG.md`.
- Update `README.md` / `README.es.md` (the "Linux only" notice), the GitHub repository description and topics.
- Disclose AI assistance in `AI-ASSISTANCE.md` for whatever you add.
- `flatpak/` and `PUBLICAR.md` only concern Linux packaging; leave them alone.

## Resumen en castellano
Falta: (1) que `idioma.py` detecte el idioma en Windows (hoy solo lee variables de Linux), (2) que los ajustes se guarden en
`%APPDATA%`, (3) compilar los `.po` a `.mo` sin `msgfmt`, (4) construir el `.exe` con PyInstaller (receta de GitHub Actions
recomendada) incluyendo `recursos/` y `locale/`, (5) probarlo a mano en Windows, (6) quitar el aviso «solo Linux» y subir el
`.zip` a la misma Release como versión 1.1.0.
