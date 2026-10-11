# Investigación: empaquetar Blender como programa propio (BIM Simple)

Fase de plan (Spec Kit), función 001. Fecha: 2026-10-11. Blender 5.2.0 LTS (hash fbe6228777e7), Windows 11.

**Marcas**: ✅ = ejecutado y comprobado (salida real guardada) · 📖 = solo leído (código instalado, código fuente de Blender o documentación oficial) · ⚠️ = conocimiento general **no verificado** (se necesita una prueba con ventana, que requiere permiso).

**Abreviaturas**
- `<BL>` = `C:\Program Files\Blender Foundation\Blender 5.2` (Blender instalado; solo se leyó).
- `<SC>` = `C:\Program Files\Blender Foundation\Blender 5.2\5.2\scripts`.
- `<R>` = `...\scratchpad\research\empaquetado\` (scripts y salidas de esta investigación).
- `<COPIA>` = `...\scratchpad\bs\blender\` (copia de prueba de `<BL>`, sin `blender.pdb`, con carpeta `portable`).
- "fuente 5.2" = `https://projects.blender.org/blender/blender/raw/branch/blender-v5.2-release/<ruta>`.

**Reglas cumplidas**: Blender siempre con `--background` o `-c` (que implica background). Nada descargado ni instalado en el sistema. La configuración del usuario quedó idéntica: SHA-256 de `config\*` y `extensions\.cache\compat.dat` antes y después (`<R>estado_usuario_antes.txt` / `estado_usuario_despues.txt`) ✅. No se tocó `<BL>`. La extensión de prueba (`bimsimple_prueba`, 2 archivos hechos aquí) solo se instaló en configuraciones del scratchpad.

---

## Resumen de decisiones

