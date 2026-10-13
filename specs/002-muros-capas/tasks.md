---
description: "Lista de tareas de la función 002: muros con capas que se pueden separar"
---

# Tareas: Muros con capas que se pueden separar

**Entrada**: documentos de diseño en `specs/002-muros-capas/`, sobre la constitución 4.0.0.

**Requisitos previos**:
- [plan.md](plan.md) y [spec.md](spec.md);
- [research.md](research.md), [data-model.md](data-model.md) y [quickstart.md](quickstart.md);
- los contratos [core_api.md](contracts/core_api.md) y [ui.md](contracts/ui.md).

**Base de código**: lo construido en la función 001 (`engine/`, `app/`). Las recetas de IfcOpenShell están probadas en
los scripts de research (carpeta temporal `plan002/v1_design.py` y `v4_catalog.py`): se reescriben ordenados dentro
del motor, sin importarlos.

**Pruebas** (constitución, Principio V):
- **Motor**: `runtime\python\python.exe -m pytest engine\tests -q -p no:cacheprovider`.
- **Programa**: `npm --prefix app test` (ventana oculta; escribe `app\test-output\resultado.json` y capturas).
- **Manual**: [quickstart.md](quickstart.md), parte B.

**Organización**: por historia de usuario de la especificación (US1 a US4). Cada historia termina con las dos
pruebas automáticas en verde (también las de la función 001) y un commit.

## Formato: `[ID] [P?] [Historia] Descripción`

- **[P]**: se puede hacer en paralelo (otro archivo, sin depender de tareas pendientes).
- **[US1]…[US4]**: historia de usuario de spec.md.
- **⛔ PERMISO**: punto de control. Hay que **detenerse y pedir permiso al usuario** antes de ejecutarlo.

## Reglas para todas las tareas

- **APIs**: usar solo las funciones verificadas en research.md (R2-R12), con los cuidados anotados allí:
  - `assign_type` y `assign_material` se llaman **una vez por muro**, porque si no comparten la usage;
  - `create_2pt_wall` no asigna la representación;
  - el eje va en el contexto Plan/Axis/GRAPH_VIEW;
  - se usa `regenerate_wall_representation` después de cambiar capas o tipo.

  Si hace falta una función nueva, primero hay que verificarla en el código instalado y anotarla en research.md.
- **Licencias**: no leer ni copiar código de Bonsai. No agregar dependencias (no hace falta ninguna).
- **Idiomas**: textos visibles en español, exactamente como en los contratos; código, órdenes y campos en inglés.
- **Transacciones**: cada orden que cambia el IFC usa `project.transaction(...)`, de modo que es un paso de deshacer.
  Una regla que no se cumple se rechaza con `EngineError` **antes** de cambiar nada.
- **Ventanas**: las pruebas corren con la ventana oculta. Abrir la ventana visible es un ⛔ PERMISO.
- **Commits**: `git commit -F <archivo>` (el archivo escrito con la herramienta Write, sin BOM). No subir nada a
  GitHub sin permiso.
- **Errores**: si el mismo error sigue después de 3 correcciones, detenerse y mostrarlo con lo que se probó.

---

## Fase 1: Preparación

- [X] T001 Correr las dos pruebas de la función 001 antes de tocar nada y anotar la salida como línea de base:
  `28 passed` y `RESULTADO: TODO OK` (46 pasos).
- [X] T002 [P] Crear los iconos propios en `app/src/renderer/icons/`, en SVG de 24 × 24 con trazo `#26231f` y sin
  texto:
  - `arrow.svg`: flecha de selección inclinada;
  - `wall.svg`: muro en planta, un rectángulo con dos líneas internas que marcan capas.

---

## Fase 2: Base (bloquea todas las historias)

**Propósito**: catálogo y materiales en el motor, datos y capas de los muros, mallas con grupos, pantalla con caja de
herramientas e Info Box, y menú Opciones.

- [X] T003 Crear `engine/bimsimple_engine/materials.py` (research R7, R11; [data-model.md](data-model.md) §1-2):
  - Paleta `DEFAULT_MATERIALS` con los nombres y colores de research R7, en orden: Hormigón `#b5b5b0`,
    Ladrillo `#c1694f`, Bloque de hormigón `#9a9a94`, Revoque `#e8e2d4`, Aislación `#f2d24b`, Placa de yeso
    `#f4f4f0`, Madera `#b9875a`.
  - `DEFAULT_STRUCTURES`:
    - "Muro de hormigón 25": Hormigón 0,20 · Aislación 0,05;
    - "Muro exterior 30": Revoque 0,02 · Ladrillo 0,20 · Aislación 0,05 · Revoque 0,03;
    - "Tabique 15": Revoque 0,015 · Ladrillo 0,12 · Revoque 0,015.
  - `body_context(project)`: `ifcopenshell.util.representation.get_context(f, "Model", "Body", "MODEL_VIEW")`.
  - `add_material(project, name, color)`:
    1. `ifcopenshell.api.material.add_material(f, name=name)`;
    2. `style.add_style` + `style.add_surface_style(ifc_class="IfcSurfaceStyleShading", attributes={"SurfaceColour":
       {"Name": None, "Red": r, "Green": g, "Blue": b}, "Transparency": 0.0})`;
    3. `style.assign_material_style(context=Body)`.

    El color entra como `#rrggbb`. Error "El color tiene que tener la forma #rrggbb." si no cumple
    `^#[0-9a-fA-F]{6}$`.
  - `material_color(project, material)`: `ifcopenshell.util.representation.get_material_style(material, body)` →
    `Styles[0].SurfaceColour`. Sin estilo devuelve `#d9d9d6`.
  - `list_materials(project)`: `[{id, name, color}]` ordenada por nombre.
  - `create_structure(project, name, layers)`:
    - layers = `[(material, thickness)]`;
    - `root.create_entity("IfcWallType", name=name, predefined_type="STANDARD")`;
    - `material.add_material_set(name=name, set_type="IfcMaterialLayerSet")`;
    - por cada capa, `add_layer` + `edit_layer({"LayerThickness": t})`;
    - `assign_material(products=[tipo], type="IfcMaterialLayerSet", material=conjunto)`.
  - `list_structures(project)`:
    - todos los `IfcWallType` cuyo `get_material` sea un `IfcMaterialLayerSet`, ordenados por nombre;
    - cada uno: `{id, name, thickness, walls: len(ifcopenshell.util.element.get_types(tipo)), layers:
      [{material_id, thickness}]}`, con las capas en el orden del conjunto, de exterior a interior.
  - `add_default_catalog(project)`: crea los 7 materiales y las 3 estructuras.
  - Todo en metros: los proyectos de BIM Simple están en metros.
