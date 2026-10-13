# Investigación (fase 0): Muros con capas que se pueden separar

**Fecha**: 2026-10-11 · **Constitución**: 4.0.0 · **Base**: lo construido en la función 001.

Marcas:
- ✅ verificado con la salida real de un script sobre el IfcOpenShell 0.9.0 instalado;
- 📖 leído en el código instalado (archivo:línea);
- ⚠️ decisión con un límite conocido.

Las rutas `ifcopenshell/…` son relativas a `runtime/python/Lib/site-packages/`. Los scripts de verificación
están fuera del repositorio, en la carpeta temporal de la sesión:
- `api002/s01`–`s09`: el informe del agente de investigación;
- `plan002/v1_design.py`: el diseño completo, 33 comprobaciones en verde;
- `plan002/v2_perf.py` y `v3_profile.py`: tiempos;
- `plan002/v4_catalog.py`: el catálogo.

No se leyó código de Bonsai (GPL; constitución, Principio VI).

## R1. Qué se reutiliza de la función 001 ✅

- **Protocolo JSON** del motor ([001 core_api.md](../001-espacio-trabajo-pisos/contracts/core_api.md)). Cada orden
  que cambia el IFC es una transacción (`Project.transaction`, `engine/bimsimple_engine/project.py:39-49`), y por
  eso cada orden es un paso de deshacer.
- **Respuestas con `changed_ids` y `deleted_ids`**, que la interfaz usa para pedir solo las mallas que cambiaron
  (`app/src/renderer/app.js:50-56`).
- **Vistas**: un solo `WebGLRenderer` con planta y 3D (`app/src/renderer/viewports.js`) y grupos por piso.
- **Pisos**: mover un piso mueve sus muros (`should_transform_children`) y borrar un piso borra sus muros (función 001).

## R2. Muros con capas en el IFC

**Decisión**:

| Concepto de BIM Simple | IFC |
|---|---|
| Estructura compuesta | `IfcWallType` (Name = nombre) con un `IfcMaterialLayerSet` (LayerSetName = nombre) |
| Capa | `IfcMaterialLayer` (Material, LayerThickness) |
| Muro con estructura compuesta | `IfcWall` con su tipo y su propia `IfcMaterialLayerSetUsage` apuntando al conjunto del tipo |
| Muro Básico (incluidas las capas separadas) | `IfcWall` **sin tipo**, con su propio `IfcMaterialLayerSet` de una capa (LayerSetName "Básica") y su usage |

**Funciones** (firmas 📖):

| Función | Uso | Firma |
|---|---|---|
| `root.create_entity` | muros y tipos | `api/root/create_entity.py:26-31` |
| `material.add_material_set` | conjunto de capas; hay que pasar `set_type="IfcMaterialLayerSet"` (por defecto crea un ConstituentSet) | `add_material_set.py:30-32` |
| `material.add_layer` | crea la capa con 0,1 m | `add_layer.py:24-29`, `87-94` |
| `material.edit_layer` | cambia el espesor o el material | `edit_layer.py:23-28` |
| `material.assign_material(type="IfcMaterialLayerSet")` | conjunto del tipo | `assign_material.py:168-173` |
| `material.assign_material(type="IfcMaterialLayerSetUsage", material=conjunto)` | usage de un muro sin tipo | `196-237` |
| `type.assign_type` | crea la usage del muro a partir del conjunto del tipo | `assign_type.py:307-319` |
| `material.edit_layer_usage` | sentido y desplazamiento | `edit_layer_usage.py:23`, `76-77` |

**Cuidados** (✅):
- `assign_type` y `assign_material` crean **una usage compartida por todos los productos de la llamada**
  (`assign_material.py:233-237`). Por eso se llama **una vez por muro**. Si no, cambiar la línea de referencia de
  un muro cambiaría la de otros.
- La usage nace con `DirectionSense="POSITIVE"` y `OffsetFromReferenceLine=0` (`assign_material.py:311-319`). Hay
  que ajustarla con `edit_layer_usage` (R3).
- Asignar un tipo o editar sus capas **no cambia la forma** hasta llamar a `regenerate_wall_representation`.
- `assign_type` borra el `PredefinedType` de la ocurrencia si el tipo tiene uno (`assign_type.py:298-304`). Es
  correcto: el tipo dice STANDARD.