| # | Tema | Decisión recomendada |
|---|---|---|
| 1 | Configuración aparte | **Modo portable**: carpeta `portable` junto a `blender.exe` de la copia del programa. |
| 2 | Desarrollo y pruebas | `BLENDER_USER_RESOURCES=<carpeta>` con el Blender instalado (aísla config, scripts, extensiones y datafiles) hasta que exista la copia del programa; después, las pruebas corren con el `blender.exe` del programa. |
| 3 | Instalar Bonsai y BIM Simple | `blender.exe -c extension install-file -r user_default -e <zip>` corrido con el `blender.exe` de la copia (escribe solo en `portable`). Las dependencias quedan en `portable\extensions\.local\lib\python3.13\site-packages`. |
| 4 | Plantilla de aplicación | Plantilla `bim_simple` en `portable\scripts\startup\bl_app_templates_user\bim_simple\` con `__init__.py`, `startup.blend` y **obligatoriamente** `userpref.blend` (activa Bonsai + BIM Simple). Se elige con `--app-template bim_simple` en el acceso directo. |
| 5 | Sin pantalla de bienvenida | `preferences.view.show_splash = False`, guardado en el `userpref.blend` de la plantilla (y en el principal). |
| 6 | Español | `view.language = 'es'`, `use_translate_interface/tooltips/reports = True`, `use_translate_new_dataname = False`, en el `userpref.blend` principal de `portable\config` (el idioma NO lo pisa la plantilla). |
| 7 | Acceso directo | `.lnk` creado con WScript.Shell → `blender-launcher.exe` (no `blender.exe`, que abre consola), argumentos `--app-template bim_simple`, icono `.ico` propio. En la barra de tareas se verá el icono de Blender salvo un ajuste por ctypes que hay que probar con ventana. |
| 8 | Título de ventana | **No existe API de Python** en Blender 5.2. El título será "(no guardado) - Blender 5.2.0 LTS" (traducido). Diferencia a anotar en el plan. |
| 9 | Tiempo de arranque | En segundo plano: 2,0 s sin extensiones; 5,8–7,1 s con Bonsai. Importar Bonsai ≈ 2,9 s. Margen amplio frente a 20 s (SC-007), falta medir con ventana. |
| 10 | Tamaño / origen de la copia | `<BL>` ocupa 915 MB (830 MB sin `blender.pdb`). Es idéntica al contenido del instalador `.msi` (6.525 archivos). Programa completo ≈ 1,45–1,5 GB. Se puede copiar de `<BL>`. |

**Hallazgos que condicionan el plan** (detalle en cada pregunta):
1. **Rutas largas** ✅: Blender no acepta rutas de más de 260 caracteres. En una ruta larga, falló la carga de un módulo propio de Blender. El programa debe instalarse en una ruta corta, por ejemplo `%LOCALAPPDATA%\Programs\BIM Simple`.
2. **La carpeta del programa debe ser escribible**: Blender guarda allí la configuración portable, y Bonsai escribe su `process.log` dentro de su propio paquete. No sirve `C:\Program Files` sin permisos de administrador.
3. **Una plantilla sin `userpref.blend` propio desactiva todas las extensiones y vuelve a mostrar la pantalla de bienvenida** ✅. Y el `register()` de la plantilla **no puede** activar extensiones, porque corre antes de que exista el sistema de extensiones ✅.
4. **El archivo de recuperación `quit.blend` se comparte** 📖: Blender lo escribe en la carpeta temporal base (`%TEMP%`), igual que el Blender del usuario. Hay que darle al programa su propia carpeta temporal (`filepaths.temporary_directory`); si no, "Recuperar última sesión" del Blender del usuario podría abrir una sesión de BIM Simple.
5. **El zip `bonsai_py313-0.9.0-windows-x64.zip` no está en la computadora** ✅. Solo están `Downloads\bonsai_py311-0.9.0-windows-x64.zip` (no sirve en 5.2) y `Downloads\blender-5.2.0-windows-x64.msi`.
6. Otro proceso (no esta investigación) usó Blender con la configuración del usuario a las 01:54–01:55: importó `bim_simple_test_mvp.ifc`. Eso escribió `bonsai\bim\data\process.log` y 83 `.pyc` en `%APPDATA%\...\extensions\.local`. Es el comportamiento normal de Bonsai, pero significa que **correr pruebas con la configuración del usuario sí la modifica** (dentro de `.local`). Es otro motivo para la configuración aislada.

---

## 1. Modo portable de Blender 5.2 en Windows

**Decisión recomendada**: usar el modo portable en la copia del programa. Basta con crear la carpeta vacía `portable` junto a `blender.exe`.

**Por qué**: lo activa una carpeta, sin variables de entorno ni scripts de arranque. Todo lo del usuario (config, scripts, extensiones, dependencias `.local`, plantillas de usuario) queda dentro de la carpeta del programa. Desinstalar = borrar la carpeta (FR-005). Se probó también que la carpeta completa se puede **mover** después de instalar extensiones y sigue funcionando, porque los repositorios guardan rutas relativas (`use_custom_directory=False`) ✅.

**Alternativas consideradas**:
- `BLENDER_USER_RESOURCES` en un lanzador `.cmd`/`.vbs`: funciona (ver pregunta 2), pero necesita un script intermedio. Un `.cmd` muestra una consola y un `.vbs` agrega una pieza más; además el acceso directo apuntaría a ese script y no al programa.
- Variables `BLENDER_USER_CONFIG/SCRIPTS/EXTENSIONS` por separado: dejan `DATAFILES` y `resource_path('USER')` apuntando a `%APPDATA%` del usuario ✅. Se descarta.

**Evidencia**
- 📖 Manual 5.2, "Blender's Directory Layout" (fuente RST `https://projects.blender.org/blender/blender-manual/raw/branch/main/manual/advanced/blender_directory_layout.rst`): en Windows y Linux, una carpeta llamada `portable` "next to the Blender executable, in the unzipped folder" hace que preferencias, archivo de inicio, extensiones y presets se guarden allí. `BLENDER_USER_RESOURCES` "can be set to a custom directory to replace the default user directory."
- 📖 fuente 5.2 `source/blender/blenkernel/intern/appdir.cc`, función `get_path_user_ex`: primero `BLENDER_USER_RESOURCES`, después `get_path_local_ex(..., "portable", ...)` (base = carpeta del ejecutable) y, si no hay ninguno, la carpeta del sistema operativo.
- ✅ `<COPIA>` con `portable\` vacía, salida `<R>t4_portable_short.txt`:
  - `resource_path USER` = `<COPIA>\portable`
  - `user_resource CONFIG` = `<COPIA>\portable\config`; `SCRIPTS` = `...\portable\scripts`; `EXTENSIONS` = `...\portable\extensions`; `DATAFILES` = `...\portable\datafiles`
  - repositorios: `blender_org` → `...\portable\extensions\blender_org`, `user_default` → `...\portable\extensions\user_default`, `System` → `<COPIA>\5.2\extensions\system`
  - Sin la versión "5.2" como subcarpeta: `config` cuelga directamente de `portable`.
  - Bonsai no se cargó: Blender limpio.
- ✅ `bpy.app.portable` **no** indica el modo portable: devolvió `False` en `<BL>` y en `<COPIA>`. La documentación lo describe como "True unless blender was built to reference absolute paths (on UNIX)" (`https://docs.blender.org/api/current/bpy.app.html`). Para saber si se está en modo portable: `bpy.utils.resource_path('USER')` termina en `portable`.
- ✅ **Rutas largas**: en `<R>copia\BIMSimple\blender` (175 caracteres de base), Blender falló al cargar su propio complemento `bl_pkg`: `ImportError: cannot import name 'blender_asset_library_openapi'` (`<R>t3_portable_out.txt`), aunque el archivo existía. Movida a `scratchpad\bs\blender` (141 caracteres), arrancó sin errores. `LongPathsEnabled=1` en el registro no alcanza: Blender no declara soporte de rutas largas. Rutas relativas más largas medidas: 143 caracteres dentro de la copia de Blender y 132 dentro de `extensions\` con Bonsai, a lo que se suma `__pycache__\...cpython-313.pyc` ✅. **Conviene una ruta base de 90 caracteres o menos.**
- ✅ Correr la copia en una carpeta escribible crea `.pyc` dentro de `<COPIA>\5.2\python\lib\__pycache__` (200 archivos nuevos en la primera corrida). Es normal y acelera los arranques siguientes.
- ✅ Caché local: incluso en modo portable, `bpy.app.cachedir` = `C:\Users\Usuario\AppData\Local\Blender Foundation\Blender\Cache\`. Allí están `gl-shader-cache`, `asset-library-indices` y `remote-assets`. No hay preferencia para cambiarla (en `PreferencesFilePaths` solo existen `temporary_directory`, `render_cache_directory` y `texture_cache_directory`). Se comparte con el Blender del usuario. No es parte de "preferencias, extensiones ni archivo de inicio" (SC-005), y la carpeta ya existe en esta computadora, pero hay que anotarlo en el plan como lo único que BIM Simple puede tocar fuera de su carpeta.

## 2. Variables de entorno para separar la configuración

**Decisión recomendada**: para desarrollar y probar antes de que exista la copia del programa, usar **solo** `BLENDER_USER_RESOURCES` apuntando a una carpeta de desarrollo, por ejemplo `.blender_dev\` dentro del proyecto (ignorada por git), con el `blender.exe` instalado. Cuando exista la copia del programa, las pruebas automáticas deben correr con el `blender.exe` del programa, que es lo que usará el usuario.

**Por qué**: una sola variable redirige config, scripts, extensiones (incluido `.local`) y datafiles. La configuración del usuario no se lee ni se escribe. No hace falta copiar Blender para desarrollar.

**Alternativas consideradas**: variables separadas (se pierde `DATAFILES`, ver abajo); `--factory-startup` (no aísla las extensiones: el repositorio `user_default` sigue apuntando a la carpeta del usuario, y activar Bonsai así podría resincronizar el `.local` del usuario; ver `addon_utils.py:1234` y `:1383-1420`). Se descarta.

**Evidencia**
- ✅ `blender.exe --help` (`<R>help.txt`, líneas 506-524), texto literal:
  ```
  Environment Variables:
    $BLENDER_USER_RESOURCES  Replace default directory of all user files.
                             Other 'BLENDER_USER_*' variables override when set.
    $BLENDER_USER_CONFIG     Directory for user configuration files.
    $BLENDER_USER_SCRIPTS    Directory for user scripts.
    $BLENDER_USER_EXTENSIONS Directory for user extensions.
    $BLENDER_USER_DATAFILES  Directory for user data files (icons, translations, ..).

    $BLENDER_SYSTEM_RESOURCES  Replace default directory of all bundled resource files.
    $BLENDER_SYSTEM_SCRIPTS    Directories to add extra scripts.
    $BLENDER_SYSTEM_EXTENSIONS Directory for system extensions repository.
    $BLENDER_SYSTEM_DATAFILES  Directory to replace bundled datafiles.
    $BLENDER_SYSTEM_PYTHON     Directory to replace bundled Python libraries.
    $BLENDER_CUSTOM_SPLASH     Full path to an image that replaces the splash screen.
    $BLENDER_CUSTOM_SPLASH_BANNER Full path to an image to overlay on the splash screen.
    $BLENDER_OCIO              Path to override the OpenColorIO configuration file.
  ```
  También hay argumentos `--env-system-datafiles`, `--env-system-scripts`, `--env-system-extensions` y `--env-system-python` (líneas 406-416), y `--python-use-system-env` (Blender ignora `PYTHONPATH` y otras variables de Python salvo con ese argumento, líneas 164-166).
- ✅ Prueba A, `BLENDER_USER_RESOURCES=<R>t1_user_resources` (`<R>t1_out.txt`):
  - `resource_path('USER')` = `<R>t1_user_resources`
  - `user_resource('CONFIG')` = `...\t1_user_resources\config`; `('SCRIPTS')` = `...\scripts`; `('EXTENSIONS')` = `...\extensions`; `('DATAFILES')` = `...\datafiles`
  - repositorios: `extensions.blender.org` (module `blender_org`, USER, remoto) → `...\t1_user_resources\extensions\blender_org`; `User Default` (`user_default`, USER) → `...\extensions\user_default`; `System` (`system`, SYSTEM) → `<BL>\5.2\extensions\system`
  - add-ons activos: solo los de fábrica (`bl_pkg`, `cycles`, `io_*`, `pose_library`); Bonsai no está en `sys.modules`; ninguna ruta `.local` en `sys.path`.
  - En `--background` la carpeta quedó **vacía**: no se escribe nada mientras no se guarden preferencias o se instale algo.
- ✅ Prueba B, variables por separado (`BLENDER_USER_CONFIG`, `_SCRIPTS`, `_EXTENSIONS`, `BLENDER_SYSTEM_EXTENSIONS`, `BLENDER_SYSTEM_SCRIPTS`), salida `<R>t2_out.txt`:
  - CONFIG, SCRIPTS y EXTENSIONS fueron a las carpetas indicadas.
  - **`user_resource('DATAFILES')` y `resource_path('USER')` siguieron en `C:\Users\Usuario\AppData\Roaming\Blender Foundation\Blender\5.2`**.
  - `BLENDER_SYSTEM_EXTENSIONS=<X>` crea el repositorio System en `<X>\system` (agrega la subcarpeta `system`).
  - `BLENDER_SYSTEM_SCRIPTS` se suma a `bpy.utils.script_paths()`.
- 📖 fuente 5.2 `appdir.cc`, `BKE_appdir_folder_id_ex`: cada `BLENDER_USER_CONFIG/SCRIPTS/EXTENSIONS/DATAFILES` se consulta antes que la ruta de usuario.
- ✅ Repositorio de desarrollo: con `-c extension repo-add bimsimple_dev --name "BIM Simple (desarrollo)" --directory <carpeta con la extensión> --source SYSTEM` en una configuración aislada (`<R>t7`), la extensión se cargó **directamente desde su carpeta de código**, sin instalar ni copiar: `register() OK, package = bl_ext.bimsimple_dev.bimsimple_prueba`. Ojo: Python escribe `__pycache__` dentro de esa carpeta de código, así que hay que ignorarlo en git.
- ✅ `--addons bl_ext.<repo>.<id>` registra una extensión solo para esa corrida, sin guardarla en las preferencias (`register() OK`, pero `prefs.addons` quedó vacío). Sirve para pruebas.

## 3. Instalar Bonsai y una extensión propia en la configuración aislada

**Decisión recomendada**: al armar el programa, correr con el `blender.exe` **de la copia** (que ya tiene `portable`):
```
blender.exe -c extension install-file -r user_default -e <ruta>\bonsai_py313-0.9.0-windows-x64.zip
blender.exe -c extension build --source-dir <proyecto>\<carpeta de la extensión> --output-dir <dist>
blender.exe -c extension install-file -r user_default -e <dist>\bim_simple-<versión>.zip
```
`-e` activa la extensión y guarda `portable\config\userpref.blend`. Así las ruedas de Bonsai (~440 MB) se descomprimen una sola vez, al armar el programa, y no en el primer arranque del usuario.

**Por qué**: es la herramienta oficial, escribe solo en la configuración de esa copia, y deja la extensión activada y registrada igual que si se instalara desde la interfaz.

**Alternativas consideradas**:
- **Repositorio System** (`<copia>\5.2\extensions\system\`, "Extensions extracted into this directory will be available from the default 'System' repository", `<BL>\5.2\extensions\system\readme.txt` ✅): solo lectura y no se puede desinstalar desde la interfaz. Pero (a) agrega archivos dentro de la carpeta de Blender, que debería quedar tal cual para actualizarla reemplazándola (Principio III); (b) las ruedas igual se descomprimen en el `.local` del **usuario** (`portable\extensions\.local`) y recién en el primer arranque; (c) hay que activarla igual en `userpref.blend`. Queda como opción para la extensión BIM Simple si se quiere que sea "de sistema".
- **Copiar la carpeta `user_default\bonsai` ya instalada del usuario**: no requiere descarga, pero no se puede comprobar su SHA-256 contra el publicado y depende de una instalación ajena. No recomendado.

**Evidencia**
- ✅ `blender.exe -c help` lista los comandos `asset_listing`, `extension` y `maketx`.
- ✅ `-c extension --help` (`<R>cmd_ext_help.txt`): subcomandos `server-generate, build, validate, list, sync, update, install, install-file, remove, repo-list, repo-add, repo-remove`.
- ✅ `-c extension install-file --help` (`<R>cmd_ext_installfile_help.txt`), literal:
  ```
  usage: blender --command extension install-file [-h] -r REPO [-e] [--no-prefs] FILE
  Install a package file into a user repository.
    FILE             The packages file.
    -r, --repo REPO  The repository identifier.
    -e, --enable     Enable the extension after installation.
    --no-prefs       Treat the user-preferences as read-only,
                     preventing updates for operations that would otherwise modify them.
  ```
- ✅ `repo-add --help`: `--name`, `--directory`, `--url`, `--access-token`, `--source` ("The type of source in ('USER', 'SYSTEM'). System repositories are managed outside of Blender and are considered read-only."), `--cache`, `--clear-all`, `--no-prefs`. Y `build --help`: `--source-dir`, `--output-dir`, `--output-filepath`, `--valid-tags`, `--split-platforms`, `--verbose`.
- ✅ Prueba en `<COPIA>` (portable) con la extensión de prueba: `install-file -r user_default -e bimsimple_prueba-0.0.1.zip` → `STATUS Installed "bimsimple_prueba"`. Creó:
  - `portable\config\userpref.blend`
  - `portable\extensions\.cache\compat.dat`
  - `portable\extensions\user_default\bimsimple_prueba\`
  - `portable\extensions\user_default\.blender_ext\`

  `-c extension list` la muestra `[installed]`, y al arrancar después `prefs.addons` = `['bl_ext.user_default.bimsimple_prueba']`. La configuración del usuario no cambió ✅.
- **Dónde quedan las dependencias de Bonsai** 📖 (código instalado):
  - `<SC>\modules\addon_utils.py:1781-1828` (`_initialize_extensions_site_packages`): agrega a `sys.path` la carpeta `<user_resource('EXTENSIONS')>\.local\lib\python3.13\site-packages`, antes que los site-packages propios de Python.
  - `addon_utils.py:1831-1840`: usa `_bpy.utils.user_resource('EXTENSIONS')`.
  - `addon_utils.py:1185-1192` y `:1383-1420`: las ruedas de **todas** las extensiones activas, de cualquier repositorio (System incluido; ver `_extension_compat_cache_create`, `:1036-1108`), se sincronizan en `<EXTENSIONS de usuario>\.local`.

  En el programa quedarán en **`<programa>\blender\portable\extensions\.local\lib\python3.13\site-packages`**. En la configuración real del usuario, ese `.local` mide 490 MB (440 MB sin `__pycache__`) y **todo es de Bonsai** (93 ruedas en su manifiesto; `mcp` no tiene ruedas) ✅.
- ✅ Detalle de Bonsai 0.9.0 (`%APPDATA%\...\user_default\bonsai\blender_manifest.toml`): `blender_version_min = "5.1.0"`, `platforms = ["windows-x64"]`, `license = ["SPDX:GPL-3.0-or-later"]`. La carpeta de la extensión solo tiene `__init__.py`, `translations.py`, el manifiesto y `wheels\` (146 MB). El propio Bonsai viene como rueda (`bonsai-0.9.0-py3-none-any.whl`) y se importa como paquete `bonsai` desde `.local`.
- ✅ **Zip `bonsai_py313-0.9.0-windows-x64.zip`: NO se encontró** en Descargas, Documentos ni Escritorio (búsqueda en todo `%USERPROFILE%` hasta 6 niveles). Solo hay:
  - `C:\Users\Usuario\Downloads\bonsai_py311-0.9.0-windows-x64.zip` (150.121.000 bytes, 2026-10-10). Es el paquete py311, que según la constitución no carga en 5.2.
  - `C:\Users\Usuario\Downloads\blender-5.2.0-windows-x64.msi` (365.240.320 bytes).

  Habrá que **volver a descargar** el paquete py313, con permiso del usuario.
- 📖 Bonsai escribe dentro de su propio paquete: `bonsai/tool/blender.py:2146-2147` (`get_internal_data_dir` = `<paquete bonsai>/bim/data`). Allí escribe `process.log` al cargar y guardar proyectos (`bonsai/bim/module/project/operator.py:1241` y `:2080`). Visto en la configuración del usuario: el archivo tenía la importación de `bim_simple_test_mvp.ifc` ✅. Por eso la carpeta del programa tiene que ser escribible.

## 4. Plantillas de aplicación (app templates)

**Decisión recomendada**: crear la plantilla `bim_simple` en `<programa>\blender\portable\scripts\startup\bl_app_templates_user\bim_simple\` con:
- `__init__.py` con `register()` y `unregister()`, solo para manejadores livianos (por ejemplo `load_factory_startup_post`). **No** para activar extensiones.
- `userpref.blend` (**obligatorio**) con Bonsai y BIM Simple activados, `show_splash=False` y los bloqueos de `preferences.apps`.
- `startup.blend` con la escena vacía y la pantalla de BIM Simple, para cumplir FR-006: el inicio de fábrica trae Cube, Camera y Light ✅.
- `splash.png` (1000×500): opcional; no se ve si la bienvenida está desactivada.

El acceso directo la elige con `--app-template bim_simple`.

**Por qué**: agrupa en una carpeta del programa todo lo propio del arranque (archivo de inicio, preferencias que activan las extensiones, imagen). Sobrevive a `wm.read_homefile` (que Bonsai usa en `bim.new_project`, según `PLAN.md` del MVP), porque Blender vuelve a cargar el `startup.blend` de la plantilla. Y no se mezcla con la carpeta de Blender, que queda sin cambios.

**Alternativas consideradas**: sin plantilla, con `portable\config\startup.blend` y `portable\config\userpref.blend` armados al instalar. También funciona y es más simple, pero el archivo de inicio queda como "del usuario" en la configuración, y un "Nuevo" de Blender cargaría ese archivo y no uno fijo del programa. Las dos opciones son válidas; la plantilla da más control.

**Evidencia**
- ✅ Plantillas que trae Blender: `<SC>\startup\bl_app_templates_system\`: `2D_Animation`, `Sculpting`, `Storyboarding` y `Video_Editing` (con `__init__.py` y `startup.blend`) y `VFX` (solo `startup.blend`). Ninguna trae `userpref.blend` ni `splash.png`.
- 📖 Todas las que traen `__init__.py` siguen el mismo patrón: `register()` agrega un manejador a `bpy.app.handlers.load_factory_startup_post` y `unregister()` lo quita. Ejemplo: `2D_Animation\__init__.py:44-56`. En el manejador ajustan pantallas, escenas y espacios (`:11-41`).
- 📖 `<SC>\modules\bl_app_template_utils.py`:
  - `:37-79` `_enable`: importa la plantilla y llama a `mod.register()` (`:66`) **dentro de `RestrictBlend()`** (`:50`), es decir con el contexto restringido.
  - `:137-149` `import_from_id`: busca la plantilla con `bpy.utils.app_template_paths(path=template_id)`.
  - `:152-166` `activate`: desactiva la anterior y activa la nueva.
  - `:169-177` `reset`: lee `bpy.context.preferences.app_template`.
- 📖 `<SC>\modules\bpy\utils\__init__.py`:
  - `:379-399` `load_scripts_extensions`: carga la plantilla (`bl_app_template_utils.reset`, `:388-391`) **antes** de inicializar add-ons y extensiones (`:393-399`).
  - `:523-548` `app_template_paths`: orden de búsqueda = `{SCRIPTS de usuario}\startup\bl_app_templates_user` (`:535`) → cada `BLENDER_SYSTEM_SCRIPTS\startup\bl_app_templates_system` (`:539-543`) → `{SCRIPTS del sistema}\startup\bl_app_templates_system` (`:546`).
- 📖 Las plantillas del usuario se instalan en `user_resource('SCRIPTS', path="startup/bl_app_templates_user")`: `<SC>\startup\bl_operators\userpref.py:976` (`PREFERENCES_OT_app_template_install`, `bl_idname = "preferences.app_template_install"`, ruta en `:1007-1009`). El menú "Install Application Template..." está en `<SC>\startup\bl_ui\space_topbar.py:139`, y la lista de "Archivo > Nuevo" en `space_topbar.py:222-279`.
- 📖 Manual (`blender-manual/.../advanced/app_templates.rst`):
  - archivos opcionales: `startup.blend` ("Factory startup file to use for this template"), `userpref.blend` ("Factory preferences file to use for this template"), `splash.png` ("a 1000x500 image"), `__init__.py` con `register`/`unregister`. El manual **no menciona `splash_2x.png`**, y el código de 5.2 solo carga `splash.png` (fuente 5.2 `wm_splash_screen.cc`, `wm_block_splash_image`).
  - la configuración del usuario de cada plantilla va en `./config/{APP_TEMPLATE_ID}/`.
  - por línea de comandos: `blender --app-template my_template`.
- 📖 fuente 5.2 `creator_args.cc`, `arg_handle_app_template`: `--app-template X` llama a `WM_init_state_app_template_set(X)`, y `default` equivale a ninguna plantilla. Se procesa en `ARG_PASS_SETTINGS`, antes de `WM_init`.
- 📖 fuente 5.2 `blenkernel/intern/blender.cc`, `BKE_blender_userdef_app_template_data_swap`: el `userpref.blend` de la plantilla reemplaza `uistyles`, `uifonts`, `themes`, **`addons`**, `user_keymaps`, `user_keyconfig_prefs`, `font_path_ui(_mono)`, `keyconfigstr`, `gizmo_flag`, **`app_flag`**, `ui_scale` y los bits de `uiflag` `USER_SAVE_PROMPT | USER_SPLASH_DISABLE | USER_SHOW_GIZMO_NAVIGATE`. **El idioma no está en esa lista.**
- ✅ **¿Puede una plantilla activar una extensión?** (`<COPIA>`, extensión desactivada en las preferencias principales):
  - **Sí, con su `userpref.blend`** (`tpl_a`): `--app-template tpl_a` → se ejecutó `TPL_A register()`, después `BIMSIMPLE_PRUEBA register() OK`, `prefs.addons = ['bl_ext.user_default.bimsimple_prueba']`, `show_splash=False` y `apps` en False.
  - **No, desde `register()`** (`tpl_b`): `addon_utils.enable("bl_ext.user_default.bimsimple_prueba", default_set=True)` devolvió `None` con `Add-on not loaded: "bl_ext.user_default.bimsimple_prueba", cause: No module named 'bl_ext'` y `ModuleNotFoundError: No module named 'bl_pkg'`. La plantilla se carga antes que las extensiones.
  - **Plantilla sin `userpref.blend`** (`tpl_b`): Blender toma los valores de fábrica para todo lo de la lista anterior. Resultado: `addons = []` (aunque las preferencias principales tenían la extensión activada), `show_splash=True` y `apps` en True. Coincide con `wm_files.cc`: `userdef_template = BKE_blendfile_userdef_from_defaults()` (fuente 5.2). Esto **contradice** la frase del manual "preferences are shared with the default Blender configuration": manda el comportamiento comprobado.
  - Con la plantilla activa, `wm.save_userpref()` escribe `portable\config\userpref.blend` **y** `portable\config\tpl_a\userpref.blend`.
  - Sin `--app-template`, la plantilla **no** queda recordada: `app_template=''`, aunque se haya guardado con la plantilla activa. El acceso directo siempre debe pasar el argumento.
- ✅ `bpy.ops.screen.area_split` funciona en `--background` (`{'FINISHED'}`) y el área nueva se guarda en el `.blend`, pero queda con ancho 0, porque no hay ventana real (`<R>probe_split.py`). Armar `startup.blend` sin ventana es **posible pero sin verificar visualmente**. Alternativa probada en el MVP: armar la pantalla al arrancar con ventana (`git show mvp-original:bim_simple/ui.py:85-133`).

## 5. Pantalla de bienvenida

**Decisión recomendada**: `bpy.context.preferences.view.show_splash = False`, guardado en el `userpref.blend` de la plantilla (manda sobre el principal) y también en `portable\config\userpref.blend`.

**Por qué**: es la preferencia oficial. Desactiva también la "configuración rápida" del primer arranque. Además, el texto de bienvenida y el de configuración rápida estarían en inglés o serían de Blender (FR-001).

**Alternativas consideradas**: `--python-expr` que la apague en cada arranque. Funcionaría, porque `--python` corre en `ARG_PASS_FINAL`, antes de `WM_init_splash_on_startup` (fuente 5.2 `creator.cc` y `creator_args.cc`, 📖), pero marca las preferencias como modificadas y agrega un argumento frágil. `BLENDER_CUSTOM_SPLASH` solo cambia la imagen.

**Evidencia**
- 📖 `<SC>\startup\bl_ui\space_userpref.py:233`: `col.prop(view, "show_splash", text="Splash Screen")`, en el panel `USERPREF_PT_interface_display` (`:222`), donde `view = prefs.view` (`:227`).
- ✅ RNA: `PreferencesView.show_splash type=BOOLEAN default=True desc='Display splash screen on startup'` (`<R>t5_rna.txt`).
- ✅ En `<COPIA>` se fijó en `False` y se guardó con `bpy.ops.wm.save_userpref()` (`{'FINISHED'}`, "Info: Preferencias guardadas"). En un proceso nuevo leyó `show_splash=False` (`<R>setup_prefs_portable.py`, `probe_prefs.py`).
- 📖 fuente 5.2 `wm_init_exit.cc`, `wm_init_splash_show_on_startup_check`: `if (U.uiflag & USER_SPLASH_DISABLE) { return false; }` va antes de cualquier otra condición. Si no, se muestra cuando no hay archivo cargado, o cuando hay archivo pero `!bke::preferences::exists()`. En `wm_splash_screen.cc`, si no existen preferencias se usa el menú `WM_MT_splash_quick_setup`.
- ✅ La plantilla manda sobre este bit (`FLAG_SWAP(uiflag, ... USER_SPLASH_DISABLE ...)`). Probado: con `tpl_b` sin `userpref.blend`, `show_splash` volvió a `True` aunque el principal tenía `False`.

## 6. Interfaz de Blender en español

**Decisión recomendada**: en `portable\config\userpref.blend` (no en la plantilla, porque el idioma no se reemplaza):
- `view.language = 'es'`
- `view.use_translate_interface = True`, `view.use_translate_tooltips = True`, `view.use_translate_reports = True`
- `view.use_translate_new_dataname = False`

**Por qué**: los diálogos, el explorador de archivos y los mensajes de Blender quedan en español (FR-024). Los nombres de datos nuevos se dejan en inglés por seguridad: Bonsai podría buscar colecciones u objetos por nombre fijo. Es un riesgo ⚠️ **no verificado**, pero los nombres que ve el usuario salen del IFC, así que no se pierde nada.

**Evidencia**
- 📖 `<SC>\startup\bl_ui\space_userpref.py:271-293` (`USERPREF_PT_interface_translation`, solo si `bpy.app.build_options.international`): `layout.prop(view, "language")` (`:283`); `use_translate_tooltips` (`:287`), `use_translate_interface` (`:288`), `use_translate_reports` (`:289`), `use_translate_new_dataname` (`:290`).
- ✅ RNA (`<R>t5_rna.txt`): `PreferencesView.language` ENUM con 51 opciones, entre ellas `('es', 'Spanish - Español')`. `bpy.app.translations.locales` contiene `'es'`, y `build_options.international = True`. Las 4 opciones `use_translate_*` son BOOLEAN, con `True` por defecto.
- ✅ `<BL>\5.2\datafiles\locale\es\LC_MESSAGES\blender.mo` (3,7 MB, 39.343 mensajes). Ejemplos: "Open" → "Abrir", "Cancel" → "Cancelar", "File" → "Archivo", "Don't Save" → "No guardar", "Save changes before closing?" → "¿Guardar cambios antes de cerrar?", "(Unsaved)" → "(no guardado)".
- ✅ En `<COPIA>`, después de guardar: `language='es'`, `bpy.app.translations.locale='es'`, `pgettext_iface("Open") = 'Abrir'`, `pgettext_iface("(Unsaved)") = '(no guardado)'`. Con `tpl_b` (plantilla sin preferencias) el idioma siguió en `'es'`, lo que confirma que la plantilla no lo pisa.
- Otras preferencias útiles comprobadas ✅ (RNA y guardado):
  - `preferences.apps.show_corner_split`, `show_edge_resize` y `show_regions_visibility_toggle` en `False`: impiden dividir o unir áreas, cambiar su tamaño y mostrar u ocultar barras. Pensadas para plantillas.
  - `preferences.system.use_online_access = False`.
  - `preferences.use_preferences_save` existe ("Save preferences on exit when modified"); se recomienda `False`, para que la configuración entregada no cambie.
  - `preferences.filepaths.temporary_directory`: ver hallazgo 4. Existe y en la copia vale `''`, es decir `%TEMP%`.

## 7. Acceso directo `.lnk` con nombre, icono y argumentos

**Decisión recomendada**: crear con PowerShell y WScript.Shell, con permiso del usuario, `BIM Simple.lnk` en el Escritorio (`C:\Users\Usuario\Desktop`) y en el menú Inicio (`C:\Users\Usuario\AppData\Roaming\Microsoft\Windows\Start Menu\Programs`):
- `TargetPath` = `<programa>\blender\blender-launcher.exe`
- `Arguments` = `--app-template bim_simple`, opcionalmente con `--window-maximized`
- `WorkingDirectory` = `<programa>\blender`
- `IconLocation` = `<programa>\bim_simple.ico,0`
- `Description` en español

Barra de tareas: aceptar en principio el icono de Blender, y probar después, con permiso y con ventana, el ajuste por ctypes descrito abajo.

**Por qué**: `blender.exe` es un programa de **consola**. Abrirlo directamente muestra una ventana negra. `blender-launcher.exe` es un programa de ventanas que lanza `blender.exe` oculto y le pasa los argumentos. Es lo que usa el acceso directo oficial.

**Evidencia**
- ✅ Subsistema PE: `blender.exe` = 3 WINDOWS_CUI (consola); `blender-launcher.exe` = 2 WINDOWS_GUI (`<R>pe_subsystem.py`).
- ✅ El acceso directo oficial del usuario, `...\Start Menu\Programs\Blender\Blender 5.2.lnk`, tiene `Target=...\Blender 5.2\blender-launcher.exe`, sin argumentos, e `Icon=,0` (el del ejecutable). Solo se leyó.
- 📖 fuente 5.2 `source/creator/blender_launcher_win32.c`:
  - arma la ruta con `PathCchCombine(path, MAX_PATH, path, L"blender.exe")`, es decir que el nombre está **fijo**;
  - pasa la línea de comandos sin cambios (`L"\"%s\" %s"`);
  - usa `CREATE_NEW_CONSOLE` con `SW_HIDE`;
  - solo espera al proceso hijo con `-b`/`--background`.

  **Consecuencia: no hay que renombrar `blender.exe`.** Renombrarlo funciona si se lo lanza directo: `BIM Simple.exe --background` arrancó bien en `<COPIA>`, con `binary_path` = `...\BIM Simple.exe` ✅. Pero rompe el lanzador.
- ✅ `.lnk` de prueba creado y vuelto a leer, **solo en el scratchpad**: `<R>lnk_prueba\BIM Simple (prueba).lnk` (3.423 bytes), con el icono `<R>lnk_prueba\bim_simple_prueba.ico`, generado con la biblioteca estándar de Python (PNG dentro de ICO, 256/48/32/16 px). Lectura posterior:
  - `TargetPath=...\scratchpad\bs\blender\blender-launcher.exe`
  - `Arguments=--app-template bim_simple --window-maximized`
  - `WorkingDirectory=...\bs\blender`
  - `IconLocation=...\bim_simple_prueba.ico,0`
  - `Description=BIM Simple - modelado BIM sobre IFC`
  - `WindowStyle=3`

  Sintaxis usada:
  ```powershell
  $sh = New-Object -ComObject WScript.Shell
  $lnk = $sh.CreateShortcut("<carpeta>\BIM Simple.lnk")
  $lnk.TargetPath = "<programa>\blender\blender-launcher.exe"
  $lnk.Arguments = '--app-template bim_simple'
  $lnk.WorkingDirectory = "<programa>\blender"
  $lnk.IconLocation = "<programa>\bim_simple.ico,0"
  $lnk.Description = "BIM Simple"
  $lnk.Save()
  ```
- **Icono en la barra de tareas mientras corre**:
  - 📖 fuente 5.2 `intern/ghost/intern/GHOST_SystemWin32.cc`: la clase de ventana usa `wc.hIcon = ::LoadIcon(wc.hInstance, "APPICON")`, es decir el icono que trae `blender.exe`. El constructor llama a `SetCurrentProcessExplicitAppUserModelID(BLENDER_WIN_APPID_16)`, con el comentario "Set App Id for the process so our console will be grouped on the Task Bar".
  - ✅ `blender.exe` importa `SetCurrentProcessExplicitAppUserModelID` y `SHGetPropertyStoreForWindow`, y contiene el texto ASCII `blender.5.2` junto a `Blender 5.2` (búsqueda de cadenas en el binario, `<R>strings_search.py`). Que el valor de `BLENDER_WIN_APPID` sea `"blender.5.2"` es una **inferencia**: no se encontró la línea que lo define.
  - **Consecuencia** ⚠️ (sin verificar con ventana): la ventana de BIM Simple mostrará el icono de Blender en la barra de tareas. Como el proceso fija su propio AppUserModelID, probablemente se **agrupe con el Blender del usuario** si los dos están abiertos. El icono del `.lnk` solo se ve en el acceso directo (Escritorio o Inicio), no en la ventana abierta.
- **Formas de cambiarlo**, de más a menos razonable:
  1. ⚠️ Desde la extensión BIM Simple, al arrancar con ventana y con `ctypes`, sin modificar Blender:
     - buscar la ventana del propio proceso (`EnumWindows` y `GetWindowThreadProcessId`);
     - `SendMessageW(hwnd, WM_SETICON, ICON_BIG/ICON_SMALL, LoadImageW(ico, IMAGE_ICON, ..., LR_LOADFROMFILE))` para el icono;
     - `SHGetPropertyStoreForWindow(hwnd, IID_IPropertyStore)` para fijar `PKEY_AppUserModel_ID` (por ejemplo `"BIMSimple.BIMSimple"`) y `PKEY_AppUserModel_RelaunchCommand`, `RelaunchDisplayNameResource` y `RelaunchIconResource`, para que la ventana se agrupe aparte y fijarla en la barra relance BIM Simple.

     Son unas 60–80 líneas de ctypes con COM y van concentradas en un solo módulo. **Hay que probarlo con ventana (requiere permiso)**. Si se usa, el `.lnk` debería llevar el mismo AppUserModelID, que WScript.Shell no permite fijar; haría falta `IPropertyStore` desde PowerShell con `Add-Type`.
  2. Cambiar el recurso de icono de `blender.exe` con una herramienta como rcedit: requiere descargarla, modifica el binario de Blender (Principio III) y **rompe su firma digital**: `Get-AuthenticodeSignature` da `Valid`, firmado por `CN=Blender Foundation` ✅. **Descartado.**
  3. Un `.exe` lanzador propio con icono: la ventana sigue siendo de `blender.exe`, así que no cambia la barra de tareas. No sirve solo.

## 8. Título de la ventana

**Decisión recomendada**: **no hay forma soportada** en Blender 5.2 de fijar el título desde Python. Hay que anotarlo en el plan como diferencia (Principio II). El título será `(no guardado) - Blender 5.2.0 LTS` con el idioma en español. La constitución pide que el usuario no vea Blender; esta es una excepción visible. Opción a evaluar con ventana: `ctypes.windll.user32.SetWindowTextW(hwnd, "BIM Simple - <archivo.ifc>")` y volver a aplicarlo con `bpy.app.timers`, porque Blender lo reescribe (ver abajo). Es un parche frágil, con posible parpadeo.

**Evidencia**
- ✅ RNA en `--background` (`<R>t5_rna.txt`):
  - `bpy.types.Window` solo tiene `parent, scene, workspace, screen, view_layer, x, y, width, height, stereo_3d_display, support_hdr_color, modal_operators` y las funciones `cursor_warp, cursor_set, cursor_modal_set, cursor_modal_restore, event_simulate, find_playing_scene`.
  - Ningún atributo con "title" en `Window`, `WindowManager` ni `Screen`, y ningún operador `bpy.ops.wm.*title*`.
- 📖 Documentación `https://docs.blender.org/api/current/bpy.types.Window.html`: las mismas propiedades y funciones; nada sobre título ni icono.
- 📖 fuente 5.2 `windowmanager/intern/wm_window.cc`:
  - `wm_window_title_text` arma el título: `"* "` si hay cambios + nombre del `.blend` o `IFACE_("(Unsaved)")` + `" - Blender " + BKE_blender_version_string()`.
  - `WM_window_title_refresh` lo aplica con `ghost_window->setTitle(...)`.
  - Existe `WM_window_title_set` en C, pero no está expuesta a Python (RNA ✅).
