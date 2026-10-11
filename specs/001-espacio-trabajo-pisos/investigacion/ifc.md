# Investigación: API real de Bonsai 0.9.0 / IfcOpenShell para proyecto y pisos

Fase de plan de `specs/001-espacio-trabajo-pisos` (FR-007 a FR-023). Todo se verificó en el código
instalado y, cuando se pudo, ejecutando Blender **solo con `--background`**.

## Entorno y convenciones

| Qué | Valor comprobado |
|---|---|
| Blender | 5.2.0 LTS (hash fbe6228777e7), `bpy.app.background = True` en todas las pruebas |
| Bonsai | 0.9.0 (`tool.Blender.get_bonsai_version()`), se carga solo con `--background` (está activo en las preferencias) |
| IfcOpenShell | 0.9.0 |

- **✅** = ejecutado en Blender 5.2 en segundo plano y comprobado (salida real abajo). **📖** = solo leído en el código.
- Rutas `archivo:línea` relativas a
  `%APPDATA%\Blender Foundation\Blender\5.2\extensions\.local\lib\python3.13\site-packages\`.
- Scripts y salidas: `scratchpad\research\ifc\`:
  - `e2e_pisos.py` (prueba de punta a punta) → `out_e2e_full.txt`
  - `_recetas.py` (recetas candidatas que usan todas las pruebas; **no** es código del producto)
  - `probe_project.py`, `probe_move_delete.py`, `probe_load_save.py`, `probe_undo.py`,
    `probe_clear_undo.py`, `probe_misc.py`, `make_test_ifcs.py` → `out_*.txt`
  - IFC de prueba en `out\` (incluye IFC "de otro programa" en milímetros, con dos edificios,
    sin pisos, sin edificio, dañado, no IFC y uno roto para la validación).
- Configuración del usuario: se copiaron los `.txt` y `userpref.blend` de
  `%APPDATA%\Blender Foundation\Blender\5.2\config` a `research\ifc\config_backup\` antes de probar.
  Al terminar, los MD5 de los 5 archivos son **idénticos** a los de antes (no hubo que restaurar
  nada): todas las llamadas a `load_project`/`save_project` usaron `skip_recent=True`.

---

## Tema 1. Proyecto nuevo sin reiniciar

| Necesidad | Función / operador | Archivo:línea | Probado |
|---|---|---|---|
| Unidades métricas en metros | `scene.unit_settings.system="METRIC"`, `length_unit="METERS"`, `scale_length=1.0` (Bonsai las convierte a `IfcSIUnit METRE` en `project.run_unit_assign_scene_units`) | `bonsai/core/project.py:55` | ✅ (`IfcSIUnit(LENGTHUNIT, METRE)`, `SQUARE_METRE`, `CUBIC_METRE`) |
| Esquema IFC4 | `tool.Project.get_project_props().export_schema = "IFC4"` y `template_file = "0"` (ya son los valores por defecto) | `bonsai/bim/module/project/operator.py:152-163` | ✅ |
| Crear proyecto | `bpy.ops.bim.create_project()` | `bonsai/bim/module/project/operator.py:137-138` | ✅ |
| No usar | `bpy.ops.bim.new_project` → `bpy.ops.wm.read_homefile()` | `bonsai/bim/module/project/operator.py:88, 98` | 📖 |
| **create_project no hace nada si ya hay un IFC abierto** | `if ifc.get(): return` | `bonsai/core/project.py:35` | ✅ (2ª llamada: mismo archivo, 1 piso) |
| Jerarquía creada | `create_empty("My Project"/"My Site"/"My Building"/"My Storey")` + `aggregate_assign_object` | `bonsai/core/project.py:49-52, 100-102` | ✅ |
| Piso activo inicial | `spatial.guess_default_container()` → primer piso | `bonsai/core/project.py:106` | ✅ |
| Si la escena es la de fábrica (cubo, luz, cámara) la vacía | `tool.Blender.is_default_scene()` | `bonsai/tool/blender.py:226`, `operator.py:155-161` | ✅ |
| Renombrar Proyecto/Sitio/Edificio | `ifcopenshell.api.attribute.edit_attributes(f, product=e, attributes={"Name": ...})` + `tool.Root.set_object_name(obj, e)` + `tool.Collector.assign(obj)` | `ifcopenshell/api/attribute/edit_attributes.py:26`, `bonsai/tool/root.py:432`, `bonsai/tool/collector.py:29` | ✅ |
| Renombrar el piso | `tool.Spatial.edit_container_name(piso, nombre)` (+ las dos líneas de arriba): es exactamente lo que hace el navegador de Bonsai en `update_name` | `bonsai/tool/spatial.py:605`, `bonsai/bim/module/spatial/prop.py:92` | ✅ |
| Descargar el proyecto actual sin `read_homefile` | No hay operador de Bonsai para cerrar. Receta propia `_recetas.close_project()`: borrar objetos y colecciones IFC, `bim_props.ifc_file=""`, `default_container=0`, `IfcStore.purge()`, `bonsai.bim.handler.refresh_ui_data()` | `bonsai/bim/ifc.py:89` (purge) | ✅ (quedan 0 objetos y solo la colección "Collection"; el nuevo proyecto sale bien) |
| Limpiar el deshacer de Blender + Bonsai + IfcOpenShell | `tool.Blender.clear_undo_history()` (Bonsai lo usa en `bim.select_ifc_file` al cambiar de IFC sin sesión nueva) | `bonsai/tool/blender.py:2311`, `bonsai/bim/operator.py:230` | ✅ en background (IfcStore.history 2→0, historial ifcopenshell 1→0); la parte de Blender 📖 |

Salida real (`out_probe_project.txt`):

```
Objetos al arrancar: ['Camera', 'Cube', 'Light'] is_default_scene: True
Por defecto: export_schema = IFC4 | template_file = '0'
create_project -> {'FINISHED'}
schema: IFC4 | unit_scale: 1.0
#1 IfcProject 'My Project'
  #27 IfcSite 'My Site'
    #33 IfcBuilding 'My Building'
      #39 IfcBuildingStorey 'My Storey' Elevation=None placementZ=0.0 GrossHeight=None
  IfcBuildingStorey: obj=IfcBuildingStorey/My Storey collection=IfcBuildingStorey/My Storey loc=(0.0, 0.0, 0.0)