- [X] T004 En `engine/bimsimple_engine/project.py` y `storeys.py`:
  - `Project.__init__` agrega `self.endpoint_index = None` y el método `discard_index()`, que lo pone en `None`.
  - `state()` agrega `"materials": materials.list_materials(self)` y `"structures":
    materials.list_structures(self)`. Sin proyecto, `[]` y `[]`.
  - `new_project` llama a `materials.add_default_catalog(project)` después de crear la Planta Baja y antes de
    `project.replace_file(f, "")` (que vacía el historial; `project.py:105`), dentro del mismo `try`.
  - `replace_file`, `undo` y `redo` llaman a `discard_index()`.
  - En `storeys.py`, `edit_storey` y `delete_storey` llaman a `project.discard_index()` después de cambiar algo
    (research R5).
- [X] T005 [P] Crear `engine/bimsimple_engine/layers.py`: geometría de capas, código propio (research R6, R10).
  - `body_solid(wall)`:
    - con `util.representation.get_representation(wall, "Model", "Body", "MODEL_VIEW")`, devuelve el
      `IfcExtrudedAreaSolid` si la representación tiene **un solo** ítem de esa clase, con `ExtrudedDirection` (0, 0,
      1) y `SweptArea` `IfcArbitraryClosedProfileDef` (`OuterCurve` `IfcIndexedPolyCurve` o `IfcPolyline`) o
      `IfcRectangleProfileDef`;
    - si no, `None`.
  - `profile_polygon(solid)`:
    - polígono 2D en coordenadas locales del muro, sin repetir el primer punto al final;
    - aplica `util.placement.get_axis2placement(solid.Position)`;
    - el rectángulo se arma con `XDim`/`YDim` centrados en su `Position`.
  - `clip_strip(polygon, y_min, y_max)`: Sutherland–Hodgman contra `y <= y_max` y `y >= y_min`, como en
    `plan002/v1_design.py`.
  - `layer_strips(usage, thicknesses)`:
    - lista de `(y_min, y_max)` por capa;
    - empieza en `y = usage.OffsetFromReferenceLine` y avanza `±espesor` según `DirectionSense` (POSITIVE +,
      NEGATIVE −).
  - `layer_polygons(wall)`: `[(capa, polígono, depth)]` o `None` si no hay `body_solid`.
  - `is_convex(polygon)`: los productos cruzados de aristas consecutivas tienen todos el mismo signo, ignorando los
    nulos (puntos colineales).
  - `prism(polygon, depth, matrix)`:
    - vértices `float32` de las dos tapas y caras laterales en el mundo (matriz = `get_local_placement` del muro);
    - tapas en abanico desde el vértice 0;
    - normales hacia afuera según la orientación del polígono.

    Devuelve `(vertices, faces)` con índices `uint32`.
  - `extend_ends(polygon, face_y, old_inner_y, new_inner_y)`, para los muros `custom_ends`:
    - el polígono tiene que ser un cuadrilátero con dos aristas sobre `y = face_y` y `y = old_inner_y`;
    - las otras dos aristas se prolongan como rectas hasta `y = new_inner_y`;
    - si no es un cuadrilátero así, `None`.
- [X] T006 Crear `engine/bimsimple_engine/walls.py`, base de datos de muros (research R3, R5, R10; data-model §3, §4,
  §6):
  - `endpoints(wall)`: extremos del eje (`util.representation.get_reference_line`) llevados al mundo con
    `get_local_placement`; `[(x, y), (x, y)]` en metros.
  - `reference_of(wall)`, según research R3:
    - `"exterior"`, `"center"` o `"interior"` si la usage es NEGATIVE y `OffsetFromReferenceLine` es 0, T/2 o T
      (tolerancia 0,0001);
    - si no, `"other"`.
  - `kind_of(wall)`, según research R10, en este orden:
    1. `"locked"` si no hay `IfcMaterialLayerSetUsage`, no hay eje Plan/Axis o `layers.body_solid` es `None`;
    2. `"regenerable"` si tiene alguna `IfcRelConnectsPathElements` (`ConnectedTo`/`ConnectedFrom`), o si su polígono
       coincide (tolerancia 0,0001) con el rectángulo `[0, L] × franja total`;
    3. si no, `"custom_ends"`.
  - `wall_info(project, wall)` con exactamente los campos de data-model §6:
    - `id`, `storey_id`, `start`, `end`, `reference`;
    - `height` (el `Depth`, o 0 si `locked` sin sólido);
    - `structure_id` (el tipo si está en `materials.list_structures`, si no `None`);
    - `layers` `[{material_id, thickness}]`, `thickness`, `kind`;
    - `locked_reason`: "Este muro viene de otro programa y BIM Simple no puede cambiar su forma; se puede borrar."
      cuando `kind == "locked"`, si no "".
  - `EndpointIndex` en `project.endpoint_index`:
    - dict `storey_id → {(round(x, 3), round(y, 3)): set(ids)}`;
    - se arma perezoso con todos los `IfcWall` del piso que no son `locked`;
    - métodos `add(wall)`, `remove(wall_id)` y `near(storey_id, point)`, que devuelve los ids con un extremo a menos
      de 1 mm (revisa la celda redondeada y sus vecinas).
