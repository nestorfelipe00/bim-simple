# Contrato: caja de herramientas, Info Box, dibujo, selección y estructuras compuestas

Fuente: spec FR-001 a FR-030. Amplía el contrato de la función 001
([../../001-espacio-trabajo-pisos/contracts/ui.md](../../001-espacio-trabajo-pisos/contracts/ui.md)), que sigue
vigente en todo lo que este archivo no cambia. Todos los textos visibles están en español (FR-030); los
identificadores van en inglés.

## Pantalla

```text
┌ Archivo  Edición  Opciones  Ayuda ─────────────────────────────────────────────────────────────┐
├ Info Box ──────────────────────────────────────────────────────────────────────────────────────┤
│ [Muro] Estructura [Muro exterior 30 ▾][…]  Material [—]  Espesor [0,30]  Altura [3,00]  Línea   │
│        de referencia [Exterior|Centro|Interior]                                                 │
├──┬────────────────────────────┬────────────────────────────┬───────────────────────────────────┤
│↖ │ Planta — Planta Baja       │ Vista 3D                   │ BIM Simple                        │
│▭ │ (grilla, muros con capas)  │ (capas con su color)       │ (panel de la función 001)         │
│  │                            │                            │                                   │
└──┴────────────────────────────┴────────────────────────────┴───────────────────────────────────┘
```

- **Info Box**: barra de una línea, a todo el ancho, debajo de los menús (FR-002).
- **Caja de herramientas**: columna de ~44 px a la izquierda de la planta (FR-001).
- Sin proyecto abierto, la caja de herramientas y el Info Box están desactivados.

## Menús (se agrega Opciones)

| Menú | Elemento | Atajo | Acción |
|---|---|---|---|
| Opciones | Estructuras compuestas… | — | Abre el diálogo "Estructuras compuestas". Desactivado sin proyecto. |

El menú **Opciones** va entre Edición y Ayuda. Los demás menús no cambian. Deshacer y Rehacer (Ctrl+Z,
Ctrl+Y) cubren también los muros y las estructuras (FR-014, FR-022, FR-027).

## Caja de herramientas (FR-001)

| Herramienta | Icono | Texto al pasar el ratón | Efecto |
|---|---|---|---|
| Flecha | flecha de selección (SVG propio) | "Flecha (seleccionar)" | Selección (FR-023). Es la activa al abrir o crear un proyecto. |
| Muro | muro en planta con capas (SVG propio) | "Muro" | Dibujo de muros (FR-005 a FR-013). |

- La herramienta activa tiene fondo resaltado. Hay siempre exactamente una activa.
- Elegir otra herramienta termina la cadena de muros en curso. Elegir Muro deja la selección vacía.

## Info Box (FR-002 a FR-004, FR-024)

**Con la herramienta Muro** (valores del próximo muro):

| Campo | Control | Regla |
|---|---|---|
| Estructura | lista: "Básica" y después las estructuras del catálogo por nombre; botón "…" con el texto al pasar el ratón "Estructuras compuestas…" | Por defecto "Básica". |
| Material | lista de materiales | Solo con "Básica"; con una compuesta muestra "—" y está desactivado. Por defecto "Hormigón". |
| Espesor (m) | número | Editable solo con "Básica" (por defecto 0,20). Con una compuesta muestra la suma de sus capas, desactivado. |
| Altura (m) | número | Por defecto, la altura del piso activo, y la sigue mientras el usuario no la cambie (FR-004). |
| Línea de referencia | tres botones: Exterior · Centro · Interior | Por defecto Exterior. |

- Números con dos decimales y coma (`0,20`). Se aceptan coma y punto al escribir.
- Un valor no válido (vacío, cero, negativo o que no es un número) se rechaza al salir del campo: vuelve
  el valor anterior y en Mensajes aparece el error del motor o "El espesor debe ser mayor que 0." /
  "La altura debe ser mayor que 0.".

**Con la Flecha y sin selección**: el Info Box muestra "Nada seleccionado. Clic en un muro para
seleccionarlo; Shift + clic para agregar o quitar.".