scene.BIMSpatialDecompositionProperties.default_container = 39
create_project 2ª vez -> mismo archivo: True | pisos: 1 -> 1
  renombrado IfcProject: IFC='Proyecto' obj='IfcProject/Proyecto' collection='IfcProject/Proyecto' is_renaming=True
  renombrado IfcBuildingStorey: IFC='Planta Baja' obj='IfcBuildingStorey/Planta Baja' collection='IfcBuildingStorey/Planta Baja' is_renaming=True
```

**Decisión 1.1 — Nuevo proyecto = unidades + IFC4 + `bim.create_project` + renombrar.**
- Por qué: es el único camino de Bonsai que no llama a `read_homefile`; deja Proyecto > Sitio >
  Edificio > piso con contextos, unidades y piso activo.
- Alternativas: `bim.new_project(preset="metric_m")` (hace lo mismo pero reinicia la sesión con
  `read_homefile`); armar el IFC a mano con `ifcopenshell.api` (habría que replicar
  `core/project.py:27-117`: contextos, objetos de Blender, colecciones).
- Evidencia: salida de arriba; `e2e_pisos.py` pasos 1 (esquema IFC4, metros, nombres).

**Decisión 1.2 — "Nuevo proyecto" con otro proyecto abierto: hay que descargar antes.**
- Por qué: `create_project` sale sin hacer nada si `tool.Ifc.get()` devuelve un archivo
  (`core/project.py:35`). Además, el deshacer de Blender queda con pasos del proyecto anterior: un
  Ctrl+Z después de "Nuevo" o "Abrir" restauraría objetos viejos que Bonsai volvería a enlazar por id
  (`handler.py:333-340`, `rebuild_element_maps`) con el archivo nuevo. Hay que llamar a
  `tool.Blender.clear_undo_history()` después de crear o abrir, como hace Bonsai en `bim.select_ifc_file`.
- Alternativas: (a) `read_homefile` (camino de Bonsai: limpia todo, también el deshacer). Con el
  Blender propio de BIM Simple recargaría **el startup.blend de BIM Simple**, no el del usuario; si la
  investigación de interfaz confirma que la pantalla de BIM Simple se reconstruye en `load_post`, es
  la opción más robusta. (b) La receta `close_project()` + `clear_undo_history()`, que evita recargar
  la interfaz. Recomiendo (b) y dejar (a) como plan B.
- Evidencia: `probe_load_save.py` sección B (✅); `probe_clear_undo.py` (✅ parte IFC). La parte del
  deshacer de Blender no se puede probar sin ventana (📖, ver Tema 7).

---

## Tema 2. Pisos: crear, renombrar, cota, altura

| Necesidad | Función / operador | Archivo:línea | Probado |
|---|---|---|---|
| Crear piso bajo el edificio | `bpy.ops.bim.add_part_to_object("EXEC_DEFAULT", element=<id edificio>, part_class="IfcBuildingStorey", part_name=...)`. Es `tool.Ifc.Operator`; llama a `core.aggregate.add_part_to_object` y luego `import_spatial_decomposition`. No devuelve el piso: se busca por diferencia de ids. Deja al edificio como objeto activo (`core/aggregate.py:87`). | `bonsai/bim/module/aggregate/operator.py:348-370`, `bonsai/core/aggregate.py:76` | ✅ |
| Nombre repetido | `tool.Blender.get_name` agrega " 2" al nombre del **objeto y del IFC** ("Piso 1 2"). Hay que renombrar después con `edit_container_name`. | `bonsai/tool/blender.py:234-240` | ✅ |
| Ubicación inicial del piso nuevo | cota 0, relativa al edificio (`PlacementRelTo` = ubicación del edificio); `Elevation = None` | — | ✅ |
| Renombrar | `tool.Spatial.edit_container_name` + `tool.Root.set_object_name` + `tool.Collector.assign` (= `spatial/prop.py:update_name`) | `bonsai/tool/spatial.py:605`, `bonsai/bim/module/spatial/prop.py:92-100` | ✅ |
| Cota (ubicación) | Ver Tema 3: `ifcopenshell.api.geometry.edit_object_placement(f, product=piso, matrix=tool.Surveyor.get_absolute_matrix(obj), should_transform_children=True)` | `ifcopenshell/api/geometry/edit_object_placement.py:33`, `bonsai/tool/surveyor.py:31` | ✅ |
| Atributo `Elevation` | Bonsai **nunca** lo escribe (ni al crear ni en `update_elevation`). `ifcopenshell.api.attribute.edit_attributes(f, product=piso, attributes={"Elevation": z_relativa_al_edificio / unit_scale})` | `ifcopenshell/api/attribute/edit_attributes.py:26` | ✅ |
| Leer la cota | `ifcopenshell.util.placement.get_storey_elevation(piso) * unit_scale`: Z **absoluta** de la ubicación; si no hay ubicación, `Elevation`. Es lo que usa el navegador de Bonsai para mostrar y ordenar. | `ifcopenshell/util/placement.py:191-203`, `bonsai/tool/spatial.py:541, 551` | ✅ |
| Altura (escribir) | `ifcopenshell.api.pset.add_qto(f, product=piso, name="Qto_BuildingStoreyBaseQuantities")` (solo si no existe) + `edit_qto(f, qto=qto, properties={"GrossHeight": h / unit_scale})` | `ifcopenshell/api/pset/add_qto.py:26`, `ifcopenshell/api/pset/edit_qto.py:38` | ✅ |
| Altura (leer) | `ifcopenshell.util.element.get_psets(piso, qtos_only=True)["Qto_BuildingStoreyBaseQuantities"]["GrossHeight"]` | `ifcopenshell/util/element.py:167` | ✅ |
| Plantilla IFC4 del Qto | `GrossHeight`, `NetHeigtht` (sic, error de la plantilla), `GrossPerimeter`, `GrossFloorArea`, `NetFloorArea`, `GrossVolume`, `NetVolume`. `Pset_BuildingStoreyCommon` **no** tiene altura. | `ifcopenshell/util/pset.py:32` (`get_template("IFC4")`) | ✅ |
| Unidades del archivo | `ifcopenshell.util.unit.calculate_unit_scale(f)` (0.001 en el IFC en milímetros) | `ifcopenshell/util/unit.py:873` | ✅ |

**Decisión 2.1 — Altura = distancia al piso de arriba; GrossHeight solo para el más alto.**
- Por qué: FR-016 define la altura como la distancia al piso de arriba. IFC4 no tiene atributo de
  altura en `IfcBuildingStorey`; la única fuente estándar es `Qto_BuildingStoreyBaseQuantities.GrossHeight`
  (`NetHeight` es altura libre, no sirve). Un IFC de otro programa puede no tenerlo o tener otro valor.
- Regla de lectura: para cada piso menos el más alto, altura = cota del siguiente − cota propia;
  para el más alto, `GrossHeight` si existe, si no 3,00. Regla de escritura: BIM Simple escribe
  `GrossHeight` en todos los pisos que crea o cambia, igual al valor mostrado, para que el IFC quede
  coherente.
- Alternativas: leer siempre `GrossHeight` primero (lo hacía el MVP, `core.py:get_storey_height`); se
  contradice con FR-016 cuando el archivo trae un valor distinto a la distancia real.
- Evidencia (`out_probe_load_save_full.txt`, IFC en mm sin Qto, pisos desordenados):
  ```
  [otro_programa_mm] edificios=['Torre'] pisos(1er edificio)=[('Subsuelo', -2.8, -2800.0, 2.8), ('Nivel 0', 0.0, 0.0, 3.2), ('Nivel 1', 3.2, 3200.0, 2.8), ('Nivel 2', 6.0, 6000.0, 3.0)] | unit_scale=0.001
  ```

**Decisión 2.2 — Crear pisos con `bim.add_part_to_object` y renombrar si Bonsai agregó " 2".**
- Por qué: es el camino de la interfaz de Bonsai; crea el `IfcBuildingStorey`, su objeto vacío, su
  colección y la agregación al edificio en una sola transacción deshacible.
- Alternativas: `bonsai.core.aggregate.add_part_to_object(...)` directo (interno, mismo efecto, sin
  transacción propia); `ifcopenshell.api.root.create_entity` + `aggregate.assign_object` (no crea el
  objeto ni la colección de Blender).
- Evidencia: `probe_project.py` (`Nombre repetido: ... ('Piso 1 2', 'IfcBuildingStorey/Piso 1 2')`).

---

## Tema 3. Mover un piso (cambiar su cota) con sus elementos

| Necesidad | Función / operador | Archivo:línea | Probado |
|---|---|---|---|
| ¿Las ubicaciones de los elementos son relativas al piso? | **Sí.** `spatial.assign_container` reubica al elemento relativo al contenedor; `edit_object_placement` usa `ContainedInStructure[0].RelatingStructure.ObjectPlacement` como `PlacementRelTo` | `ifcopenshell/api/spatial/assign_container.py:165-173`, `ifcopenshell/api/geometry/edit_object_placement.py:141-142` | ✅ (muro de `DumbWallGenerator` y columna de `assign_class`: `localZ=0.0 PlacementRelTo=Piso 1`) |
| Cómo mueve un piso Bonsai | `obj.matrix_world[2][3] = z` + `bonsai.core.geometry.edit_object_placement(...)`, que llama `ifc.run("geometry.edit_object_placement", ...)` **sin** `should_transform_children` (por defecto `False`) | `bonsai/bim/module/spatial/prop.py:48-89`, `bonsai/core/geometry.py:31-51` | ✅ |
| Efecto de lo anterior | Con `False` IfcOpenShell **reescribe la ubicación local de los hijos para que no se muevan** (`localZ=-0.5`). En Blender tampoco se mueven (no hay parentesco). | `ifcopenshell/api/geometry/edit_object_placement.py:54-59, 86-88, 147-173` | ✅ |
| Mover el piso **con** sus elementos (IFC) | `ifcopenshell.api.geometry.edit_object_placement(f, product=piso, matrix=M, is_si=True, should_transform_children=True)`: los hijos conservan su ubicación relativa y se mueven | `ifcopenshell/api/geometry/edit_object_placement.py:33-39` | ✅ |
| Mover los objetos de Blender | Para el piso y cada elemento de `ifcopenshell.util.element.get_decomposition(piso)` con objeto: `obj.matrix_world.translation.z += delta` y `tool.Geometry.record_object_position(obj)` (si no, `bim.save_project` los ve "movidos" y los vuelve a escribir) | `ifcopenshell/util/element.py:1144`, `bonsai/tool/geometry.py:1441`, `bonsai/tool/ifc.py:107` (`is_moved`), `bonsai/bim/export_ifc.py:99-129` | ✅ |
| Matriz absoluta correcta aun con origen desplazado | `tool.Surveyor.get_absolute_matrix(obj)` (descuenta el "blender offset" de modelos georreferenciados) | `bonsai/tool/surveyor.py:31-50` | ✅ (sin offset) |

Salida real (`out_probe_move_delete_full.txt`):

```
== 2. Mover Piso 1 de 3,00 a 3,50 como lo hace Bonsai (spatial/prop.py:update_elevation) ==
   IfcBuildingStorey 'Piso 1': IFC worldZ=3.5 localZ=3.5 PlacementRelTo=Edificio | Blender z=3.5 is_moved=False
   IfcWall 'Wall': IFC worldZ=3.0 localZ=-0.5 PlacementRelTo=Piso 1 | Blender z=3.0 is_moved=False
   IfcColumn 'Columna P1': IFC worldZ=3.0 localZ=-0.5 PlacementRelTo=Piso 1 | Blender z=3.0 is_moved=False
