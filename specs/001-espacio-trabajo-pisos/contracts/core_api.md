# Contrato: funciones de `bim_simple/core.py`

`core.py` es la lógica sin interfaz (Principio V). La usan los operadores y la prueba automática, y no
importa `ui`, `props`, `screen` ni `keymaps`. Para hablar con Bonsai usa solo `bonsai_api`; para el IFC, la API
pública de IfcOpenShell (`ifcopenshell.api`, `ifcopenshell.util`). Las recetas están en
[research.md](../research.md) §C.

## Convenciones

- **Unidades**: cotas y alturas siempre en **metros** (`float`). `core` convierte con el `unit_scale` del archivo.
- **Pisos**: se identifican por `ifc_id: int` (`entity.id()`).
- **Errores**: si una regla no se cumple, la función lanza `BIMSimpleError(mensaje_en_español)` **sin haber
  cambiado nada**. Los mensajes son los de [ui.md](ui.md).
- **Transacciones**: las funciones que cambian el IFC **no** abren transacción. Los operadores las llaman
  dentro de `IfcOperator._execute`, lo que da un paso de deshacer y marca `is_dirty`. La prueba puede llamarlas
  directamente.

```python
class BIMSimpleError(Exception): ...

@dataclass(frozen=True)
class StoreyInfo:
    ifc_id: int
    name: str
    elevation: float      # m, cota de la ubicación
    height: float         # m, distancia al piso de arriba (el más alto: GrossHeight o 3,00)
    is_active: bool
```

## Proyecto

| Función | Devuelve | Comportamiento | Requisitos |
|---|---|---|---|
| `has_project()` | `bool` | Hay un IFC abierto. | |
| `project_path()` | `str` | Ruta actual, o `""` si nunca se guardó. | FR-009 |
| `is_dirty()` | `bool` | Hay cambios sin guardar. | FR-010 |
| `new_project()` | `None` | Si hay proyecto, primero `close_project()`. Luego crea un IFC4 en metros: Proyecto > Sitio > Edificio > "Planta Baja" (cota 0,00, `GrossHeight` 3,00), la deja activa y borra el historial de deshacer. | FR-007, FR-021 |
| `open_project(path, add_to_recent=True)` | `None` | Valida con `ifcopenshell.open` y exige `IfcProject`; si falla, lanza `BIMSimpleError` y **no cambia nada**. Si pasa: cierra el proyecto actual, carga sin reiniciar la sesión, activa el piso de cota más cercana a 0,00 y borra el historial de deshacer. | FR-008, FR-011 |
| `save_project(path=None, add_to_recent=True)` | `str` (ruta guardada) | Con `path`, guarda ahí y esa pasa a ser la ruta actual (guardar como). Sin `path`, usa la ruta actual; si no hay, lanza `BIMSimpleError` y el operador abre el explorador. Siempre con `bim.save_project`. | FR-009 |
| `close_project()` | `None` | Descarga el IFC y sus objetos sin `read_homefile`. Uso interno y de pruebas. | |

## Edificio y pisos

| Función | Devuelve | Comportamiento | Requisitos |
|---|---|---|---|
| `building_notice()` | `str` | `""`; "El archivo tiene N edificios; se muestran los pisos de «…»"; o "Este archivo no tiene pisos". | Casos límite |
| `list_storeys()` | `list[StoreyInfo]` | Pisos del primer edificio, de mayor a menor cota (empate por nombre). | FR-011, FR-012 |
| `add_storey_above()` | `StoreyInfo` | Encima del más alto: cota = cota + altura del más alto, la misma altura, nombre "Piso N". | FR-013 |
| `add_storey_below()` | `StoreyInfo` | Debajo del más bajo: cota − 3,00, altura 3,00, nombre "Sótano N". | FR-014 |
| `rename_storey(ifc_id, name)` | `None` | Nombre recortado; vacío → error. Se permiten repetidos y se corrige el " 2" de Bonsai. | FR-015, casos límite |
| `set_storey_elevation(ifc_id, elevation)` | `None` | Regla de cota de FR-016 (mueve ese piso y los de arriba con sus elementos, en el IFC y en Blender, y ajusta `Elevation` y `GrossHeight`). | FR-015, FR-016 |
| `set_storey_height(ifc_id, height)` | `None` | Regla de altura de FR-016. Altura ≤ 0 → error. | FR-015, FR-016 |
| `count_storey_elements(ifc_id)` | `int` | `IfcElement` de la descomposición, sin aberturas. | FR-017 |
| `delete_storey(ifc_id)` | `int` (elementos borrados) | Único piso → error. Borra los elementos y el piso; activa el inferior (o el superior). Los de arriba no se mueven. | FR-017, FR-021 |
| `activate_storey(ifc_id)` | `None` | Fija el contenedor por defecto. No cambia el IFC ni marca cambios. | FR-020, FR-021, FR-023 |
| `active_storey_id()` | `int \| None` | | FR-021 |

## Lo que `core` no hace

- No dibuja nada ni cambia la pantalla: la visibilidad de la planta es de `screen.show_storey_in_plan`.
- No pregunta nada: los diálogos son de los operadores.
- No guarda con `ifcopenshell.file.write()`: no sincroniza los objetos movidos (research R11).