- [X] T007 Ampliar `engine/bimsimple_engine/geometry.py` ([data-model.md](data-model.md) §5):
  - cada malla suma `"groups": []` y `"wall": walls.wall_info(...)` si es `IfcWall`, si no `None`;
  - para un `IfcWall` `regenerable` o `custom_ends` cuyos polígonos de capa (`layers.layer_polygons`) sean todos
    convexos y no vacíos, la malla se arma con `layers.prism` por capa:
    - `vertices` y `faces` concatenados;
    - `groups` = `[{start, count, material_id}]`, con `start` y `count` en índices de `faces` (múltiplos de 3);
  - el resto sigue igual (OpenCASCADE, `groups` vacío).
  - Mantener la nota sobre `enable-layerset-slicing` y citar research R6.
- [X] T008 [P] Ampliar `engine/tests/make_fixtures.py` con `muros_otro_programa.ifc`, en metros, con un piso
  "Planta Baja" a 0,00 y tres muros:
  - **"Muro con capas"**:
    - tipo con 2 capas (Ladrillo 0,15 y Revoque 0,02) asignado con `type.assign_type`;
    - `create_2pt_wall` de (0, 0) a (5, 0) + `assign_representation`;
    - eje Plan/Axis;
    - usage POSITIVE con desplazamiento 0 (la de `assign_type`);
    - `regenerate_wall_representation`.

    Queda `regenerable` con referencia `"other"`.
  - **"Muro sin capas"**: como `_wall` (sin material). Queda `locked`.
  - **"Muro con recorte"**: `geometry.add_wall_representation(..., clippings=[...])` con un plano inclinado (research
    R4, `add_wall_representation.py:27-38`), con usage y eje. Queda `locked`, porque su cuerpo no es una extrusión
    simple.

  Crear también los contextos Plan y Plan/Axis/GRAPH_VIEW en ese archivo.
- [X] T009 Crear `engine/tests/test_walls.py` con las pruebas de la base (deben pasar al terminar T003-T008):
  - `test_proyecto_nuevo_trae_el_catalogo`:
    - `state.materials` tiene los 7 nombres con sus colores exactos;
    - `state.structures` tiene los 3 nombres, ordenados, con espesores 0,25, 0,30 y 0,15 y capas exactas;
    - `can_undo` es falso.
  - `test_capas_de_un_muro_suman_su_volumen`: con un recinto armado con la receta de research R4 directamente con la
    API en un `project.file`, la suma de áreas × depth de `layers.layer_polygons` es igual a
    `ifcopenshell.util.shape.get_volume(create_shape(...).geometry)` (± 1e-6).
  - `test_clases_de_muros_de_otro_programa`: abre `muros_otro_programa` → clases `regenerable`/`locked`/`locked` y
    referencia `"other"` en el primero.
  - `test_mallas_con_grupos`: en el recinto anterior, cada malla de muro tiene un grupo por capa, con `count`
    múltiplo de 3 y la suma de `count` igual a `len(faces)`.
- [X] T010 [P] Pantalla en `app/src/renderer/index.html` y `styles.css` ([contracts/ui.md](contracts/ui.md),
  "Pantalla"):
  - `body` pasa a columna: arriba `<header id="infobox">` a todo el ancho (~44 px) y debajo una fila con
    `<nav id="toolbox">` (44 px), `<main id="views">` y `<aside id="panel">`;
  - botones de la caja con `<img src="icons/arrow.svg">` / `wall.svg`, `title` "Flecha (seleccionar)" / "Muro" y
    `data-tool` `arrow`/`wall`;
  - `<dialog id="structures-dialog">` con la estructura del contrato: lista, botones Nueva, Duplicar, Renombrar y
    Borrar, tabla de capas, Agregar capa, Quitar capa, Subir y Bajar, "Espesor total", Nuevo material… (nombre +
    `<input type="color">`), zona de error, Cancelar y Aceptar;
  - estilos de la herramienta activa (fondo `--activo`), de los campos del Info Box y del diálogo (más ancho: ~720
    px).
- [X] T011 [P] Mallas en `app/src/renderer/meshes.js`:
  - si `item.groups` no está vacío:
    - `geometry.addGroup(start, count, i)` por grupo, **antes** de `toNonIndexed()`, que copia los grupos con los
      mismos rangos (`three/src/core/BufferGeometry.js:1123`, verificado);
    - el material es un arreglo con un `MeshStandardMaterial` por grupo, del color de `state.materials` por
      `material_id`;
  - guardar `mesh.userData.wall = item.wall`;
  - métodos `setMaterials(list)` (colores por id, se llama en cada `render`), `planMaterialsFor(mesh)`
    (`MeshBasicMaterial` del mismo color, para la planta) y `setSelected(ids)` (material azul `#2f6fd6` en las dos
    vistas para los seleccionados);
  - `walls(storeyId)`: lista de `userData.wall` del piso.
- [X] T012 [P] Vistas en `app/src/renderer/viewports.js`:
  - En `draw()`, la planta usa `meshes.planMaterialsFor(mesh)` (en lugar de un solo `planMaterial`), y el 3D,
    `mesh.userData.material` o el de selección.
  - `overlay`: `THREE.Group` aparte, siempre visible en la planta y oculto en el 3D, para la vista previa.
  - `planPoint(event)`: `Raycaster.setFromCamera` con la cámara de la planta y corte con el plano Z = cota del piso
    activo (`THREE.Plane`) → `{x, y}` en metros (research R12).
  - `pixelsToMeters(px)`: tamaño de 1 px en la planta (`(top − bottom) / zoom / alto`).
  - `onPlanPointer(handlers)`: registra `pointerdown`, `pointermove` y `contextmenu` en `planDiv`, que se pasan a la
    herramienta activa. El botón central sigue desplazando.
  - En el 3D, `click3d(handler)`: llama a `handler(event, hit)` en un clic izquierdo con menos de 4 px entre
    `pointerdown` y `pointerup` (`Raycaster` contra `meshes()`).
  - `worldToClient(x, y)` (para la prueba del programa).
  - Ampliar la grilla a 200 m (`GridHelper(200, 200)`).
- [X] T013 Menú en `app/src/main/main.js`:
  - agregar entre "Edición" y "Ayuda" `{label: "Opciones", submenu: [{label: "Estructuras compuestas…", enabled:
    !!state.has_project, click: sendMenu("structures")}]}`;
  - en `app/test/window-test.js`, `EXPECTED_MENUS` suma `{label: "Opciones", items: ["Estructuras compuestas…"]}`
    entre Edición y Ayuda, y el texto del paso pasa a "Menús Archivo, Edición, Opciones y Ayuda con sus textos
    (FR-003, FR-030)".