== 3. Mover Piso 2 de 6,00 a 6,50 con la receta (should_transform_children=True + objetos) ==
   IfcBuildingStorey 'Piso 2': IFC worldZ=6.5 localZ=6.5 PlacementRelTo=Edificio | Blender z=6.5 is_moved=False
   IfcColumn 'Columna P2': IFC worldZ=6.5 localZ=0.0 PlacementRelTo=Piso 2 | Blender z=6.5 is_moved=False
   IfcWall 'Wall': IFC worldZ=6.5 localZ=0.0 PlacementRelTo=Piso 2 | Blender z=6.5 is_moved=False
   Elevation de Piso 2: 6.5
== 4. Guardar con bim.save_project (sincroniza objetos movidos) y comparar ==
   (mismos valores después de guardar: Bonsai no reescribe nada)
```

**Decisión 3.1 — Función propia `set_storey_elevation(piso, cota)` (ver `_recetas.py`).**
1. `delta = cota − obj.matrix_world.translation.z`; 2. `obj.matrix_world.translation.z = cota`;
3. `ifcopenshell.api.geometry.edit_object_placement(f, product=piso, matrix=tool.Surveyor.get_absolute_matrix(obj), is_si=True, should_transform_children=True)`;
4. `record_object_position(obj)`; 5. para cada objeto de `get_decomposition(piso)`: `z += delta` y
`record_object_position`; 6. `edit_attributes(Elevation = (cota − z_edificio) / unit_scale)`.
Para FR-016 se llama de arriba hacia abajo sobre el piso y todos los de arriba, y se ajusta el
`GrossHeight` del piso de abajo.
- Por qué: es la única forma verificada de que piso y elementos se muevan juntos en el IFC y en
  Blender, sin que el guardado de Bonsai deshaga el movimiento.
- Alternativas: (a) camino de Bonsai + mover cada elemento con `core.geometry.edit_object_placement`
  (dos escrituras por elemento, mismo resultado); (b) mover solo los objetos de Blender y dejar que
  `bim.save_project` sincronice (el IFC queda desactualizado hasta guardar y `write()` no sincroniza).
- Evidencia: secciones 2-4 de arriba y `e2e_pisos.py` paso 4.

---

## Tema 4. Borrar un piso

| Necesidad | Función / operador | Archivo:línea | Probado |
|---|---|---|---|
| Borrar el contenedor | `bonsai.core.spatial.delete_container(tool.Ifc, tool.Spatial, tool.Geometry, piso)` → `tool.Geometry.delete_ifc_object(obj)` → `ifcopenshell.api.root.remove_product` | `bonsai/core/spatial.py:158-165`, `bonsai/tool/geometry.py:453, 548`, `ifcopenshell/api/root/remove_product.py:30` | ✅ |
| `bim.delete_container` (operador) | su `poll` exige `active_container` de la lista de Bonsai → no sirve desde BIM Simple | `bonsai/bim/module/spatial/operator.py:378-397` | 📖 |
| Qué pasa con los elementos | **Quedan huérfanos**: siguen en el IFC sin contenedor (se borra el `IfcRelContainedInSpatialStructure`), su `PlacementRelTo` apunta a la ubicación del piso borrado, que queda suelta porque tiene inversos; sus objetos de Blender pasan a la colección del edificio | `ifcopenshell/api/root/remove_product.py:70-75, 159-164`, `bonsai/tool/geometry.py:507-526` | ✅ |
| Qué pasa con el piso activo | si el piso borrado era el contenedor por defecto, pasa a ser **el edificio** (no otro piso) | `bonsai/tool/geometry.py:512-514` | ✅ |
| Contar elementos para el aviso (FR-017) | `[e for e in ifcopenshell.util.element.get_decomposition(piso) if e.is_a("IfcElement") and not e.is_a("IfcFeatureElementSubtraction")]` (contenidos, partes, rellenos; sin aberturas). `get_contained` solo da los contenidos directos. | `ifcopenshell/util/element.py:1144, 1447` | ✅ |
| Borrar los elementos con el piso | para cada elemento de `get_decomposition(piso)` sin aberturas: `tool.Geometry.delete_ifc_object(obj)` (si no tiene objeto, `ifcopenshell.api.root.remove_product`); después `delete_container` | ídem | ✅ |
| Alternativa de Bonsai con selección | `bim.override_object_delete` (borra los objetos seleccionados; además borra agregados vacíos) | `bonsai/bim/module/geometry/operator.py:808-985` | 📖 |

Salida real:

```
== 5. Contar contenido y borrar Piso 3 SOLO con delete_container ==
   get_contained(Piso 3): ['Columna P3'] | count: 1
   Columna P3 sigue en el IFC: IfcColumn | contenedor: None | PlacementRelTo: #142 (huérfano) | worldZ: 9.0
   Objeto Blender: IfcColumn/Columna P3 | colecciones: ['IfcBuilding/Edificio', 'Scene Collection']
