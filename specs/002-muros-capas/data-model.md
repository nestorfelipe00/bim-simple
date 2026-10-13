# Modelo de datos: Muros con capas que se pueden separar

**Fuente**: entidades clave de [spec.md](spec.md) y decisiones de [research.md](research.md).

Amplía el modelo de la función 001 ([../001-espacio-trabajo-pisos/data-model.md](../001-espacio-trabajo-pisos/data-model.md)).
La regla general sigue igual: **los datos del edificio viven solo en el IFC**, en el motor. La interfaz guarda una
copia para dibujar, que se reemplaza con lo que devuelve el motor.

## 1. Material

| Campo | IFC | Regla |
|---|---|---|
| `id` | `IfcMaterial.id()` | — |
| Nombre | `IfcMaterial.Name` | No vacío. Único dentro del proyecto, sin distinguir mayúsculas. |
| Color | `IfcSurfaceStyle` > `IfcSurfaceStyleShading.SurfaceColour`, asignado al material en el contexto Body (research R7) | `#rrggbb`. Sin estilo: `#d9d9d6`. |

- **Proyecto nuevo**: 7 materiales con sus colores (research R7).
- No se borran materiales en esta función.

## 2. Estructura compuesta

| Campo | IFC | Regla |
|---|---|---|
| `id` | `IfcWallType.id()` | — |
| Nombre | `IfcWallType.Name`, igual a `IfcMaterialLayerSet.LayerSetName` | No vacío. Único entre las estructuras, sin distinguir mayúsculas. |
| Capas | `IfcMaterialLayerSet.MaterialLayers` en orden (la primera es la exterior) | Al menos una. Cada una tiene material y espesor > 0. |
| Espesor | suma de `LayerThickness` | Calculado. |
| Muros que la usan | ocurrencias del tipo (`ifcopenshell.util.element.get_types`) | Si es mayor que 0, la estructura no se puede borrar. |

- **Catálogo**: todos los `IfcWallType` con un `IfcMaterialLayerSet`, ordenados por nombre.
- Los tipos de otros programas que cumplen eso también entran.
- **Proyecto nuevo**: "Muro de hormigón 25", "Muro exterior 30" y "Tabique 15" (spec, Supuestos).

## 3. Muro

Entidad `IfcWall` contenida en un `IfcBuildingStorey`.

| Campo | Lectura | Escritura (research) | Validación |
|---|---|---|---|
| `id` | `entity.id()` | — | — |
| Piso | `util.element.get_container` | `spatial.assign_container` (al crear) | Siempre el piso activo al crear. |
| Inicio y fin (x, y, en m) | Eje Plan/Axis (`get_reference_line`) llevado al mundo con la ubicación | `create_2pt_wall` + `add_axis_representation`; después `regenerate` (R4) | Longitud ≥ 0,01 m. |
| Estructura | Tipo (`util.element.get_type`) si es un `IfcWallType` del catálogo; si no, "Básica" | `type.assign_type` / `type.unassign_type` (R9) | — |
| Capas | `IfcMaterialLayerSetUsage.ForLayerSet.MaterialLayers` | Las del tipo, o el conjunto propio del Básico | Al menos una. |
| Material (Básica) | La única capa | `edit_layer(material)` | Debe existir. |
| Espesor | Suma de las capas | Básica: `edit_layer(LayerThickness)`; compuesta: la del tipo | > 0. |
| Altura | `Depth` del `IfcExtrudedAreaSolid` del cuerpo | `edit_attributes(Depth)` (R9) | > 0. |
| Línea de referencia | Usage: NEGATIVE con desplazamiento 0, T/2 o T → `exterior`, `center` o `interior`; cualquier otro valor → `other` (R3) | `edit_layer_usage` | Fija después de dibujar (spec, Supuestos). |
| Uniones | `ConnectedTo` y `ConnectedFrom` filtrados por `IfcRelConnectsPathElements` (research R4) | `connect_wall` al crear (solo en extremos coincidentes, a menos de 1 mm) | Una por extremo. |
| Clase | Regla de research R10 | — | `regenerable`, `custom_ends` o `locked`. |
| Nombre | `Name` | "Muro"; las capas separadas, «nombre — material» | — |

**Al crear**: la base es la cota del piso (`create_2pt_wall` recibe la cota absoluta del piso; research R4) y la altura viene del Info Box. Por defecto es la altura del
piso, pero queda como un número fijo.

**Reglas de cambio**. Cada fila es **una** orden y **una** transacción:

| Orden | Efecto en el IFC | Muros que se regeneran |
|---|---|---|
| Crear | Receta R4 | El nuevo y los unidos a él (no se une con muros `custom_ends`) |
| Cambiar altura | `Depth` | Ninguno |
| Cambiar estructura | R9 | El muro y sus unidos |
| Cambiar material (Básica) | `edit_layer(material)` | Ninguno |
| Cambiar espesor (Básica) | `edit_layer` + desplazamiento | El muro y sus unidos (`regenerable`); polígono nuevo con los cortes prolongados (`custom_ends`) |
| Separar | R8: una pared nueva por capa y se borra el original | Ninguno (los vecinos quedan iguales) |
| Borrar | `remove_product` + conjunto propio del Básico | Los que estaban unidos |
| Editar una estructura del catálogo | R11 | Todos los muros que la usan y sus unidos |

**Estados de un muro**:

```
(no existe) ──crear──▶ regenerable
regenerable ──separar (≥2 capas)──▶ (no existe) + N muros Básicos:
                                      · los que no tienen cortes en las esquinas: regenerable
                                      · los que tienen cortes: custom_ends
custom_ends ──cambiar estructura──▶ regenerable (extremos rectos)
cualquiera ──borrar──▶ (no existe)
cualquiera ──Ctrl+Z──▶ estado anterior
```

## 4. Índice de extremos (motor, fuera del IFC)

| Campo | Regla |
|---|---|
| Clave | Piso → `(round(x, 3), round(y, 3))` → ids de muros con un extremo ahí. |
| Vida | Se arma la primera vez que se necesita. Se actualiza al crear, separar, borrar y cambiar muros. Se descarta al abrir, crear un proyecto, deshacer, rehacer, editar o borrar pisos. |
| Uso | Buscar con qué muros unir el muro nuevo (research R5). |

## 5. Malla (motor → interfaz)

Amplía la sección 5 de la función 001.

| Campo | Tipo | Regla |
|---|---|---|
| `id`, `ifc_class`, `storey_id`, `vertices`, `faces` | como en la función 001 | En un muro editable, `vertices` y `faces` reúnen los prismas de todas sus capas (research R6). |
| `groups` | `[{start, count, material_id}]` | Índices en `faces` (de a 3 por triángulo, como `BufferGeometry.addGroup`), uno por capa, en orden de exterior a interior. Vacío para los demás elementos. |
| `wall` | objeto o `null` | Datos del muro para la interfaz (sección 6). `null` para lo que no es un `IfcWall`. |

## 6. Datos de un muro (motor → interfaz)

```jsonc
{
  "id": 412,
  "storey_id": 40,
  "start": [0.0, 4.0], "end": [6.0, 4.0],        // eje, en metros, coordenadas del mundo
  "reference": "exterior",                        // exterior | center | interior | other
  "height": 3.0,
  "structure_id": 77,                             // null = Básica
  "layers": [{"material_id": 12, "thickness": 0.02}, {"material_id": 9, "thickness": 0.20}],
  "thickness": 0.22,
  "kind": "regenerable",                          // regenerable | custom_ends | locked
  "locked_reason": ""                             // texto para el Info Box si kind = locked
}
```

## 7. Estado (amplía el `State` de la función 001)

```jsonc
{
  // … todo lo de la función 001 …
  "materials": [{"id": 9, "name": "Ladrillo", "color": "#c1694f"}],
  "structures": [{"id": 77, "name": "Muro exterior 30", "thickness": 0.30, "walls": 12,
                  "layers": [{"material_id": 11, "thickness": 0.02}, {"material_id": 9, "thickness": 0.20}]}]
}
```

- Las listas de materiales y estructuras son cortas, decenas de elementos, así que viajan en cada estado.
- Los datos de los muros viajan con sus mallas (sección 5), porque pueden ser cientos.

## 8. Estado de la interfaz (no es del edificio)

| Dato | Regla |
|---|---|
| Herramienta activa | `arrow` o `wall`. Al abrir o crear un proyecto: `arrow`. |
| Valores del próximo muro | Estructura, material, espesor, altura (o "la del piso" mientras el usuario no la cambie) y línea de referencia. En memoria mientras el programa esté abierto (FR-004). |
| Cadena en curso | Primer punto, último punto y longitud escrita. Se borra con Esc, clic derecho, al cerrar la cadena o al cambiar de piso, herramienta o proyecto. |
| Selección | Ids de muros. Después de cada respuesta del motor se quitan los que ya no existen; después de separar, pasa a las capas nuevas (`new_ids`). |
| Imán | Extremos de los muros del piso activo (de `wall.start` y `wall.end`) y grilla de 0,10 m. Se calcula en la interfaz. |