- 📖 fuente 5.2 `wm_event_system.cc`, `wm_event_do_notifiers`: el título se vuelve a escribir con `ND_FILEREAD`, `ND_FILESAVE` y `ND_DATACHANGED`. Por eso un `SetWindowTextW` externo se pierde enseguida.
- Como BIM Simple guarda solo `.ifc` y nunca `.blend`, el título siempre mostrará "(no guardado)". Ayuda a mostrar el nombre del IFC y "cambios sin guardar" en el panel de BIM Simple.

## 9. Tiempo de arranque (SC-007 < 20 s)

**Decisión recomendada**: el presupuesto alcanza con margen en segundo plano. Hay que medir el arranque **con ventana** (permiso del usuario) en la copia del programa, desde el doble clic hasta que se puede pulsar "Nuevo proyecto". Bonsai debe instalarse al armar el programa, para que el primer arranque no tenga que descomprimir 440 MB de ruedas.

**Evidencia** ✅ (`<R>run_timing.py`, `<R>probe_time.py`, Blender instalado; tiempo de pared medido desde afuera; "interno" = desde la creación del proceso hasta que corre el script, ya cargadas preferencias y extensiones):

| Corrida | Configuración | Comando | Pared (s) | Interno (s) |
|---|---|---|---|---|
| 1 / 2 / 3 | usuario (Bonsai + mcp + print3d_toolbox) | `--background --python-expr "import bpy"` | 5,84 / 5,88 / 7,08 | — |
| 1 / 2 / 3 | usuario | `--background --python probe_time.py` | 6,20 / 7,02 / 6,99 | 5,59 / 6,28 / 6,26 |
| 1 / 2 / 3 | aislada vacía (`BLENDER_USER_RESOURCES`) | `--background --python-expr "import bpy"` | 2,06 / 2,06 / 1,96 | — |
| 1 / 2 / 3 | aislada vacía | `--background --python probe_time.py` | 2,05 / 2,04 / 1,98 | 1,90 / 1,88 / 1,82 |

