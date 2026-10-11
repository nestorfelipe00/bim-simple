# Contrato: órdenes nuevas del motor (muros y estructuras)

Amplía el protocolo de la función 001 ([../../001-espacio-trabajo-pisos/contracts/core_api.md](../../001-espacio-trabajo-pisos/contracts/core_api.md)).
Sigue igual todo lo que allí se dice:
- una línea JSON por mensaje;
- `cmd` y campos en inglés;
- errores en español;
- metros;
- una transacción, y por lo tanto un paso de deshacer, por cada orden que cambia el IFC;
- si una regla no se cumple, `ok: false` **sin haber cambiado nada**.

## Cambios en lo existente

| Orden | Cambio |
|---|---|
| `state` y `result.state` de todas las órdenes | Suma `materials[]` y `structures[]` ([data-model.md](../data-model.md) §7). |
| `new_project` | Además crea los 7 materiales y las 3 estructuras de ejemplo, antes de vaciar el historial. |
| `meshes` | Cada malla suma `groups[]` y `wall` ([data-model.md](../data-model.md) §5-6). |
| `undo`, `redo`, `open_project`, `edit_storey`, `delete_storey` | Descartan el índice de extremos (research R5). |

## Órdenes nuevas

| `cmd` | `args` | `result` | Requisitos |
|---|---|---|---|
| `create_wall` | `start` [x, y], `end` [x, y], `structure_id` (null = Básica), `material_id` (solo Básica), `thickness` (solo Básica), `height`, `reference` (`exterior`/`center`/`interior`) | `{state, wall_id, changed_ids[]}` | FR-005, FR-011 a FR-014. Se crea en el piso activo. `changed_ids` incluye los muros unidos que se regeneraron. |
| `edit_walls` | `ids[]` y uno o más de: `height`, `structure_id` (null = Básica), `material_id`, `thickness` | `{state, changed_ids[]}` | FR-024, FR-025, FR-027. Todo en una transacción. `material_id` y `thickness` solo se aplican a los muros Básicos. Si algún muro es `locked`, o la línea de referencia es `other` y se pide cambiar la estructura o el espesor, se rechaza toda la orden. |
| `delete_walls` | `ids[]` | `{state, deleted_ids[], changed_ids[]}` | FR-026, FR-027. `changed_ids`: los vecinos regenerados. |
| `split_walls` | `ids[]` | `{state, deleted_ids[], new_ids[], changed_ids[]}` | FR-019 a FR-022. Separa los muros de 2 o más capas e ignora los de 1. Si ninguno tiene 2 o más capas: error. `changed_ids` = `new_ids`. |
| `apply_structures` | ver abajo | `{state, changed_ids[]}` | FR-015, FR-016. Todos los cambios del diálogo en una transacción. |

### `apply_structures`

```jsonc
{
  "materials": [                                  // materiales nuevos (el diálogo les da una referencia temporal)
    {"ref": "m1", "name": "Piedra", "color": "#8a8174"}
  ],
  "structures": [                                 // estado final de cada estructura creada o cambiada
    {"id": 77,   "name": "Muro exterior 30", "layers": [{"material": 11, "thickness": 0.02}, {"material": "m1", "thickness": 0.20}]},
    {"id": null, "ref": "s1", "name": "Muro 35", "copy_of": 77, "layers": [ ... ]}
  ],
  "deleted": [81]                                 // ids de estructuras borradas
}
```

- `material` es el id de un material existente o la `ref` de uno nuevo de la misma orden.
- Las estructuras que no aparecen no cambian.
- El motor comprueba primero todas las reglas (nombres únicos y no vacíos, al menos una capa, espesores > 0,
  estructuras borradas sin muros) y, solo si todas se cumplen, aplica los cambios (research R11).
- Después ajusta el desplazamiento de los muros afectados según su línea de referencia y los regenera junto con sus
  unidos.

## Errores esperables (texto exacto)

| Situación | `error` |
|---|---|
| Muro de menos de 1 cm | "El muro es demasiado corto (mínimo 1 cm)." |
| Espesor ≤ 0 | "El espesor debe ser mayor que 0." |
| Altura ≤ 0 | "La altura debe ser mayor que 0." |
| Línea de referencia desconocida | "Línea de referencia no válida." |
| Estructura o material inexistente | "La estructura elegida ya no existe." / "El material elegido ya no existe." |
| Muro inexistente | "Uno de los muros elegidos ya no existe." |
| Muro no editable | "BIM Simple no puede cambiar la forma de este muro (viene de otro programa)." |
| Cambiar la estructura o el espesor con línea de referencia "Otra" | "Este muro tiene una línea de referencia que BIM Simple no maneja; solo se puede cambiar su altura y su material." |
| Separar sin muros de varias capas | "El muro ya tiene una sola capa." |
| Nombre de estructura vacío | "El nombre no puede quedar vacío." |
| Nombre de estructura repetido | «Ya existe una estructura llamada «X».» |
| Estructura sin capas | "La estructura tiene que tener al menos una capa." |
| Capa con espesor ≤ 0 | «La capa N de «X» tiene que tener un espesor mayor que 0.» |
| Borrar una estructura en uso | «La estructura «X» la usan N muros; no se puede borrar.» (N = 1: «la usa 1 muro») |
| Material repetido o vacío | «Ya existe un material llamado «X».» / "El nombre del material no puede quedar vacío." |
| Color inválido | "El color tiene que tener la forma #rrggbb." |

## Lo que el motor no hace

- No dibuja la vista previa ni resuelve el imán: recibe puntos ya resueltos.
- No guarda la herramienta activa ni los valores del Info Box: son datos de la interfaz.
- No crea uniones en T ni cruces (spec, Supuestos).