== 6. Borrar Piso 2 con su contenido (receta) ==
   aviso: el piso tiene 2 elementos
   IfcElement: 5 -> 3
   objetos borrados de Blender: ['IfcBuildingStorey/Piso 2', 'IfcColumn/Columna P2', 'IfcWall/Wall.001']
   Pisos: ['Planta Baja', 'Piso 1'] | contenedor por defecto: IfcBuilding Edificio
== 7. Borrar el piso activo: ¿a qué pasa el contenedor por defecto? ==
   contenedor por defecto tras borrar el activo: IfcBuilding Edificio
```

(La "Scene Collection" es un efecto de la prueba: el cubo se enlazó ahí antes de `assign_class`.)

**Decisión 4.1 — `delete_storey(piso)` = borrar contenido con `delete_ifc_object` + `delete_container` + activar el piso de abajo.**
- Por qué: `delete_container` solo deja elementos huérfanos (rompe el Principio I) y deja como
  contenedor por defecto al edificio; los casos límite piden activar el piso inferior (o el superior).
- Alternativas: reasignar los elementos a otro piso (no es lo que pide FR-017); `bim.override_object_delete`
  (depende de la selección y borra agregados vacíos).
- Evidencia: secciones 5-7 y `e2e_pisos.py` paso 5.

---

## Tema 5. Piso activo (contenedor por defecto)

| Necesidad | Función / operador | Archivo:línea | Probado |
|---|---|---|---|
| Activar | `tool.Spatial.set_default_container(piso)` (también activa la colección del piso en la capa de vista) | `bonsai/tool/spatial.py:1282-1298` | ✅ |
| Leer | `tool.Root.get_default_container()` (si el id ya no existe, lo pone en 0 y devuelve None) | `bonsai/tool/root.py:139-146` | ✅ |
| Dónde se guarda | **En la escena de Blender, no en el IFC**: `scene.BIMSpatialDecompositionProperties.default_container` (entero = id de la entidad) | `bonsai/bim/module/spatial/prop.py:276`, `bonsai/bim/module/spatial/__init__.py:66`, `bonsai/tool/spatial.py:64` | ✅ (`= 39`) |
| Uso al crear elementos | `core.root.assign_class` contiene el elemento en `root.get_default_container()` | `bonsai/core/root.py:97-101` | ✅ |
| Al abrir un IFC | el cargador llama `guess_default_container()`: **el primer piso del primer edificio según el orden de `IfcRelAggregates.RelatedObjects`**, no por cota | `bonsai/bim/import_ifc.py:306-307`, `bonsai/tool/spatial.py:1301-1315` | ✅ (abrió con "Piso 2" en un archivo de BIM Simple y con "Subsuelo" en el de otro programa) |

**Decisión 5.1 — BIM Simple fija el piso activo él mismo** después de crear, abrir y borrar
(cota más cercana a 0,00 al abrir, FR-008; inferior/superior al borrar). El valor vive en la escena,
lo que coincide con el Principio III ("piso activo" = ajuste de interfaz).
- Alternativas: confiar en `guess_default_container` (orden arbitrario, ver evidencia).
- Evidencia: `out_probe_load_save_full.txt`, secciones C y D.

---

## Tema 6. Abrir, guardar, guardar como, ruta y cambios sin guardar

| Necesidad | Función / operador | Archivo:línea | Probado |
|---|---|---|---|
| Abrir | `bpy.ops.bim.load_project(filepath=..., should_start_fresh_session=False, skip_recent=True, skip_autosave_recovery=True)`. Con `should_start_fresh_session=True` (por defecto) llama a `wm.read_homefile` y termina en `load_post`. | `bonsai/bim/module/project/operator.py:958-1176` (`975`, `1118-1127`) | ✅ (ambos modos funcionan en background) |
| Con `should_start_fresh_session=False` | primero llama `bim.convert_to_blender`: **deja los objetos del proyecto anterior como objetos de Blender sin IFC** → hay que descargar antes con `close_project()` | `operator.py:1141-1142`, `bonsai/bim/module/debug/operator.py:97-120` | ✅ |
| Lista de recientes | `load_project`/`save_project` escriben `config\recent-ifc-projects.txt` salvo con `skip_recent=True` | `operator.py:991, 1168-1169, 1989, 2126-2127`, `bonsai/tool/project.py:240, 284` | ✅ (MD5 sin cambios) |
| Archivo dañado | `load_project` lanza `RuntimeError` ("Error loading IFC file...") **después** de haber descargado el proyecto anterior y deja `bim_props.ifc_file` apuntando al archivo malo (`IfcStore.get_file` reintenta cargarlo en cada `tool.Ifc.get()`) | `operator.py:1144-1150`, `bonsai/bim/ifc.py:108-119` | ✅ |
| Comprobar antes de descargar (FR-011) | `ifcopenshell.open(ruta)` en `try`: "Unable to parse IFC SPF header" o `FileNotFoundError`; luego exigir `by_type("IfcProject")` (Bonsai también lo exige, `operator.py:1151-1158`) | `ifcopenshell/__init__.py:166` | ✅ |
| Guardar | `bpy.ops.bim.save_project(filepath=..., skip_recent=True)`; sin `filepath` usa `bim_props.ifc_file` | `operator.py:1976-2152` (`2055-2062` respaldo de ruta) | ✅ |
| Qué hace además de escribir | sincroniza objetos movidos (`IfcExporter.sync_all_objects`), pone la cabecera (nombre, fecha, "Bonsai 0.9.0"), fija la ruta y `is_dirty=False` | `bonsai/bim/export_ifc.py:43-59, 72-78`, `operator.py:2122-2134` | ✅ |
| Guardar como | la misma llamada con otra `filepath`: la ruta pasa al archivo nuevo y los siguientes "Guardar" van ahí. En la interfaz, `should_save_as=True` abre el selector (`invoke`). | `operator.py:1988, 2013-2023, 2133` | ✅ (ruta y `header.file_name.name` = `guardado_como.ifc`) |
| `write()` directo | `tool.Ifc.get().write(ruta)` **no** sincroniza objetos movidos ni actualiza la cabecera (`FILE_NAME('/dev/null', ...)`), ni la ruta ni `is_dirty` | `ifcopenshell/file.py:880` | ✅ |
| Ruta actual | `tool.Ifc.get_path()` (= `IfcStore.path`) y `scene.BIMProperties.ifc_file`; se fija con `tool.Ifc.set_path` | `bonsai/tool/ifc.py:81-89`, `bonsai/bim/prop.py:605` | ✅ |
| Cambios sin guardar | `scene.BIMProperties.is_dirty`: lo pone en `True` **todo** `tool.Ifc.Operator` (al empezar), lo pone en `False` `save_project`. No lo cambian: `create_project`, `load_project`, llamadas directas a `ifcopenshell.api`, deshacer. | `bonsai/bim/prop.py:600`, `bonsai/bim/ifc.py:396-398`, `operator.py:2134` | ✅ |
| Autoguardado de Bonsai | desactivado por defecto (`autosave_enabled=False`); si existiera `<nombre>_autosaved.ifc` más nuevo, `load_project` abre un diálogo salvo `skip_autosave_recovery=True` | `bonsai/bim/ui.py:589-592`, `operator.py:1047-1068`, `bonsai/tool/autosave.py:156` | 📖 |

Salida real (`out_probe_load_save_full.txt`, rutas acortadas a `<R>`):

```
[tras new_project] path='' is_dirty=False history=1 default_container=('IfcBuildingStorey', 'Planta Baja')
[tras add_storey (operador IFC)] is_dirty=True history=2
[tras ifcopenshell.api directo (sin operador)] is_dirty=False history=2      <- no lo marca
save_project -> {'FINISHED'}
[tras save_project(filepath)] path='<R>/out/guardado_1.ifc' is_dirty=False
save_project sin filepath -> {'FINISHED'}            (escribió en guardado_1.ifc: ['Planta Baja', 'Piso 1', 'Piso 2'])
[tras 'Guardar como'] path='<R>/out/guardado_como.ifc' is_dirty=False
header.file_name.name: guardado_como.ifc
[tras close_project] file=no path='' objetos=0 colecciones=1
ifcopenshell.open(danado.ifc) -> ERROR Error: Unable to parse IFC SPF header
ifcopenshell.open(no_existe.ifc) -> ERROR FileNotFoundError: Path does not exist: ...
load_project lanzó RuntimeError Error: Error loading IFC file from filepath '<R>/out/no_es_ifc.ifc'. ...
[tras load dañado] file=no path='<R>/out/no_es_ifc.ifc' ... objetos=0
```

**Decisión 6.1 — Guardar siempre con `bim.save_project`** (también "Guardar como"), nunca con
`write()` en el producto. Por qué: sincroniza objetos movidos, actualiza cabecera, ruta e `is_dirty`.
`write()` sirve en la prueba automática para escribir una copia sin cambiar la ruta.

**Decisión 6.2 — Abrir = comprobar con `ifcopenshell.open` → descargar → `load_project(should_start_fresh_session=False, skip_recent=True, skip_autosave_recovery=True)` → fijar piso activo → `clear_undo_history()`.**
- Por qué: cumple FR-011 (si falla, el proyecto abierto no se tocó) y evita `read_homefile`.
  Abrir dos veces el archivo cuesta algo de tiempo en modelos grandes; alternativa más barata:
  `ifcopenshell.util.file.IfcHeaderExtractor` (`ifcopenshell/util/file.py:34`) solo valida la cabecera.
- `skip_recent`: en el programa propio la lista de recientes vive en su propia carpeta de
  configuración, así que puede quedar en `False` allí; en las pruebas debe ser `True`.

**Decisión 6.3 — "Cambios sin guardar" = `scene.BIMProperties.is_dirty`.** Todos los operadores de
BIM Simple que tocan el IFC deben heredar de `tool.Ifc.Operator` (así lo marcan solos). Un proyecto
recién creado o recién abierto queda en `False`, así que no pregunta. Deshacer después de guardar
deja `True`; preguntar de más es aceptable.

---

## Tema 7. Deshacer / rehacer IFC

| Necesidad | Función / operador | Archivo:línea | Probado |
|---|---|---|---|
| Operador IFC deshacible | `class X(bpy.types.Operator, tool.Ifc.Operator)` con `bl_options={"REGISTER","UNDO"}` e implementar `_execute`; `execute` es `@final` y llama `IfcStore.execute_ifc_operator` | `bonsai/tool/ifc.py:400-421` | ✅ |
| Transacción | `execute_ifc_operator`: abre `IfcStore` + `ifc_file.begin_transaction()`; los `bpy.ops.bim.*` llamados dentro no abren otra (`is_top_level_operator=False`); al final guarda `scene.BIMProperties.last_transaction` | `bonsai/bim/ifc.py:389-470, 510-526`, `bonsai/bim/prop.py:606` | ✅ (un operador propio con `add_part_to_object` dentro = 1 paso) |
| Integración con Ctrl+Z | el deshacer de Blender restaura `last_transaction` (propiedad de escena) y el `undo_post` de Bonsai llama `IfcStore.undo(until_key=...)`; igual con `redo_post` | `bonsai/bim/handler.py:333-350`, `bonsai/bim/__init__.py:269-270`, `bonsai/bim/ifc.py:529-559` | ✅ simulado / 📖 real |
| En `--background` | `bpy.ops.ed.undo.poll()` y `ed.redo.poll()` = **False** (no hay ventana); `ed.undo_push.poll()` = True | — | ✅ |
| Limpiar historial | `tool.Blender.clear_undo_history()` | `bonsai/tool/blender.py:2311-2323` | ✅ (parte IFC) |

Salida real (`out_probe_undo_full.txt`; se simula Ctrl+Z poniendo `last_transaction` al paso
anterior y llamando `handler.undo_post`, que es lo que hace Blender):

```
ed.undo.poll() en background: False | ed.redo.poll(): False
bimsimple.probe_add_storey -> {'FINISHED'}
is_dirty: True | pasos IFC por la operación: dBIMSIMPLE_OT_probe_add_storey
[tras mover Piso 1 a 3,50] pisos=[('Planta Baja', 0.0), ('Piso 1', 3.5)] columnas=[('Columna', 'Piso 1')] history=4 future=0
[Ctrl+Z simulado (mover)] pisos=[('Planta Baja', 0.0), ('Piso 1', 3.0)] ... history=3 future=1
[Ctrl+Shift+Z simulado (mover)] pisos=[('Planta Baja', 0.0), ('Piso 1', 3.5)] ... history=4 future=0
[tras borrar Piso 1 con contenido] pisos=[('Planta Baja', 0.0)] columnas=[] history=5 future=0
[Ctrl+Z simulado (borrar)] pisos=[('Planta Baja', 0.0), ('Piso 1', 3.5)] columnas=[('Columna', 'Piso 1')] history=4 future=1
```

**Decisión 7.1 — Cada acción del navegador es un único `tool.Ifc.Operator`** (agregar, renombrar,
cota, altura, borrar). La mitad IFC del deshacer queda probada en segundo plano; la mitad Blender
(memoria de deshacer que restaura objetos y posiciones) solo se puede probar con ventana.
- **Prueba manual** (📖): con BIM Simple abierto, (1) agregar piso → Ctrl+Z → desaparece de la lista y
  de la vista; Ctrl+Shift+Z → vuelve; (2) cambiar cota de un piso con un muro → Ctrl+Z → piso y muro
  vuelven a la cota anterior; (3) borrar un piso con elementos → Ctrl+Z → vuelven piso y elementos,
  seleccionables; (4) renombrar → Ctrl+Z; (5) después de cada caso, guardar y abrir el IFC: coincide
  con lo que se ve; (6) "Nuevo proyecto" y luego Ctrl+Z: no debe reaparecer el proyecto anterior.
- Alternativas: operadores sin `tool.Ifc.Operator` (no quedan en el historial IFC: riesgo 5 del MVP).

---

## Tema 8. IFC con varios edificios, sin edificio, sin pisos

| Necesidad | Función | Archivo:línea | Probado |
|---|---|---|---|
| Edificios | `f.by_type("IfcBuilding")` (orden del archivo) | — | ✅ |
| Pisos de un edificio (también los de partes del edificio) | `[e for e in ifcopenshell.util.element.get_decomposition(edificio) if e.is_a("IfcBuildingStorey")]` | `ifcopenshell/util/element.py:1144` | ✅ |
| Hijos directos | `ifcopenshell.util.element.get_parts(e)` / padre `get_aggregate(e)` / contenedor `get_container(e)` | `ifcopenshell/util/element.py:1424, 1374, 1061` | ✅ |
| Ordenar | por `get_storey_elevation` (ubicación; si falta, `Elevation`) y desempate por nombre o id, igual que Bonsai | `ifcopenshell/util/placement.py:191`, `bonsai/tool/spatial.py:551` | ✅ |
| Cota real: ubicación vs `Elevation` | manda la **ubicación** (es lo que se ve). `Elevation` es opcional en IFC4 y muchos programas no lo escriben. Un piso **sin ubicación** se lee con `Elevation` pero Bonsai lo dibuja a z=0. | `ifcopenshell/util/placement.py:200-203` | ✅ ("Subsuelo": cota −2,80 leída, objeto de Blender a z=0,0) |

```
[dos_edificios.ifc] edificios=['Edificio A', 'Edificio B'] pisos(1er edificio)=[('A - PB', 0.0, 0.0, 3.0)] | todos IfcBuildingStorey=3
[sin_pisos.ifc] edificios=['Galpón'] pisos(1er edificio)=[] | default_container=('IfcSite', 'Terreno')
[sin_edificio.ifc] edificios=[] pisos(1er edificio)=[] | default_container=('IfcSite', 'Terreno')
```

**Decisión 8.1** — Navegador = pisos de `get_decomposition(primer edificio)` ordenados por
`get_storey_elevation`; aviso si `len(by_type("IfcBuilding")) > 1`; mensaje si no hay edificio o
pisos (en esos archivos Bonsai deja como contenedor por defecto al sitio: BIM Simple no debe dejar
crear elementos ahí). Si un piso no tiene ubicación, al editar su cota se le crea una con
`set_storey_elevation` (queda coherente con lo que se ve).

---

## Tema 9. Validación IFC4 (SC-003)

| Necesidad | Función | Archivo:línea | Probado |
|---|---|---|---|
| Validar | `logger = ifcopenshell.validate.json_logger()`; `ifcopenshell.validate.validate(ruta, logger, express_rules=True)`; errores en `logger.statements` (lista de dicts con `level`, `message`, `instance`, `attribute`). No devuelve nada. | `ifcopenshell/validate.py:91, 419, 625-629` | ✅ |
| Reglas EXPRESS | `express_rules=True` ejecuta `ifcopenshell.express.rule_executor` con `ifcopenshell/express/rules/IFC4.py` (incluido) | ídem | ✅ |
| Operador de Bonsai | `bim.validate_ifc_file` (solo informa en la interfaz) | `bonsai/bim/module/debug/operator.py:126-127` | 📖 |

```
e2e_pisos.ifc express_rules=True: 0 mensajes []
guardado_como.ifc express_rules=True: 0 mensajes []
otro_programa_mm.ifc express_rules=True: 0 mensajes []
roto.ifc express_rules=False: 1 mensajes [('error', 'Attribute not optional')]
roto.ifc express_rules=True: 2 mensajes [('error', 'Attribute not optional'), ('error', "(hiindex(SELF.Decomposes) == 1 and ...")]
```

**Decisión 9.1** — La prueba automática valida el IFC guardado con `express_rules=True` y falla si
hay algún mensaje de nivel `error`. El archivo "roto" demuestra que la validación sí detecta errores.

---

## Tema 10. Llamadas que no son API pública (Principio IV)

Todas deben vivir en **un solo módulo** del producto (por ejemplo `bim_simple/bonsai_api.py`).

**Estables (API pública y documentada de IfcOpenShell):**
`ifcopenshell.open`, `file.write`, `ifcopenshell.api.attribute.edit_attributes`,
`ifcopenshell.api.pset.add_qto` / `edit_qto`, `ifcopenshell.api.geometry.edit_object_placement`
(con `should_transform_children`), `ifcopenshell.api.root.remove_product`,
`ifcopenshell.util.element.get_decomposition` / `get_contained` / `get_container` / `get_parts` /
`get_aggregate` / `get_psets`, `ifcopenshell.util.placement.get_storey_elevation` /
`get_local_placement`, `ifcopenshell.util.unit.calculate_unit_scale`,
`ifcopenshell.validate.validate` / `json_logger`, `ifcopenshell.util.pset.get_template`.

**Operadores de Bonsai (`bpy.ops.bim.*`, semipúblicos: son la interfaz de Bonsai):**
`bim.create_project`, `bim.add_part_to_object`, `bim.load_project` (parámetros
`should_start_fresh_session`, `skip_recent`, `skip_autosave_recovery`), `bim.save_project`
(`filepath`, `skip_recent`), `bim.assign_class` (solo en pruebas).

**Internas de Bonsai (pueden cambiar con cualquier versión):**

| Llamada | Para qué | Archivo:línea |
|---|---|---|
| `bonsai.tool.Ifc.get` / `get_path` / `set_path` / `get_object` / `get_entity` / `is_moved` / `Operator` | archivo vivo, ruta, enlace objeto↔entidad, base de operadores | `bonsai/tool/ifc.py:72, 81, 87, 107, 400` |
| `bonsai.tool.Spatial.edit_container_name` / `set_default_container` / `get_spatial_props` | renombrar, piso activo | `bonsai/tool/spatial.py:605, 1282, 64` |
| `bonsai.tool.Root.get_default_container` / `set_object_name` | piso activo, nombre del objeto | `bonsai/tool/root.py:139, 432` |
| `bonsai.tool.Collector.assign` | nombre de la colección | `bonsai/tool/collector.py:29` |
| `bonsai.tool.Geometry.delete_ifc_object` / `record_object_position` | borrar, registrar posición | `bonsai/tool/geometry.py:453, 1441` |
| `bonsai.tool.Surveyor.get_absolute_matrix` | matriz absoluta del piso | `bonsai/tool/surveyor.py:31` |
| `bonsai.tool.Blender.get_bim_props` (`is_dirty`, `ifc_file`, `last_transaction`) / `clear_undo_history` / `get_bonsai_version` | estado del proyecto, limpiar deshacer | `bonsai/bim/prop.py:600-606`, `bonsai/tool/blender.py:2311` |
| `bonsai.tool.Project.get_project_props` (`export_schema`, `template_file`) | esquema del proyecto nuevo | `bonsai/bim/module/project/operator.py:153, 162` |
| `bonsai.core.spatial.delete_container` | borrar piso | `bonsai/core/spatial.py:158` |
| `bonsai.bim.ifc.IfcStore.purge` | descargar el proyecto | `bonsai/bim/ifc.py:89` |
| `bonsai.bim.handler.refresh_ui_data` | refrescar datos de Bonsai tras cambios fuera de operadores | `bonsai/bim/handler.py:288` |
| `bonsai.bim.module.model.wall.DumbWallGenerator` | solo para crear el muro de prueba (función 2) | `bonsai/bim/module/model/wall.py:1236, 1380` |

---

## Prueba de punta a punta (✅)

Script: `scratchpad\research\ifc\e2e_pisos.py` (usa `_recetas.py`). Comando:
`"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --python e2e_pisos.py`.
Código de salida: **0**. Salida real (`out_e2e_full.txt`, sin las líneas de carga de Blender):

