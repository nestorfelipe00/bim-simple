# Contrato: pantalla, menú, panel y operadores de BIM Simple

Fuente: spec FR-001 a FR-024; research R7 a R15. Todos los textos visibles están en español
(FR-024). Los identificadores van en inglés con el prefijo `bimsimple.` / `BIMSIMPLE_` (constitución,
Principio II).

## Pantalla

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Archivo                                          [mensajes de BIM Simple] │  ← barra superior: solo esto
├────────────────────────────────┬─────────────────────────┬───────────────┤
│                                │                         │ BIM Simple    │
│   PLANTA (piso activo)         │   3D (todo el edificio) │ ───────────── │
│   vista superior, ortogonal,   │   orbitar, zoom,        │ Proyecto: …   │
│   rotación bloqueada           │   desplazar             │ Navegador de  │
│                                │                         │ pisos         │
│                                │                         │ [lista]       │
│                                │                         │ [botones]     │
└────────────────────────────────┴─────────────────────────┴───────────────┘
   sin barra de estado, sin encabezados de vista, sin barra de herramientas, sin pestañas
```

| Elemento | Visible | Cómo (research) |
|---|---|---|
| Menú "Archivo" | Sí | Reemplazo de `TOPBAR_HT_upper_bar.draw` (R8) |
| Mensajes (reportes) | Sí, a la derecha de la barra superior | `template_reports_banner()` |
| Pestañas de espacios de trabajo, menús de Blender | No | Mismo reemplazo |
| Barra de estado | No | `screen.show_statusbar = False` |
| Encabezados, barra de herramientas, encabezado de herramienta, HUD, gizmo de navegación, textos de la vista | No | `ensure_layout` (R8) |
| Barra lateral | Solo en la vista derecha, con una única categoría "BIM Simple" | Paneles de Blender ocultos; Bonsai filtrado por dueño (R8) |
| Flechas de regiones ocultas, división por esquinas | No | `PreferencesApps` (R5) |
| Menú de clic derecho sobre botones | **Sí (no se puede quitar)** | Diferencia D3 |

## Menú "Archivo" (`BIMSIMPLE_MT_file`)

| Texto | Atajo | Operador |
|---|---|---|
| Nuevo proyecto | Ctrl+N | `bimsimple.new_project` |
| Abrir IFC… | Ctrl+O | `bimsimple.open_ifc` |
| Guardar IFC | Ctrl+S | `bimsimple.save_ifc` |
| Guardar IFC como… | Mayús+Ctrl+S | `bimsimple.save_ifc_as` |
| Salir | Ctrl+Q | `bimsimple.quit` |

## Panel "BIM Simple" (`BIMSIMPLE_PT_navigator`, barra lateral de la vista derecha)

**Sin proyecto**: el texto "No hay ningún proyecto abierto" y los botones "Nuevo proyecto" y "Abrir IFC…".

**Con proyecto**:
1. **Encabezado del proyecto**: nombre del archivo (o "Proyecto sin guardar"); si hay cambios sin guardar,
   "• Cambios sin guardar".
2. **Aviso** (si corresponde): "El archivo tiene N edificios; se muestran los pisos de «…»" o "Este
   archivo no tiene pisos".
3. **"Navegador de pisos"**: lista `BIMSIMPLE_UL_storeys` con columnas Piso | Cota | Altura.
   - Valores en metros con dos decimales, por ejemplo `3,00`.
   - El más alto va arriba.
   - El piso activo se marca con un icono.
   - Los valores se dibujan como texto, no como campos, así el doble clic no renombra (D6).
   - **Un clic en una fila activa el piso** (FR-020).
4. **Botones**: "Agregar piso arriba", "Agregar piso abajo", "Editar piso…" y "Borrar piso". Los que no
   aplican se desactivan, por ejemplo "Borrar piso" cuando queda un solo piso o "Agregar" sin edificio.

## Operadores

Los marcados con **IFC** cambian el archivo: heredan de `bonsai_api.IfcOperator`
(`tool.Ifc.Operator`), son **un** paso de Ctrl+Z, marcan "cambios sin guardar" y al terminar llaman a
`refresh_storeys()`. Si la función de `core` lanza `BIMSimpleError`, el operador muestra el mensaje con
`self.report({'ERROR'}, mensaje)` y no cambia nada.

| `bl_idname` | Texto | IFC | Comportamiento |
|---|---|---|---|
| `bimsimple.new_project` | Nuevo proyecto | — (crea) | Si hay cambios, primero la pregunta de cierre. Llama a `core.new_project()`. |
| `bimsimple.open_ifc` | Abrir IFC… | — (abre) | Si hay cambios, primero la pregunta. Explorador de archivos con filtro `*.ifc`. Llama a `core.open_project(ruta)`. Si el archivo no sirve: mensaje y nada cambia (FR-011). |
| `bimsimple.save_ifc` | Guardar IFC | — | Con ruta: `core.save_project()`. Sin ruta: actúa como `save_ifc_as`. |
| `bimsimple.save_ifc_as` | Guardar IFC como… | — | Explorador de archivos (`.ifc`) y `core.save_project(ruta)`. |
| `bimsimple.quit` | Salir | — | Con cambios: diálogo «¿Guardar cambios antes de cerrar?» con Guardar / No guardar / Cancelar (FR-010). Después sale sin el diálogo `.blend` de Blender (R15). |
| `bimsimple.add_storey_above` | Agregar piso arriba | IFC | `core.add_storey_above()` |
| `bimsimple.add_storey_below` | Agregar piso abajo | IFC | `core.add_storey_below()` |
| `bimsimple.edit_storey` | Editar piso… | IFC | Diálogo con Nombre, Cota (m) y Altura (m) del piso seleccionado. Al aceptar, aplica solo lo que cambió, en un paso de deshacer: `rename_storey`, `set_storey_elevation`, `set_storey_height`. |
| `bimsimple.delete_storey` | Borrar piso | IFC | Si `count_storey_elements > 0`: confirmación «El piso «X» tiene N elementos. Se borrarán junto con el piso.» con [Borrar] / [Cancelar]. Llama a `core.delete_storey()`. |

**Firmas de diálogos a verificar en Blender 5.2 antes de usarlas** (Principio IV): `WindowManager.invoke_confirm`
(título, mensaje y texto del botón) e `invoke_props_dialog`. `invoke_popup` ya está comprobado ✅.

## Atajos

- **Activos**:
  - los de la tabla del menú Archivo;
  - Ctrl+Z / Mayús+Ctrl+Z;
  - navegación de las vistas con el ratón y la rueda;
  - selección con clic;
  - teclas del explorador de archivos.
- **Desactivados**: todo lo que lleve a modos, menús o editores de Blender o de Bonsai, por ejemplo Tab, F3,
  F4, Mayús+A, clic derecho en la vista, T, N, Ctrl+Espacio y Mayús+F1…F12. Lista completa y por keymap:
  `investigacion/interfaz.md` §4.

## Mensajes (texto exacto)

| Situación | Mensaje |
|---|---|
| Archivo dañado o no IFC | "No se pudo abrir «archivo»: no es un archivo IFC válido." |
| IFC sin `IfcProject` | "No se pudo abrir «archivo»: no contiene un proyecto IFC." |
| Cota inválida | "La cota debe ser mayor que la del piso de abajo («nombre», X,XX m)." |
| Altura inválida | "La altura debe ser mayor que 0." |
| Nombre vacío | "El nombre del piso no puede quedar vacío." |
| Último piso | "No se puede borrar el único piso del edificio." |
| Recuperación al arrancar | "Hay una copia de recuperación del <fecha>. ¿Abrirla?" |
