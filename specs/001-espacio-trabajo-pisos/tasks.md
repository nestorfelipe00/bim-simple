---
description: "Lista de tareas de la función 001: programa BIM Simple y navegador de pisos"
---

# Tareas: Programa BIM Simple y navegador de pisos

**Entrada**: documentos de diseño en `specs/001-espacio-trabajo-pisos/`

**Requisitos previos**:
- [plan.md](plan.md) y [spec.md](spec.md);
- [research.md](research.md) y su evidencia en [investigacion/](investigacion/);
- [data-model.md](data-model.md), [contracts/](contracts/) y [quickstart.md](quickstart.md);
- la constitución v2.0.0.

**Pruebas**: se incluyen porque las exige la constitución (Principio V) y el usuario las pidió:
- `tests/test_pisos.py` corre con el Blender **del programa**:
  `"%LOCALAPPDATA%\Programs\BIM Simple\blender\blender.exe" --background --app-template bim_simple --python tests\test_pisos.py`.
  Sale con 1 si falla y termina con `RESULTADO: TODO OK`.
- Lo que solo se ve con ventana va a la prueba manual ([quickstart.md](quickstart.md) parte B).

**Organización**: por historia de usuario de la especificación (US1 a US4). Cada historia termina con la
prueba automática en verde y un commit.

## Formato: `[ID] [P?] [Historia] Descripción`

- **[P]**: se puede hacer en paralelo (otro archivo, sin depender de tareas pendientes).
- **[US1]…[US4]**: historia de usuario de spec.md.
- **⛔ PERMISO**: punto de control. Hay que **detenerse y pedir permiso al usuario** antes de ejecutarlo
  (constitución, "Flujo de trabajo").

## Reglas para todas las tareas

- **Nunca** inventar nombres de `bpy.ops.bim.*`, `ifcopenshell.api` ni `bpy`. Usar los citados en research.md e
  `investigacion/`. Si hace falta uno nuevo, verificarlo antes en el código instalado y anotarlo con
  archivo:línea en research.md.
- **Solo** `bim_simple/bonsai_api.py` importa `bonsai` o llama a `bpy.ops.bim.*`. La única excepción son los
  ayudantes de prueba de `tests/test_pisos.py`.
- Textos visibles en español, exactamente como en [contracts/ui.md](contracts/ui.md). Identificadores en inglés
  con el prefijo `bimsimple.` / `BIMSIMPLE_`.
- Blender solo con `--background`, salvo en los puntos ⛔ de ventana. Nunca usar la configuración del Blender
  del usuario (`%APPDATA%\Blender Foundation\Blender\5.2`).
- Los commits usan `git commit -F <archivo>`, porque en PowerShell 5.1 las comillas del mensaje se rompen.
- Si el mismo error sigue después de 3 correcciones, detenerse y mostrar el error y lo que se probó.

---

## Fase 1: Preparación

**Propósito**: carpetas, manifiesto, plantilla, icono y textos fijos.

- [ ] T001 Crear las carpetas `bim_simple/`, `app_template/bim_simple/`, `assets/`, `tools/` y `tests/` en la raíz del repositorio, y agregar `dist/` a `.gitignore`. `__pycache__/` ya está.
- [ ] T002 [P] Crear `bim_simple/blender_manifest.toml` con estos campos:
  - `schema_version = "1.0.0"`, `id = "bim_simple"`, `version = "0.1.0"`, `name = "BIM Simple"`;
  - `tagline` en español, de 64 caracteres o menos y sin punto final;
  - `maintainer = "Nestor Torres"`, `type = "add-on"`, `blender_version_min = "5.2.0"`;
  - `license = ["SPDX:GPL-3.0-or-later"]`, `platforms = ["windows-x64"]`.

  Verificarlo con `"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -c extension validate bim_simple`.