```
Blender 5.2.0 LTS | Bonsai 0.9.0 | ifcopenshell 0.9.0
1. Proyecto nuevo
  OK    esquema IFC4 (IFC4)
  OK    unidades en metros (1.0)
  OK    nombres Proyecto/Sitio/Edificio
  OK    Planta Baja activa
2. Pisos con cota y altura
  OK    3 pisos ordenados (['Planta Baja', 'Piso 1', 'Piso 2'])
  OK    cotas 0/3/6
3. Elemento en Piso 1 (muro con la receta del MVP)
  OK    muro contenido en Piso 1
  OK    ubicación del muro relativa al Piso 1
4. Cambiar la cota de Piso 1 a 3,50 (desplaza Piso 1 y los de arriba, FR-016)
  OK    Piso 1 a 3,50 y Piso 2 a 6,50
  OK    muro se movió en el IFC
  OK    muro se movió en Blender (3.5)
  OK    Bonsai no ve el muro como 'movido sin guardar'
5. Borrar Piso 2 (con un elemento)
   [assign_class] ObjectPlacement tras assign_class: None
  OK    aviso: Piso 2 tiene 1 elemento (1)
  OK    quedan 2 pisos
  OK    la columna se borró del IFC
  OK    la columna se borró de Blender
  OK    el piso de abajo pasa a medir hasta el siguiente (el más alto usa GrossHeight) (3.0)
6. Guardar con write() y reabrir
   objetos movidos sin sincronizar antes de write(): []
   pisos reabiertos:
     Planta Baja: Elevation=0.0 placementZ=0.0 GrossHeight=3.5 contenidos=[]
     Piso 1: Elevation=3.5 placementZ=3.5 GrossHeight=3.0 contenidos=['Wall']
  OK    2 pisos en el archivo (['Planta Baja', 'Piso 1'])
  OK    Elevation = cota de la ubicación
  OK    cotas 0,00 y 3,50
  OK    GrossHeight 3,50 y 3,00
  OK    1 muro, contenido en Piso 1
  OK    muro a cota 3,50, local 0,00 respecto del piso
  OK    sin columnas ni elementos huérfanos
  OK    jerarquía Proyecto > Sitio > Edificio > pisos
--- Jerarquía archivo reabierto ---
#1 IfcProject 'Proyecto'
  #27 IfcSite 'Sitio'
    #33 IfcBuilding 'Edificio'
      #71 IfcBuildingStorey 'Piso 1' Elevation=3.5 placementZ=3.5 GrossHeight=3.0
        [contenido] #126 IfcWall 'Wall' worldZ=3.5 PlacementRelTo=#162 ['IfcBuildingStorey:Piso 1']
      #39 IfcBuildingStorey 'Planta Baja' Elevation=0.0 placementZ=0.0 GrossHeight=3.5
7. Validación IFC4 (ifcopenshell.validate)
   express_rules=False: 0 mensajes, 0 errores
  OK    validación sin errores (express_rules=False)
   express_rules=True: 0 mensajes, 0 errores
  OK    validación sin errores (express_rules=True)
RESULTADO: TODO OK
```