- Extensiones activas del usuario: `bl_ext.blender_org.print3d_toolbox`, `bl_ext.user_default.bonsai` y `bl_ext.user_default.mcp`; `bonsai` e `ifcopenshell` cargados ✅.
- Importación de Bonsai (`PYTHONPROFILEIMPORTTIME=1` con `--python-use-system-env`, una corrida, `<R>importtime_user.txt`):
  - `bonsai.bim` 2,78 s acumulados (de eso, `bonsai.bim.handler` → `bonsai.tool` 1,92 s; `brickschema` 0,36 s; `pandas` 0,30 s; `ifcfm` 0,41 s);
  - `bonsai` 0,11 s; `ifcopenshell` 0,28 s; `bpy` 0,66 s.
  - Las extensiones `mcp` y `print3d_toolbox` suman menos de 30 ms.
  - **Bonsai ≈ 2,9 s de importación más ~1–2 s de registro**, que explica la diferencia de 4–5 s entre la configuración del usuario y la vacía.
- Estimación para el programa: unos 6 s en segundo plano con la caché `.pyc` ya escrita (la carpeta del programa es escribible; en `<BL>` no se pueden escribir `.pyc`). Con ventana se suman la creación de la ventana y la compilación de shaders; la caché de shaders es compartida (`...\Cache\gl-shader-cache`, ver pregunta 1). ⚠️ Sin medir con ventana.
- La configuración del usuario quedó idéntica después de estas corridas (SHA-256 ✅).

