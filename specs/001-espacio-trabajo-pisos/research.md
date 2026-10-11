# Investigación (fase 0): Programa BIM Simple y navegador de pisos

**Fecha**: 2026-10-11 · **Función**: [spec.md](spec.md) · **Plan**: [plan.md](plan.md)

Todo se verificó con Blender 5.2.0 LTS (hash fbe6228777e7), Bonsai 0.9.0 e IfcOpenShell 0.9.0. Blender
se ejecutó siempre con `--background`, sin abrir ventanas. Las marcas son las de la constitución:
- ✅ ejecutado y comprobado;
- 📖 solo leído en el código instalado, en el código fuente de Blender 5.2 o en el manual;
- 🖥 comprobado con ventana en el MVP anterior (etiqueta `mvp-original`);
- ⚠️ solo se puede comprobar con ventana y va a la prueba manual.

El detalle de cada punto (tablas archivo:línea, salidas reales y alternativas) está en:
- [investigacion/empaquetado.md](investigacion/empaquetado.md): programa propio, configuración aparte, acceso directo.
- [investigacion/interfaz.md](investigacion/interfaz.md): pantalla partida, ocultar Blender y Bonsai, atajos, salir.
- [investigacion/ifc.md](investigacion/ifc.md): proyecto, pisos, abrir y guardar, deshacer, validación.
- [investigacion/scripts/](investigacion/scripts/): recetas verificadas (`_recetas.py`) y la prueba de punta a
  punta (`e2e_pisos.py`, salida con código 0, "RESULTADO: TODO OK").