Nota: en el archivo, "Piso 1" aparece antes que "Planta Baja" en la agregación; por eso Bonsai, al
abrir, elige mal el piso activo (Tema 5).

---

## Diferencias con el `PLAN.md` del MVP (etiqueta `mvp-original`)

Los números de línea del MVP siguen siendo correctos (create_project 137, new_project/read_homefile 98,
save_project 1976, `tool.Ifc.get` 72, `tool.Ifc.Operator` 400, add_part_to_object 348,
`core/geometry.py:31`, `edit_attributes.py:26`, `spatial.py:605/1282`, `root.py:139`,
`core/spatial.py:158`, set_container_visibility 494-495, `wall.py:1236/1380`, `file.py:880`).
Lo que **ya no coincide o faltaba**:

1. **Cota del piso**: la receta del MVP (`matrix_world` + `core.geometry.edit_object_placement`) mueve
   solo el piso; los elementos **se quedan** (IfcOpenShell reescribe su ubicación local a −Δ).
   FR-015/016 exigen moverlos: nueva receta con `should_transform_children=True` + mover objetos +
   `record_object_position` (Tema 3).
2. **`delete_container`** (📖 en el MVP): ahora probado; deja los elementos **huérfanos** y el piso
   activo pasa al **edificio**. El `delete_storey` del MVP borraba los contenidos directos; hay que
   usar `get_decomposition` (partes, rellenos, espacios) y activar el piso de abajo.