**Con la Flecha y muros seleccionados**:

| Campo | Regla |
|---|---|
| Título | "1 muro seleccionado" / "N muros seleccionados". |
| Estructura, Material, Espesor, Altura | Como con la herramienta Muro, pero muestran los valores de la selección. Si difieren, el campo muestra "varios" (FR-024). Cambiar un campo manda **una** orden `edit_walls` para toda la selección. |
| Línea de referencia | Solo se muestra; no se cambia en esta función (spec, Supuestos). Con valores distintos: "varios". Un muro de otro programa con otra línea muestra "Otra" (research R3). |
| Botón **Separar en capas** | Activo si al menos un muro seleccionado tiene 2 o más capas (FR-019). Un clic manda `split_walls`. |
| Botón **Borrar** | Igual que Supr (FR-026). |
| Aviso de muros no editables | Si algún seleccionado no es editable (spec, casos límite): "Este muro viene de otro programa y BIM Simple no puede cambiar su forma; se puede borrar." Los campos quedan desactivados para esos muros. |

## Dibujo en la planta (FR-005 a FR-012)

| Acción | Resultado |
|---|---|
| Clic izquierdo (sin cadena) | Fija el inicio. |
| Mover el ratón | Vista previa: el contorno del muro con su espesor y sus capas (línea de referencia según el Info Box) y una etiqueta junto al cursor con la longitud, por ejemplo "4,50 m" (FR-006). La vista previa es lo único que la interfaz dibuja sin que exista en el IFC (constitución, Principio I). |
| Clic izquierdo (con cadena) | Manda `create_wall` del inicio al punto; el final pasa a ser el inicio del siguiente. |
| Escribir dígitos, coma o punto | Aparece "Longitud: 4,5" junto al cursor; Retroceso borra. |
| Enter con longitud escrita | Crea el muro con esa longitud en la dirección del ratón (FR-007). Longitud inválida: "La longitud debe ser mayor que 0." y se sigue dibujando. |
| Shift mantenido | La dirección se fija en el múltiplo de 45° más cercano (FR-008). |
| Esc o clic derecho | Termina la cadena; la herramienta sigue activa (FR-010). Sin cadena, Esc no hace nada. |
| Clic en el primer punto de la cadena | Crea el último muro hasta ese punto y termina la cadena (FR-010). |
| Imán (FR-009) | A menos de 10 px: extremos de muros del piso activo (marca: cuadrado) y, si no hay, puntos de la grilla cada 0,10 m (marca: cruz). Los extremos tienen prioridad. Con Shift, el imán de grilla se aplica sobre la dirección fija. |

- La planta muestra la grilla: líneas finas cada 1,00 m.
- Cambiar de piso activo, de herramienta o de proyecto termina la cadena.
- Un muro de menos de 1 cm no se crea; la cadena sigue desde el mismo punto (spec, casos límite).
- El botón central y la rueda siguen navegando la planta mientras se dibuja (función 001).

## Selección (FR-023)

| Vista | Acción con la Flecha | Resultado |
|---|---|---|
| Planta | clic izquierdo sobre un muro | Lo selecciona (y solo a él). |
| Planta / 3D | Shift + clic sobre un muro | Lo agrega o lo quita de la selección. |
| Planta | clic en un lugar vacío | Deja todo sin seleccionar. |
| 3D | clic izquierdo **sin arrastrar** (menos de 4 px de movimiento) sobre un muro | Lo selecciona. Arrastrar sigue girando la vista (función 001). |
| Cualquiera | Esc | Deja todo sin seleccionar. |
| Cualquiera | Supr | Borra los seleccionados (`delete_walls`). |