**Por qué**: es la forma estándar de IFC4 para muros con capas. Otro programa BIM lee las capas desde la usage y el
conjunto. ArchiCAD y Revit exportan así, y la validación da 0 errores (✅ v1). Las estructuras como tipos se
comparten entre muros, que es lo que pide FR-015 y FR-018.

**Alternativas descartadas**:
- Conjunto de capas sin tipo para las compuestas: no queda un "tipo" con nombre que reaparezca como catálogo.
- Un tipo por cada muro Básico: llenaría el catálogo de entradas que el usuario no creó.

## R3. Línea de referencia (FR-012) ✅

`regenerate_wall_representation` arma las caras así (`regenerate_wall_representation.py:626-638`, `get_axes`):
1. Suma `OffsetFromReferenceLine` a la Y del eje.
2. Apila las capas en +Y con POSITIVE o en −Y con NEGATIVE.

No lee `LayerSetDirection` (asume AXIS2).

**Decisión**: todos los muros que crea BIM Simple llevan `DirectionSense = NEGATIVE`. Así crecen a la derecha del
sentido de dibujo y la primera capa queda del lado izquierdo, que es el exterior al dibujar en sentido horario.

| Línea de referencia | `OffsetFromReferenceLine` | Y local del muro (espesor T) | Verificado con 0,20 |
|---|---|---|---|
| Exterior | 0 | [−T, 0] | [−0,20; 0] ✅ |
| Centro | T/2 | [−T/2, T/2] | [−0,10; 0,10] ✅ |
| Interior | T | [0, T] | [0; 0,20] ✅ |

**Cómo se lee** la línea de referencia de un muro: se compara el desplazamiento con 0, T/2 y T, con una tolerancia
de 0,1 mm. Un muro de otro programa con otro valor, o con sentido POSITIVE, se informa como "Otra". Se puede
separar y cambiar su altura, pero no su estructura: no se sabe qué línea mantener fija.

## R4. Dibujar y unir en esquina (FR-005, FR-011, FR-013) ✅

**Receta por muro**, dentro de una transacción:
1. `root.create_entity("IfcWall", name="Muro")`.
2. `spatial.assign_container(piso activo)`.
3. Estructura:
   - compuesta: `type.assign_type`;
   - Básica: `add_material_set` + `add_layer` + `edit_layer` + `assign_material(Usage)`.
4. `edit_layer_usage` con NEGATIVE y el desplazamiento de R3.
5. `geometry.create_2pt_wall(file, element, context, p1, p2, elevation, height, thickness)`
   (`create_2pt_wall.py:27-37`). **Devuelve la representación sin asignarla** (`88`), así que después va
   `geometry.assign_representation`.
   - `elevation` es la **cota absoluta** del piso: la matriz que arma (`77-87`) es del mundo, y
     `edit_object_placement` la pasa a relativa al contenedor (`edit_object_placement.py:175-194`). Con 0, un muro
     del Piso 1 quedaría en la cota 0.
6. Eje: `geometry.add_axis_representation(file, context=Plan/Axis, axis=[(0,0),(L,0)])` (`add_axis_representation.py:26-28`).
   - Tiene que ser el contexto **Plan/Axis/GRAPH_VIEW**, porque `util.representation.get_reference_line` solo lee
     ese (`util/representation.py:499`).
   - La función 001 ya lo crea en el proyecto nuevo (`project.py:89-91`).
7. Por cada muro del mismo piso con un extremo a menos de 1 mm de `p1` o `p2`: `geometry.connect_wall(file, nuevo,
   otro)` (`connect_wall.py:30-35`). Crea un `IfcRelConnectsPathElements` ATSTART/ATEND. Cada extremo admite una
   sola unión; `connect_path` borra la anterior incompatible (`connect_path.py:36-70`).
   - Por eso, si el extremo del otro muro **ya está unido**, no se une el muro nuevo: llega a tope y la esquina
     existente no cambia. Si no, la unión nueva reemplazaría a la vieja y rompería esa esquina (encontrado en la
     implementación, T016; caso límite de la especificación).
   - **El muro nuevo se regenera siempre**: `create_2pt_wall` deja el cuerpo hacia +Y sin mirar la usage, y recién
     la regeneración lo pone del lado de su línea de referencia.
