# Modelo de datos: Programa BIM Simple y navegador de pisos

**Fuente**: entidades clave de [spec.md](spec.md) y decisiones de [research.md](research.md).
Regla general (constitución, Principios I y III): **los datos del edificio viven solo en el IFC**,
que vive en el motor. La interfaz guarda una copia para dibujar (mallas y lista de pisos), que
se reemplaza con lo que devuelve el motor después de cada orden.

## 1. Proyecto (motor)

Es el archivo IFC abierto en el motor (`ifcopenshell.file`).

| Campo | Fuente | Regla |
|---|---|---|
| Archivo vivo | objeto `ifcopenshell.file` del motor | No hay archivo abierto si no hay proyecto. |
| Ruta | la guarda el motor | Vacía si nunca se guardó. "Guardar" sin ruta = "Guardar como". |
| Esquema | `file.schema` | Los proyectos nuevos son `IFC4`. Al abrir, se acepta el esquema que traiga el archivo, siempre que tenga `IfcProject`. |
| Escala de unidades | `ifcopenshell.util.unit.calculate_unit_scale(file)` | Todo lo que viaja por el protocolo está en **metros**; el motor convierte. |
| Cambios sin guardar | bandera del motor | Se pone en `True` en cada orden que cambia el IFC (incluso deshacer y rehacer) y en `False` al guardar, crear o abrir. |
| Historial | `file.history` / `file.future` (transacciones de IfcOpenShell) | Una transacción por orden. Nuevo y Abrir lo vacían. Tamaño: 64 pasos (valor por defecto de IfcOpenShell). |
| Edificio de trabajo | primer `IfcBuilding` del archivo | Si hay más de uno, aviso "El archivo tiene N edificios; se muestran los pisos de «…»". |

**Estados**:

```
sin proyecto ──Nuevo / Abrir──▶ abierto (sin cambios)
abierto (sin cambios) ──orden que cambia el IFC──▶ abierto (con cambios)
abierto (con cambios) ──Guardar / Guardar como──▶ abierto (sin cambios)
abierto (con cambios) ──Nuevo / Abrir / Salir / cerrar con la X──▶ pregunta Guardar / No guardar / Cancelar
Abrir con archivo inválido ──▶ mismo estado anterior + mensaje (FR-011)
motor detenido inesperadamente ──▶ aviso + motor reiniciado sin proyecto (el último archivo guardado no se toca)
```

## 2. Edificio

| Campo | Fuente | Regla |
|---|---|---|
| Entidad | `IfcBuilding` dentro de `IfcSite` dentro de `IfcProject` | Uno por proyecto para BIM Simple. |
| Pisos | `IfcBuildingStorey` de `ifcopenshell.util.element.get_decomposition(edificio)` | Si no hay edificio o pisos: lista vacía, mensaje, y agregar pisos desactivado. |

## 3. Piso

Entidad IFC `IfcBuildingStorey` agregada al edificio.

| Campo | Lectura | Escritura | Validación |
|---|---|---|---|
| `id` | `entity.id()` | — | Identifica el piso en el protocolo. |
| Nombre | `Name` | `ifcopenshell.api.attribute.edit_attributes(Name=…)` | No vacío (si no, se rechaza y queda el anterior). Puede repetirse. |
| Cota (m) | `ifcopenshell.util.placement.get_storey_elevation(piso) × escala`: Z absoluta de la ubicación, o `Elevation` si no tiene ubicación | `ifcopenshell.api.geometry.edit_object_placement(…, should_transform_children=True)` + `Elevation` | Mayor que la cota del piso de abajo (FR-016). Puede ser negativa. |
| Altura (m) | Distancia al piso de arriba; para el más alto, `Qto_BuildingStoreyBaseQuantities.GrossHeight`, o 3,00 si no existe | `pset.add_qto` / `pset.edit_qto(GrossHeight)` en cada piso que se crea o cambia | Mayor que 0 (si no, se rechaza y queda la anterior). |
| Elementos | `IfcElement` de `get_decomposition(piso)`, sin aberturas (`IfcFeatureElementSubtraction`) | — | Para el aviso de FR-017. |

**Orden**: por cota, de mayor a menor (el más alto arriba en la lista). Si hay empate, por nombre.

**Reglas de cambio**, cada una una sola transacción, es decir, un paso de deshacer:

| Acción | Efecto |
|---|---|
| Agregar arriba | Cota = cota del más alto + su altura. Altura = la del más alto. Nombre "Piso N" (N = pisos con cota > 0 contando el nuevo). |
| Agregar abajo | Cota = cota del más bajo − 3,00. Altura 3,00. Nombre "Sótano N" (N = pisos con cota < 0 contando el nuevo). |
| Cambiar altura del piso *i* | Si es el más alto, solo `GrossHeight`. Si no, Δ = nueva − actual: todos los pisos de arriba se mueven Δ con sus elementos y `GrossHeight(i)` = nueva. |
| Cambiar cota del piso *i* | Se rechaza si es menor o igual que la del piso de abajo. Δ = nueva − actual: el piso *i* y todos los de arriba se mueven Δ con sus elementos. `GrossHeight` del piso de abajo = nueva distancia. |
| Borrar piso *i* | Se rechaza si es el único. Se borran sus elementos (`ifcopenshell.api.root.remove_product`) y después el piso. Los de arriba no se mueven. El de abajo pasa a medir hasta el siguiente (si queda como el más alto, conserva su valor). |

## 4. Piso activo (motor)

| Campo | Regla |
|---|---|
| `active_storey_id` | Lo guarda el motor, fuera del IFC (constitución, Principio III). Exactamente uno mientras haya proyecto (FR-021). |
| Al crear | Planta Baja. |
| Al abrir | Piso de cota más cercana a 0,00. |
| Al borrar el activo | El inmediatamente inferior; si no hay, el superior. |
| Después de deshacer o rehacer | Si el piso activo dejó de existir, el de cota más cercana a 0,00. |
| Efecto | Los elementos nuevos (función 2) se contienen en él. La planta muestra solo sus elementos. Activar no cambia el IFC ni marca cambios. |

## 5. Malla (motor → interfaz)

Forma 3D de un elemento, calculada por el motor con `ifcopenshell.geom` en coordenadas del mundo.

| Campo | Tipo | Regla |
|---|---|---|
| `id` | entero | `entity.id()` del elemento. |
| `ifc_class` | texto | Por ejemplo `IfcWall`. |
| `storey_id` | entero o `null` | Piso que lo contiene. |
| `vertices` | base64 de `float32` (x, y, z) | Metros, Z hacia arriba. |
| `faces` | base64 de `uint32` (triángulos) | Índices a `vertices`. |

La interfaz agrupa las mallas por `storey_id`. La planta muestra solo el grupo del piso activo;
el 3D muestra todos.

## 6. Estado de la interfaz (no es del edificio)

| Dato | Dónde | Regla |
|---|---|---|
| Copia del estado del motor (pisos, activo, ruta, cambios) | memoria de la interfaz | Se reemplaza con cada respuesta del motor; nunca se edita a mano. |
| Fila seleccionada del navegador | memoria de la interfaz | Un clic la selecciona (para Editar o Borrar). El doble clic manda `activate_storey`. |
| Cámaras de la planta y del 3D | memoria de la interfaz | "Encuadrar" las lleva al modelo. No se guardan en el IFC. |
