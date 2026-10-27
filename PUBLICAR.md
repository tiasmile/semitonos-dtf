# Cómo publicar Semitonos DTF · guía paso a paso

Guía para ti (Tiasmile). Está pensada para hacerse en orden. Lo que **ya está hecho** y lo que **te toca a ti** va marcado:
✅ = hecho y comprobado · 👉 = lo haces tú.

---

## 0. LÉELO PRIMERO: la política de IA de Flathub

Flathub (la tienda que alimenta a Bazaar, Discover y GNOME Software) tiene una política sobre IA generativa. Esto es lo que
dice su documentación oficial hoy (<https://docs.flathub.org/docs/for-app-authors/requirements>, apartado «Generative AI
policy»), resumido:

- Tienes que **declarar** el código, la documentación, el empaquetado u otro material generado con IA que sepas que está
  incluido, indicando qué partes y en qué medida.
- **«Los manifiestos de Flathub no deben contener contenido generado o asistido por IA».** Declararlo no lo permite.
- Una herramienta de IA **no puede abrir ni automatizar el PR de envío, ni redactar sus mensajes de commit, descripciones,
  comentarios o respuestas**. Esas cosas las escribes tú.
- Si falta la declaración o es engañosa, o si hay «contenido excesivo generado con IA», el envío puede **cerrarse sin
  revisión**; las infracciones repetidas pueden acabar en prohibición.

Qué significa para Semitonos DTF, con total sinceridad:
- El port a Linux, las traducciones, el empaquetado y las pruebas los he hecho yo (Claude). Por tanto hay que declararlo
  (te dejé el borrador en `AI-ASSISTANCE.md`, con un hueco para que cuentes tú qué partes hiciste a mano).
- **Mi manifiesto (`flatpak/com.tiasmile.SemitonosDTF.yml`) no puede ser el que envíes a Flathub**: el manifiesto de Flathub
  lo tienes que escribir tú. Por eso he quitado de mis herramientas la generación de un «paquete para Flathub» y no he
  preparado el texto del PR. Puedo explicarte qué es cada campo, qué hace y cómo se comprueba (eso cuenta como
  consulta/explicación), pero no debo darte el archivo para copiarlo.
- Con tanto contenido asistido por IA, **existe el riesgo real de que lo cierren sin revisar**. No puedo decirte la
  probabilidad; es tu decisión si lo intentas.

Por eso hay **dos rutas**. Puedes hacer las dos (la B no impide la A):

| | Ruta A: Flathub | Ruta B: GitHub + archivo `.flatpak` |
|---|---|---|
| Aparece en Bazaar/Discover para todo el mundo | Sí, una vez aceptada | No (no sé con certeza cómo lista Bazaar los remotos que no son Flathub) |
| Revisión | Sí, voluntarios, de días a semanas | Ninguna |
| Manifiesto escrito por ti | Obligatorio | No hace falta |
| Riesgo por la política de IA | Alto (puede cerrarse sin revisar) | Ninguno |
| Necesita tiasmile.com pública | Sí (verificación del ID `com.tiasmile`) | No |

---

## 1. Subir el código a GitHub (sirve para las dos rutas)

### 1.1 👉 Cuenta de GitHub y seguridad
1. Si no tienes cuenta: <https://github.com/signup>. Usa un nombre que quieras que sea público (saldrá en las URLs).
2. Activa la verificación en dos pasos (Settings → Password and authentication → Two-factor authentication). Flathub la
   exige más adelante.

### 1.2 👉 Clave SSH (para poder subir código sin escribir contraseñas)
En una terminal:
```
ssh-keygen -t ed25519 -C "contacto@tiasmile.com"
cat ~/.ssh/id_ed25519.pub
```
(Pulsa Intro para aceptar la ruta; pon una contraseña si quieres.) Copia el texto que sale de `cat` y pégalo en GitHub →
Settings → SSH and GPG keys → **New SSH key**. Comprueba:
```
ssh -T git@github.com
```
Debe decir «Hi TU_USUARIO! You've successfully authenticated…». (La primera vez pregunta «yes/no»: escribe `yes`.)