- [X] T014 Correr las dos pruebas. Esperado: la función 001 sigue en verde y pasan las de T009. Commit "feat: base de
  muros con capas (función 002, fase 2)".

**Punto de control**: el catálogo existe en los proyectos nuevos, los muros de otros programas se clasifican y la
pantalla tiene caja de herramientas e Info Box (todavía sin dibujar).

---

## Fase 3: Historia 1 — Dibujar muros en la planta (Prioridad: P1) 🎯 MVP

**Objetivo**: con la herramienta Muro se dibujan cadenas de muros Básicos unidos en las esquinas, en el piso activo.

**Prueba independiente**: con pisos a 0,00, 3,00 y 6,00 y el Piso 1 activo, dibujar un rectángulo de 6 × 4 m,
guardar y volver a abrir: 4 muros en el Piso 1, con el espesor y la altura del Info Box, y las 4 esquinas unidas.

### Pruebas de la Historia 1

- [X] T015 [US1] En `engine/tests/test_walls.py`, antes de implementar:
  - `test_recinto_basico_6x4` (SC-002):
    - 4 `create_wall` en sentido horario `(0,4)→(6,4)→(6,0)→(0,0)→(0,4)` en un proyecto nuevo con pisos 0/3/6 y el
      Piso 1 activo;
    - quedan 4 `IfcWall` contenidos en el Piso 1 (`get_container`), con espesor 0,20 y altura 3,00;
    - hay 4 `IfcRelConnectsPathElements`;
    - la suma de áreas de `layer_polygons` es 3,84 ± 0,1 %;
    - el volumen OpenCASCADE total es 3,84 × 3.
  - `test_lineas_de_referencia`: un muro de (20,0) a (24,0) con `exterior`, `center` e `interior` → la Y local de la
    capa está en [−0,20, 0], [−0,10, 0,10] y [0, 0,20], y `wall_info.reference` coincide.
  - `test_rechazos_al_dibujar`, con los textos exactos de [core_api.md](contracts/core_api.md):
    - muro de 0,005 m → "El muro es demasiado corto (mínimo 1 cm).";
    - espesor 0 → "El espesor debe ser mayor que 0.";
    - altura −1 → "La altura debe ser mayor que 0.";
    - referencia "x" → "Línea de referencia no válida.";
    - material inexistente → "El material elegido ya no existe.".

    En cada caso, la cantidad de entidades del archivo no cambia.
  - `test_deshacer_un_muro`: Ctrl+Z quita el muro y su unión; el muro siguiente vuelve a unirse bien (índice
    descartado).
  - `test_muros_guardados_y_reabiertos` (SC-004; constitución, Principio V): guardar, `open_project`, y cada
    `wall_info` es igual al de antes (± 1 mm). Las **uniones** también: el conjunto de pares de muros unidos, con
    `RelatingConnectionType`/`RelatedConnectionType`, es el mismo.
  - `test_mover_piso_y_seguir_dibujando` (caso límite): recinto en el Piso 1, cambiar la cota del Piso 1 con
    `edit_storey`, dibujar un muro desde un extremo del recinto → queda unido (el índice se rearmó). Cambiar la
    altura del Piso 1 no cambia la altura de sus muros.
  - `test_validacion_con_muros` (SC-005): `validate_file` da 0 errores.
  - `test_muro_numero_201_rapido` (SC-006): 50 recintos (200 muros) en un piso, y el muro 201 tarda < 0,2 s en
    `create_wall`, medido con `time.perf_counter`.

### Implementación de la Historia 1

- [X] T016 [US1] `create_wall` en `engine/bimsimple_engine/walls.py` y `commands.py`
  ([core_api.md](contracts/core_api.md); research R4):
  1. **Validaciones antes de la transacción**:
     - longitud ≥ 0,01;
     - `height` > 0;
     - Básica: `thickness` > 0 y el material existe;
     - compuesta: el tipo existe;
     - `reference` en `exterior`/`center`/`interior`.
  2. **En una transacción**, la receta de research R4:
     - `create_entity(name="Muro")`;
     - `assign_container(piso activo)`;
     - `assign_type` (una llamada), o el conjunto Básico de una capa (LayerSetName "Básica") +
       `assign_material(type="IfcMaterialLayerSetUsage", material=conjunto)`;
     - `edit_layer_usage(DirectionSense="NEGATIVE", OffsetFromReferenceLine=0, T/2 o T)`;
     - `create_2pt_wall(elevation=cota del piso activo)` + `assign_representation` (la matriz es absoluta y
       `edit_object_placement` la pasa a relativa al piso, `edit_object_placement.py:175-194`);
     - eje Plan/Axis;
     - `connect_wall` con cada id de `endpoint_index.near` en `start` y `end`, que no sea `custom_ends` ni `locked`;
     - `regenerate_wall_representation(length=1.0, height=Depth)` del nuevo y los unidos.
  3. Actualiza el índice.
  4. Devuelve `{state, wall_id, changed_ids}`.
- [X] T017 [P] [US1] Crear `app/src/renderer/toolbox.js`:
  - clase `Toolbox({onChange})`: clic en un botón activa esa herramienta;
  - `set(tool)` marca la activa (FR-001) y `enable(bool)` (desactivada sin proyecto).
- [X] T018 [P] [US1] Crear `app/src/renderer/infobox.js`, modo herramienta ([ui.md](contracts/ui.md) "Info Box"):
  - Campos:
    - **Estructura** (lista: "Básica" y después el catálogo; botón "…" con `title` "Estructuras compuestas…");
    - **Material** (lista de `state.materials`);
    - **Espesor (m)**;
    - **Altura (m)**;
    - **Línea de referencia**: tres botones, Exterior · Centro · Interior.
  - Números con `formatMeters`; al escribir se acepta coma o punto.
  - Valor inválido al salir del campo: vuelve el anterior y muestra "El espesor debe ser mayor que 0." / "La altura
    debe ser mayor que 0." en Mensajes.
  - Expone `toolValues()` → `{structure_id, material_id, thickness, height, reference}`.
  - **Altura**:
    - mientras el usuario no la cambie, sigue la del piso activo (FR-004; `followStoreyHeight`);
    - los demás valores se recuerdan mientras el programa esté abierto.
  - **Valores por defecto**: Básica, "Hormigón", 0,20, Exterior.
