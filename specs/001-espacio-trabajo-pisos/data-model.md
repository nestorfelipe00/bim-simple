# Modelo de datos: Programa BIM Simple y navegador de pisos

**Fuente**: entidades clave de [spec.md](spec.md) y decisiones de [research.md](research.md).
Regla general (Principio III): **los datos del edificio viven solo en el IFC**. Lo que guarda BIM Simple
fuera del IFC son ajustes de interfaz (piso activo, lista espejo, avisos) y la configuración del programa.

## 1. Programa BIM Simple

Carpeta `%LOCALAPPDATA%\Programs\BIM Simple\` (ver [contracts/programa.md](contracts/programa.md)).

| Campo | Dónde | Regla |
|---|---|---|
| Copia de Blender | `blender\` | Idéntica a Blender 5.2.0 instalado, sin `blender.pdb`. No se modifica. |
| Configuración | `blender\portable\` | Su existencia activa el modo portable. Todo lo variable vive aquí. |
| Preferencias principales | `portable\config\userpref.blend` | Valores de research R5 (idioma, carpeta temporal, sin guardar preferencias al salir). |
| Plantilla | `portable\scripts\startup\bl_app_templates_user\bim_simple\` | `__init__.py`, `userpref.blend` (obligatorio) y `startup.blend` de datos. |
| Extensiones | `portable\extensions\user_default\{bonsai, bim_simple}` + `.local\…\site-packages` | Las instala `-c extension install-file`. |
| Carpeta temporal | `portable\temp\` | `quit.blend`, `.blend` de sesión, `recuperacion\`. |
| Icono, licencias, LEEME | raíz | Copiados por el script de armado. |

## 2. Proyecto

Es el archivo IFC abierto en Bonsai.

| Campo | Fuente | Regla |
|---|---|---|
| Archivo vivo | `tool.Ifc.get()` (en `bonsai_api`) | `None` si no hay proyecto. |
| Ruta | `tool.Ifc.get_path()` / `scene.BIMProperties.ifc_file` | Vacía si nunca se guardó. "Guardar" sin ruta = "Guardar como". |
| Esquema | `file.schema` | Los proyectos nuevos son `IFC4`. Al abrir, se acepta lo que traiga el archivo, siempre que tenga `IfcProject`. |
| Escala de unidades | `ifcopenshell.util.unit.calculate_unit_scale(f)` | Todo lo que se muestra o se recibe está en metros; se convierte con esta escala. |
| Cambios sin guardar | `scene.BIMProperties.is_dirty` | Lo pone en `True` cada operador que cambia el IFC y en `False` "Guardar". Nuevo y Abrir lo dejan en `False`. |
| Edificio de trabajo | primer `IfcBuilding` del archivo | Si hay más de uno, aviso "El archivo tiene N edificios; se muestran los pisos de «…»". |

**Estados**:

```
sin proyecto ──Nuevo / Abrir──▶ abierto (sin cambios)
abierto (sin cambios) ──acción de piso──▶ abierto (con cambios)
abierto (con cambios) ──Guardar / Guardar como──▶ abierto (sin cambios)
abierto (con cambios) ──Ctrl+Z hasta el estado guardado──▶ sigue "con cambios" (se pregunta de más; aceptado)
abierto (cualquiera) ──Nuevo / Abrir / Salir──▶ si hay cambios: Guardar / No guardar / Cancelar
Abrir con archivo inválido ──▶ mismo estado anterior + mensaje (FR-011)
```

Al pasar a "abierto" por Nuevo o Abrir se borra el historial de deshacer (`clear_undo_history`), para que
Ctrl+Z no traiga el proyecto anterior.

## 3. Edificio

| Campo | Fuente | Regla |
|---|---|---|
| Entidad | `IfcBuilding` dentro de `IfcSite` dentro de `IfcProject` | BIM Simple trabaja con uno por proyecto. |
| Pisos | `IfcBuildingStorey` en `get_decomposition(edificio)` | Si no hay edificio o no hay pisos: lista vacía, mensaje, y "Agregar piso" desactivado. |

## 4. Piso

Entidad IFC `IfcBuildingStorey` agregada al edificio. En el IFC, los campos se guardan así:

| Campo | Lectura | Escritura | Validación |
|---|---|---|---|
| `ifc_id` | `entity.id()` | — | Identifica el piso entre el IFC y la lista espejo. |
| Nombre | `Name` | `tool.Spatial.edit_container_name` + nombre del objeto y de la colección | No vacío (si no, se rechaza y queda el anterior). Puede repetirse; si Bonsai agrega " 2", se corrige. |
| Cota (m) | `get_storey_elevation(piso) × unit_scale`: Z absoluta de la ubicación, o `Elevation` si no tiene ubicación | Ubicación del piso con `edit_object_placement(should_transform_children=True)` + objetos de Blender + `Elevation` (relativo al edificio) | Mayor que la cota del piso de abajo (FR-016). Puede ser negativa. |
| Altura (m) | Distancia al piso de arriba; para el más alto, `Qto_BuildingStoreyBaseQuantities.GrossHeight`, o 3,00 si no existe | `GrossHeight` en todos los pisos que se crean o cambian, igual al valor mostrado | Mayor que 0 (si no, se rechaza y queda el anterior). |
| Elementos | `IfcElement` de `get_decomposition(piso)`, sin aberturas (`IfcFeatureElementSubtraction`) | — | Se usa para el aviso de FR-017. |

**Orden**: por cota, de mayor a menor (el más alto arriba en la lista). Si hay empate, por nombre.

**Reglas de cambio (FR-012 a FR-017)**, siempre como un solo paso de deshacer:

| Acción | Efecto |
|---|---|
| Agregar arriba | Cota = cota del más alto + su altura. Altura = altura del más alto. Nombre "Piso N" (N = pisos con cota > 0 contando el nuevo). |
| Agregar abajo | Cota = cota del más bajo − 3,00. Altura 3,00. Nombre "Sótano N" (N = pisos con cota < 0 contando el nuevo). |
| Cambiar altura del piso *i* | Si es el más alto, solo `GrossHeight`. Si no, Δ = nueva − actual: todos los pisos de arriba suben Δ con sus elementos, y `GrossHeight(i)` = nueva. |
| Cambiar cota del piso *i* | Se rechaza si es menor o igual que la del piso de abajo. Δ = nueva − actual: el piso *i* y todos los de arriba se mueven Δ con sus elementos. `GrossHeight` del piso de abajo = nueva distancia. |
| Borrar piso *i* | Se rechaza si es el único. Con elementos, primero se confirma (cantidad). Se borran elementos y piso. Los de arriba no se mueven. El de abajo pasa a medir hasta el siguiente (si queda como el más alto, conserva su valor). |

## 5. Piso activo

| Campo | Fuente | Regla |
|---|---|---|
| Contenedor por defecto | `scene.BIMSpatialDecompositionProperties.default_container` (vía `tool.Spatial.set_default_container` / `tool.Root.get_default_container`) | Se guarda en la escena, no en el IFC. Exactamente uno mientras haya proyecto (FR-021). |
| Al crear | Planta Baja | |
| Al abrir | Piso de cota más cercana a 0,00 | Bonsai elegiría el primero de la agregación, por eso lo fija BIM Simple. |
| Al borrar el activo | El inmediatamente inferior; si no hay, el superior | `delete_container` lo dejaría en el edificio, por eso lo fija BIM Simple. |
| Efecto en la planta | Solo la colección del piso activo es visible en la vista izquierda (colecciones locales) | La vista 3D muestra la colección del proyecto completa. |

## 6. Lista espejo para la interfaz (`props.py`)

La lista de Blender (`UIList`) necesita una colección de propiedades. Es **solo una copia** del IFC para
dibujar; nunca es la fuente de verdad.

| Propiedad | Tipo | Regla |
|---|---|---|
| `Scene.bim_simple.storeys` | colección de `BIMSimpleStorey` (`ifc_id`, `name`, `elevation`, `height`) | Se vuelve a llenar con `refresh_storeys()` después de cada operador, en `load_post` y en `undo_post`/`redo_post`. |
| `Scene.bim_simple.active_storey_index` | entero | Al cambiar por un clic, llama a `core.activate_storey` y a `screen.show_storey_in_plan`. No cambia el IFC y no marca cambios. |
| `Scene.bim_simple.notice` | texto | Avisos del navegador (varios edificios, sin pisos). |

## 7. Sesión (cerrar con la X, research R15)

| Campo | Dónde | Regla |
|---|---|---|
| `.blend` de sesión | `portable\temp\BIM Simple.blend` | Se guarda al arrancar y después de Nuevo y Abrir. "Guardar IFC" también lo actualiza (`bim.save_project`). Nunca se muestra ni se abre. |
| Recuperación | `portable\temp\recuperacion\<fecha>.ifc` | Solo si se cierra con la X, se elige "Guardar" y el proyecto nunca se guardó. Al siguiente arranque, aviso para abrirla. |