## 10. Tamaño de la copia y de dónde sale

**Decisión recomendada**: armar la copia del programa **copiando `<BL>`**, sin `blender.pdb` (símbolos de depuración, 85 MB) y conservando `license\` y `copyright.txt` (GPL). No hace falta descargar el zip de Blender. Como alternativa sin tocar `Program Files`, se puede extraer del `.msi` que está en Descargas (mismo contenido).

**Por qué**: el contenido instalado es exactamente el del instalador oficial: mismos 6.525 archivos. Según la documentación, el zip es el mismo Blender sin integración con Windows. Lo que el instalador agrega fuera de la carpeta (accesos directos, registro, desinstalador) no se copia, que es justo lo que se quiere.

**Evidencia**
- ✅ `du -sh <BL>` = **915 MB**, 6.525 archivos:
  - `blender.shared` 324 MB, `5.2\` 350 MB (`python` 138 MB, `datafiles` 128 MB, `scripts` 84 MB), `blender.exe` 108 MB, `blender.pdb` 85 MB, `cycles_kernel_oneapi_aot.dll` 38 MB.
  - Copia sin `blender.pdb`: **830 MB**. Funciona: todas las pruebas de `<COPIA>`, incluida la instalación de la extensión.
- ✅ Tabla `File` del `.msi` (`Downloads\blender-5.2.0-windows-x64.msi`, solo lectura con `WindowsInstaller.Installer`): **6.525 filas**, 944.682.170 bytes, igual que lo instalado.
  - Tabla `Shortcut`: 2 accesos directos "Blender 5.2" a `blender_launcher.exe` (Inicio y Escritorio).
  - Tabla `Registry`: `Software\Blender Foundation\Blender` → `Blender_installed`, `Blender_installed_desktop` (raíz 1 = HKCU).
  - `ProductVersion` 5.2.0, `Manufacturer` Blender Foundation.
- 📖 Manual, instalación en Windows (`blender-manual/.../getting_started/installing/windows.rst`):
  - instalador: "Requires administrator rights", crea entrada en el menú Inicio y asocia `.blend`;
  - zip: "Requires no administrator rights", sin menú Inicio ni asociación (se puede registrar con `blender -r`), y "it's perfectly possible to have multiple versions installed side by side".

  ⚠️ No se comprobó si el zip oficial trae `blender.pdb` u otras diferencias de archivos: habría que descargarlo.
- ✅ Tamaño estimado del programa: Blender 830 MB + extensión Bonsai con `wheels\` 146 MB + `.local` 440–490 MB + BIM Simple (pocos MB) ≈ **1,45–1,5 GB**. Las ruedas de `wheels\` no se deben borrar después de instalar: Blender las vuelve a usar si tiene que regenerar la caché de compatibilidad (`addon_utils.py:1111-1192` 📖).
- 📖 Licencias: `<BL>\license\spdx\GPL-3.0-or-later.txt` (y GPL-2.0, LGPL), `license.md`, `licenses.json`. La rueda de Bonsai no trae texto de licencia en su `dist-info` (solo METADATA, RECORD, WHEEL, top_level.txt ✅); su manifiesto declara `SPDX:GPL-3.0-or-later`. El paquete del programa debe incluir una carpeta `licencias\` con la GPL-3.0 y el aviso de Bonsai e IfcOpenShell (constitución, "Restricciones técnicas").

---

## Propuesta de empaquetado

### Estructura de carpetas del programa instalado

Ruta corta, escribible y sin administrador: `%LOCALAPPDATA%\Programs\BIM Simple\` (= `C:\Users\Usuario\AppData\Local\Programs\BIM Simple`, 46 caracteres).

```
BIM Simple\
├─ bim_simple.ico                       icono propio (accesos directos)
├─ licencias\                           GPL-3.0 + avisos de Blender, Bonsai, IfcOpenShell
├─ LEEME.txt                            cómo desinstalar: borrar esta carpeta y los 2 accesos directos
└─ blender\                             copia SIN CAMBIOS de "C:\Program Files\Blender Foundation\Blender 5.2" (sin blender.pdb)
   ├─ blender.exe, blender-launcher.exe, blender.shared\, 5.2\, license\ ...
   └─ portable\                         ← activa el modo portable; TODO lo variable vive acá
      ├─ config\
      │  ├─ userpref.blend              idioma es, traducciones, sin bienvenida, sin conexión,
      │  │                              temporary_directory=..\portable\temp, use_preferences_save=False
      │  ├─ bim_simple\userpref.blend   (lo crea Blender si se guardan preferencias con la plantilla)
      │  └─ recent-files.txt, recent-ifc-projects.txt (los escriben Blender y Bonsai)
      ├─ temp\                          carpeta temporal propia (quit.blend, autoguardado)
      ├─ extensions\
      │  ├─ user_default\bonsai\        Bonsai 0.9.0 py313 (install-file)
      │  ├─ user_default\bim_simple\    extensión BIM Simple (install-file)
      │  ├─ .local\lib\python3.13\site-packages\   dependencias de Bonsai (~440 MB)
      │  └─ .cache\compat.dat
      └─ scripts\startup\bl_app_templates_user\bim_simple\
         ├─ __init__.py                 register/unregister (manejadores livianos)
         ├─ userpref.blend              Bonsai + BIM Simple activados, show_splash=False, apps bloqueados
         └─ startup.blend               escena vacía + pantalla de BIM Simple (planta | 3D)
