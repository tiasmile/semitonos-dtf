# Semitonos DTF

Prepara imágenes para estampar en **DTF** (direct to film) con semitonos.

La tinta blanca del DTF necesita que cada píxel sea totalmente opaco o totalmente transparente. Semitonos DTF coge una
imagen, le quita el color de la camiseta, suaviza los bordes hacia dentro o hacia fuera y convierte la transparencia en
una trama de puntos, con vista previa en directo del antes y el después sobre cualquier color de camiseta.

![Semitonos DTF](flatpak/capturas/claro.png)

## Qué hace
- Quita el color de la camiseta (con cuentagotas) para que se imprima como transparencia.
- Degradado del borde: hacia dentro o hacia fuera, siguiendo el diseño, ovalado o redondo.
- Semitono con lineatura (lpi), ángulo, forma del punto (redondo, euclídeo, cuadrado, líneas) y punto mínimo/máximo ajustables.
- Comparación en directo del original y el resultado, zoom y modo claro/oscuro.
- Guarda un PNG con los ppp que elijas. Nunca sobrescribe nada.
- Interfaz en **castellano, inglés, alemán, italiano, francés, portugués de Brasil y catalán** (sigue el idioma del sistema).

## Instalar
Se distribuye como Flatpak: `com.tiasmile.SemitonosDTF`. Descarga el archivo `.flatpak` de
[Releases](../../releases) e instálalo con `flatpak install --user semitonos-dtf-1.0.0.flatpak`.

## Ejecutar desde el código
Necesita Python 3, PySide6, Pillow y NumPy: `cd codigo && python3 semitonos.py [imagen.png]`.

## Traducciones y uso de IA
Las traducciones se han hecho con ayuda de IA y **aún no las ha revisado ningún hablante nativo**: se agradecen
correcciones ([TRADUCIR.md](TRADUCIR.md)). Ver también [AI-ASSISTANCE.md](AI-ASSISTANCE.md).

## Licencia
GNU Affero General Public License v3.0 o posterior ([LICENSE](LICENSE)).