8. `geometry.regenerate_wall_representation(file, wall, length, height)` (`regenerate_wall_representation.py:41-47`)
   sobre el muro nuevo y los unidos:
   - hace el inglete por capas en las esquinas (`146-162`, `528`);
   - genera un `IfcArbitraryClosedProfileDef` extruido, `SweptSolid` (`266-332`);
   - reemplaza cuerpo, eje y ubicación (`337-369`);
   - `length` solo se usa si el muro no tiene eje (`120-123`). La altura se pasa como el `Depth` actual del cuerpo.

**Resultados** (✅ v1):
- Recinto Básico de 6 × 4 m dibujado en sentido horario con Exterior: superficie en planta **3,84000 m²**
  (SC-002) y volumen OpenCASCADE 11,52.
- Recinto con "Muro exterior 30": la suma de las capas es igual al volumen de cada muro.
- 4 uniones y 0 errores de validación.

**Fuera de esta función**: uniones en T (`connect_wall(..., is_atpath=True)`) y prioridades de capas
(`Priority`). La API las soporta (`422-543`), pero la especificación las deja fuera.

## R5. Rendimiento: índice de extremos ✅ ⚠️

**Medido** con 211 muros en el piso (v2 y v3):
- Buscar vecinos recorriendo el piso cuesta **unos 80 ms por muro**: `get_local_placement` tarda 0,3 ms por muro y
  `get_reference_line`, 0,06 ms.
- Por eso el primer intento tardó 179 ms en crear un muro.
- Sin esa búsqueda, crear un muro compuesto con transacción, unión y regeneración tarda **7–14 ms**.

**Decisión**: el motor guarda en memoria un **índice de extremos** por piso, con este diccionario:

```text
(x, y) redondeados a 1 mm → ids de muros
```

- Se arma la primera vez que hace falta (85 ms con 211 muros) y la consulta tarda menos de 0,01 ms.
- Se actualiza al crear, separar, borrar y cambiar muros.
- Se descarta después de abrir, deshacer, rehacer y cambiar o borrar pisos, porque esas órdenes pueden mover
  cualquier cosa. Se vuelve a armar la próxima vez que se lo necesita.
- Es un dato de la interfaz del motor, no del edificio: no se guarda en el IFC (constitución, Principio III).

**Total medido** para un muro nuevo con 211 en el piso:
- motor: < 20 ms (unión y regeneración incluidas);
- capas para la pantalla: 0,34 ms;
- con el redibujo, la meta de SC-006 (< 0,2 s) queda con margen.

## R6. Capas en pantalla (FR-017) ✅ ⚠️

**Hallazgo**: la opción `enable-layerset-slicing` de `ifcopenshell.geom` falla **siempre** en 0.9.0 (api002/s04,
s05 y s09).
- Mensaje: `Unexpected topology` ([GEO060]).
- Falla en todos los casos probados: muro de 1 o 3 capas, eje Plan o Model, L unida, IFC2X3, losa, los 5 núcleos
  geométricos y 9 opciones extra.
- El elemento queda **sin forma**, y con un hilo el iterador puede no devolver nada. Confirma la nota del
  prototipo (`engine/bimsimple_engine/geometry.py:12`).
- `layerset-first` solo da el color de la primera capa.

**Decisión: el motor calcula cada capa a partir del IFC.**

Para un muro editable (R10):
1. Se lee el perfil del cuerpo: el `IfcArbitraryClosedProfileDef` (`IfcIndexedPolyCurve` o `IfcPolyline`) del
   `IfcExtrudedAreaSolid`, con su `Position`, vía `util.placement.get_axis2placement` (`util/placement.py:52`).
2. Se recorta el perfil con la franja en Y local de cada capa (Sutherland–Hodgman), con los límites de R3.
3. Cada capa es un prisma: el polígono recortado extruido el `Depth` del cuerpo, llevado al mundo con la ubicación
   del muro.
4. Las tapas se triangulan en abanico: los perfiles de BIM Simple son convexos, porque la regeneración hace
   trapecios con ingletes.
5. Si una capa no es convexa, el muro se muestra como un solo sólido de OpenCASCADE.

**Verificado** (✅ v1): en los 4 muros del recinto compuesto, la suma de los volúmenes de las capas es igual al
volumen OpenCASCADE del muro (5,13 y 3,33). Calcular las capas de un muro tarda 0,34 ms.