```

En el repositorio del proyecto se guardan solo las fuentes: la extensión con `blender_manifest.toml`, la carpeta de la plantilla, el icono y los scripts de armado (`tools\armar_programa.ps1` y `tools\configurar_preferencias.py`). Los `.blend` de la plantilla y de la configuración los genera el script de armado. La copia de Blender, Bonsai y la carpeta del programa **no** entran en git.

### Cómo se arma (script de armado, cada paso con salida verificable)

1. Comprobar requisitos: Blender 5.2.0 en `<BL>` (`blender.exe --version`) y el zip de Bonsai py313 con su SHA-256 publicado.
2. Copiar `<BL>` → `BIM Simple\blender\` sin `blender.pdb` (por ejemplo `robocopy ... /E /XF blender.pdb`). Crear `blender\portable\` y `blender\portable\temp\`.
3. `blender\blender.exe -c extension install-file -r user_default -e bonsai_py313-0.9.0-windows-x64.zip`.
4. `blender\blender.exe -c extension build --source-dir <proyecto>\<extensión> --output-dir <dist>` y después `blender\blender.exe -c extension install-file -r user_default -e <dist>\bim_simple-<v>.zip`.
5. `blender\blender.exe --background --python tools\configurar_preferencias.py`. El script:
   - se niega a correr si `bpy.utils.resource_path('USER')` no termina en `portable`;
   - fija idioma y traducciones, `show_splash=False`, `apps.*=False`, `system.use_online_access=False`, `filepaths.temporary_directory` y `use_preferences_save=False`;
   - opcionalmente quita el repositorio remoto con `-c extension repo-remove blender_org`, a decidir;
   - corre `bpy.ops.wm.save_userpref()`.

   Todo esto se probó en `<COPIA>` ✅, salvo `temporary_directory`, `use_preferences_save` y `repo-remove`.
6. Copiar la plantilla `bim_simple` y generar su `userpref.blend`: con la plantilla activa (`--app-template bim_simple`), activar Bonsai y BIM Simple, fijar `show_splash=False` y los bloqueos de `apps`, y guardar. Generar `startup.blend` (escena vacía; la pantalla se arma según lo que decida la investigación de interfaz).
7. Copiar `bim_simple.ico`, `licencias\` y `LEEME.txt`.
8. Correr la prueba automática con **`BIM Simple\blender\blender.exe --background --python tests\...`** y mostrar la salida real.
9. Crear los dos accesos directos (paso 7 de la sección siguiente).

### Cómo se lanza

`BIM Simple.lnk` → `"%LOCALAPPDATA%\Programs\BIM Simple\blender\blender-launcher.exe" --app-template bim_simple`, con carpeta de trabajo `...\blender` e icono `...\bim_simple.ico`. El lanzador abre `blender.exe` sin consola. El modo portable usa `portable\`. La plantilla carga su `startup.blend` y su `userpref.blend`, que activan Bonsai y BIM Simple sin bienvenida. El idioma español sale de `portable\config\userpref.blend`. El Blender del usuario usa `%APPDATA%\Blender Foundation\Blender\5.2`, así que los dos pueden estar abiertos a la vez.

Desarrollo diario sin copiar Blender: `BLENDER_USER_RESOURCES=<proyecto>\.blender_dev` con el `blender.exe` instalado. Bonsai se instala allí una vez y la extensión se carga desde el código, con un repositorio `--source SYSTEM` apuntando a la carpeta de la extensión, o con `--addons` en las pruebas.

### Pasos que requieren permiso del usuario (constitución, "Flujo de trabajo")

| Paso | Por qué pide permiso |
|---|---|
| Descargar `bonsai_py313-0.9.0-windows-x64.zip` (y comprobar su SHA-256) | No está en la computadora; solo está el py311. |
| Instalar Bonsai en la configuración de desarrollo (`.blender_dev`) y en la del programa | Instalar software o paquetes. |
| Crear `%LOCALAPPDATA%\Programs\BIM Simple\` y copiar allí Blender (830 MB) | Instala software fuera de la carpeta del proyecto. |
| Crear `BIM Simple.lnk` en el Escritorio y en el menú Inicio | Accesos directos (permiso explícito). |
| Abrir BIM Simple con ventana para medir el arranque (SC-007), ver el icono de la barra de tareas y el título, y armar o verificar `startup.blend` | Abrir ventanas de Blender. |
| Agregar `.blender_dev/` y `__pycache__/` a `.gitignore` | Cambio en archivos del proyecto. |
| (Opcional) Ajuste por ctypes de icono y AppUserModelID de la ventana | Agrega código específico de Windows; hay que aprobarlo como diferencia. |

### Diferencias con ArchiCAD o con el pedido, para el plan (Principio II)

1. El título de la ventana dirá "(no guardado) - Blender 5.2.0 LTS": no hay API para cambiarlo (pregunta 8).
2. El icono de la barra de tareas será el de Blender, y es probable que se agrupe con el Blender del usuario, salvo que se apruebe y funcione el ajuste por ctypes (pregunta 7).
3. La caché de shaders y de índices de assets (`%LOCALAPPDATA%\Blender Foundation\Blender\Cache`) se comparte con el Blender del usuario y no se puede mover (pregunta 1).

### Archivos de esta investigación

- `<R>`: `probe_paths.py`, `probe_rna.py`, `probe_prefs.py`, `probe_time.py`, `run_timing.py`, `probe_split.py`, `setup_prefs_portable.py`, `enable_ext_portable.py`, `disable_ext_portable.py`, `make_ico.py`, `pe_subsystem.py`, `strings_search.py`, `mo_lookup.py`, las salidas `t1…t5_*.txt`, `help.txt`, `cmd_*.txt`, `importtime_user.txt`, `ext_prueba\`, `lnk_prueba\` y `backup_config\` (copia de `config\*` del usuario, sin uso porque no hubo cambios).
- `scratchpad\bs\` (842 MB): copia portable de prueba de Blender. Se puede borrar cuando el usuario lo autorice.