- [ ] T003 [P] Crear `app_template/bim_simple/__init__.py` con `register()` y `unregister()` vacíos y un comentario explicando por qué: las preferencias y la activación de extensiones vienen del `userpref.blend` de la plantilla, porque `register()` corre antes que las extensiones (research R4).
- [ ] T004 [P] Crear `tools/make_icon.py`, solo con la biblioteca estándar y partiendo de `investigacion/scripts/empaquetado_make_ico.py`: genera `assets/bim_simple.ico` (PNG dentro de ICO, 256/48/32/16 px) con un dibujo plano simple de un edificio. Ejecutarlo con `python tools/make_icon.py`, es decir con el Python del sistema y **no** con Blender, y comprobar que el `.ico` existe.
- [ ] T005 [P] Crear `assets/LEEME.txt` en español con cuatro puntos:
  - qué es BIM Simple;
  - cómo abrirlo (acceso directo "BIM Simple");
  - cómo desinstalarlo: borrar `%LOCALAPPDATA%\Programs\BIM Simple` y los dos `BIM Simple.lnk`;
  - aviso de la caché compartida de Blender (diferencia D7) y de las licencias en `licencias\`.

---

## Fase 2: Base (bloquea todas las historias)

**Propósito**: acceso a Bonsai, núcleo de lectura de pisos, lista espejo, registro, configuración y armado del programa, esqueleto de la prueba y primer armado.

**⚠️ Ninguna historia puede empezar hasta terminar esta fase.**

- [ ] T006 Crear `bim_simple/bonsai_api.py`, el ÚNICO módulo que importa `bonsai`. Envoltorios finos, sin lógica, de lo que lista `investigacion/ifc.md` §10:
  - **Archivo y proyecto**: `get_file()` (`tool.Ifc.get`), `get_path()`, `get_object(entity)`, `get_entity(obj)`, `bim_props()` (`is_dirty`, `ifc_file`, `last_transaction`), `set_export_schema(schema)` (`tool.Project.get_project_props().export_schema`), `purge()` (`IfcStore.purge`), `refresh_ui_data()`, `clear_undo_history()`, `bonsai_version()`.
  - **Pisos**: `edit_container_name(storey, name)`, `set_object_name(obj, entity)`, `collector_assign(obj)`, `set_default_container(storey)`, `get_default_container()`, `delete_container(storey)` (`bonsai.core.spatial.delete_container` con `tool.Ifc, tool.Spatial, tool.Geometry`).
  - **Geometría**: `delete_ifc_object(obj)`, `record_object_position(obj)`, `get_absolute_matrix(obj)`.
  - **Operadores**: `create_project()`, `add_storey_part(building, name)` (`bim.add_part_to_object` con `"EXEC_DEFAULT"` y `part_class="IfcBuildingStorey"`; devuelve el piso nuevo buscando por diferencia de ids), `load_project(path, add_to_recent)` (`should_start_fresh_session=False`, `skip_autosave_recovery=True`, `skip_recent=not add_to_recent`), `save_project(path, add_to_recent)`.
  - **Base de operadores**: `IfcOperator = tool.Ifc.Operator`.

  Cada envoltorio lleva un comentario con el archivo:línea de research.
- [ ] T007 Crear `bim_simple/core.py` con la base de lectura, según [contracts/core_api.md](contracts/core_api.md):
  - `BIMSimpleError`; `StoreyInfo` (dataclass congelada con `ifc_id`, `name`, `elevation`, `height`, `is_active`);
  - conversión de unidades con `ifcopenshell.util.unit.calculate_unit_scale`;
  - `has_project()`, `project_path()`, `is_dirty()`;
  - `building_notice()`;
  - `list_storeys()`:
    - pisos de `get_decomposition` del primer `IfcBuilding`;
    - cota con `ifcopenshell.util.placement.get_storey_elevation × unit_scale`;
    - orden de mayor a menor cota, con empate por nombre;
    - "Altura: distancia al piso de arriba; para el más alto, `Qto_BuildingStoreyBaseQuantities.GrossHeight`, o 3,00 si no existe";
  - `activate_storey(ifc_id)`, `active_storey_id()`.

  Solo importa `bonsai_api`, `ifcopenshell` y `bpy`; nunca módulos de interfaz.
- [ ] T008 Crear `bim_simple/props.py`:
  - `BIMSimpleStorey` (`ifc_id`, `name`, `elevation`, `height`);
  - `BIMSimpleProperties` en `bpy.types.Scene.bim_simple`, con `storeys`, `active_storey_index` y `notice`;
  - `refresh_storeys(scene)`: vuelve a llenar la lista desde `core.list_storeys()` y ubica el índice en el piso activo **sin** disparar la activación (bandera de guarda);
  - el `update` de `active_storey_index` llama a `core.activate_storey`. La parte visual de la planta se agrega en T032.

  Regla de data-model §6: la lista es solo una copia; nunca es la fuente de verdad.
- [ ] T009 Crear `bim_simple/__init__.py`:
  - registro y desregistro ordenado de `props` y, a medida que existan, `operators`, `ui`, `screen`, `keymaps` y `session`;
  - manejadores `@persistent`: `load_post`, `undo_post` y `redo_post`, que llaman a `props.refresh_storeys`;
  - si `bpy.app.background` es `True`, no registra timers de ventana.
- [ ] T010 Crear `tools/configurar_programa.py`, que se ejecuta con el Blender del programa. Si `bpy.utils.resource_path('USER')` no termina en `portable`, se niega a correr. Recibe el modo después de `--`:
  - **`principal`**:
    - fija los valores "principal" de research R5: `view.language='es'`, `use_translate_interface/tooltips/reports=True`, `use_translate_new_dataname=False`, `filepaths.temporary_directory=<…>\portable\temp\`, `use_preferences_save=False`, `system.use_online_access=False`;
    - después llama a `bpy.ops.wm.save_userpref()`.
  - **`plantilla`** (con `--app-template bim_simple`):
    - activa `bl_ext.user_default.bonsai` y `bl_ext.user_default.bim_simple` con `bpy.ops.preferences.addon_enable`, y desactiva los add-ons de fábrica que no se usan;
    - fija los valores "plantilla" de R5, incluidas las preferencias de Bonsai `should_setup_workspace`, `activate_workspace` y `should_setup_toolbar` en `False`;
    - guarda con `wm.save_userpref()` y copia el `config\bim_simple\userpref.blend` resultante a `…\bl_app_templates_user\bim_simple\userpref.blend`;
    - genera `startup.blend` de datos en la carpeta de la plantilla, partiendo de `investigacion/scripts/interfaz_startup_datos.py`: un solo espacio "BIM Simple" con `use_filter_by_owner=True` y `owner_ids` = `bl_ext.user_default.bim_simple`, el resto borrado con `bpy.data.batch_remove`, escena sin objetos y `show_statusbar=False`.
  - **Verificación**: en un proceso nuevo con `--app-template bim_simple`, imprimir que los add-ons activos incluyen Bonsai y BIM Simple, `show_splash=False` y `language='es'` (Principio IV: el procedimiento de la plantilla no estaba verificado de punta a punta).
- [ ] T011 Crear `tools/armar_programa.ps1` según [contracts/programa.md](contracts/programa.md) y los 11 pasos de [plan.md](plan.md), sección "Armado del programa":
  - **Parámetros**: `-Destino`, `-BonsaiZip`, `-SoloExtension`, `-CrearAccesos`.
  - **Comprobaciones previas**: Blender 5.2.0, SHA-256 del zip y largo de la ruta (90 caracteres o menos).
  - **Pasos**:
    - `robocopy` sin `blender.pdb`;
    - `portable\` y `portable\temp\`;
    - `-c extension install-file -r user_default -e` para Bonsai y para el zip de `-c extension build --source-dir bim_simple --output-dir dist`;
    - copia de la plantilla;
    - `configurar_programa.py` en sus dos modos;
    - icono, `LEEME.txt` y `licencias\`, con la GPL-3.0 de `blender\license\` y los avisos de Blender, Bonsai e IfcOpenShell;
    - prueba automática;
    - control SC-005, con hashes SHA-256 de `%APPDATA%\Blender Foundation\Blender\5.2\config\*` y `extensions\user_default` antes y después;
    - accesos directos con WScript.Shell **solo** con `-CrearAccesos` (research R6).
  - **Salida**: una línea `OK`/`ERROR` por paso y código 1 ante cualquier fallo. **Nunca** escribe en `C:\Program Files\…` ni en `%APPDATA%\Blender Foundation\…`, y **nunca** descarga nada.
- [ ] T012 Crear `tests/test_pisos.py` con:
  - **Arnés**: `check(nombre, condición, detalle)` imprime `OK`/`FALLA`. Al final: `RESULTADO: TODO OK`, o `RESULTADO: N FALLAS` y `sys.exit(1)`. Cualquier excepción no atrapada también sale con 1.
  - **Ayudantes de prueba**: crear un elemento contenido en un piso con la receta verificada de `investigacion/scripts/_recetas.py` (muro de `DumbWallGenerator`); `reopen(path)` con `ifcopenshell.open`; `validate(path)` con `ifcopenshell.validate.validate(path, json_logger(), express_rules=True)`, que cuenta los mensajes de nivel `error`.
  - **Sección "Entorno"**: comprobar cada fila de la tabla de preferencias de [contracts/programa.md](contracts/programa.md), más Blender 5.2.0 y Bonsai 0.9.0.

  Los IFC de prueba se escriben en una carpeta temporal (`tempfile`) y nunca en el proyecto.
- [ ] T013 ⛔ PERMISO: pedir permiso y descargar `bonsai_py313-0.9.0-windows-x64.zip` (~150 MB) del release oficial de Bonsai 0.9.0. Antes de descargar, confirmar en docs.bonsaibim.org o en el release de GitHub de IfcOpenShell la URL y el SHA-256 publicado. Guardarlo en `C:\Users\Usuario\Downloads\` y comprobar el SHA-256 con `Get-FileHash`. Si no coincide, detenerse.
- [ ] T014 ⛔ PERMISO: pedir permiso y hacer el primer armado con `powershell -ExecutionPolicy Bypass -File tools/armar_programa.ps1 -BonsaiZip "C:\Users\Usuario\Downloads\bonsai_py313-0.9.0-windows-x64.zip"`. Crea `%LOCALAPPDATA%\Programs\BIM Simple` (~1,5 GB). Mostrar la salida real: todos los pasos `OK`, la sección "Entorno" en `OK` y SC-005 "Blender del usuario sin cambios". Hacer commit de las fases 1 y 2.

**Punto de control**: el programa existe, arranca en segundo plano con Bonsai y BIM Simple, y la prueba de entorno pasa.

---

## Fase 3: Historia 1. Abrir BIM Simple, empezar un proyecto y guardarlo (P1) 🎯 MVP

**Objetivo**: el programa abre en su pantalla (planta | 3D, solo "Archivo" y el panel), crea un proyecto IFC4 con Planta Baja y lo guarda.

**Prueba independiente**: proyecto nuevo → guardar → el IFC tiene Proyecto > Sitio > Edificio > Planta Baja a 0,00 y pasa la validación IFC4.

### Implementación de la Historia 1

- [ ] T015 [US1] En `bim_simple/core.py`, implementar `close_project()`, `new_project()` y `save_project(path=None, add_to_recent=True)` según [contracts/core_api.md](contracts/core_api.md) y la tabla R11 de research:
  - **`close_project`**: borrar objetos y colecciones IFC, `ifc_file=""`, `default_container=0`, `bonsai_api.purge()` y `refresh_ui_data()`.
  - **`new_project`**: cerrar si hace falta, porque `create_project` no hace nada si ya hay un IFC. Después: unidades de escena `METRIC`/`METERS`/`scale_length=1.0`, esquema `IFC4` y `create_project()`. Luego renombrar a "Proyecto", "Sitio", "Edificio" y "Planta Baja", con `Elevation=0` y `GrossHeight` 3,00 (`pset.add_qto` + `edit_qto`). Por último, activar Planta Baja y `clear_undo_history()`.
  - **`save_project`**: siempre con `bonsai_api.save_project`, nunca con `write()`; sin ruta ni ruta actual lanza `BIMSimpleError`; devuelve la ruta.
- [ ] T016 [P] [US1] Crear `bim_simple/keymaps.py`:
  - `apply_keymap_policy()` con la tabla por keymap de `investigacion/interfaz.md` §4. Desactiva `kmi.active` en `wm.keyconfigs.default` y `wm.keyconfigs.addon`, conserva lo que esa tabla marca como "se conserva" y luego llama a `wm.keyconfigs.update()`.
  - Atajos propios en `keyconfigs.addon`: Ctrl+N `bimsimple.new_project`, Ctrl+O `bimsimple.open_ifc`, Ctrl+S `bimsimple.save_ifc`, Mayús+Ctrl+S `bimsimple.save_ifc_as` y Ctrl+Q `bimsimple.quit`.
  - `restore_keymaps()` vuelve a activar solo lo que se desactivó y quita los propios.

  La lista vive en una tabla de datos al principio del archivo.
- [ ] T017 [US1] Crear `bim_simple/screen.py`, según research R7, R8 y R10 y la tabla "Pantalla" de [contracts/ui.md](contracts/ui.md):
  - **`ensure_layout(window)`**, idempotente:
    - deja exactamente dos `VIEW_3D` lado a lado, cerrando y dividiendo con `screen.area_close`/`area_split` dentro de `context.temp_override(window=…, screen=…, area=…)`, como `mvp-original:bim_simple/ui.py:85-155`;
    - oculta encabezado, barra de herramientas, encabezado de herramienta, HUD, estantería, gizmo de navegación y textos de la vista;
    - `screen.show_statusbar=False`;
    - planta izquierda con `view_rotation=(1,0,0,0)`, `ORTHO`, `is_orthographic_side_view=True` y `lock_rotation=True`;
    - barra lateral visible solo en la vista derecha, con `active_panel_category="BIM Simple"` (en un segundo timer, como el MVP);
    - colecciones locales en la vista derecha, aislando la colección del proyecto IFC (FR-006).
  - **`install_topbar()` / `restore_topbar()`**: reemplazan `bl_ui.space_topbar.TOPBAR_HT_upper_bar.draw` por uno que dibuja `BIMSIMPLE_MT_file` a la izquierda y `template_reports_banner()` + `template_running_jobs()` a la derecha.
  - **`hide_blender_panels()` / `restore_blender_panels()`**:
    - paneles Python de `VIEW_3D/UI` con `poll` falso y re-registro, como `bonsai/tool/blender.py:1893-1917`;
    - paneles C `VIEW3D_PT_transform`, `VIEW3D_PT_vgroup` y `VIEW3D_PT_curves` reemplazados por paneles Python con el mismo `bl_idname` y `poll` falso.
- [ ] T018 [US1] Crear `bim_simple/ui.py` (contrato en [contracts/ui.md](contracts/ui.md)):
  - **`BIMSIMPLE_MT_file`** ("Archivo"), con los cinco elementos y sus atajos.
  - **`BIMSIMPLE_UL_storeys`**: nombre, cota y altura como **texto** (`layout.label`, nunca `prop`), con dos decimales y coma decimal (`3,00`) y un icono en el piso activo.
  - **`BIMSIMPLE_PT_navigator`** (`VIEW_3D`, `UI`, `bl_category="BIM Simple"`):
    - estado "No hay ningún proyecto abierto" con "Nuevo proyecto" y "Abrir IFC…";
    - con proyecto, encabezado con nombre de archivo o "Proyecto sin guardar" y "• Cambios sin guardar";
    - `notice`;
    - título "Navegador de pisos" y la lista.
- [ ] T019 [US1] Crear `bim_simple/operators.py` con `bimsimple.new_project`, `bimsimple.save_ifc`, `bimsimple.save_ifc_as` (explorador de archivos con filtro `*.ifc`) y `bimsimple.quit`, según [contracts/ui.md](contracts/ui.md):
  - **Pregunta compartida de cierre**: «¿Guardar cambios antes de cerrar?» con Guardar / No guardar / Cancelar, con `WindowManager.invoke_popup` ✅ y botones de operador. La usan `new_project` y `quit` cuando `core.is_dirty()`.
  - **`quit`**: pone `preferences.view.use_save_prompt=False` en la sesión y llama a `bpy.ops.wm.quit_blender()`.
  - **Errores**: `BIMSimpleError` → `self.report({'ERROR'}, mensaje)`.
  - **Diálogos**: antes de usar `invoke_props_dialog` o `invoke_confirm`, verificar su firma en Blender 5.2 (RNA en `--background`) y anotarla en research.md.
- [ ] T020 [US1] Crear `bim_simple/session.py` (research R15, X2):
  - `save_session()` guarda `bpy.ops.wm.save_mainfile(filepath=<portable\temp>\BIM Simple.blend)`;
  - se llama al arrancar con ventana y después de Nuevo y Abrir;
  - el manejador `@persistent` `save_pre`, si la ruta es la de sesión y `core.is_dirty()`:
    - con ruta: guarda el IFC con `core.save_project()`;
    - sin ruta: escribe una copia en `portable\temp\recuperacion\<AAAA-MM-DD_HHMM>.ifc`;
  - `check_recovery()` al arrancar: si hay una copia, ofrece abrirla con el mensaje exacto de [contracts/ui.md](contracts/ui.md).
- [ ] T021 [US1] En `bim_simple/__init__.py`, conectar la pantalla:
  - con ventana (no en background): un timer de ~0,1 s llama a `screen.ensure_layout`, `keymaps.apply_keymap_policy`, `session.save_session` y `session.check_recovery`;
  - `load_post` vuelve a aplicar `ensure_layout` y la política de atajos;
  - `install_topbar` y `hide_blender_panels` se llaman en `register()`;
  - `unregister()` restaura todo en orden inverso.
- [ ] T022 [US1] En `tests/test_pisos.py`, sección "Historia 1":
  - **FR-007**:
    - esquema `IFC4`, unidad `METRE` y nombres Proyecto/Sitio/Edificio/Planta Baja;
    - Planta Baja con cota 0,00, `GrossHeight` 3,00 y activa;
    - ningún objeto de la escena fuera de colecciones IFC (FR-006);
    - un segundo `new_project()` con un proyecto abierto deja un solo piso.
  - **FR-009**: guardar en temporal → `project_path()`; "guardar como" cambia la ruta; `is_dirty()` en `False` después de guardar.
  - **SC-003**: el archivo guardado valida sin errores.
  - **FR-003 (lógica)**, después de `bpy.utils.keyconfig_init()`:
    - `TOPBAR_HT_upper_bar.draw` reemplazado;
    - paneles de `VIEW_3D/UI` de Blender con `poll` falso;
    - atajos de la tabla inactivos y los cinco propios activos;
    - el espacio "BIM Simple" filtra por dueño.
- [ ] T023 [US1] Ejecutar `tools/armar_programa.ps1 -SoloExtension` y mostrar la salida real: "Entorno" e "Historia 1" en `OK`, SC-005 sin cambios. Hacer commit.

**Punto de control**: la Historia 1 funciona y se prueba sola (lo visual queda para T037).

---

## Fase 4: Historia 2. Organizar los pisos del edificio (P2)

**Objetivo**: agregar arriba y abajo, renombrar, cambiar cota y altura con la regla de ArchiCAD y borrar pisos, todo deshacible.

**Prueba independiente**: proyecto nuevo → agregar dos pisos → renombrar → cambiar una altura → borrar uno → guardar y reabrir: mismos nombres, cotas y alturas.

### Implementación de la Historia 2

- [ ] T024 [US2] En `bim_simple/core.py`, implementar `add_storey_above()`, `add_storey_below()`, `rename_storey()`, `set_storey_elevation()`, `set_storey_height()`, `count_storey_elements()` y `delete_storey()`. Usar las recetas de research R12 y de `investigacion/scripts/_recetas.py`, y respetar estas reglas de [data-model.md](data-model.md) §4:
  - **Agregar arriba**: «Cota = cota del más alto + su altura. Altura = altura del más alto. Nombre "Piso N" (N = pisos con cota > 0 contando el nuevo).»
  - **Agregar abajo**: «Cota = cota del más bajo − 3,00. Altura 3,00. Nombre "Sótano N" (N = pisos con cota < 0 contando el nuevo).»
  - **Crear**: `bonsai_api.add_storey_part` y luego renombrar siempre, porque Bonsai agrega " 2" a los nombres repetidos.
  - **Nombre**: «No vacío (si no, se rechaza y queda el anterior). Puede repetirse.»
  - **Cambiar cota**: «Se rechaza si es menor o igual que la del piso de abajo. Δ = nueva − actual: el piso *i* y todos los de arriba se mueven Δ con sus elementos. `GrossHeight` del piso de abajo = nueva distancia.» Mover con `ifcopenshell.api.geometry.edit_object_placement(…, matrix=bonsai_api.get_absolute_matrix(obj), is_si=True, should_transform_children=True)`, más los objetos de Blender del piso y de `get_decomposition(piso)` con `record_object_position`, más `Elevation` relativo al edificio. **No** usar el camino de Bonsai, que no mueve los elementos.
  - **Cambiar altura**: «Si es el más alto, solo `GrossHeight`. Si no, Δ = nueva − actual: todos los pisos de arriba suben Δ con sus elementos, y `GrossHeight(i)` = nueva.» «Mayor que 0.»
  - **Contar**: «`IfcElement` de `get_decomposition(piso)`, sin aberturas (`IfcFeatureElementSubtraction`).»
  - **Borrar**: «Se rechaza si es el único. Se borran elementos y piso. Los de arriba no se mueven. El de abajo pasa a medir hasta el siguiente (si queda como el más alto, conserva su valor).» Primero `delete_ifc_object` de cada elemento (o `ifcopenshell.api.root.remove_product` si no tiene objeto) y después `delete_container`. Luego activar el inferior o, si no hay, el superior.

  Mensajes de error exactos de [contracts/ui.md](contracts/ui.md).
- [ ] T025 [US2] En `bim_simple/operators.py`, agregar `bimsimple.add_storey_above`, `bimsimple.add_storey_below`, `bimsimple.edit_storey` y `bimsimple.delete_storey`:
  - heredan de `bonsai_api.IfcOperator` con `_execute` y `bl_options={"REGISTER","UNDO"}`, son un paso de deshacer y al final llaman a `props.refresh_storeys`;
  - **`edit_storey`**: diálogo con Nombre, Cota (m) y Altura (m) del piso seleccionado. Aplica solo lo que cambió, en un único `_execute`.
  - **`delete_storey`**: si `count_storey_elements > 0`, pide confirmación con «El piso «X» tiene N elementos. Se borrarán junto con el piso.» y los botones [Borrar] / [Cancelar].
- [ ] T026 [US2] En `bim_simple/ui.py`, agregar al panel los botones "Agregar piso arriba", "Agregar piso abajo", "Editar piso…" y "Borrar piso". Se desactivan cuando no aplican: "Borrar piso" con un solo piso, y los de agregar si no hay edificio.
- [ ] T027 [US2] En `tests/test_pisos.py`, sección "Historia 2":
  - escenarios 1 a 5 de la Historia 2 de [spec.md](spec.md), con los valores exactos (Piso 1 a 3,00; Sótano 1 a −3,00; altura de Planta Baja a 3,50 → Piso 1 a 3,50 y Piso 2 a 6,50);
  - el elemento de prueba se mueve en el IFC (`worldZ`) y en Blender (`matrix_world`) y no queda "movido sin guardar";
  - rechazos: cota menor o igual que la del piso de abajo, altura 0, nombre vacío, borrar el único piso;
  - un nombre repetido queda sin " 2";
  - borrar con elementos: la cuenta es correcta, no quedan elementos sin contenedor y se activa el inferior;
  - **FR-018**: Ctrl+Z y Ctrl+Mayús+Z simulados del lado IFC, como `investigacion/ifc.md` §7;
  - **FR-019 / SC-002**: guardar, reabrir con `ifcopenshell.open` y comprobar nombres, `Elevation` = cota de la ubicación, `GrossHeight` y contención;
  - **SC-003**: validación sin errores.
- [ ] T028 [US2] Ejecutar `tools/armar_programa.ps1 -SoloExtension` y mostrar la salida real (Historias 1 y 2 en `OK`). Hacer commit.

**Punto de control**: las Historias 1 y 2 funcionan y se prueban por separado.

---

## Fase 5: Historia 3. Trabajar en un piso (P3)

**Objetivo**: un clic activa un piso; la planta muestra solo ese piso; lo nuevo se crea en él.

**Prueba independiente**: con tres pisos que tengan elementos, activar el Piso 1 → es el único activo y un elemento nuevo queda contenido en el Piso 1. Lo visual se comprueba en T037.

### Implementación de la Historia 3

- [ ] T029 [US3] En `bim_simple/screen.py`, agregar `storey_collection_index(storey)` y `show_storey_in_plan(storey)`:
  - **índice**: recorrido de la capa de vista igual que `BKE_layer_collection_from_index` (primero los hermanos, después los hijos), como `mvp-original:bim_simple/ui.py:173-209`;
  - **en la planta**: `bpy.ops.object.hide_collection(collection_index=i, toggle=False, extend=False)` con `temp_override(window, screen, area=planta, region=WINDOW)` y `use_local_collections=True`;
  - **sin ventana**: no hace nada;
  - además vuelve a mostrar la barra lateral de la vista derecha si estaba plegada (plan, riesgo 5).
- [ ] T030 [US3] En `bim_simple/props.py`, completar el `update` de `active_storey_index`: `core.activate_storey(ifc_id)` y después `screen.show_storey_in_plan`. Debe haber «exactamente uno mientras haya proyecto» (FR-021) y la activación no cambia el IFC ni marca cambios.
- [ ] T031 [US3] En `tests/test_pisos.py`, sección "Historia 3":
  - activar cada piso por el índice de la lista → `active_storey_id()` coincide y `is_dirty()` no cambia;
  - un elemento creado después de activar el Piso 1 queda contenido en el Piso 1, a su cota (FR-023);
  - `storey_collection_index` devuelve un índice distinto y válido para cada piso;
  - **SC-004**: con 10 pisos, activar + calcular el índice tarda menos de 1 s.
- [ ] T032 [US3] Ejecutar `tools/armar_programa.ps1 -SoloExtension` y mostrar la salida real (Historias 1 a 3 en `OK`). Hacer commit.

**Punto de control**: las Historias 1 a 3 funcionan.

---

## Fase 6: Historia 4. Abrir un IFC existente (P4)

**Objetivo**: abrir un `.ifc` propio o de otro programa sin perder el proyecto actual si el archivo no sirve.

**Prueba independiente**: abrir un IFC de otro programa con tres pisos → se ven sus pisos; "Guardar IFC como…" crea otro archivo y no toca el original.

### Implementación de la Historia 4

- [ ] T033 [US4] En `bim_simple/core.py`, implementar `open_project(path, add_to_recent=True)` según [contracts/core_api.md](contracts/core_api.md):
  1. validar con `ifcopenshell.open` y exigir `IfcProject`; si falla, lanzar `BIMSimpleError` con el mensaje exacto **sin tocar nada**, porque `load_project` descarga el proyecto antes de fallar;
  2. `close_project()`;
  3. `bonsai_api.load_project(path, add_to_recent)`;
  4. activar el piso de cota más cercana a 0,00, porque Bonsai elige el primero de la agregación;
  5. `clear_undo_history()`.

  Después de abrir, `is_dirty()` es `False`.
- [ ] T034 [US4] En `bim_simple/operators.py`, agregar `bimsimple.open_ifc`:
  - si `core.is_dirty()`, primero la pregunta de cierre de T019;
  - explorador de archivos con filtro `*.ifc`;
  - llama a `core.open_project`; los errores se muestran con `report`;
  - con ventana, después llama a `session.save_session()`.
- [ ] T035 [US4] En `tests/test_pisos.py`, sección "Historia 4":
  - generar en temporal los IFC de prueba con la lógica de `investigacion/scripts/make_test_ifcs.py`, copiada como ayudante dentro de la prueba: otro programa en milímetros, dos edificios, sin pisos, sin edificio, dañado y no IFC;
  - abrir el de milímetros → 4 pisos con cotas −2,80 / 0,00 / 3,20 / 6,00, alturas por distancia, activo "Nivel 0";
  - dos edificios → `building_notice()` con el texto exacto; sin pisos y sin edificio → lista vacía con mensaje;
  - dañado y no IFC → `BIMSimpleError` y el proyecto abierto antes sigue igual (mismo archivo y mismos pisos);
  - "guardar como" sobre un archivo abierto deja el original sin cambios (hash);
  - `is_dirty()` en `False` después de abrir.
- [ ] T036 [US4] Ejecutar `tools/armar_programa.ps1 -SoloExtension` y mostrar la salida real (Historias 1 a 4 en `OK`, SC-005 sin cambios). Hacer commit.

**Punto de control**: las cuatro historias funcionan en la prueba automática.

---

## Fase 7: Cierre y prueba manual

**Propósito**: comprobar con ventana lo que la prueba automática no puede, crear los accesos directos y actualizar los documentos del MVP.

- [ ] T037 ⛔ PERMISO: pedir permiso para abrir BIM Simple con ventana. Hacer con el usuario la parte B de [quickstart.md](quickstart.md) (B1 a B8):
  - incluye SC-007 (cronometrar el arranque), SC-001 (proyecto con tres pisos en menos de 3 minutos), SC-006 (dos clics como máximo por acción), las diferencias D1 a D3 y la X de la ventana (B7);
  - anotar cada resultado en el mensaje de commit de T041.
- [ ] T038 Si en T037 falla la X de la ventana (B7): cambiar `bim_simple/session.py` al plan B X1 (research R15: `use_save_prompt=False` y un `exit_pre` que guarda una copia de recuperación sin preguntar), actualizar la diferencia D5 en `research.md` §E y repetir B7. Si B7 pasa, marcar esta tarea como no necesaria.
- [ ] T039 Corregir lo que haya fallado en T037, con su prueba automática cuando se pueda comprobar sin ventana, y repetir `tools/armar_programa.ps1 -SoloExtension`.
- [ ] T040 ⛔ PERMISO: pedir permiso y crear los accesos directos con `tools/armar_programa.ps1 -SoloExtension -CrearAccesos`. Volver a leer los dos `.lnk` (destino `blender-launcher.exe`, argumentos `--app-template bim_simple`, icono `bim_simple.ico`) y mostrar sus propiedades.
- [ ] T041 [P] Reescribir `README.md` para el programa nuevo:
  - qué es; requisitos (Windows 11, Blender 5.2 instalado, zip de Bonsai py313);
  - cómo armarlo y cómo probarlo (comandos de [quickstart.md](quickstart.md));
  - estructura de carpetas según [plan.md](plan.md);
  - método Spec Kit (`.specify/`, `specs/`) y licencia GPL-3.0-or-later.
- [ ] T042 [P] Reescribir `PRUEBA_MANUAL.md` como la lista de prueba manual para el usuario: la parte B de [quickstart.md](quickstart.md) en lenguaje simple, con casillas y sin términos de programación.
- [ ] T043 Marcar la especificación como implementada (`**Estado**: Implementada` en [spec.md](spec.md)), comprobar que todas las tareas de este archivo están marcadas y hacer el commit final con los resultados de T037. Preguntar al usuario antes de subir a GitHub.

---

## Dependencias y orden de ejecución

### Dependencias entre fases

- **Fase 1 (Preparación)**: sin dependencias.
- **Fase 2 (Base)**: depende de la Fase 1. **Bloquea todas las historias.** T013 (descarga) y T014 (primer armado) necesitan permiso.
- **Fase 3 (US1)**: depende de la Fase 2. Es el MVP.
- **Fase 4 (US2)**: depende de la Fase 2. Usa la pantalla y el panel de US1 para mostrarse, pero su prueba automática es independiente.
- **Fase 5 (US3)**: depende de la Fase 2. Usa `screen.py` de US1 (T017).
- **Fase 6 (US4)**: depende de la Fase 2. Usa la pregunta de cierre de US1 (T019).
- **Fase 7 (Cierre)**: depende de todas las historias.

### Dentro de cada historia

- Primero `core.py`, después `operators.py`, después `ui.py`/`screen.py`, después la sección de la prueba, y por último el armado con `-SoloExtension` y el commit.
- Varias tareas tocan los mismos archivos (`core.py`, `operators.py`, `ui.py`, `tests/test_pisos.py`), así que dentro de una historia van **en orden**.

### Oportunidades de paralelo

- Fase 1: T002, T003, T004 y T005 (archivos distintos).
- Fase 3: T016 (`keymaps.py`) en paralelo con T015 (`core.py`).
- Fase 7: T041 y T042 (documentos distintos).

## Ejemplo de paralelo: Historia 1

```text
Tarea: "T015 [US1] close_project/new_project/save_project en bim_simple/core.py"
Tarea: "T016 [P] [US1] política de atajos en bim_simple/keymaps.py"
```

## Estrategia de implementación

### MVP primero (solo la Historia 1)

1. Fases 1 y 2, con los permisos de T013 y T014.
2. Fase 3 (US1).
3. **Detenerse y validar**: prueba automática en verde. Si el usuario quiere, adelantar la parte B1–B2 de la prueba manual (requiere permiso de ventana).

### Entrega incremental

Cada historia termina con `armar_programa.ps1 -SoloExtension`, la prueba automática completa en verde (las
historias anteriores siguen pasando) y un commit. Después US2 → US3 → US4 → Fase 7.

## Notas

- Puntos ⛔ PERMISO: T013 (descarga), T014 (instalar el programa), T037 (abrir ventanas) y T040 (accesos directos).
- Nada de esta función toca el Blender del usuario. Cada armado lo comprueba con el control SC-005.
- No borrar archivos sin permiso, incluidas las carpetas `__pycache__` (constitución).