**Por qué**:
- Lo que se ve sale del IFC: perfil, capas, espesores y ubicación (constitución, Principio I).
- Es exacto: el área y el volumen coinciden con OpenCASCADE.
- No guarda en el IFC nada más que el cuerpo estándar.

**Alternativas descartadas**:
- Guardar cada capa como un ítem del cuerpo en el IFC (api002/s06, variante B-1): funciona y valida, pero
  `regenerate` reemplaza el cuerpo por un solo ítem (`337-342`), así que habría que rehacerlo después de cada
  regeneración. Tampoco se sabe cómo lo leen otros programas.
- Teselar ítems sueltos con OpenCASCADE (5,2 ms por muro): es más lento y deja entidades temporales en el
  archivo.

**Muros no editables** (de otros programas, sin usage o con cuerpos que no son una extrusión simple): un solo sólido
de OpenCASCADE, como en la función 001, con el color de su primera capa si la tiene, o el gris por defecto.

## R7. Colores de los materiales (FR-016) ✅

- **Guardar**:
  1. `style.add_style(file, name)` (`add_style.py:23-25`);
  2. `style.add_surface_style(file, style, ifc_class="IfcSurfaceStyleShading", attributes={"SurfaceColour": {…},
     "Transparency": 0.0})` (`add_surface_style.py:34-39`);
  3. `style.assign_material_style(file, material, style, context=Body)` (`assign_material_style.py:26-32`).

  El color queda en el IFC y otros programas lo muestran.
- **Leer**: `util.representation.get_material_style(material, Body)` (`util/representation.py:465-484`) →
  `Styles[0].SurfaceColour`. Verificado: (0,76, 0,41, 0,31) ✅ v1.
- Un material sin estilo se muestra en el gris por defecto `#d9d9d6`.
- **Paleta inicial**:

  | Material | Color |
  |---|---|
  | Hormigón | `#b5b5b0` |
  | Ladrillo | `#c1694f` |
  | Bloque de hormigón | `#9a9a94` |
  | Revoque | `#e8e2d4` |
  | Aislación | `#f2d24b` |
  | Placa de yeso | `#f4f4f0` |
  | Madera | `#b9875a` |

## R8. Separar en capas (FR-019 a FR-022) ✅

**Receta por muro compuesto**, en una sola transacción para toda la selección:
1. Se calculan los polígonos de las capas (R6).
2. Por cada capa:
   - un `IfcWall` nuevo con el nombre «nombre original — material»;
   - el mismo piso;
   - un conjunto Básico de una capa con el mismo material y espesor;
   - usage con el mismo sentido y `OffsetFromReferenceLine = 0`.
3. **Ubicación** (`edit_object_placement`): la del muro original corrida en su Y local hasta la **cara exterior de
   la capa**. Así su línea de referencia es Exterior, sobre su propia cara (spec, Supuestos).
4. **Cuerpo**: `ShapeBuilder.extrude(profile(polyline(polígono, closed=True)), magnitude=Depth)`
   (`util/shape_builder.py:440`, `727`, `1179`) y `get_representation(Body, [sólido])` (`1244`). Es un `SweptSolid`
   que conserva los cortes de las esquinas.
5. **Eje**: `add_axis_representation` sobre la cara exterior de la capa, del primer al último punto del polígono en
   esa cara. En una esquina con inglete, las capas interiores son más cortas, así que su eje también: el imán cae en
   sus esquinas reales (ajuste de la implementación, T030).
6. Sin uniones.
7. Al final, `root.remove_product(original)`: borra también sus `IfcRelConnectsPathElements`
   (`api/root/remove_product.py:165-174`). Si el original era Básico, también se borra su conjunto con
   `material.remove_material_set`.

**Resultados** (✅ v1, muro de 4 capas en un recinto):

| Comprobación | Resultado |
|---|---|
| Muros nuevos | 4, cada uno de una capa |
| Materiales y espesores | Iguales a los del muro original |
| Suma de volúmenes | 5,13000 contra 5,13000 |
| Muros vecinos | Sin cambios |
| Validación | 0 errores |
| Tiempo | 15,5 ms |
| Ctrl+Z | Vuelven el muro compuesto y sus 2 uniones |
| Ctrl+Y | Vuelven las 4 capas |

## R9. Cambiar y borrar (FR-024 a FR-027) ✅

