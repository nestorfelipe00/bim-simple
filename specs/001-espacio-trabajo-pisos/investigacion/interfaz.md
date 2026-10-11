# Investigación: la pantalla de BIM Simple dentro de Blender 5.2

Fase de plan (Spec Kit) de `specs/001-espacio-trabajo-pisos`. Tema: pantalla partida, ocultar la
interfaz de Blender y Bonsai, atajos, salir con cambios sin guardar, doble clic en la lista.

## Método y leyenda

- Blender 5.2.0 LTS (hash fbe6228777e7), siempre con `--background`. Ninguna ventana abierta.
- Casi todos los experimentos corrieron con **configuración aislada**:
  `BLENDER_USER_RESOURCES=<scratchpad>\research\interfaz\cfg_aislada` + `--factory-startup`.
  Comprobado: `bpy.utils.user_resource("CONFIG")` apuntaba a esa carpeta.
- Un solo experimento (exp10) usó la configuración del usuario **solo para leer** los atajos de Bonsai.
  No guardó nada: `userpref.blend` del usuario conserva la fecha 01:36:38, anterior a la prueba (02:08).
- Rutas abreviadas:
  - `bl_ui/…` = `C:\Program Files\Blender Foundation\Blender 5.2\5.2\scripts\startup\bl_ui\…`
  - `blender_default.py` = `…\5.2\scripts\presets\keyconfig\keymap_data\blender_default.py`
  - `bonsai/…` = `%APPDATA%\Blender Foundation\Blender\5.2\extensions\.local\lib\python3.13\site-packages\bonsai\…`
  - Código C de Blender 5.2: `projects.blender.org/blender/blender/raw/branch/blender-v5.2-release/source/…`
- Marcas:
  - ✅ ejecutado en Blender 5.2 `--background` y comprobado (salida en `research\interfaz\exp*_out.txt`).
  - 📖 solo leído (código instalado, código fuente C de 5.2 o manual 5.2).
  - 🖥 comprobado con ventana por el MVP (`mvp-original`, prueba manual del usuario). Aquí no se pudo
    repetir porque exige ventana.
  - ⚠️ no verificable en `--background`. Va a la lista de prueba manual.

## Resumen de decisiones

| # | Tema | Decisión recomendada |
|---|---|---|
| 1 | MVP | Se reutiliza el mecanismo del MVP (cerrar áreas, dividir y configurar con `temp_override` desde un timer), con los cambios de abajo. |
| 2 | Pantalla partida | El diseño se arma en la **ventana real, en tiempo de ejecución**, al arrancar (timer + `load_post` persistente) y se corrige si hace falta. En `--background` no se puede dividir ni cerrar áreas de forma fiable. Opcional: un `startup.blend` propio generado en `--background` solo con los ajustes de datos. |
| 3 | Ocultar interfaz | Se reemplaza el dibujo de `TOPBAR_HT_upper_bar` por un menú "Archivo" propio y se oculta la barra de estado (`Screen.show_statusbar`). Se ocultan el encabezado, la barra de herramientas, el encabezado de herramienta y el HUD de cada vista. El panel "BIM Simple" va en la barra lateral de la vista 3D derecha, sola: se ocultan los paneles de Blender (poll + re-registro, como hace Bonsai) y se reemplazan los paneles C por idname. Se usan `PreferencesApps` para quitar las flechas y la división por esquinas, y el filtro por dueño para Bonsai. |
| 4 | Atajos | En tiempo de ejecución se ponen `kmi.active = False` en `keyconfigs.default` y `keyconfigs.addon` con una lista por keymap, y luego `keyconfigs.update()`. Se agregan atajos propios (Ctrl+N/O/S/Mayús+S/Q) en `keyconfigs.addon`. |
| 5 | Planta | Vista superior por RNA (`view_rotation` identidad + `is_orthographic_side_view = True` + `ORTHO` + `lock_rotation`), o `view3d.view_axis(type='TOP')`. Un piso por vista con `SpaceView3D.use_local_collections` + `object.hide_collection(collection_index, toggle=False, extend=False)` con `temp_override`. |
| 6 | Salir con cambios | Ctrl+Q y Archivo > Salir usan un operador propio con la pregunta exacta. **La X de la ventana no se puede interceptar desde Python.** Lo más cercano es el diálogo propio de Blender, que en español dice exactamente «¿Guardar cambios antes de cerrar?», Guardar, No guardar y Cancelar, conectado a un `save_pre` que guarda el IFC. Respaldo: `exit_pre` con copia de recuperación. |
| 7 | Doble clic | No hay forma fiable en 5.2. Se confirma **un clic** para activar (D6); el doble clic queda para renombrar, como en Blender. |

---

## 1. Cómo armó el MVP el espacio "BIM Simple" y qué problemas anotó

**Decisión recomendada:** reutilizar el patrón del MVP. Hay cuatro cambios porque ahora es un
programa propio: (a) no se duplica "Layout" para convivir con otros espacios, sino que el programa
arranca ya en su espacio; (b) se ocultan también el encabezado, la barra superior y la barra de estado;
(c) la barra lateral queda sola con "BIM Simple"; (d) se controlan los atajos y las preferencias de Bonsai.

**Mecanismo del MVP** (`git show mvp-original:bim_simple/…`), todo 🖥:

| Paso | Código del MVP |
|---|---|
| Crear el espacio duplicando "Layout" con `bpy.ops.workspace.duplicate()` dentro de `temp_override(window, workspace)`, renombrarlo "BIM Simple" y poner `object_mode = "OBJECT"` | `ui.py:85-96` |
| Filtro de add-ons por espacio: `workspace.use_filter_by_owner = True` + `workspace.owner_ids.new(__package__)` | `ui.py:97-99` |
| El cambio de espacio se aplica en el siguiente ciclo de eventos, así que el armado va en un timer de 0,1 s | `ui.py:100-102` |
| Cerrar todo lo que no es vista 3D: `bpy.ops.screen.area_close()` con `temp_override(window, screen, area)` | `ui.py:117-120` |
| Dividir: `bpy.ops.screen.area_split(direction="VERTICAL", factor=0.5)`; izquierda planta, derecha 3D (orden por `area.x`) | `ui.py:121-125`, `:108-110` |
| Regiones: `area.show_menus = False`, `show_region_toolbar`, `show_region_tool_header`, `show_region_ui`. Comentario: «Cambiar regiones sin contexto de ventana cierra Blender (ED_region_visibility_change_update)» | `ui.py:126-133` |
| Planta: `wm.tool_set_by_id`, `view3d.view_axis(type="TOP")`, `view_perspective = "ORTHO"`, `lock_rotation = True`, `use_local_collections = True` | `ui.py:135-142` |
| Pestaña de la barra lateral: `region.active_panel_category = "BIM Simple"` en otro timer de 0,3 s, porque «la pestaña solo se puede elegir cuando la barra lateral ya se dibujó una vez» | `ui.py:145-155` |
| Un piso en planta: índice para `object.hide_collection`, recorriendo primero los hermanos y después los hijos (igual que `BKE_layer_collection_from_index`), y llamada con `temp_override(window, screen, area=plan, region=WINDOW)` y `toggle=False` | `ui.py:173-209` |
| Menú File: con el filtro activo desaparecen las opciones IFC que Bonsai agrega, así que el MVP antepone "Abrir IFC…", "Guardar IFC" y "Guardar IFC como…" (`bim.load_project`, `bim.save_project`) solo en "BIM Simple" | `ui.py:212-232` |
| Barra de herramientas: el filtro **no** oculta las herramientas de Bonsai. Se reemplaza `VIEW3D_PT_tools_active.draw` por una versión que, en "BIM Simple" y modo Objeto, dibuja solo las herramientas propias. Se restaura al desregistrar | `tools.py:107-141` |
| `register_tool(after=…)` metía la herramienta dentro del desplegable de un grupo, así que se reordenó `_tools["OBJECT"]` a mano | `tools.py:144-156` |
| Sin ventana no se registran herramientas, igual que en Bonsai | `tools.py:159-166` |
| Activar piso con un clic: callback `update` de `active_storey_index` | `props.py:39-46`, `:58` |

**Problemas que anotó el MVP** (`PLAN.md`, D5–D7, Riesgos 2, 3 y 7; `PRUEBA_MANUAL.md`):

1. El filtro por dueño oculta paneles y menús de Bonsai (verificado en su Fase 1), pero no las
   herramientas de la barra. Reemplazar `VIEW3D_PT_tools_active.draw` toca una parte interna de Blender (D7, Riesgo 2).
2. Bonsai cambia la interfaz global. Al abrir un archivo agrega su espacio "BIM", reinstala su barra
   de herramientas al crear o abrir un proyecto y, en modo Objeto, redefine G, X, Supr, Tab y Ctrl+J. El MVP
   no tocó las preferencias de Bonsai y esas teclas quedaron activas (Riesgo 3; la prueba manual lo
   anota como diferencia conocida).
3. Los planos de corte a 1,20 m recortaban la vista previa y las cotas de dibujo de Bonsai, así que se quitaron (D5).
4. Las listas no distinguen el doble clic: un clic activa y el doble clic renombra (D6).
5. El menú File: el filtro también oculta las opciones IFC de Bonsai (Riesgo 7).
6. Regiones: cambiarlas sin contexto de ventana cierra Blender (comentario en `ui.py:127`).

---

## 2. Pantalla partida: ¿se puede armar en `--background`?

**Decisión recomendada:** armar el diseño en la ventana real, en tiempo de ejecución, como el MVP (🖥):

- Una función idempotente `ensure_layout(window)`. Si la pantalla activa no tiene exactamente dos
  `VIEW_3D` lado a lado, cierra las otras áreas (`screen.area_close`) y divide (`screen.area_split`),
  siempre con `context.temp_override(window=…, screen=…, area=…)`. Después aplica las regiones, la
  planta y la barra lateral (puntos 3 y 5).
- Se dispara con `bpy.app.timers.register(…, first_interval≈0.1)` desde `register()` y desde un
  `bpy.app.handlers.load_post` marcado `@persistent`. Bonsai usa `load_post` y `bpy.context.window`
  al arrancar (`bonsai/bim/handler.py:466-478`, `:571-573`) 📖. Como `load_post` llega antes de
  que la ventana termine de iniciarse, las operaciones de pantalla van en el timer, igual que en el MVP.
- **Opcional:** para no arrancar con el cubo y los 11 espacios de fábrica, el programa puede llevar
  su propio `startup.blend`, en su configuración (`config\startup.blend`) o en una plantilla de
  aplicación. Ese archivo **sí** se puede generar en `--background`, pero solo con ajustes de datos
  (ver la evidencia). La división de áreas la sigue haciendo `ensure_layout` en tiempo de ejecución.
  Después de la primera división se podría guardar con `wm.save_homefile()` en la configuración del
  programa (nunca en la del usuario), para que los arranques siguientes ya abran partidos. Queda a decidir en el plan.

**Por qué:** en `--background` hay ventana y pantallas, pero la ventana mide 0×0. Por eso los
operadores de geometría de pantalla no dan un resultado fiable: `area_close` se cuelga, y `area_split`
y `area_join` dejan áreas de tamaño 0. Además, ocultar regiones no se conserva.

**Evidencia:**

| Pregunta | Resultado | Marca |
|---|---|---|
| ¿Hay ventanas en `wm.windows` en background? | Sí, 1 ventana, `size 0 0`, pantalla "Layout"; `context.window` existe y `context.area` es `None` (`exp1_out.txt`) | ✅ |
| ¿Existen `bpy.data.screens` y sus áreas? | Sí, 11 pantallas con sus áreas y coordenadas guardadas en el archivo (por ejemplo, Layout: PROPERTIES, OUTLINER, TIMELINE, VIEW_3D) | ✅ |
| ¿Se puede cambiar `area.type` / `ui_type`? | Sí, pero **solo en la pantalla activa de la ventana**. En "UV Editing" (inactiva), `area.type = 'VIEW_3D'` no cambió `spaces.active` (siguió IMAGE_EDITOR). En "Layout" (activa) sí cambió (`exp2b_split_then_type.txt`) | ✅ |
| `screen.area_split` | `poll` True y `{'FINISHED'}`, pero el área nueva queda en `(0,0,0,0)` y la original no se reduce: la geometría no se calcula sin ventana (`exp1_out.txt`, `exp2b_split_then_type.txt`) | ✅ (no fiable) |
| `screen.area_close` | **Se cuelga**: `poll` True y luego no termina; corte del timeout a los 40 s, código 124 (`exp2b_close_props.txt`; también `exp2_out.txt` a los 60 s) | ✅ |
| `screen.area_join(source_xy, target_xy)` | `{'FINISHED'}` pero deja áreas duplicadas de tamaño 0 (`exp2b_join.txt`) | ✅ (no fiable) |
| Ocultar regiones (`show_region_header/toolbar = False`) | Al releerlas siguen en `True`: no se conservan en background (`exp11_out.txt`: `regions True True False True False`) | ✅ (no se conserva) ⚠️ |
| `bpy.data.workspaces.remove` | No existe (`AttributeError`). `bpy.ops.workspace.delete()` devuelve FINISHED pero se aplica después; `bpy.data.batch_remove(lista)` sí borra en el acto (`exp11_out.txt`, `exp12_out.txt`) | ✅ |
| Generar un `startup.blend` solo con datos | Hecho y vuelto a abrir. Se conservan: un solo espacio "BIM Simple" con `use_filter_by_owner` y `owner_ids`, escena sin objetos, `show_statusbar = False`, un área convertida a VIEW_3D, y en la vista `use_local_collections`, `ORTHO`, `lock_rotation`, `is_orthographic_side_view` (`exp15_gen.txt`, `exp15_load.txt`) | ✅ |
| Plantillas de Blender con dos vistas lado a lado | Ninguna sirve. "Texture Paint" y "UV Editing" tienen editor de imagen + 3D lado a lado, pero también propiedades y esquema (`exp2b_templates.txt`) | ✅ |
| Plantilla de aplicación | Puede llevar `startup.blend`, `userpref.blend`, `splash.png` y `__init__.py` (con `register`/`unregister`). Va en `{BLENDER_USER_SCRIPTS}/startup/bl_app_templates_user`. Sus preferencias se guardan en `config/{APP_TEMPLATE_ID}/userpref.blend` y se activa con `--app-template` (manual 5.2, `advanced/app_templates.html`; `blender --help`) | 📖 |
| ¿Se puede poner título a la ventana desde Python? | No: `Window` no tiene ninguna propiedad de título (`exp13_out.txt`). Lo ve quien arme el paquete | ✅ |