- [X] T019 [US1] Crear `app/src/renderer/wall-tool.js` ([ui.md](contracts/ui.md) "Dibujo"; research R12):
  - **Cadena**:
    - primer clic fija el inicio;
    - cada clic manda `onCreate(start, end)`;
    - el final pasa a ser el inicio siguiente;
    - un clic a menos de 10 px del primer punto crea el último muro hasta él y termina;
    - Esc o clic derecho terminan.
  - **Vista previa** en `viewports.overlay`:
    - `ShapeGeometry` de la franja del muro según la línea de referencia y el espesor del Info Box, con las líneas
      entre capas (`LineSegments`);
    - etiqueta de longitud en un `<div>` absoluto sobre la planta ("4,50 m").
  - **Shift**: ángulo al múltiplo de 45° más cercano.
  - **Imán**:
    - a menos de 10 px (`pixelsToMeters(10)`), primero los extremos de `meshes.walls(pisoActivo)` y después la grilla
      de 0,10 m, sobre la dirección fija si hay Shift;
    - marca: cuadrado para el extremo y cruz para la grilla.
  - **Teclado**:
    - dígitos, `,`, `.` y Retroceso arman "Longitud: …";
    - Enter crea el muro con esa longitud en la dirección del ratón;
    - una longitud inválida muestra "La longitud debe ser mayor que 0.".
  - Un muro < 1 cm no se manda.
  - `cancel()` termina la cadena.
- [X] T020 [US1] `app/src/renderer/app.js`:
  - crea `Toolbox`, `InfoBox` y `WallTool`;
  - la herramienta activa es `arrow` al crear o abrir un proyecto (FR-001);
  - `keydown` de la página: Esc, Enter, dígitos y Retroceso van a la herramienta activa; Supr se usa en US4;
  - `WallTool.onCreate` → `dispatch("create_wall", {start, end, ...infobox.toolValues()})`;
  - si falla, se muestra el error y la cadena sigue desde el mismo punto;
  - la cadena termina al cambiar de piso activo, de herramienta o de proyecto (`render`) y cuando el motor se
    reinicia;
  - en cada `render`, `meshes.setMaterials(state.materials)` y `infobox.render(state)`.
- [X] T021 [US1] Sección "Muros 1 — dibujar" en `app/test/window-test.js`. Simula el ratón con `PointerEvent` sobre
  `#plan-view` en `viewports.worldToClient(x, y)`.
  - **Preparación**: proyecto nuevo con pisos 0/3/6, Piso 1 activo y herramienta Muro.
  - **Info Box**: muestra "Básica", "Hormigón", "0,20", "3,00" y Exterior.
  - **Cadena**: 4 clics en (0,4), (6,4), (6,0) y (0,0), y un clic en (0,4) → 4 muros del Piso 1. La superficie en
    planta es 3,84 ± 0,1 % (SC-002): la suma de las áreas de los triángulos de las mallas de muro con normal +Z (las
    tapas de arriba).
  - **Cambiar de piso**: empezar una cadena, hacer doble clic en otro piso → la cadena terminó (el próximo clic
    empieza una nueva).
  - **Shift + longitud**: un muro empezado en (10,0), Shift con el ratón cerca de 44°, escribir `4,5` + Enter → muro
    de 4,50 m a 45°.
  - **Imán**: un clic a 5 px de un extremo existente → el muro empieza exactamente en el extremo.
  - **Rechazos**: Esc termina la cadena; un muro de 0,5 cm no se crea.
  - **Tiempo**: cada `create_wall` con su redibujo tarda < 200 ms (SC-006, con los muros de la prueba).
  - Captura `m1`.
- [X] T022 [US1] Correr las dos pruebas. Esperado: todo en verde, también la función 001. Commit "feat: Historia 1 de
  la función 002, dibujar muros".

**Punto de control**: el MVP de la función 002, con muros Básicos dibujados y unidos. Si el usuario quiere verlo,
prueba manual B1-B2 (⛔ abrir la ventana).

---

## Fase 4: Historia 2 — Muros compuestos por capas (Prioridad: P2)

**Objetivo**: elegir una estructura compuesta, ver las capas con sus colores y editar el catálogo.

**Prueba independiente**: dibujar con una estructura de 3 capas, guardar y comprobar en el IFC un solo muro con 3
capas en orden; editar la estructura cambia los muros que la usan.

### Pruebas de la Historia 2

- [X] T023 [US2] En `engine/tests/test_walls.py`:
  - `test_muro_compuesto`:
    - recinto con "Muro exterior 30" → cada muro tiene su propia usage y todas apuntan al mismo conjunto;
    - la malla tiene 4 grupos con los `material_id` de Revoque, Ladrillo, Aislación y Revoque;
    - la superficie en planta es (6 × 4 − 5,40 × 3,40) = 5,64 ± 0,1 %;
    - la primera capa (Revoque 0,02) queda afuera del recinto.
  - `test_apply_structures_reglas`, cada caso con su texto exacto de [core_api.md](contracts/core_api.md):
    - nombre vacío;
    - nombre repetido, sin distinguir mayúsculas;
    - sin capas;
    - capa con espesor 0 («La capa 2 de «X» tiene que tener un espesor mayor que 0.»);
    - borrar una estructura usada por 1 muro («La estructura «Muro exterior 30» la usa 1 muro; no se puede
      borrar.») y por 3 («la usan 3 muros»);
    - material repetido;
    - color inválido.

    En cada caso no cambia nada del IFC.
  - `test_apply_structures_crea_duplica_renombra_y_borra`:
    - crea "Muro 35" con un material nuevo (`ref`);
    - duplica "Tabique 15" (`copy_of`);
    - renombra "Muro de hormigón 25" (cambian el `Name` del tipo y el `LayerSetName`);
    - borra la duplicada sin muros;
    - todo en **un** paso de deshacer.
  - `test_editar_estructura_cambia_sus_muros`:
    - dos muros con "Muro exterior 30", uno con línea Exterior y otro con Centro;
    - se cambia Aislación 0,05 → 0,08;
    - los dos pasan a 0,33;
    - el de Exterior conserva la cara exterior en su línea y el de Centro queda centrado;
    - siguen unidos;
    - la validación da 0 errores.
  - `test_catalogo_guardado_y_reabierto`: los nombres, capas y colores reaparecen.