3. **Altura**: el MVP leía `GrossHeight` primero; FR-016 pide distancia al piso de arriba primero.
4. **`create_project` no hace nada** si ya hay un IFC (`core/project.py:35`); el MVP nunca creaba un
   segundo proyecto en la misma sesión. "Nuevo" y "Abrir" necesitan descargar + `clear_undo_history()`.
5. **Abrir**: el MVP no lo investigó. `load_project` reinicia la sesión por defecto; sin reiniciar
   deja los objetos viejos; si el archivo está dañado ya descargó el proyecto y deja la ruta mala.
6. **Piso activo al abrir**: Bonsai elige el primero de la agregación, no el más cercano a 0,00.
7. **Nombres repetidos**: `add_part_to_object` cambia también el nombre IFC a "Piso 1 2".
8. **`write()` vs `save_project`**: `write()` no sincroniza objetos movidos ni actualiza cabecera,
   ruta ni `is_dirty`.
9. **Deshacer**: el MVP lo dejaba en 📖; la parte IFC queda ✅ (simulada), la de Blender sigue 📖.
10. Hallazgo menor: `bim.assign_class` con una malla (vía de teselado, `root/operator.py:333-345`)
    **no escribe `ObjectPlacement`** hasta que `save_project` sincroniza; no afecta a los muros de
    `DumbWallGenerator`, que sí la escriben.

## Bloqueos y riesgos

- **Sin bloqueos.** Todo lo pedido se pudo verificar salvo el Ctrl+Z real de Blender, que en
  `--background` no tiene `poll` (queda la lista de prueba manual del Tema 7).
- Riesgo: el deshacer de Blender después de "Nuevo"/"Abrir" sin `read_homefile` depende de
  `tool.Blender.clear_undo_history()` (interna; cambia temporalmente `preferences.edit.undo_steps`, lo
  que marca las preferencias como modificadas; en segundo plano no se guardaron: MD5 igual). En el
  programa propio afecta solo a su propia configuración.
- Riesgo: las recetas dependen de 13 llamadas internas de Bonsai (Tema 10); la prueba automática
  debe ejercitarlas todas para detectar cambios de versión.