| Cambio | Receta | Verificado |
|---|---|---|
| Altura | Se edita `Depth` del `IfcExtrudedAreaSolid` del cuerpo con `attribute.edit_attributes`. Conserva los ingletes y los cortes. | Capa separada a 3,60: volumen × 1,2 exacto; Ctrl+Z ✅ |
| Estructura compuesta | `type.assign_type` (una llamada) → `edit_layer_usage` (NEGATIVE + desplazamiento de R3 con el espesor nuevo) → regenerar el muro y los unidos. Si era Básico, se borra su conjunto propio. | "Tabique 15" en lugar de "Muro exterior 30": la cara exterior queda en la línea ✅ |
| Pasar a Básica | `type.unassign_type` (`api/type/unassign_type.py:24`) + conjunto propio de una capa + usage + regenerar. | Se prueba en la implementación (misma receta que crear) |
| Material de un Básico | `edit_layer(material=…)`. La forma no cambia. | — |
| Espesor de un Básico | `edit_layer(LayerThickness)` + desplazamiento según la línea de referencia + regenerar si es regenerable (R10). Si tiene extremos propios, se recalcula su polígono prolongando los cortes (R10). | Se prueba en la implementación |
| Borrar | `root.remove_product` (borra sus uniones) + `remove_material_set` del conjunto propio + regenerar los que estaban unidos. Su extremo queda recto. | Validación 0 ✅ |

## R10. Tres clases de muro ⚠️

El motor clasifica cada `IfcWall` al leerlo. No guarda ninguna marca propia en el IFC.

| Clase | Cómo se reconoce | Qué se puede hacer |
|---|---|---|
| **Regenerable** | Tiene `IfcMaterialLayerSetUsage` (sentido NEGATIVE o POSITIVE), eje Plan/Axis y un cuerpo con un solo `IfcExtrudedAreaSolid` vertical de perfil poligonal o rectangular. Además, o tiene uniones de camino, o su perfil es el rectángulo justo de su franja. | Todo: unirse, cambiar altura, estructura, material y espesor, separar y borrar. |
| **Con extremos propios** | Como el anterior, pero sin uniones y con un perfil que no es el rectángulo de su franja. Son las capas separadas en una esquina. | Cambiar altura, material y espesor, separar (si tiene más de una capa) y borrar. **No se une** a muros nuevos: un muro que empieza en su extremo queda a tope. Así no se pierde el corte de su otra esquina, porque regenerar lo haría rectángulo. El espesor se cambia prolongando las dos aristas de los extremos hasta la cara nueva; si el polígono no es un cuadrilátero, el espesor queda desactivado. |
| **No editable** | Todo lo demás: sin capas, con booleanos, aberturas, brep o perfil curvo. | Se ve (OpenCASCADE), se conserva y se puede borrar (spec, casos límite). |

**Límite conocido** ⚠️:
- Cuando se separa un muro, el muro vecino conserva el inglete hacia ese lado. Ya no hay unión, así que su cuerpo no
  cambia.
- Si después se le cambia la estructura o el espesor, se regenera sin esa unión y **ese extremo queda recto**, como
  en ArchiCAD cuando se borra un muro de una esquina.
- Se anota en los casos límite de la especificación.

## R11. Catálogo de estructuras (FR-015, FR-016) ✅

| Acción del diálogo | Receta | Verificado (v4) |
|---|---|---|
| Nueva | `create_entity("IfcWallType", predefined_type="STANDARD")` + `add_material_set` + capas + `assign_material(type="IfcMaterialLayerSet")` | (igual que v1) ✅ |
| Duplicar | `material.copy_material(conjunto)` (`copy_material.py:23`): copia las capas, con los mismos materiales; + tipo nuevo + `assign_material` | ✅ |
| Renombrar | `attribute.edit_attributes` sobre `Name` del tipo y `LayerSetName` del conjunto (`edit_attributes.py:26`, `63-64`) | ✅ |
| Borrar (sin muros) | `material.remove_material_set` + `root.remove_product(tipo)`; los materiales quedan | ✅, Ctrl+Z lo devuelve |
| Editar capas | `edit_layer`, `add_layer`, `remove_layer` (`remove_layer.py:21-23`; nunca dejar 0 capas), `reorder_set_item` (`reorder_set_item.py:21-23`) y después: ajustar el desplazamiento de cada muro que la usa según su línea de referencia, y regenerar esos muros y sus unidos | 202 muros regenerados, validación 0 ✅ |
| Material nuevo | `add_material` + estilo (R7) | ✅ |