### Implementación de la Historia 2

- [X] T024 [US2] `apply_structures` en `engine/bimsimple_engine/materials.py` y `commands.py`
  ([core_api.md](contracts/core_api.md) "apply_structures"; research R11).
  1. **Validar todo antes de cambiar nada**:
     - nombres no vacíos y únicos sin distinguir mayúsculas, contra el catálogo resultante;
     - al menos una capa por estructura;
     - espesores > 0;
     - `material` existente o `ref` nueva;
     - `deleted` sin muros;
     - materiales nuevos con nombre único no vacío y color `#rrggbb`.
  2. **Aplicar en una transacción**:
     1. materiales nuevos;
     2. estructuras nuevas (`copy_of` → `material.copy_material(conjunto)` + tipo nuevo; si no, `create_structure`);
     3. estructuras cambiadas: rehacer las capas del conjunto con `edit_layer`, `add_layer`, `remove_layer` y
        `reorder_set_item` hasta coincidir, sin dejar nunca 0 capas; si cambió el nombre, `edit_attributes` del
        `Name` y del `LayerSetName`;
     4. borradas: `remove_material_set` + `root.remove_product(tipo)`;
     5. por cada muro de una estructura cambiada: `edit_layer_usage` con el desplazamiento de su referencia y el
        espesor nuevo (research R3), y `regenerate_wall_representation` de él y sus unidos.
  3. Devuelve `{state, changed_ids}`.
