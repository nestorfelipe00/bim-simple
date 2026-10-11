# Contrato: ventana, menús, pantalla y navegación

Fuente: spec FR-001 a FR-025. Base: el prototipo validado (`docs/base-tecnologica/prototipo/app/`).
Todos los textos visibles están en español (FR-024). Los identificadores van en inglés.

## Ventana

| Elemento | Contrato |
|---|---|
| Título | `«archivo.ifc» — BIM Simple`, o `Proyecto sin guardar — BIM Simple`. Con cambios sin guardar empieza con `* ` (FR-004). La página nunca cambia el título por su cuenta. |
| Icono | El de BIM Simple, en la ventana y en la barra de tareas (appId propio; ver [programa.md](programa.md)). |
| Cerrar (X, Archivo > Salir, Ctrl+Q) | Si hay cambios: diálogo de Windows con el título "BIM Simple", el mensaje «¿Guardar cambios antes de cerrar?», el detalle "Si no los guardas, se perderán." y los botones **Guardar**, **No guardar** y **Cancelar**. "Guardar" sin ruta abre Guardar como; si se cancela, no se cierra (FR-010). |
| Abrir y guardar | Diálogos nativos de Windows con el filtro "Modelo IFC (*.ifc)". |

## Menús

| Menú | Elemento | Atajo | Acción |
|---|---|---|---|
| Archivo | Nuevo proyecto | Ctrl+N | Pregunta si hay cambios → `new_project` |
| Archivo | Abrir IFC… | Ctrl+O | Pregunta si hay cambios → diálogo → `open_project` |
| Archivo | Guardar IFC | Ctrl+S | `save_project` (sin ruta → Guardar como) |
| Archivo | Guardar IFC como… | Ctrl+Mayús+S | diálogo → `save_project(path)` |
| Archivo | Salir | Ctrl+Q | Igual que cerrar la ventana |
| Edición | Deshacer | Ctrl+Z | `undo` (desactivado si `can_undo` es falso) |
| Edición | Rehacer | Ctrl+Y | `redo` (desactivado si `can_redo` es falso) |
| Ayuda | Acerca de BIM Simple | — | Diálogo de Windows "Acerca de BIM Simple" (ver abajo) |

No hay otros menús. Las herramientas de desarrollo de Electron no están a la vista: el menú propio
reemplaza al de Electron y no las incluye.

**"Acerca de BIM Simple"** (`dialog.showMessageBox`, título "Acerca de BIM Simple", botón "Cerrar"),
con este texto exacto:

> BIM Simple 0.1.0
> Copyright (c) 2026 Nestor Torres.
> Software libre bajo la GPL-3.0 o posterior, sin ninguna garantía.
> Código fuente: https://github.com/nestorfelipe00/bim-simple
>
> Usa estas librerías, cada una con su licencia:
> • IfcOpenShell 0.9.0 — LGPL-3.0. Código fuente: https://github.com/IfcOpenShell/IfcOpenShell
> • Electron 44.4.5, Three.js 0.186.1 y camera-controls 3.1.2 — MIT
> • Python 3.14.7 — PSF
>
> Los textos completos de las licencias están en la carpeta «licencias» del programa.

## Pantalla

```text
┌ Archivo  Edición  Ayuda ────────────────────────────────────────────────────────┐
├───────────────────────────────┬───────────────────────────────┬─────────────────┤
│ Planta — Planta Baja          │ Vista 3D                      │ BIM Simple      │
│ (piso activo, desde arriba)   │ (todo el edificio)            │ Casa.ifc •      │
│                               │                               │ Navegador de    │
│                               │                               │ pisos           │
│                               │                               │ [tabla]         │
│                               │                               │ [botones]       │
│                               │                               │ [mensajes]      │
└───────────────────────────────┴───────────────────────────────┴─────────────────┘
```

**Panel "BIM Simple"** (columna derecha, ~290 px):
1. **Proyecto**: nombre del archivo o "Proyecto sin guardar"; "• Cambios sin guardar" si
   corresponde. Sin proyecto: "No hay ningún proyecto abierto" y los botones **Nuevo proyecto** y
   **Abrir IFC…**.
2. **Aviso** (`state.notice`) si lo hay:
   - varios edificios: "El archivo tiene N edificios; se muestran los pisos de «X»";
   - sin edificio: "Este archivo no tiene un edificio, por eso no hay pisos. El modelo se ve en la vista 3D.";
   - edificio sin pisos: "Este archivo no tiene pisos. Usa «Agregar piso arriba» para crear el primero.".
3. **Navegador de pisos**: tabla Piso | Cota | Altura.
   - Valores con dos decimales y coma decimal (`3,00`).
   - El más alto va arriba.
   - El activo se marca con "●" y fondo resaltado.
   - Un clic selecciona la fila; el **doble clic** la activa (FR-020).
   - Debajo, la ayuda "Doble clic en un piso para activarlo."
4. **Botones**:
   - **Agregar piso arriba** y **Agregar piso abajo**;
   - **Editar piso…**: diálogo con Nombre, Cota (m) y Altura (m) del piso seleccionado; Aceptar
     manda un solo `edit_storey`;
   - **Borrar piso**: si `count_storey_elements > 0`, confirmación «El piso «X» tiene N
     elementos. Se borrarán junto con el piso.» (con N = 1: «tiene 1 elemento») con [Borrar] / [Cancelar];
   - **Encuadrar**.

   Se desactivan cuando no aplican: Borrar con un solo piso, Agregar sin edificio, Editar o Borrar
   sin fila seleccionada.
5. **Mensajes**: el último error o aviso, en español. Por ejemplo: "Guardado. Validación IFC4: 0
   errores."

## Vistas y navegación (FR-002, FR-022, FR-025)

| Vista | Cámara | Muestra | Ratón |
|---|---|---|---|
| Planta (izquierda) | ortogonal, desde arriba, sin rotación | solo el grupo del piso activo, con los sólidos en gris oscuro | rueda: zoom hacia el ratón · botón central: desplazar |
| 3D (derecha) | perspectiva | todos los pisos | botón izquierdo, o Mayús + botón central: girar alrededor del punto del modelo bajo el ratón · botón central o derecho: desplazar · rueda: zoom hacia el ratón · movimiento suave · no pasa por debajo del suelo (ángulo polar máximo 88°) |

"Encuadrar" y la primera vez que aparecen elementos: la planta encuadra el piso activo y el 3D,
todo el edificio, con una transición suave.

## Rendimiento visible (SC-004)

Cada acción del navegador se refleja en pantalla en **menos de 0,2 s** con 10 pisos. El prototipo
midió unos 30 ms por orden con su redibujo.

## Motor detenido

Si el proceso del motor termina sin que se lo pida:
- la ventana muestra "El motor de BIM Simple se detuvo. Los cambios sin guardar se perdieron; el
  último archivo guardado no se modificó.";
- el motor se reinicia sin proyecto;
- las órdenes que estaban pendientes responden con error.