- "Aceptar" manda **una** orden `apply_structures` con todos los cambios, en **una** transacción, que es un solo
  paso de deshacer.
- Un proyecto nuevo trae los 7 materiales de R7 y las 3 estructuras de ejemplo (spec, Supuestos), creados antes de
  vaciar el historial (`project.py:105`).

## R12. Interfaz ✅

Three.js 0.186.1 (📖 `app/node_modules/three/src`):

| Para qué | Función | Archivo |
|---|---|---|
| Elegir muros y hallar el punto de la planta (también con cámara ortogonal) | `Raycaster.setFromCamera` | `core/Raycaster.js:119-129` |
| Tolerancias de líneas | `Raycaster.params` | `Raycaster.js:88` |
| Un material por capa | `BufferGeometry.addGroup(start, count, materialIndex)` | `core/BufferGeometry.js:335` |
| Vista previa | `ShapeGeometry` y `LineLoop` | `geometries/ShapeGeometry.js:24`, `objects/LineLoop.js:10` |
| Aristas | `EdgesGeometry` | `geometries/EdgesGeometry.js:26` |
| Vista previa encima de los muros | `Material.polygonOffset` | `materials/Material.js:375` |

**Decisiones**:
- **Mallas con grupos**: cada muro editable llega como **una** malla con un grupo por capa (`groups`) y un arreglo de
  materiales de Three.js, uno por material IFC (color de R7). En la planta se usan esos mismos colores con
  `MeshBasicMaterial` y aristas oscuras.
- **Dibujo, imán y vista previa** en la interfaz: son cálculos de pantalla (constitución, Principio I, excepción de
  la vista previa). El motor recibe puntos ya resueltos y vuelve a comprobar la longitud mínima y las uniones.
- **Shift** fija la dirección en el múltiplo de 45° más cercano; el imán de grilla se aplica después sobre esa
  dirección.
- **Seleccionar en el 3D**: se elige con un clic sin arrastre (menos de 4 px entre `pointerdown` y `pointerup`), así
  arrastrar sigue girando, como en la función 001.
- **Teclado**: Esc, Enter, Supr, dígitos, coma, punto y Retroceso en `keydown` de la página. Ctrl+Z y Ctrl+Y siguen
  en el menú de Electron.
- **Iconos** de Flecha y Muro: SVG propios en `app/src/renderer/icons/` (sin licencia de terceros). La CSP actual
  (`img-src 'self' data:`) los permite.
- **Menú "Opciones"**: se agrega a la plantilla de `main.js`, con la acción `structures` enviada a la página, como
  las demás del menú.

## R13. Pruebas (Principio V)

**Motor** (pytest, `engine/tests/test_walls.py`):
- recinto 6 × 4 con 3,84 m² y 4 uniones (SC-002);
- las tres líneas de referencia (R3);
- compuesta con capas iguales al volumen (R6);
- separar: volumen, materiales, vecinos, deshacer y rehacer (SC-003);
- cambiar altura, estructura, material y espesor;
- borrar con vecinos;
- catálogo completo con reglas y errores exactos;
- guardar y volver a abrir (SC-004);
- validación con 0 errores (SC-005);
- 200 muros con un muro nuevo en < 0,2 s en el motor (SC-006);
- muros de otro programa: editable, con extremos propios y no editable.

**Programa** (ventana oculta, `app/test/window-test.js`), secciones nuevas:
- dibujar una cadena de 4 muros cerrada con clics simulados en la planta;
- Shift, longitud escrita, imán;
- selección y "Separar en capas";
- diálogo de estructuras;
- capturas.

**IFC de prueba nuevos** (`engine/tests/make_fixtures.py`): un muro de "otro programa" con capas en POSITIVE, uno sin
capas y uno con booleano.

## R14. Licencias (Principio VI) ✅

- **Sin dependencias nuevas**: numpy e IfcOpenShell ya están (función 001, R10).
- El recorte por franjas, el índice de extremos y la prolongación de cortes son código propio.
- Los iconos son propios.
- No se leyó ni copió código de Bonsai.