### 1.3 👉 Crear el repositorio vacío
GitHub → **New repository** → nombre **`semitonos-dtf`** → **Public** → **no marques** README, .gitignore ni licencia
(ya los tenemos) → Create repository.

### 1.4 👉 Escribir tu usuario y completar los avisos
1. Abre `flatpak/publicacion.json` y pon tu usuario: `{ "usuario_github": "TU_USUARIO" }`.
2. Regenera los metadatos (añade los enlaces al repositorio y las capturas a la ficha de tienda):
   ```
   python3 ~/Claude/Programas/flatpak/generar-flatpak.py ~/Claude/Programas/"Semitonos DTF"
   ```
3. Abre `AI-ASSISTANCE.md` y completa «Author's note»: cuenta, con tus palabras, qué partes del programa escribiste o
   diseñaste tú (el programa original, la lógica del semitono, las decisiones de diseño…). Es lo que hace que la
   declaración sea exacta.
4. 👉 Pide a alguien que hable inglés, alemán, italiano, francés, portugués o catalán que mire su idioma (o corrígelas tú
   si hablas alguno): las traducciones están **sin revisar por nativos**. Cada corrección: editar `codigo/po/<idioma>.po`
   (ver `TRADUCIR.md`).
5. Guarda los cambios:
   ```
   cd ~/Claude/Programas/"Semitonos DTF"
   git add -A && git commit -m "Usuario de GitHub y declaración de IA"
   ```
   (Los mensajes de commit los escribes tú: aquí te pongo uno de ejemplo, cámbialo si quieres.)

### 1.5 👉 Subir
```
cd ~/Claude/Programas/"Semitonos DTF"
git remote add origin git@github.com:TU_USUARIO/semitonos-dtf.git
git push -u origin main
```
Debes ver el código en `https://github.com/TU_USUARIO/semitonos-dtf` con el README en inglés y la captura.

### 1.6 👉 Etiqueta de versión
Las capturas de la ficha apuntan a la etiqueta `v1.0.0`, así que créala **después** de tener todo listo:
```
git tag -a v1.0.0 -m "Semitonos DTF 1.0.0"
git push origin v1.0.0
```
Comprueba que esta URL enseña la imagen:
`https://raw.githubusercontent.com/TU_USUARIO/semitonos-dtf/v1.0.0/flatpak/capturas/claro.png`

---

## 2. Ruta B: archivo `.flatpak` en «Releases» (sin revisión)

✅ Ya puedo generar el archivo (probado: ~41 MB). Cuando quieras la versión final:
```
~/Claude/Programas/flatpak/construir.sh "Semitonos DTF"            # reconstruye con lo último
~/Claude/Programas/flatpak/empaquetar-release.sh "Semitonos DTF" 1.0.0
```
Deja `Semitonos DTF/dist/semitonos-dtf-1.0.0.flatpak` y su `.sha256`.

👉 En GitHub: repositorio → **Releases** → **Draft a new release** → elige la etiqueta `v1.0.0` → título «Semitonos DTF
1.0.0» → arrastra el `.flatpak` y el `.sha256` → **Publish release**. Quien lo descargue lo instala con
`flatpak install --user semitonos-dtf-1.0.0.flatpak` (baja el runtime de KDE de Flathub si le falta).

Más adelante puedo montar además un **repositorio Flatpak propio** (una dirección a la que la gente se suscribe y recibe
actualizaciones con `flatpak update`), alojado en GitHub Pages o en tiasmile.com. Dime si lo quieres.

---

## 3. Ruta A: Flathub (con revisión)

### 3.1 👉 Decidir el identificador
- `com.tiasmile.SemitonosDTF` (el actual) exige **demostrar que tiasmile.com es tuyo**: Flathub te da un código (token) en
  su portal de desarrolladores y lo pones en
  **`https://tiasmile.com/.well-known/org.flathub.VerifiedApps.txt`** (HTTPS; una línea por app; las líneas con `#` se
  ignoran). Hasta que la web esté pública y con HTTPS, no se puede verificar.
- Si prefieres no esperar: `io.github.TU_USUARIO.SemitonosDTF`, que se verifica entrando en Flathub con tu cuenta de
  GitHub. Si eliges esto, avísame y cambio el identificador en todo el proyecto (renombrado, metadatos, pruebas).