Rutas abreviadas:
- `<BL>`: `C:\Program Files\Blender Foundation\Blender 5.2`
- `<SC>`: `<BL>\5.2\scripts`
- `bonsai/…`, `ifcopenshell/…`: relativas a `extensions\.local\lib\python3.13\site-packages\`

No queda ningún "NEEDS CLARIFICATION" abierto.

---

## A. Programa propio

### R1. Configuración aparte: modo portable
- **Decisión**: el programa lleva una copia de Blender con una carpeta vacía `portable\` junto a
  `blender.exe`. Config, scripts, extensiones y dependencias de Bonsai quedan dentro de esa carpeta.
- **Por qué**: lo activa una carpeta, sin variables ni scripts intermedios. Desinstalar = borrar la carpeta
  (FR-005). Se comprobó que la carpeta se puede mover y sigue funcionando ✅.
- **Alternativas**:
  - `BLENDER_USER_RESOURCES` en un lanzador `.cmd`/`.vbs`: funciona ✅, pero suma una pieza y el `.cmd` abre consola.
  - Variables `BLENDER_USER_*` sueltas: dejan `DATAFILES` en `%APPDATA%` ✅. Se descartan.
- **Evidencia**: manual 5.2 "Blender's Directory Layout" 📖; fuente 5.2 `appdir.cc` `get_path_user_ex` 📖;
  copia de prueba con `resource_path('USER')` = `…\portable` ✅.

### R2. Origen de la copia de Blender
- **Decisión**: copiar `<BL>` sin `blender.pdb`, que son 85 MB de símbolos de depuración, y conservar `license\`.
- **Por qué**: lo instalado es idéntico al instalador oficial: 6.525 archivos, igual que la tabla `File` del `.msi` ✅.
  No hace falta descargar Blender. La copia ocupa 830 MB ✅.
- **Alternativas**: extraer del `.msi` que está en Descargas (mismo contenido); descargar el zip oficial (innecesario).

### R3. Bonsai dentro del programa
- **Decisión**: `blender.exe -c extension install-file -r user_default -e bonsai_py313-0.9.0-windows-x64.zip`,
  ejecutado con el `blender.exe` **de la copia**. Escribe solo en `portable\`. Las dependencias (~440 MB)
  quedan en `portable\extensions\.local\lib\python3.13\site-packages` ✅ (probado con una extensión de prueba).
- **Bloqueo que se resuelve con permiso**: el zip py313 **no está** en la computadora; solo está el py311, que no
  carga en 5.2 ✅. Hay que descargarlo del release oficial y comparar su SHA-256 con el publicado. **Requiere
  permiso del usuario.**
- **Alternativa descartada**: copiar el Bonsai ya instalado en el Blender del usuario. No se puede verificar
  su SHA-256 y depende de una instalación ajena.

### R4. Plantilla de aplicación `bim_simple`
- **Decisión**: una plantilla en `portable\scripts\startup\bl_app_templates_user\bim_simple\` con:
  - `__init__.py` mínimo;
  - `userpref.blend` **obligatorio**;
  - `startup.blend` solo de datos.

  El acceso directo pasa `--app-template bim_simple`.
- **Por qué**:
  - Una plantilla **sin** `userpref.blend` propio desactiva todas las extensiones y vuelve a mostrar la
    bienvenida ✅. Su `userpref.blend` reemplaza `addons`, atajos, `app_flag` y los bits de bienvenida y
    pregunta al salir 📖 (fuente 5.2 `BKE_blender_userdef_app_template_data_swap`).
  - El `register()` de la plantilla **no puede** activar extensiones: corre antes que ellas (`No module named 'bl_ext'`) ✅.
  - El idioma **no** lo reemplaza la plantilla; va en `portable\config\userpref.blend` ✅.
- **`startup.blend` de datos**: se genera en `--background` ✅ con:
  - un solo espacio "BIM Simple" con `use_filter_by_owner` y `owner_ids`;
  - escena sin objetos (FR-006; el inicio de fábrica trae cubo, cámara y luz ✅);
  - `show_statusbar = False`;
  - ajustes de vista.

  **La división en dos áreas no se puede guardar ahí** (ver R7).
- **Alternativa**: `portable\config\startup.blend` sin plantilla. Es más simple, pero un "Nuevo" de Blender lo
  trataría como archivo del usuario.

### R5. Preferencias del programa
Todas existen en RNA ✅. Las fija `tools/configurar_programa.py`, que se niega a correr si
`resource_path('USER')` no termina en `portable`.

| Dónde | Preferencia | Valor | Para qué |
|---|---|---|---|
| principal | `view.language`, `use_translate_interface/tooltips/reports` | `'es'`, `True` | Diálogos, explorador de archivos y mensajes en español (FR-024). Ejemplo: "Save changes before closing?" → «¿Guardar cambios antes de cerrar?» ✅ |
| principal | `view.use_translate_new_dataname` | `False` | Los nombres internos quedan en inglés, para que Bonsai los encuentre |
| principal | `filepaths.temporary_directory` | `<programa>\blender\portable\temp\` | Que `quit.blend` no se mezcle con el del Blender del usuario 📖 |
| principal | `use_preferences_save` | `False` | La configuración entregada no cambia al usar el programa |
| principal | `system.use_online_access` | `False` | Sin conexiones |
| plantilla | `view.show_splash` | `False` | Sin pantalla de bienvenida (FR-001) ✅ |
| plantilla | `view.use_save_prompt` | `True` | Pregunta al cerrar con la X (R15) |
| plantilla | `view.show_developer_ui`, `show_tooltips_python` | `False` | Menos opciones de Blender en los menús contextuales |
| plantilla | `apps.show_regions_visibility_toggle`, `apps.show_corner_split` | `False` | Sin flechas de regiones ocultas ni división de áreas por las esquinas ✅ |
| plantilla | add-ons activos | Bonsai + BIM Simple; se quitan los de fábrica que no se usan | |
| plantilla | Bonsai: `should_setup_workspace`, `activate_workspace`, `should_setup_toolbar` | `False` | Si no, Bonsai agrega y activa su espacio "BIM" en cada carga (`bonsai/bim/handler.py:466-478`, `bonsai/bim/ui.py:464, 472, 480`) 📖 |

### R6. Lanzador, acceso directo e icono
- **Decisión**: `BIM Simple.lnk` (WScript.Shell) apunta a `<programa>\blender\blender-launcher.exe`:
  - argumentos `--app-template bim_simple`;
  - carpeta de trabajo `<programa>\blender`;
  - icono `<programa>\bim_simple.ico`.

  Se crea en el Escritorio y en el menú Inicio **con permiso**.
- **Por qué**: `blender.exe` es de consola y abre una ventana negra ✅. `blender-launcher.exe` es de ventanas
  y busca `blender.exe` por nombre fijo, así que **no se renombra** 📖 (`blender_launcher_win32.c`). Sintaxis
  del `.lnk` probada en una carpeta temporal ✅.
- **Dónde se instala**: `%LOCALAPPDATA%\Programs\BIM Simple\` (46 caracteres). Tiene que ser una ruta
  **corta**: Blender falla con rutas de más de 260 caracteres ✅, así que la base debe tener 90 caracteres o
  menos. Además tiene que ser **escribible**: Blender guarda allí la configuración y Bonsai escribe
  `process.log` dentro de su paquete 📖. Sin administrador.
- **Tamaño total** ≈ 1,45–1,5 GB ✅.
- **Licencias**: el programa incluye `licencias\` con la GPL-3.0 y los avisos de Blender, Bonsai e
  IfcOpenShell (constitución).

### R7. Pantalla partida: se arma al arrancar, en la ventana real
- **Decisión**: una función idempotente `ensure_layout(window)` en `screen.py`:
  - Si la pantalla no tiene exactamente dos `VIEW_3D` lado a lado, cierra las demás áreas y divide.
  - Siempre con `context.temp_override(window, screen, area)`.
  - Se dispara desde un timer (`bpy.app.timers`, ~0,1 s) en `register()` y desde un `load_post`
    `@persistent`, como el MVP 🖥 (`mvp-original:bim_simple/ui.py:85-155`).
- **Por qué**: en `--background` la ventana mide 0×0: `area_close` se cuelga, `area_split` y `area_join`
  dejan áreas de tamaño 0, y ocultar regiones no se conserva ✅.
- **Costo**: un parpadeo al arrancar ⚠️.

---

## B. Ocultar Blender y Bonsai (FR-003)

### R8. Pieza por pieza
| Pieza | Cómo | Evidencia |
|---|---|---|
| Barra superior (menús de Blender y pestañas de espacios) | No se puede ocultar el área. Se reemplaza `TOPBAR_HT_upper_bar.draw` por un dibujo con **solo** el menú "Archivo" propio y, a la derecha, `template_reports_banner()` y `template_running_jobs()` (mensajes de FR-011). Se restaura al desregistrar. | `<SC>\startup\bl_ui\space_topbar.py:14-53` 📖; reemplazo de `draw` ✅; mecanismo 🖥 (MVP D7) |
| Barra de estado | `screen.show_statusbar = False` | RNA ✅; se conserva en `startup.blend` ✅ |
| Encabezado, barra de herramientas, encabezado de herramienta, HUD y estantería de recursos de cada vista | `space.show_region_header/toolbar/tool_header/hud/asset_shelf = False` y `area.show_menus = False`, aplicados en `ensure_layout` con contexto de ventana | RNA ✅; con ventana 🖥 |
| Gizmo de navegación y textos sobre la vista | `space.show_gizmo_navigate = False`, `space.overlay.show_text = False` | RNA ✅ |
| Barra lateral | Solo en la vista **derecha**, con una única categoría "BIM Simple", así Blender no dibuja pestañas. Paneles Python de Blender en `VIEW_3D/UI`: `poll` falso y volver a registrarlos, como Bonsai (`bonsai/tool/blender.py:1893-1917`) ✅. Paneles C (`VIEW3D_PT_transform`, `VIEW3D_PT_vgroup`, `VIEW3D_PT_curves`): se reemplazan registrando un `Panel` Python con el mismo `bl_idname` y `poll` falso ✅. | `investigacion/interfaz.md` §3c |
| Paneles y menús de Bonsai | `WorkSpace.use_filter_by_owner = True` + `owner_ids` = solo BIM Simple. Las funciones que Bonsai agrega tienen `_owner = 'bl_ext.user_default.bonsai'` ✅ | `_bpy_types.py:1186-1224` 📖; MVP 🖥 |
| Menú contextual de clic derecho sobre un botón | **No se puede quitar** (fijo en C, `interface_handlers.cc`). `show_developer_ui = False` lo reduce. | 📖 → diferencia D3 |
| Explorador de archivos (Abrir/Guardar IFC) | Es el de Blender, en español | ✅ traducción |

### R9. Atajos de teclado
- **Decisión**: `apply_keymap_policy()` en `keymaps.py`, en un timer al arrancar y en `load_post`:
  - pone `kmi.active = False` en `wm.keyconfigs.default` y en `wm.keyconfigs.addon` según una lista por keymap;
  - llama a `wm.keyconfigs.update()`;
  - registra los atajos propios en `keyconfigs.addon`: Ctrl+N nuevo, Ctrl+O abrir, Ctrl+S guardar,
    Mayús+Ctrl+S guardar como, Ctrl+Q salir.

  Se conservan Ctrl+Z / Mayús+Ctrl+Z, la navegación de las vistas, la selección y los keymaps modales.
  La lista completa está en `investigacion/interfaz.md` §4.
- **Por qué**: hay que desactivar **los dos lados**. Si se apaga el Tab de Bonsai, el evento llega al Tab de
  Blender ✅. En tiempo de ejecución no queda nada guardado.
- **Atención para la prueba**: en `--background` los keymaps vienen vacíos hasta llamar a
  `bpy.utils.keyconfig_init()` ✅.
- **Alternativa**: un preset de keyconfig propio. No cubre los atajos de Bonsai.

### R10. Planta: vista superior y solo el piso activo
- **Decisión**:
  - **Vista superior**: `rv3d.view_rotation = (1,0,0,0)`, `view_perspective = 'ORTHO'`,
    `is_orthographic_side_view = True` y `lock_rotation = True` ✅.
  - **Solo el piso activo en la planta**: `plan_space.use_local_collections = True` y
    `bpy.ops.object.hide_collection(collection_index=i, toggle=False, extend=False)` con `temp_override` de
    la planta. El índice se calcula con el recorrido del MVP (`mvp-original:bim_simple/ui.py:173-209`) 🖥.
  - **Vista 3D**: también con colecciones locales, aislando la colección del proyecto IFC (FR-006).
- **Por qué**: es el único mecanismo de Blender para mostrar colecciones distintas en cada vista.
  `LayerCollection.hide_viewport` y `Collection.hide_viewport` son globales ✅.
- **Límite**: en `--background` las colecciones locales no se evalúan ✅. La prueba automática comprueba qué
  colección e índice se eligen; lo que se ve va a la prueba manual ⚠️.

---

## C. Modelo IFC (todas las recetas probadas en la prueba de punta a punta ✅)

### R11. Proyecto: nuevo, abrir, guardar, cerrar
| Acción | Receta | Archivo:línea |
|---|---|---|
| Nuevo | Si hay proyecto abierto, `close_project()` primero, porque `create_project` no hace nada si ya hay un IFC (`bonsai/core/project.py:35` ✅). Después: unidades de la escena en metros, `export_schema="IFC4"`, `bpy.ops.bim.create_project()`, renombrar a Proyecto/Sitio/Edificio/Planta Baja (`edit_attributes` + `tool.Root.set_object_name` + `tool.Collector.assign`; el piso con `tool.Spatial.edit_container_name`), `Elevation=0`, `GrossHeight=3,00`, piso activo y `tool.Blender.clear_undo_history()`. | `bonsai/bim/module/project/operator.py:137`, `bonsai/tool/spatial.py:605`, `bonsai/tool/blender.py:2311` |
| No usar | `bim.new_project` (llama a `read_homefile`) | `operator.py:98` 📖 |
| Cerrar (interno) | Borrar objetos y colecciones IFC, `ifc_file=""`, `default_container=0`, `IfcStore.purge()`, `refresh_ui_data()`. No existe operador de Bonsai para esto. | `bonsai/bim/ifc.py:89`, `bonsai/bim/handler.py:288` ✅ |
| Abrir | (1) comprobar el archivo con `ifcopenshell.open` y exigir `IfcProject`. Si falla, mensaje y **no se toca nada** (FR-011): `load_project` descarga **antes** de fallar y deja la ruta mala ✅. (2) `close_project()`. (3) `bpy.ops.bim.load_project(filepath, should_start_fresh_session=False, skip_recent=…, skip_autosave_recovery=True)`. (4) piso activo = cota más cercana a 0,00; Bonsai elige el primero de la agregación ✅. (5) `clear_undo_history()`. | `operator.py:958-1176` |
| Guardar / Guardar como | `bpy.ops.bim.save_project(filepath=…, skip_recent=…)`. Sincroniza objetos movidos, actualiza la cabecera, fija la ruta y `is_dirty=False` ✅. **Nunca** `write()` en el producto: no sincroniza ✅. | `operator.py:1976-2152` |
| Cambios sin guardar | `scene.BIMProperties.is_dirty`. Lo pone en `True` todo `tool.Ifc.Operator` ✅. | `bonsai/bim/prop.py:600`, `bonsai/bim/ifc.py:396-398` |

### R12. Pisos
| Acción | Receta (en `core.py`) | Evidencia |
|---|---|---|
| Listar | Pisos de `get_decomposition(primer IfcBuilding)`, ordenados por `get_storey_elevation × unit_scale`, de mayor a menor. Aviso si hay más de un edificio. Mensaje si no hay edificio o pisos, y en ese caso no se permite agregar. | `ifcopenshell/util/element.py:1144`, `util/placement.py:191` ✅ |
| Altura (leer) | Distancia al piso de arriba. Para el más alto: `GrossHeight` si existe, si no 3,00. | Decisión 2.1 de `investigacion/ifc.md` ✅ |
| Altura (escribir) | `pset.add_qto("Qto_BuildingStoreyBaseQuantities")` + `edit_qto(GrossHeight)`, en todos los pisos que se crean o cambian. | `ifcopenshell/api/pset/` ✅ |
| Crear | `bpy.ops.bim.add_part_to_object(element=<edificio>, part_class="IfcBuildingStorey", part_name=…)`; después renombrar siempre, porque Bonsai agrega " 2" a los nombres repetidos ✅. Por último, cota y altura. | `bonsai/bim/module/aggregate/operator.py:348` |
| Renombrar | `tool.Spatial.edit_container_name` + `set_object_name` + `Collector.assign` | `bonsai/tool/spatial.py:605` ✅ |
| Cota (mover piso **con** sus elementos) | `ifcopenshell.api.geometry.edit_object_placement(product=piso, matrix=Surveyor.get_absolute_matrix(obj), is_si=True, should_transform_children=True)` + mover los objetos de Blender del piso y de `get_decomposition(piso)` + `tool.Geometry.record_object_position` + `Elevation`. **El camino de Bonsai no mueve los elementos** ✅. | `ifcopenshell/api/geometry/edit_object_placement.py:33` |
| FR-016 cambiar cota | Rechazar si la cota es menor o igual que la del piso de abajo. Mover el piso y todos los de arriba en Δ. Actualizar el `GrossHeight` del piso de abajo. | e2e paso 4 ✅ |
| FR-016 cambiar altura | Piso más alto: solo `GrossHeight`. Los demás: mover todos los de arriba en Δ y fijar `GrossHeight`. | e2e ✅ |
| Contar elementos (FR-017) | `[e for e in get_decomposition(piso) if e.is_a("IfcElement") and not e.is_a("IfcFeatureElementSubtraction")]` | ✅ |
| Borrar | Borrar el contenido (`tool.Geometry.delete_ifc_object(obj)`, o `ifcopenshell.api.root.remove_product` si no tiene objeto) y después `bonsai.core.spatial.delete_container`. **`delete_container` solo deja huérfanos y pasa el piso activo al edificio** ✅. Activar el piso de abajo, o el de arriba. | `bonsai/core/spatial.py:158` |

### R13. Piso activo
- **Decisión**: `tool.Spatial.set_default_container(piso)`, que se lee con `tool.Root.get_default_container()`.
  Se guarda en la **escena**, no en el IFC ✅, así que es un ajuste de interfaz (Principio III). Los elementos
  nuevos se contienen ahí (`bonsai/core/root.py:97-101`) ✅.
- BIM Simple fija el piso activo después de crear, abrir y borrar.

### R14. Deshacer
- **Decisión**: cada acción que cambia el IFC es **un** operador que hereda de `tool.Ifc.Operator`
  (`_execute`, `bl_options={"REGISTER","UNDO"}`, `bonsai/tool/ifc.py:400-421`). Las llamadas a `bpy.ops.bim.*`
  de adentro no abren otra transacción ✅. Ctrl+Z restaura `last_transaction` y Bonsai deshace el IFC en
  `undo_post` (`bonsai/bim/handler.py:333-350`).
- La parte IFC está ✅ (simulada). La parte Blender es ⚠️: en `--background`, `ed.undo.poll()` es `False`.
- "Nuevo" y "Abrir" llaman a `clear_undo_history()`, para que Ctrl+Z no traiga objetos del proyecto anterior ✅.

### R15. Salir con cambios sin guardar (FR-010)
- **Ctrl+Q y Archivo > Salir**: operador propio `bimsimple.quit`. Si `is_dirty`, muestra Guardar IFC /
  No guardar / Cancelar. Guardar un proyecto nuevo abre el explorador y sale después. Para no mostrar además el
  diálogo de Blender: `use_save_prompt = False` en la sesión y `wm.quit_blender()`. **Cumple FR-010.**
- **X de la ventana: no se puede interceptar desde Python** 📖. La ventana pide cerrar y
  `wm_quit_with_optional_confirmation_prompt` decide sin llamar a Python. Tampoco se puede reemplazar
  `wm.save_mainfile` ✅.
- **Decisión (X2)**: usar el diálogo de Blender, que en español dice exactamente «¿Guardar cambios antes de
  cerrar?» con Guardar / No guardar / Cancelar ✅. Funciona así:
  - el programa guarda un `.blend` de sesión oculto en `portable\temp\BIM Simple.blend` al arrancar y después
    de "Nuevo" y "Abrir";
  - un `save_pre` `@persistent` hace de puente: si el IFC tiene cambios, lo guarda en su ruta;
  - si el IFC nunca se guardó, lo escribe en `portable\temp\recuperacion\` y lo ofrece en el próximo arranque.

  `bim.save_project` también guarda el `.blend` de sesión (`operator.py:2152-2154`), así que el estado de
  Blender y el del IFC quedan juntos ⚠️.
- **Efecto secundario a verificar** ⚠️: el título de la ventana mostraría "BIM Simple - Blender 5.2.0 LTS" en
  lugar de "(no guardado) - Blender 5.2.0 LTS".
- **Plan B (X1)**, si X2 no pasa la prueba manual: `use_save_prompt = False` y un `exit_pre` que guarda una
  copia de recuperación sin preguntar. Se anotaría como diferencia.

### R16. Validación IFC4 (SC-003)
`ifcopenshell.validate.validate(ruta, json_logger(), express_rules=True)`. Falla si hay un mensaje de
nivel `error` ✅. Un archivo roto a propósito da 2 errores, así que la validación sí detecta problemas ✅.

---

## D. Pruebas

### R17. Dónde corren las pruebas automáticas
- **Decisión**: con el `blender.exe` **del programa** y la plantilla:
  `"%LOCALAPPDATA%\Programs\BIM Simple\blender\blender.exe" --background --app-template bim_simple --python tests\test_pisos.py`.
  `armar_programa.ps1 -SoloExtension` reinstala solo la extensión y la plantilla (rápido) para probar
  cambios del código.
- **Por qué**: prueba lo mismo que usa el usuario y **nunca** usa la configuración del Blender del usuario.
  Hallazgo: correr Bonsai con esa configuración sí escribe `.pyc` y `process.log` dentro de su `.local` ✅.
- **Alternativa**: `BLENDER_USER_RESOURCES=.blender_dev` con el Blender instalado ✅. Evita copiar Blender, pero
  prueba un entorno distinto del que se entrega y obliga a instalar Bonsai dos veces.
- **Arranque (SC-007)**: 5,8–7,1 s en segundo plano con Bonsai, contra 2,0 s sin extensiones ✅. Con ventana ⚠️.

---

## E. Diferencias con la especificación (Principio II)

| # | Requisito | Qué no se puede en Blender 5.2 | Qué se hace |
|---|---|---|---|
| D1 | FR-001, FR-024 | Cambiar el título de la ventana desde Python (`Window` no tiene título ✅) | El título dice "… - Blender 5.2.0 LTS". Con el `.blend` de sesión (R15) quedaría "BIM Simple - Blender 5.2.0 LTS" ⚠️ |
| D2 | FR-001 | Que la ventana abierta muestre el icono de BIM Simple: Blender usa el suyo y fija su propio AppUserModelID 📖 | El icono propio se ve en los accesos directos. En la barra de tareas se ve el de Blender, y puede agruparse con el Blender del usuario ⚠️. Un ajuste con `ctypes` es posible pero queda fuera de esta función. Cambiar el icono de `blender.exe` rompe su firma digital ✅ y queda descartado |
| D3 | FR-003 | Quitar el menú de clic derecho sobre los botones (fijo en C) y el área de la barra superior | El menú se reduce con `show_developer_ui=False`; la barra superior solo muestra "Archivo" |
| D4 | FR-003 | Explorador de archivos propio | Se usa el de Blender, en español |
| D5 | FR-010 | Interceptar la X de la ventana | X2 (R15): diálogo de Blender en español con puente al IFC. Puede preguntar aunque solo se haya seleccionado algo. En un proyecto nunca guardado, "Guardar" deja una copia de recuperación |
| D6 | FR-020 | Doble clic en una fila de la lista | Un clic activa el piso (aprobado, D6 del MVP) ✅ 📖 |
| D7 | FR-005 | Mover la caché de Blender (`%LOCALAPPDATA%\Blender Foundation\Blender\Cache`, shaders e índices) | Se comparte con el Blender del usuario. No son preferencias, extensiones ni archivo de inicio (SC-005) ✅ |