- [X] T025 [US2] Crear `app/src/renderer/structures-dialog.js` ([ui.md](contracts/ui.md) "Diálogo"):
  - trabaja sobre una copia de `state.structures` y `state.materials`;
  - Nueva ("Estructura N" con Hormigón 0,20), Duplicar («nombre» (copia)), Renombrar, Borrar (con el aviso de
    estructura en uso, calculado con `walls`);
  - tabla de capas con Agregar (Hormigón 0,10 debajo de la elegida), Quitar (no la única: "La estructura tiene que
    tener al menos una capa."), Subir y Bajar;
  - "Espesor total: X,XX m";
  - Nuevo material… con nombre y color;
  - Aceptar arma **un** `apply_structures` con lo creado, cambiado y borrado. Si el motor responde con error, el
    diálogo queda abierto con ese texto;
  - Cancelar o Esc cierran sin cambios.
- [X] T026 [US2] En `app/src/renderer/app.js` y `infobox.js`:
  - la acción de menú `structures` y el botón "…" abren el diálogo y, al aceptar, `dispatch("apply_structures",
    cambios)`;
  - en el Info Box, con una estructura compuesta: Material "—" desactivado y Espesor = suma de capas, desactivado;
  - si la estructura elegida deja de existir, vuelve a "Básica".
- [X] T027 [US2] Sección "Muros 2 — compuestos" en `app/test/window-test.js`:
  - elegir "Muro exterior 30" → Espesor "0,30" desactivado;
  - dibujar 2 muros encadenados → la malla tiene 4 grupos con los colores del catálogo;
  - **Opciones > Estructuras compuestas…** (vía `handleAction("structures")`):
    - crear "Muro de prueba" con 3 capas, Aceptar → aparece en la lista del Info Box;
    - renombrarla a "Muro exterior 30" → el error exacto en el diálogo;
  - editar la Aislación de "Muro exterior 30" a 0,08 → los muros dibujados pasan a 0,33;
  - Ctrl+Z vuelve a 0,30;
  - captura `m2`.
- [X] T028 [US2] Correr las dos pruebas y hacer el commit "feat: Historia 2 de la función 002, muros compuestos".

---

## Fase 5: Historia 3 — Separar un muro en capas (Prioridad: P3)

**Objetivo**: seleccionar muros compuestos y separarlos en muros de una capa sin que nada se mueva.

**Prueba independiente**: un muro de 4 capas se separa en 4 muros de una capa con el mismo material y espesor y el
mismo volumen total; Ctrl+Z lo devuelve.

### Pruebas de la Historia 3

- [X] T029 [US3] En `engine/tests/test_walls.py`:
  - `test_separar_en_capas` (SC-003), en un recinto "Muro exterior 30":
    - separar un muro → `deleted_ids` = [muro] y 4 `new_ids`;
    - materiales y espesores (Revoque 0,02, Ladrillo 0,20, Aislación 0,05 y Revoque 0,03, ± 1 mm);
    - suma de volúmenes OpenCASCADE = original ± 0,1 %;
    - los 2 vecinos tienen el mismo volumen que antes;
    - nombres «Muro — Revoque», etc.;
    - cada capa es `Básica` con referencia `exterior`;
    - las de la esquina son `custom_ends`;
    - "Muro exterior 30" sigue en `state.structures` aunque ya no la use ese muro;
    - validación 0.
  - `test_separar_deshacer_y_rehacer`: Ctrl+Z → vuelve el muro con sus 2 uniones; Ctrl+Y → las 4 capas.
  - `test_separar_varios_y_uno_de_una_capa`:
    - separar 2 muros compuestos y uno Básico en una orden → se separan los 2 y el Básico queda;
    - solo Básicos → "El muro ya tiene una sola capa.".
  - `test_no_se_une_a_una_capa_con_esquina_cortada`: dibujar desde el extremo de una capa `custom_ends` → no se crea
    la unión y esa capa conserva su volumen (spec, casos límite).
  - `test_separar_muro_de_otro_programa`: el "Muro con capas" de `muros_otro_programa` (POSITIVE) se separa en 2
    muros con el volumen total igual.

### Implementación de la Historia 3

- [X] T030 [US3] `split_walls` en `engine/bimsimple_engine/walls.py` y `commands.py` (research R8):
  - por cada muro con 2 o más capas que no sea `locked`:
    - polígonos de las capas;
    - por cada capa, un `IfcWall` «nombre — material» en el mismo piso, con un conjunto Básico de una capa;
    - usage con el mismo sentido y desplazamiento 0;
    - ubicación corrida en Y local hasta la cara exterior de la capa (la de mayor Y con NEGATIVE, la de menor Y con
      POSITIVE);
    - cuerpo con `ShapeBuilder.extrude(profile(polyline(polígono local corrido, closed=True)), magnitude=Depth)`;
    - eje Plan/Axis con la misma longitud;
  - después, `root.remove_product(original)`, y `remove_material_set` si era Básico;
  - todo en una transacción;
  - actualiza el índice;
  - devuelve `{state, deleted_ids, new_ids, changed_ids: new_ids}`.
- [X] T031 [US3] Crear `app/src/renderer/selection.js` ([ui.md](contracts/ui.md) "Selección"):
  - con la Flecha:
    - clic en la planta → `Raycaster` contra las mallas del piso activo;
    - clic sin arrastre en el 3D (`viewports.click3d`) → contra todas;
  - Shift + clic agrega o quita; clic en vacío o Esc vacían;
  - `ids()` y `set(ids)`;
  - `meshes.setSelected(ids)`;
  - después de cada respuesta del motor, `keepExisting(existingIds)`.
- [X] T032 [US3] En `app/src/renderer/infobox.js` y `app.js`, modo selección:
  - sin selección: "Nada seleccionado. Clic en un muro para seleccionarlo; Shift + clic para agregar o quitar.";
  - con selección:
    - título "1 muro seleccionado" / "N muros seleccionados";
    - campos con los valores, o "varios" si difieren (desactivados en esta historia);
    - botón **Separar en capas**, activo si algún seleccionado tiene 2 o más capas → `dispatch("split_walls", {ids})`
      → la selección pasa a `new_ids`;
  - Muro activa la herramienta y vacía la selección.
- [X] T033 [US3] Sección "Muros 3 — separar" en `app/test/window-test.js`:
  - recinto "Muro exterior 30";
  - Flecha y clic sobre un muro en la planta → Info Box "1 muro seleccionado" y "Separar en capas" activo;
  - un clic → 4 muros seleccionados y el volumen sin cambios (con la suma de `wall.thickness` × longitud × altura de
    los nuevos);
  - el contorno de la planta es igual: los extremos de los vecinos no cambian;
  - Ctrl+Z → 1 muro;
  - Ctrl+Y → 4;
  - captura `m3`.
- [X] T034 [US3] Correr las dos pruebas y hacer el commit "feat: Historia 3 de la función 002, separar en capas".

---

## Fase 6: Historia 4 — Seleccionar, cambiar y borrar muros (Prioridad: P4)

**Objetivo**: cambiar la altura, la estructura, el material y el espesor de los muros elegidos, y borrarlos.

**Prueba independiente**: separar un muro de 3 capas, subir solo la exterior a 3,60, borrar la interior, guardar y
reabrir: igual.

### Pruebas de la Historia 4

- [ ] T035 [US4] En `engine/tests/test_walls.py`:
  - `test_cambiar_altura`: una capa separada a 3,60 → volumen × 1,2 y misma esquina; los demás no cambian.
  - `test_cambiar_estructura`:
    - Básica → "Tabique 15" con línea Exterior → la cara exterior sigue en la línea, el espesor es 0,15 y los unidos
      se regeneran;
    - "Tabique 15" → Básica → conjunto propio de una capa (Hormigón 0,20).
  - `test_cambiar_material_y_espesor_de_un_basico`:
    - el material cambia la capa y no la forma;
    - el espesor 0,25 en un `regenerable` con referencia Centro queda centrado;
    - en un `custom_ends` prolonga los cortes (`extend_ends`): la cara exterior y las aristas de los extremos siguen
      sobre sus rectas.
  - `test_rechazos_al_cambiar`:
    - un `locked` → "BIM Simple no puede cambiar la forma de este muro (viene de otro programa).";
    - cambiar la estructura con referencia `other` → "Este muro tiene una línea de referencia que BIM Simple no
      maneja; solo se puede cambiar su altura y su material.";
    - altura 0;
    - muro inexistente → "Uno de los muros elegidos ya no existe.".

    Nada cambia.
  - `test_borrar_muros`:
    - borrar un muro de un recinto → los 2 vecinos se regeneran con el extremo recto y sin uniones hacia él;
    - se borra el conjunto Básico propio;
    - Ctrl+Z lo devuelve;
    - validación 0.
  - `test_cambios_guardados_y_reabiertos` (SC-004; Principio V): después de los cambios, guardar y volver a abrir →
    mismos `wall_info` y mismas uniones.
  - `test_muros_de_otro_programa_se_conservan` (FR-029): abrir `muros_otro_programa`, dibujar y borrar un muro,
    guardar y volver a abrir → los dos muros `locked` tienen la misma representación (mismas entidades del cuerpo y
    mismo volumen OpenCASCADE).
  - Primero comprobar `type.unassign_type` con un script corto (que quita el tipo y la usage queda sin conjunto) y
    anotarlo en research R9 (Principio IV).

### Implementación de la Historia 4

- [ ] T036 [US4] `edit_walls` y `delete_walls` en `engine/bimsimple_engine/walls.py` y `commands.py` (research R9;
  data-model §3, "Reglas de cambio"):
  - **Validar primero** (`locked`, `other`, valores > 0 y existencia), y aplicar todo en una transacción.
  - **Altura**: `edit_attributes(Depth)` del sólido.
  - **Estructura**:
    - `assign_type` + `edit_layer_usage` con la misma referencia y el espesor nuevo + regenerar el muro y sus unidos;
    - si era Básico, `remove_material_set` del conjunto propio;
    - a Básica: `type.unassign_type` + conjunto propio Hormigón 0,20, o el `material_id`/`thickness` que vengan.
  - **Material** (Básicos): `edit_layer(material=…)`.
  - **Espesor** (Básicos):
    - `edit_layer(LayerThickness)` + desplazamiento según la referencia;
    - `regenerable`: regenerar el muro y sus unidos;
    - `custom_ends`: `layers.extend_ends` y reemplazar el perfil del sólido (`ShapeBuilder`); si devuelve `None`,
      error "El espesor de esta capa no se puede cambiar porque su forma no es un tramo recto." (core_api.md).
  - **Borrar**:
    - `remove_product`;
    - `remove_material_set` del conjunto propio si no lo usa otro;
    - regenerar los vecinos que estaban unidos;
    - actualizar el índice.
- [ ] T037 [US4] En `app/src/renderer/infobox.js` y `app.js`:
  - en modo selección se habilitan Estructura, Material, Espesor y Altura con las reglas de [ui.md](contracts/ui.md):
    - Material y Espesor solo si todos los seleccionados son Básicos;
    - campos desactivados y aviso `locked_reason` si hay `locked`;
  - cada cambio manda **un** `edit_walls` con todos los ids;
  - el botón **Borrar** y la tecla Supr mandan `delete_walls`;
  - la Línea de referencia solo se muestra ("Otra" si es `other`).
- [ ] T038 [US4] Sección "Muros 4 — cambiar y borrar" en `app/test/window-test.js`:
  - separar un muro, elegir solo la capa exterior, Altura 3,60 → solo esa malla sube (su caja llega a 3,60 y las
    demás quedan en 3,00);
  - Shift + clic en otra capa → Altura "varios";
  - Supr → se borran las 2 elegidas;
  - Ctrl+Z las devuelve;
  - cambiar un muro a "Tabique 15" → espesor 0,15;
  - captura `m4`.
- [ ] T039 [US4] Correr las dos pruebas y hacer el commit "feat: Historia 4 de la función 002, cambiar y borrar
  muros".

---

## Fase 7: Pulido y cierre

- [ ] T040 Sección "Muros — rendimiento" en `app/test/window-test.js` (SC-006):
  - con 50 recintos creados por `dispatch("create_wall", …)` en un piso nuevo, un muro más con su redibujo tarda
    < 200 ms;
  - registrar el tiempo.
- [ ] T041 [P] Agregar a `PRUEBA_MANUAL.md` la sección "7. Muros con capas", con la parte B de
  [quickstart.md](quickstart.md) (B1-B6) en lenguaje simple y con casillas.
- [ ] T042 [P] Actualizar `README.md`:
  - el estado (funciones 001 y 002);
  - los módulos nuevos en "Estructura";
  - la línea de muros en "Qué es".
- [ ] T043 Anotar en `research.md` los tiempos medidos por las pruebas (crear, separar y redibujar), correr las dos
  pruebas completas y hacer el commit "docs: cierre de la función 002 (pruebas y documentos)".
- [ ] T044 ⛔ PERMISO: pedir permiso para abrir BIM Simple con ventana (`npm --prefix app start`). El usuario hace la
  parte B de [quickstart.md](quickstart.md):
  - los tiempos de SC-001 y SC-007;
  - abrir el IFC en otro programa BIM (SC-005).

  Anotar sus resultados y corregir lo que falle, con su prueba automática.
- [ ] T045 Marcar `**Estado**: Implementada` en [spec.md](spec.md), comprobar que todas las tareas están marcadas y
  hacer el commit final con los resultados de T044.
- [ ] T046 ⛔ PERMISO: pedir permiso para subir los commits a GitHub (`git push origin main`).

---

## Dependencias y orden de ejecución

### Dependencias entre fases

- **Fase 1**: sin dependencias.
- **Fase 2 (Base)**: depende de la Fase 1. **Bloquea todas las historias.**
- **US1 (Fase 3)**: depende de la Fase 2.
- **US2 (Fase 4)**: depende de US1, porque dibuja muros compuestos con la misma herramienta. Sus pruebas del motor
  (T023) solo necesitan `create_wall`.
- **US3 (Fase 5)**: depende de US2, porque separa muros compuestos. Trae la selección.
- **US4 (Fase 6)**: depende de US3: usa la selección y las capas separadas.
- **Fase 7**: depende de todas. T044 y T046 necesitan permiso.

### Dentro de cada historia

- Primero las pruebas del motor (fallan), después el motor, después la interfaz, después la sección de la prueba del
  programa, y al final las dos pruebas y el commit.
- `walls.py`, `app.js`, `infobox.js`, `test_walls.py` y `window-test.js` se tocan en varias tareas, así que van **en
  orden**.

### Oportunidades de paralelo

- **Fase 1**: T002.
- **Fase 2**: T005, T008, T010, T011 y T012 (archivos distintos), después de T003-T004.
- **Fase 3**: T017 y T018, en paralelo con T016.
- **Fase 7**: T041 y T042.

## Ejemplo de paralelo: Fase 2

```text
Tarea: "T005 [P] Geometría de capas en engine/bimsimple_engine/layers.py"
Tarea: "T008 [P] IFC de otro programa en engine/tests/make_fixtures.py"
Tarea: "T010 [P] Pantalla en app/src/renderer/index.html y styles.css"
Tarea: "T011 [P] Mallas con grupos en app/src/renderer/meshes.js"
Tarea: "T012 [P] Vistas en app/src/renderer/viewports.js"
```

## Estrategia de implementación

### MVP primero (Historia 1)

1. Fases 1 y 2.
2. Fase 3 (US1).
3. **Detenerse y validar**: las dos pruebas en verde. Si el usuario quiere, prueba manual B1-B2 (⛔ ventana).

### Entrega incremental

US2 → US3 → US4 → Fase 7. Cada historia termina con todas las pruebas en verde, las de la función 001 incluidas, y
un commit.

## Notas

- Puntos ⛔: T044 (ventana y prueba manual) y T046 (subir a GitHub).
- No hay descargas ni instalaciones (research R14).
- FR-023 de la función 001 ("los elementos nuevos quedan en el piso activo") se verifica en T015 y T021.
- No borrar archivos sin permiso.
