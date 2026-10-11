# Contrato: protocolo del motor BIM

El motor es un proceso de Python (`python -m bimsimple_engine`) que usa IfcOpenShell. La interfaz
no le habla directamente: el proceso principal de Electron lo lanza, le escribe órdenes por
**stdin** y lee las respuestas por **stdout**, una línea JSON por mensaje (UTF-8, sin BOM). Los
errores inesperados y los registros del motor van por **stderr**. Base: el prototipo validado
(`docs/base-tecnologica/prototipo/motor/motor.py`).

## Mensajes

```jsonc
// interfaz → motor (vía proceso principal)
{"id": 12, "cmd": "add_storey_above", "args": {}}

// motor → interfaz: éxito
{"id": 12, "ok": true, "result": { ... }, "ms": 3.8}

// motor → interfaz: error esperable (regla del modelo, archivo inválido…)
{"id": 12, "ok": false, "error": "La cota debe ser mayor que la del piso de abajo («Planta Baja», 0,00 m).", "ms": 0.4}

// motor → interfaz: error interno (falla del motor; se registra la traza)
{"id": 12, "ok": false, "error": "Error interno: …", "trace": "…", "ms": 2.1}

// al arrancar, una sola vez
{"id": 0, "ok": true, "result": {"ready": true, "ifcopenshell": "0.9.0", "import_ms": 300}}
```

- Los `cmd` y los nombres de campos van en inglés (constitución, Principio II). Los textos de
  `error` van en español, listos para mostrar al usuario.
- Cotas y alturas siempre en **metros** (`float`). Los pisos y elementos se identifican por su
  `id` IFC (entero).
- Cada orden que cambia el IFC es **una** transacción, es decir, un paso de deshacer. Si una regla
  no se cumple, el motor responde `ok: false` **sin haber cambiado nada**.
- El motor atiende las órdenes de a una y en orden.

## Estado (`State`)

Lo devuelven `state` y todas las órdenes que cambian algo (en `result.state`).

```jsonc
{
  "has_project": true,
  "path": "C:\\…\\Casa.ifc",        // "" si nunca se guardó
  "dirty": true,                     // cambios sin guardar
  "storeys": [                       // de mayor a menor cota
    {"id": 59, "name": "Piso 1", "elevation": 3.0, "height": 3.0, "elements": 4},
    {"id": 40, "name": "Planta Baja", "elevation": 0.0, "height": 3.0, "elements": 4}
  ],
  "active_storey_id": 40,
  "notice": "",                      // aviso del navegador (varios edificios, sin pisos)
  "can_undo": true,
  "can_redo": false
}
```

## Órdenes

| `cmd` | `args` | `result` | Requisitos |
|---|---|---|---|
| `state` | — | `State` | |
| `new_project` | — | `{state}` | FR-007, FR-021 |
| `open_project` | `path` | `{state}` | FR-008, FR-011 |
| `save_project` | `path` (opcional; sin él usa la ruta actual) | `{state, path}` | FR-009 |
| `validate_file` | `path` | `{errors, messages[]}` | SC-003. Lo usa el proceso de validación aparte (research R6). |
| `add_storey_above` | — | `{state, storey_id}` | FR-013 |
| `add_storey_below` | — | `{state, storey_id}` | FR-014 |
| `edit_storey` | `id`, `name`?, `elevation`?, `height`? | `{state, changed_ids[]}` | FR-015, FR-016. Aplica solo lo que viene, en **una** transacción. `changed_ids` incluye los elementos que se movieron. |
| `count_storey_elements` | `id` | `{count}` | FR-017 |
| `delete_storey` | `id` | `{state, deleted_ids[]}` | FR-017, FR-021 |
| `activate_storey` | `id` | `{state}` | FR-020, FR-021, FR-023. No cambia el IFC ni marca cambios. |
| `undo` / `redo` | — | `{state}` | FR-018 |
| `meshes` | `ids`? (sin él, todos) | `{meshes[], existing_ids[], failures[]}` | FR-002, FR-022; formato en [data-model.md](../data-model.md) §5 |

## Errores esperables (texto exacto)

| Situación | `error` |
|---|---|
| Orden sin proyecto abierto | "No hay ningún proyecto abierto." |
| Archivo dañado o que no es IFC | "No se pudo abrir «archivo»: no es un archivo IFC válido." |
| IFC sin `IfcProject` | "No se pudo abrir «archivo»: no contiene un proyecto IFC." |
| Guardar sin ruta | "Elige dónde guardar el proyecto." (la interfaz abre el diálogo de Guardar como) |
| Cota inválida | "La cota debe ser mayor que la del piso de abajo («nombre», X,XX m)." |
| Altura inválida | "La altura debe ser mayor que 0." |
| Nombre vacío | "El nombre del piso no puede quedar vacío." |
| Último piso | "No se puede borrar el único piso del edificio." |
| Sin edificio | "Este archivo no tiene un edificio donde agregar pisos." |
| Nada que deshacer o rehacer | "No hay nada que deshacer." / "No hay nada que rehacer." |
| Orden desconocida | "Orden desconocida: <cmd>" |

## Lo que el motor no hace

- No dibuja ni conoce la pantalla.
- No pregunta nada al usuario: las preguntas las hace la ventana.
- No valida dentro de `save_project`, porque bloquearía ~1,7 s. La validación corre aparte
  (research R6).
