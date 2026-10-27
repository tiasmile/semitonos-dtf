# Changelog

## 1.0.0 — 2026-10-27
- Interface available in Spanish, English, German, Italian, French, Brazilian Portuguese and Catalan (follows the system language; English if the language isn't supported). Translations are machine-assisted and not yet reviewed by native speakers.
- Decimal separator follows the language (`22.5` in English, `22,5` elsewhere).
- Packaged as a Flatpak (`com.tiasmile.SemitonosDTF`) with store metadata in all seven languages.
- Language test (`codigo/pruebas/prueba_idiomas.py`): checks the `.po` files, that stored settings keep their Spanish keys in any language, and that nothing is cut off.