**Alternativas consideradas:**

- (a) Armar en la ventana real (**elegida**): probada por el MVP 🖥. Cuesta un parpadeo al arrancar.
- (b) Generar el `startup.blend` completo en background: **descartada**, porque `area_close` se
  cuelga, `area_split` deja áreas de tamaño 0 y ocultar regiones no se conserva.
- (c) Plantilla de aplicación con su `startup.blend`: útil para separar preferencias y como
  `startup.blend` de datos, pero tampoco se puede generar su división en background. Generarla una
  vez abriendo Blender con ventana necesitaría permiso del usuario (constitución). Ver la opción de
  `wm.save_homefile()` en la primera ejecución.

---

## 3. Ocultar la interfaz de Blender y Bonsai

### 3a. Barra superior (TOPBAR) y menú "Archivo" propio

**Decisión:** reemplazar en tiempo de ejecución `bl_ui.space_topbar.TOPBAR_HT_upper_bar.draw` y
restaurarlo al desregistrar, con la misma técnica del MVP con `VIEW3D_PT_tools_active.draw`. La versión nueva:

- Región izquierda: solo `layout.menu("BIMSIMPLE_MT_file")` (etiqueta "Archivo"), con
  `bimsimple.new_project`, `bimsimple.open_ifc`, `bimsimple.save_ifc`, `bimsimple.save_ifc_as` y
  `bimsimple.quit`. Opcional: el nombre del proyecto.
- Región derecha (`context.region.alignment == 'RIGHT'`): `layout.template_reports_banner()` y
  `layout.template_running_jobs()`. Así se siguen viendo los mensajes (FR-011) aunque la barra de
  estado esté oculta, igual que hace Blender en `space_topbar.py:46-50`.

**Por qué:** no hay ninguna propiedad para ocultar la barra superior. Es un área global, y `Window` y
`Screen` no tienen nada parecido (`exp13_out.txt`: `Screen` solo tiene `show_statusbar` y
`show_fullscreen`). Las pestañas de espacios de trabajo y los menús Blender/File/Edit/Render/Window/Help
salen todos de ese `draw`.

**Evidencia:**

- `space_topbar.py:14` `class TOPBAR_HT_upper_bar(Header)`: `:17` draw; `:25` draw_left;
  `:31` `TOPBAR_MT_editor_menus.draw_collapsible`; `:36` `layout.template_ID_tabs(window, "workspace", …)`
  (pestañas de espacios); `:40` draw_right; `:53` selector de escena y capa de vista 📖.
- Es el único `Header` de TOPBAR en `bl_ui` (grep) 📖.
- Reemplazar el método es posible: `TOPBAR_HT_upper_bar.draw = …` cambia el método (`exp6_out.txt`) ✅.
  Que Blender use el reemplazo al dibujar lo demostró el MVP con `VIEW3D_PT_tools_active.draw` 🖥.
- Detalle: si un add-on usó `append`/`prepend`, `draw` ya es el envoltorio `draw_ls`
  (`_bpy_types.py:1174-1214`). Reemplazarlo descarta esos agregados, que es justo lo que se busca 📖.

### 3b. Barra de estado

**Decisión:** `screen.show_statusbar = False` en la pantalla del espacio. Se guarda en el
`startup.blend` y además lo aplica `ensure_layout`.

**Evidencia:** RNA `Screen.show_statusbar` «Show status bar» ✅ (`exp4_out.txt`). Se conserva al
guardar y volver a abrir ✅ (`exp15_load.txt`). Es el mismo interruptor del menú
Window (`space_topbar.py:578`) 📖. Bonsai agrega su dibujo a `STATUSBAR_HT_header`
(`bonsai/bim/__init__.py:289`), pero con la barra oculta da igual 📖.

### 3c. Vistas 3D: encabezado, menús, barra de herramientas, encabezado de herramienta, barra lateral y HUD

**Decisión** (en `ensure_layout`, con `temp_override(window, screen, area)` por la advertencia del MVP):

| Pieza | Cómo se oculta | Evidencia |
|---|---|---|
| Encabezado `VIEW3D_HT_header` (`space_view3d.py:702`) con `VIEW3D_MT_editor_menus` (`:1143`) | `space.show_region_header = False`; además `area.show_menus = False` por si el encabezado vuelve | RNA existe ✅ `exp1`; en background no se conserva ⚠️ |
| Barra de herramientas | `space.show_region_toolbar = False` en la función 1 (la caja de herramientas llega en la función 2 con la técnica D7) | ✅ RNA; 🖥 MVP |
| Encabezado de herramienta `VIEW3D_HT_tool_header` (`space_view3d.py:58`) | `space.show_region_tool_header = False` (en la función 2 será el Info Box) | ✅ RNA |
| HUD "Ajustar última operación" | `space.show_region_hud = False`; los operadores propios no llevan `'REGISTER'` salvo que haga falta | ✅ RNA; 📖 |
| Estantería de recursos | `space.show_region_asset_shelf = False` | ✅ RNA |
| Gizmo de navegación (incluye el botón perspectiva/ortogonal) | `space.show_gizmo_navigate = False`, al menos en la planta; la navegación sigue con el ratón (FR-003) | ✅ RNA |
| Textos sobre la vista ("Top Orthographic", nombre del objeto) | `space.overlay.show_text = False`, o `preferences.view.show_view_name = False` y `show_object_info = False` | ✅ RNA (`exp11`, `exp13`) |
| Flechas para volver a mostrar regiones ocultas y división/unión de áreas por las esquinas | `preferences.apps.show_regions_visibility_toggle = False` y `show_corner_split = False`. `show_edge_resize` puede quedar en `True` para cambiar la proporción planta/3D | ✅ `PreferencesApps` (`exp6_out.txt`). Fuente C `area.cc` `region_azone_edge_poll`: `if (is_hidden && (U.app_flag & USER_APP_HIDE_REGION_TOGGLE)) return false;`. Sin esa preferencia, un encabezado oculto **sí** muestra una flecha 📖 |