### 3.2 👉 Escribir TÚ el manifiesto
Es el archivo `.yml` que dice cómo se construye la app. Tiene que ser tuyo (política de IA). Para aprender:
- La guía oficial: <https://docs.flathub.org/docs/for-app-authors/requirements> y
  <https://docs.flatpak.org/en/latest/first-build.html>.
- Mi `flatpak/com.tiasmile.SemitonosDTF.yml` es **para uso local en tu PC**, no para enviar. Puedes preguntarme qué hace
  cada campo (runtime, base, `finish-args`, módulos, `sources`…) y te lo explico.
- Reglas que debes cumplir (de la documentación de Flathub): sin red durante la construcción, todas las fuentes con
  dirección pública y hash, nada precompilado dentro del PR, permisos al mínimo (si hay un portal, hay que usarlo), y la
  licencia correcta en el metainfo (ya está: AGPL-3.0-or-later).
- Ojo con los permisos de carpetas: Flathub revisa cada uno por separado y te pedirá justificarlo; cuanto menos pidas,
  mejor.

### 3.3 👉 Probar antes de enviar
```
flatpak run --command=flathub-build org.flatpak.Builder --install TU_MANIFIESTO.yml
flatpak run com.tiasmile.SemitonosDTF
flatpak run --command=flatpak-builder-lint org.flatpak.Builder manifest TU_MANIFIESTO.yml
flatpak run --command=flatpak-builder-lint org.flatpak.Builder repo repo
```
El validador debe salir sin errores. (✅ Comprobé que el metainfo y la estructura del proyecto pasan la parte que me
corresponde; los avisos que quedaban eran solo por no existir todavía tu usuario de GitHub.)

### 3.4 👉 Enviar el PR (lo haces tú, a mano)
1. Haz un *fork* de <https://github.com/flathub/flathub> **desmarcando** «Copy the master branch only».
2. Clona tu fork en la rama `new-pr`:
   `git clone --branch=new-pr git@github.com:TU_USUARIO/flathub.git && cd flathub`
3. Crea una rama: `git checkout -b semitonos-dtf new-pr`
4. Añade tus archivos (manifiesto, módulos…), `git add`, `git commit`, `git push`.
5. En GitHub abre un *pull request* con base **`new-pr`** (no `master`), título **«Add com.tiasmile.SemitonosDTF»**,
   rellenando la plantilla con tus palabras: qué es, la licencia, los permisos y su justificación, y **la declaración de
   IA** (qué partes, en qué medida; puedes apoyarte en `AI-ASSISTANCE.md`).
6. Los revisores son voluntarios: pueden tardar. **No cierres el PR** para corregir; responde tú a todo. Cuando hayas
   resuelto sus comentarios, escribe un comentario `bot, build` para lanzar una construcción de prueba (no enseña las
   capturas; salen cuando se publica la oficial).

### 3.5 Si la aceptan
Recibes una invitación a un repositorio nuevo de la organización `flathub` (con la 2FA activada, acéptala en menos de una
semana). La compilación oficial suele publicarse 1–2 horas después de fusionarse y la app tarda unas horas más en
aparecer. Ahí es cuando saldrá en Bazaar. Verifica entonces el identificador en el portal de desarrolladores.

---

## 4. Después de publicar
- Cada versión nueva: sube el número en el metainfo y el CHANGELOG, haz commit, crea la etiqueta (`v1.0.1`…),
  `construir.sh` + `empaquetar-release.sh` y una nueva Release (ruta B); para Flathub, actualiza tu manifiesto con la
  nueva etiqueta y abre el cambio tú.
- Cuando alguien corrija una traducción por GitHub, la acepto en el repositorio y recompilamos.

## Qué puedo seguir haciendo yo
Traducciones y pruebas, repositorio Flatpak propio, cambiar el identificador a `io.github…`, aplicar las correcciones de
idiomas que me pases, explicarte cualquier paso y preparar versiones nuevas. **No** puedo: crear tu cuenta ni subir
nada a GitHub por ti, abrir o redactar el PR de Flathub, escribir su manifiesto ni responder a los revisores.