- Los muros seleccionados se ven en azul (#2f6fd6) en la planta y en el 3D.
- Después de deshacer, rehacer, separar o borrar, la selección conserva solo los muros que siguen
  existiendo; después de separar, quedan seleccionadas las capas nuevas.

## Cómo se ven los muros (FR-017)

| Vista | Muro |
|---|---|
| Planta | Cada capa rellena con el color de su material; líneas oscuras (#3b3833) en el contorno y entre capas. |
| 3D | Cada capa con el color de su material, con sus aristas. |

## Diálogo "Estructuras compuestas" (FR-015, FR-016)

Diálogo modal de la página (`<dialog>`), como "Editar piso" de la función 001.

```text
┌ Estructuras compuestas ──────────────────────────────────────────────────────────┐
│ Estructuras                    │ Capas de «Muro exterior 30» (de exterior a interior) │
│ ┌────────────────────────────┐ │ ┌───┬──────────────────┬────────────┐                │
│ │ Muro de hormigón 25  0,25 │ │ │ 1 │ Revoque ▾        │ 0,02       │                │
│ │ Muro exterior 30     0,30 │ │ │ 2 │ Ladrillo ▾       │ 0,20       │                │
│ │ Tabique 15           0,15 │ │ │ 3 │ Aislación ▾      │ 0,05       │                │
│ └────────────────────────────┘ │ │ 4 │ Revoque ▾        │ 0,03       │                │
│ [Nueva] [Duplicar] [Renombrar] │ └───┴──────────────────┴────────────┘                │
│ [Borrar]                       │ [Agregar capa] [Quitar capa] [Subir] [Bajar]         │
│                                │ Espesor total: 0,30 m                                │
│ Materiales: [Nuevo material…]  │                                                      │
│ (error)                                                    [Cancelar]  [Aceptar]      │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

| Control | Regla |
|---|---|
| Lista de estructuras | Ordenada por nombre, con su espesor total. La primera queda elegida al abrir. |
| Nueva | Crea "Estructura N" con una capa de Hormigón 0,20 y la elige. |
| Duplicar | Copia la elegida como "«nombre» (copia)". |
| Renombrar | Edita el nombre en la lista. Vacío o repetido: «Ya existe una estructura llamada «X».» / «El nombre no puede quedar vacío.» y vuelve el anterior. |
| Borrar | Si la usan muros: «La estructura «X» la usan N muros; no se puede borrar.» (N = 1: «la usa 1 muro»). Si no, la quita de la lista. |
| Tabla de capas | Material (lista) y espesor (número > 0). Agregar capa agrega Hormigón 0,10 debajo de la elegida; Quitar capa no deja quitar la única («La estructura tiene que tener al menos una capa.»); Subir y Bajar cambian el orden. |
| Nuevo material… | Pide nombre y color (`<input type="color">`). Nombre vacío o repetido: «Ya existe un material llamado «X».» |
| Aceptar | Manda **una** orden `apply_structures` con todos los cambios: un solo paso de deshacer. Los muros que usan una estructura cambiada se actualizan (FR-015). Si el motor rechaza algo, el diálogo queda abierto con el error. |
| Cancelar o Esc | Cierra sin cambiar nada. |

## Errores visibles (texto exacto; los manda el motor salvo que se indique)

| Situación | Texto |
|---|---|
| Espesor inválido | "El espesor debe ser mayor que 0." |
| Altura inválida | "La altura debe ser mayor que 0." |
| Longitud escrita inválida (interfaz) | "La longitud debe ser mayor que 0." |
| Muro de menos de 1 cm | "El muro es demasiado corto (mínimo 1 cm)." |
| Separar un muro de una capa | "El muro ya tiene una sola capa." |
| Cambiar un muro no editable | "BIM Simple no puede cambiar la forma de este muro (viene de otro programa)." |
| Nombre de estructura repetido / vacío | «Ya existe una estructura llamada «X».» / «El nombre no puede quedar vacío.» |
| Estructura en uso | «La estructura «X» la usan N muros; no se puede borrar.» |
| Estructura sin capas | "La estructura tiene que tener al menos una capa." |
| Capa con espesor inválido | «La capa N de «X» tiene que tener un espesor mayor que 0.» |
| Material repetido | «Ya existe un material llamado «X».» |

## Rendimiento visible (SC-006)

- Cada muro aparece en la planta y en el 3D en menos de 0,2 s después del clic, con 200 muros en el piso.
- La vista previa se redibuja en cada movimiento del ratón sin pedir nada al motor.