**Dónde va el panel "BIM Simple":** en la barra lateral (región `UI`) de la **vista 3D derecha**,
pegada al borde derecho de la ventana, como la paleta Navegador de ArchiCAD. `show_region_ui = True`
solo en esa área, y `bl_category = "BIM Simple"`. Si en esa región queda **una sola** categoría,
Blender no dibuja pestañas. Para lograrlo:

1. **Paneles Python de Blender** en `VIEW_3D/UI`: categorías "Item", "Tool", "View" y "Animation"
   (`VIEW3D_PT_copy_global_transform`, que no tiene `poll`: `space_view3d_sidebar.py:16`) (`exp3_out.txt`
   ✅). Se ocultan poniendo un `poll` que devuelve `False` y **volviendo a registrarlos**, porque sin
   re-registro un `poll` nuevo no se aplica a las clases que no tenían uno. Es exactamente lo que hace
   Bonsai con los paneles de escena (`bonsai/tool/blender.py:1893-1917`, `override_scene_panel`) y
   en su pantalla de error (`bonsai/__init__.py:391-406`) 📖. Probado con
   `VIEW3D_PT_view3d_properties` (`exp6_out.txt`) ✅.
2. **Paneles C** (no existen en `bpy.types`; `exp3_out.txt` ✅): `VIEW3D_PT_transform` ("Item >
   Transform", aparece con cualquier objeto activo), `VIEW3D_PT_vgroup` y `VIEW3D_PT_curves`
   (`view3d_buttons.cc`, `view3d_buttons_register`; poll `view3d_panel_transform_poll` = hay base
   activa) 📖. Se reemplazan registrando un `Panel` Python con el **mismo `bl_idname`** y
   `poll → False`. Registrar `VIEW3D_PT_transform` desde Python funcionó (`exp7_out.txt`) ✅. En el
   fuente `rna_ui.cc`, `rna_Panel_register` libera el tipo C anterior con
   `BLI_freelinkN(&art->paneltypes, pt);` sin error 📖. **No se puede deshacer en la sesión**, lo que
   es aceptable porque es la copia propia del programa.
3. **Paneles de Bonsai:** los oculta el filtro por dueño (3d).
4. Riesgo: si el usuario arrastra el borde y la barra lateral se pliega, sin flechas ni N no hay cómo
   volver a abrirla. Mitigación: `ensure_layout` vuelve a poner `show_region_ui = True` (timer o
   `load_post`) ⚠️.

Alternativas consideradas para el panel:

- Popover en la barra superior (`layout.popover(...)`): no queda a la vista; abrirlo cuesta un clic más.
- Un área de Propiedades: `SpaceProperties` tiene `show_properties_*` para ocultar pestañas
  (`exp3_out.txt`) ✅, pero agrega un tercer área y choca con el secuestro de los paneles de escena de Bonsai.
- La región `TOOLS`: se puede registrar un panel ahí (`exp7`) ✅, pero es angosta y es la caja de
  herramientas de la función 2.

**Lo que no se puede ocultar desde Python:** el menú contextual de **clic derecho sobre un botón**
(Copiar ruta de datos, Asignar atajo, Manual en línea…). Está fijo en el código C: en
`interface_handlers.cc`, `do_button()` abre `popup_context_menu_for_button` con
`event->type == RIGHTMOUSE && event->modifier == 0`, y el comentario dice «Only hard-coded stuff here» 📖.
Atenuante: con `show_developer_ui = False` (preferencia) desaparecen las opciones de desarrollador.
Se anota como diferencia con FR-003.

**El explorador de archivos** de Abrir y Guardar IFC es una ventana de Blender. Con el idioma en
español aparece traducido (3e). Alternativa a evaluar en el plan, sin verificar: el diálogo nativo de
Windows con `ctypes` (biblioteca estándar).

### 3d. Paneles y menús de Bonsai: ¿basta `use_filter_by_owner` + `owner_ids`?

**Decisión:** sí para paneles y para menús y encabezados extendidos con `append`/`prepend`. **No
alcanza** para lo siguiente, que se resuelve aparte:

| No lo filtra | Cómo se resuelve |
|---|---|
| Herramientas de Bonsai en la barra de herramientas | Función 1: barra oculta. Función 2: técnica D7 del MVP |
| Atajos de Bonsai (keyconfig de add-ons) | Punto 4 |
| Espacio "BIM" que Bonsai agrega y activa en cada `load_post` (`bonsai/bim/handler.py:466-478`; preferencias `should_setup_workspace` y `activate_workspace`, por defecto `True`: `bonsai/bim/ui.py:464`, `:472`) | En las preferencias **del programa**: `should_setup_workspace = False`, `activate_workspace = False`, y `should_setup_toolbar = False` (`ui.py:480`; `handler.py:470`) |
| Decoraciones y gizmos de Bonsai dibujados en la vista | No son menús ni paneles; se aceptan, porque son las ayudas de dibujo |

**Evidencia:**

- RNA `WorkSpace.use_filter_by_owner` «Filter the UI by tags» y `WorkSpace.owner_ids` ✅
  (`exp1`, `exp4`, `exp11`).
- Filtro de las funciones agregadas: `_bpy_types.py:1186-1201`. Si el espacio filtra, se omite toda
  función cuyo `_owner` no esté en `owner_ids`. `_owner` se asigna en `_dyn_owner_apply`
  (`:1220-1224`) con el id de dueño activo durante el `register` del add-on
  (`addon_utils.py:536-554`; `use_owner = is_extension or …`) 📖.
- Paneles: `rna_ui.cc`, `rna_Panel_register`: `pt->owner_id` = `RNA_struct_state_owner_get()` 📖.
  El MVP comprobó que se ocultan 🖥.
- Dueño real de Bonsai: las funciones que Bonsai agregó a `TOPBAR_MT_file` y `VIEW3D_HT_header`
  tienen `_owner = 'bl_ext.user_default.bonsai'` (`exp10_out.txt`, config del usuario, solo lectura) ✅.
  En el programa, el nombre depende del repositorio donde se instale Bonsai. `owner_ids` debe tener
  **solo** el id de la extensión BIM Simple (MVP: `owner_ids.new(__package__)`).
- Los paneles y menús de Blender (dueño vacío) **no** se filtran. Por eso hacen falta 3a–3c 📖.

### 3e. Preferencias del programa (su propio `userpref.blend`)

Todas existen en RNA ✅ (`exp1`, `exp4`, `exp6`, `exp8`, `exp13`). Esta lista es lo que la tarea de
empaquetado tiene que dejar fijo:

- `view.show_splash = False`: sin pantalla de bienvenida (FR-001). Sin un `userpref.blend` propio,
  Blender usa los valores de fábrica, donde vale `True`.
- `view.language = 'es'`, `use_translate_interface/tooltips/reports = True`: el diálogo de cierre y
  el explorador de archivos salen en español (`exp8_out.txt` ✅).
- `use_preferences_save = False`: los cambios en tiempo de ejecución, como `use_save_prompt`, no se guardan.
- `view.show_developer_ui = False`, `view.show_tooltips_python = False`.
- `apps.show_regions_visibility_toggle = False`, `apps.show_corner_split = False`.
- Bonsai: `should_setup_workspace`, `activate_workspace` y `should_setup_toolbar` en `False`.
- Desactivar los add-ons que trae Blender de fábrica y no se usan (por ejemplo `io_scene_gltf2`, que
  tiene un panel en la barra lateral, aunque con `poll`).

---

## 4. Atajos de teclado

**Decisión recomendada:** una función `apply_keymap_policy()` de la extensión, que corre en un timer
al arrancar y otra vez en `load_post`:

1. Recorre `wm.keyconfigs.default` (atajos de Blender) y `wm.keyconfigs.addon` (atajos de Bonsai) y
   pone `kmi.active = False` según una lista por keymap.
2. Llama a `wm.keyconfigs.update()`.
3. Registra los atajos propios en `keyconfigs.addon`: Ctrl+N → nuevo proyecto, Ctrl+O → abrir,
   Ctrl+S → guardar, Mayús+Ctrl+S → guardar como, Ctrl+Q → salir. Ctrl+Z y Mayús+Ctrl+Z se dejan
   como están (`ed.undo`/`ed.redo`, keymap "Screen").

**Lista propuesta** (desactivar en *default* y en *addon*):

| Keymap | Qué se desactiva (ejemplos con línea de `blender_default.py`) | Qué se conserva |
|---|---|---|
| Window | Ctrl+N `TOPBAR_MT_file_new`; Ctrl+O `wm.open_mainfile` (`:722`); Ctrl+S `wm.save_mainfile` (`:723`); Ctrl+Q `wm.quit_blender` (`:730`, se reemplaza); Mayús+F1…F12 `screen.space_type_set_or_cycle` (`:737`); F1 manual; F2 `TOPBAR_PT_name`; F3 `wm.search_menu` (`:775`); F4 `TOPBAR_MT_file_context_menu` (`:776`); Q `SCREEN_MT_user_menu`; Mayús+Ctrl+O; `wm.toolbar*` | `info.reports_display_update` (TIMER_REPORT) y NDOF |
| Screen | Ctrl+Tab `space_context_cycle`; Ctrl+RePág/AvPág `workspace_cycle` (`:823`); Ctrl+Alt+Q quad view; Mayús+R repetir; F9 `redo_last`; F11/F12 render; Ctrl+Espacio y Ctrl+Alt+Espacio `screen_full_area` (`:857-858`); Ctrl+, preferencias (`:885`) | `ed.undo`/`ed.redo`; `file.execute`/`file.cancel` (explorador de archivos); `screen.animation_step`/`region_blend` (timers) |
| Screen Editing | clic derecho `screen.area_options` (`:925`) | `actionzone`, `region_scale`, `area_move` (la división por esquinas ya la quita `show_corner_split`) |
| Region Context Menu | `screen.region_context_menu` (`:946`) | — |
| Object Non-modal | todo: Tab `object.mode_set`, Ctrl+Tab `view3d.object_mode_pie_or_toggle` (`km_object_non_modal` `:4615`, `:4625`, `:4647`), Alt+Q `transfer_mode` | — |
| Object Mode | todo menos la selección (`object.select_all`): Mayús+A `VIEW3D_MT_add` (`:4560`), clic derecho `VIEW3D_MT_object_context_menu` (`:4583`), G/R/S y arrastre `transform.translate CLICK_DRAG`, X/Supr `object.delete`, H/Alt+H, M, Ctrl+J, Ctrl+P, I, K, Ctrl+G… | `object.select_all` |
| 3D View | `view3d.view_axis` (teclado numérico), `view_persportho`, `localview` (`:1639-1641`), `wm.call_menu_pie` (Z, `), `wm.context_toggle`, `wm.call_panel`, `toggle_xray`, `toggle_shading`, `navigate` (vuelo), `cursor3d`, `copybuffer`/`pastebuffer`, `view_camera`, `camera_to_view`, `render_border`, `clip_border`, `transform.translate` | `rotate`, `move`, `zoom`, `dolly`, `view_pan`, `view_all`, `view_selected`, `select`, `select_box/circle/lasso`, `zoom_border`, `smoothview`, `ndof_*` |
| 3D View Generic | T y N `wm.context_toggle` (`:358`, `:363`) | — |
| Frames | todo (Espacio reproduce la animación) | — |
| User Interface | `anim.keyframe_*_button` (I), `anim.driver_button_*` (Ctrl+D), `keyingset_button_*`, `ui.copy_data_path_button` | lo demás (edición de textos, cuentagotas) |
| Bonsai (*addon*) | Window: Ctrl+N `BIM_MT_new_project`, Ctrl+S `bim.save_project` (se reemplaza por el propio), Ctrl+Tab `bim.switch_tab`. Object Mode: Ctrl+J, Mayús+D, Alt+D, Ctrl+Mayús+D, G, Ctrl+V, Tab, Espacio, X, Mayús+X, Supr, Mayús+Supr. Mesh: Tab, Espacio, P. Curve: Tab. 3D View: Esc `bim.override_escape` (revisar en la función 2: puede hacer falta para cancelar el dibujo). Outliner: Ctrl+V, X, Supr | — |

Los keymaps modales ("Transform Modal Map", "View3D … Modal", "Standard Modal Map"), los de "View2D",
"View2D Buttons List", "File Browser …" y los de gizmos no se tocan.

**Por qué:**

- Hay que desactivar **los dos lados**. Si se apaga el Tab de Bonsai, el evento sigue de largo y
  llega al Tab de Blender (`object.mode_set` en "Object Non-modal"), y al revés.
- Hacerlo en tiempo de ejecución no deja nada guardado y cubre los atajos que Bonsai registra cuando
  ya arrancó el programa.
- No hace falta ningún archivo de keyconfig extra.

**Evidencia:**

- **En `--background` los keymaps vienen vacíos** hasta llamar a `bpy.utils.keyconfig_init()`:
  "Window" de *default* pasa de 0 a 33 elementos (`exp3_out.txt`) ✅. La docstring dice «called
  from the Blender window manager on startup and refresh» (`bpy/utils/__init__.py:852-867`) 📖.
  **La prueba automática tiene que llamar a `keyconfig_init()` antes de comprobar atajos.**
- Keyconfigs que existen en background: `Blender` (default, 108 keymaps), `Blender addon`,
  `Blender user`; `active` = Blender (`exp1_out.txt`) ✅.
- Apagar en *default* se ve en *user* después de `update()`. Prueba con Ctrl+Espacio: `default
  disabled -> user copy active? False` ✅.
- Apagar en *addon* se ve en *user*: `addon item inactive -> user copy active? [False]` ✅.
- Apagar en *user* se conserva después de `update()` y de registrar nuevos keymaps de add-on (`after
  addon+update F3 user active False`) ✅. Pero `km.is_user_modified` queda en `False`, así que no es
  seguro cómo se guardaría. Por eso se prefiere *default*/*addon*.
- Atajos encontrados con su estado (`exp3_out.txt`): Ctrl+N, Ctrl+Mayús+O, Ctrl+Q, Q, F3, F4,
  Ctrl+Espacio, Ctrl+Alt+Espacio, Tab, Ctrl+Tab, Mayús+A, Ctrl+A, Ctrl+L, M, Mayús+M, clic derecho
  (menú contextual), T, N ✅.
- Atajos de Bonsai, en el código: `bonsai/bim/__init__.py:298-301` (Ctrl+Tab);
  `bonsai/bim/module/project/__init__.py:125-137` (Ctrl+N, Ctrl+S);
  `bonsai/bim/module/geometry/__init__.py:146-205` (Object Mode, Mesh, Curve, 3D View, Outliner) 📖.
  En ejecución, la lista coincide (`exp10_out.txt`) ✅.
- Volcado completo de los keymaps de usuario en background: `research\interfaz\out3\keymaps_user.txt`.

**Alternativas consideradas:**

- Un preset de keyconfig propio ("BIM Simple.py" en `scripts/presets/keyconfig/`, filtrando
  `blender_default.generate_keymaps`): es declarativo, pero **no cubre** los atajos de Bonsai y agrega un archivo.
- Editar `keyconfigs.user`: funciona en la sesión, pero no se sabe bien cómo se guardaría.
- Solo una lista negra sin listas de "conservar": es fácil que se escape algo (por ejemplo Mayús+F*
  cambia el tipo de editor). Conviene revisar keymap por keymap, como en la tabla.

---

## 5. Vista de planta y un piso por vista

**Decisión:**

- Planta, por RNA y sin necesidad de contexto: `rv3d.view_rotation = Quaternion((1, 0, 0, 0))`,
  `rv3d.view_perspective = 'ORTHO'`, `rv3d.is_orthographic_side_view = True` (lo alinea al eje; sin
  esto la vista queda como "USER" y el bloqueo no la trata como vista lateral) y `rv3d.lock_rotation = True`.
  Equivale a `bpy.ops.view3d.view_axis(type='TOP')` con `temp_override(…, region=WINDOW)`, como en el MVP.
- Solo el piso activo en la planta: `plan_space.use_local_collections = True` y, al activar un piso,
  `bpy.ops.object.hide_collection(collection_index=i, toggle=False, extend=False)` con
  `temp_override(window, screen, area=planta, region=WINDOW)`. El índice se calcula con el recorrido
  del MVP (`ui.py:173-188`).
- **Sugerencia** para FR-006: activar también `use_local_collections` en la vista 3D derecha y aislar
  allí la colección del proyecto IFC. Así los objetos sueltos que no son IFC no se ven en ninguna vista.

**Por qué:** es el único mecanismo de Blender para ver colecciones distintas en cada vista.
`LayerCollection.hide_viewport` y `Collection.hide_viewport` son globales.

**Evidencia:**

- RNA: `RegionView3D.view_perspective`, `view_rotation`, `lock_rotation` («Lock view rotation of side
  views to Top/Front/Right»), `is_orthographic_side_view` (escribible: «Setting this will rotate the
  view to the closest axis») ✅ (`exp1`, `exp4`, `exp9`).
- Con solo `view_rotation` + `ORTHO`, `side` queda en `False`. Después de
  `is_orthographic_side_view = True` pasa a `True`. `view3d.view_axis(type="TOP")` en background da
  `FINISHED`, rotación `(1,0,0,0)`, `ORTHO`, `side True` (`exp9_out.txt`) ✅.
- `SpaceView3D.use_local_collections` «Display a different set of collections in this viewport» ✅.
  `object.hide_collection` tiene las propiedades `collection_index`, `toggle` y `extend` («Show only
  objects in collection (Shift to extend)») ✅ (`exp14_out.txt`).
- `LayerCollection.hide_viewport` «Temporarily hide in viewport» es **por capa de vista**: con P2
  oculto así, desaparece también de la vista 3D (`exp3_out.txt`: `after LayerCollection.hide_viewport
  P2 -> … 3d False`) ✅. `Collection.hide_viewport` «Globally disable in viewports» ✅.
- No hay RNA para la visibilidad de colecciones por vista: `LayerCollection` solo tiene
  `visible_get()`, `has_objects()` y `has_selected_objects()` (`exp1_out.txt`) ✅. Existen
  `Object.local_view_get/set(viewport)` (vista local, otro mecanismo que obliga a entrar en vista
  local y encuadra) y `Object.visible_in_viewport_get(viewport)` ✅.
- ⚠️ **En background las colecciones locales no se pueden comprobar.** Con
  `use_local_collections = True`, `visible_in_viewport_get` da "nada visible" y `hide_collection`
  devuelve `FINISHED` sin cambiar nada (`exp3b_out.txt`, `exp3c_out.txt`, con y sin área dividida).
  El MVP sí lo comprobó con ventana: «Un clic sobre Piso 1 lo activa: la planta queda vacía», y en la
  sección 7 «En la planta solo se ve lo del Piso 1» 🖥. **Consecuencia:** la prueba automática solo
  puede comprobar la lógica (qué índice y qué colección se elige). Lo visual va a la prueba manual.
- Cuidado: `hide_collection` también lee Mayús del estado del teclado para extender. Hay que pasar
  `extend=False` explícitamente (📖 por la descripción del operador).

**Alternativas consideradas:**

- `bim.set_container_visibility(mode="ISOLATE")` de Bonsai: global, afecta a las dos vistas (MVP 📖).
- `LayerCollection.hide_viewport`: global (✅ arriba).
- Vista local (`view3d.localview`): encuadra y depende de los objetos, no de la colección.
- Planos de corte: descartados en el MVP (D5).

---

## 6. Salir con cambios sin guardar (FR-010)

**Cómo cierra Blender 5.2** (fuente C, 📖):

- Ctrl+Q: `wm.quit_blender` (`blender_default.py:730`).
- X de la ventana: `GHOST_kEventWindowClose` → `wm_window_close_request` →
  `wm_quit_with_optional_confirmation_prompt` cuando es la última ventana principal. El sistema
  operativo pidiendo salir pasa por `GHOST_kEventQuitRequest` → la misma función (`wm_window.cc`).
- `wm_quit_with_optional_confirmation_prompt`: solo pregunta si `U.uiflag & USER_SAVE_PROMPT`
  (preferencia `use_save_prompt`) **y** `wm_file_or_session_data_has_unsaved_changes()` = `!wm->file_saved
  || imágenes modificadas || catálogos de recursos sin guardar`, y `!G.background`. Si no, sale.
  **No llama a nada de Python antes del diálogo** (`wm_window.cc`, `wm_files.cc`).
- El diálogo (`block_create__close_file_dialog`, `wm_files.cc`) dice "Save changes before closing?" y
  tiene Guardar, No guardar y Cancelar. **Guardar** llama a `WM_OT_save_mainfile`: con
  `ExecDefault` si el `.blend` ya tiene ruta (y sale solo si no se cancela), y con `InvokeDefault`
  (explorador de archivos `.blend`) si nunca se guardó (`wm_block_file_close_save`).
- **No se puede reemplazar** `wm.save_mainfile` con un operador Python: «Registering operator class:
  'FakeSave', bl_idname 'wm.save_mainfile' could not be unregistered» (`exp5_out.txt`) ✅.
- `bpy.app.handlers.exit_pre`: «just before Blender shuts down, while all data is still valid».
  Recibe un booleano y no puede cancelar. Corre también en background con `args=(False, None)`
  (`exp4`, `exp5`, `out5/exit_pre.txt`) ✅.
- `save_pre`/`save_post` reciben la ruta del `.blend`. `save_pre` corrió con `wm.save_mainfile`
  (`exp4_out.txt`) ✅.
- En español, Blender traduce el diálogo exactamente a la pregunta de la especificación: «¿Guardar
  cambios antes de cerrar?», «Guardar», «No guardar», «Cancelar» (`exp8_out.txt`) ✅.
- `bpy.data.is_dirty` («Have recent edits been saved to disk») pasa a `True` con `ed.undo_push` ✅.
  En background **seguía en `True` después de `wm.save_mainfile`** (`exp4_out.txt`) ⚠️: hay que
  comprobar con ventana que guardar lo pone en `False`.
- Bonsai lleva su propio estado del IFC: `BIMProperties.is_dirty` se pone en `True` en cada operador
  IFC (`bonsai/bim/ifc.py:396-398`) y en `False` al guardar (`bonsai/bim/module/project/operator.py:2134`).
  `bim.save_project` también guarda el `.blend` si `bpy.data.is_saved and bpy.data.is_dirty and
  bpy.data.filepath` (`:2152-2154`) 📖.

**Decisión recomendada:**

1. **Ctrl+Q y Archivo > Salir** van a un operador propio `bimsimple.quit`. Si `is_dirty` de Bonsai
   está en `True`, muestra la pregunta propia Guardar IFC / No guardar / Cancelar, como popup
   (`WindowManager.invoke_popup` o `popup_menu`, ✅ en `exp13`). Si se elige guardar y el proyecto
   nunca se guardó, abre el explorador de archivos y sale después. Para salir sin que aparezca además
   el diálogo `.blend` de Blender: `preferences.view.use_save_prompt = False` y luego
   `bpy.ops.wm.quit_blender()`. No queda guardado porque `use_preferences_save = False`. **Cumple FR-010 exacto.**
2. **X de la ventana: NO se puede interceptar desde Python en Blender 5.2.** Alternativa más cercana
   (X2), a confirmar en la prueba manual:
   - `use_save_prompt = True` e idioma español: la X muestra el diálogo de Blender con el texto exacto de FR-010.
   - El programa mantiene un `.blend` de sesión oculto en su carpeta temporal (se guarda con
     `wm.save_mainfile(filepath=…)` al arrancar y después de abrir un IFC). Así "Guardar" usa
     `ExecDefault` y no abre un explorador de archivos `.blend`, y `bim.save_project` deja el estado
     de Blender en "guardado" cuando se guarda el IFC.
   - Un `save_pre` `@persistent` hace de puente: si la ruta es el `.blend` de sesión y el IFC de Bonsai
     tiene cambios, escribe el IFC en su ruta (`tool.Ifc.get().write(ruta)` y `is_dirty = False`).
     Si el IFC nunca se guardó, lo escribe en una carpeta de recuperación y lo avisa en el próximo arranque.
3. **Respaldo** si X2 no pasa la prueba manual (X1): `use_save_prompt = False` y un `exit_pre` que, si
   el IFC tiene cambios, guarda una **copia de recuperación**, nunca el original. Al arrancar se ofrece
   abrirla. Se anota como diferencia: "cerrar con la X no pregunta, pero no se pierde nada".

**Limitaciones de X2** (para la tabla de complejidad o de diferencias del plan):

- El diálogo es de Blender y muestra el nombre del `.blend` de sesión, no el del IFC.
- Puede preguntar aunque el IFC no tenga cambios: cualquier paso de deshacer, como seleccionar, marca
  la sesión como modificada. En ese caso el puente no reescribe el IFC si Bonsai dice que no hay cambios.
- Con un proyecto nunca guardado, "Guardar" no puede abrir el explorador de archivos del IFC. Va a la
  carpeta de recuperación con aviso.
- Cada guardado del IFC también escribe un `.blend` pequeño.
- Todo esto solo se puede comprobar con ventana ⚠️.

**Alternativas descartadas:**

- Dejar el diálogo de Blender sin puente: "Guardar" guardaría un `.blend`, no el IFC.
- Reemplazar `wm.save_mainfile`: imposible (✅ arriba).
- Desactivar la X con Win32 desde `ctypes` (`GetSystemMenu` + `EnableMenuItem(SC_CLOSE, MF_GRAYED)`):
  sin verificar, poco habitual para el usuario, y depende de cómo maneja GHOST la ventana.
- Bonsai tiene autoguardado propio (`bonsai/tool/autosave.py:36-37`, sufijo `_autosaved.ifc`;
  preferencias `autosave_enabled` y `autosave_mode`, `bonsai/bim/ui.py:589`, `:603`; por defecto
  apagado según `exp10`). Puede servir de red de seguridad, pero no pregunta al cerrar.

---

## 7. Doble clic en una fila de la lista

**Decisión:** se confirma **un clic** para activar el piso (D6 del MVP, aprobada; FR-020). El doble
clic sobre el nombre queda para renombrar, que es como funcionan las listas de Blender.

**Por qué:** en 5.2 no hay ninguna forma fiable ni documentada de recibir el doble clic de una fila
desde Python, y Blender ya usa el doble clic de las listas para renombrar.

**Evidencia:**

- Manual 5.2, "List View": «By double-clicking on an item, you can edit its name via a text field»;
  también con Ctrl+clic. «To select an item, click LMB on it» 📖.
- La API de `UIList` solo tiene `draw_item`, `draw_filter` y `filter_items`, sin evento
  (`exp1_out.txt`) ✅.
- En `interface_handlers.cc`, `handle_uilist_event` solo maneja flechas, Ctrl+rueda y rueda. Los
  `KM_DBL_CLICK` que no se atienden se vuelven a tratar como pulsaciones normales 📖.
- `blender_default.py` no tiene ningún operador de "activar fila de lista" con `DOUBLE_CLICK`. Los
  `ui.view_item_*` son para vistas de árbol y cuadrícula de C++, que no existen en Python (grep) 📖.

**Alternativa considerada y no recomendada:** dibujar cada fila como un botón de operador y medir el
tiempo entre dos invocaciones contra `preferences.inputs.mouse_double_click_time` (350 ms por
defecto, ✅ RNA). No es nativo, choca con renombrar y con la selección de la lista, el primer clic
igual ejecuta la acción de un clic, y no se puede probar automáticamente.

---

## Lo que NO se puede hacer en Blender 5.2 (diferencias con la especificación)

| Requisito | Qué no se puede | Alternativa elegida |
|---|---|---|
| FR-010 (cerrar la ventana) | Interceptar la X o cancelar el cierre desde Python. Reemplazar el "Guardar" del diálogo de Blender | X2: diálogo de Blender en español + puente `save_pre` (prueba manual). Respaldo X1: copia de recuperación en `exit_pre` |
| FR-003 (nada de Blender a la vista) | Quitar el menú contextual de clic derecho sobre los botones (fijo en C) | Se acepta. `show_developer_ui = False` lo reduce |
| FR-003 | Ocultar el área de la barra superior | Se reemplaza su dibujo por el menú "Archivo" propio |
| FR-003 | El explorador de archivos de Abrir y Guardar es de Blender | En español. Opcional: diálogo nativo de Windows con `ctypes` (a evaluar) |
| FR-001 | Poner el título de la ventana desde Python (`Window` no tiene título) | Para la tarea de empaquetado |
| FR-020 | Detectar el doble clic en la lista | Un clic activa (D6, aprobado) |
| FR-022 | Comprobar en `--background` qué se ve en cada vista (las colecciones locales no se evalúan sin ventana) | La prueba automática comprueba la lógica. Lo visual va a la prueba manual |
| Construcción | Dividir o cerrar áreas en `--background` para generar el `startup.blend` | Se arma al arrancar, en la ventana real |

## Puntos para la prueba manual (⚠️)

1. Al abrir el programa: dos vistas lado a lado; sin encabezados, sin flechas de regiones, sin barra
   de estado; arriba solo "Archivo".
2. Paneles C reemplazados: con un objeto activo no aparece la pestaña "Item"; la barra lateral
   muestra solo "BIM Simple", sin pestañas.
3. Planta: Ctrl+arrastre o botón central desplaza y no rota; no se pasa a perspectiva.
4. Activar un piso: la planta muestra solo ese piso y la vista 3D todo. Un elemento nuevo aparece en
   la planta (base nueva con bits locales).
5. Cada tecla de la tabla del punto 4 no hace nada. Ctrl+Z y Ctrl+Mayús+Z siguen funcionando.
6. X de la ventana con y sin cambios, con un proyecto guardado y otro sin guardar (X2). Ver si
   `bpy.data.is_dirty` vuelve a `False` después de guardar.
7. La barra lateral plegada con el ratón se vuelve a mostrar sola.

## Archivos de los experimentos

En `…\scratchpad\research\interfaz\`:

| Archivos | Qué cubren |
|---|---|
| `exp1_screens.py` / `exp1_out.txt` | Ventanas, pantallas, RNA, operadores, handlers |
| `exp2_build_startup.py`, `exp2b_variants.py` y sus `.txt` | Dividir, cerrar, unir; plantillas |
| `exp3_keymaps_panels.py` / `exp3_out.txt` + `out3\keymaps_user.txt` | Atajos y paneles de la barra lateral |
| `exp3b_local_collections.py`, `exp3c_nosplit.py` | Colecciones locales |
| `exp4_quit_dirty.py`, `exp5_override_exit.py` | Salir: estado sin guardar, `save_pre`, `exit_pre`, reemplazo de operador |
| `exp6_apps.py` | `PreferencesApps`, poll + re-registro, reemplazo de `draw` |
| `exp7_cpanel.py` | Reemplazo de un panel C |
| `exp8_lang.py` | Traducción al español |
| `exp9_view.py` | Vista superior |
| `exp10_bonsai_readonly.py` | Config del usuario, solo lectura |
| `exp11_ws.py`, `exp12_wsdel.py` | Espacios de trabajo y regiones |
| `exp13_misc.py` | Propiedades RNA de ventana, pantalla y preferencias |
| `exp14_ops.py` | Firmas de operadores |
| `exp15_gen.py`, `exp15_load.py` | `startup.blend` de datos |
