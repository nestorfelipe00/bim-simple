# Plan de implementación: Muros con capas que se pueden separar

**Carpeta**: `specs/002-muros-capas` (sin rama propia; se trabaja en `main`) | **Fecha**: 2026-10-11 | **Especificación**: [spec.md](spec.md)

**Entrada**: especificación con las aclaraciones del usuario ("A,A"): separar convierte cada capa en un muro
independiente, y las estructuras compuestas forman un catálogo editable como en ArchiCAD.

## Resumen

Se agregan a BIM Simple:
- la caja de herramientas (Flecha y Muro) y el Info Box;
- el dibujo de muros en la planta;
- el catálogo de estructuras compuestas;
- "Separar en capas";
- la selección con cambios y borrado.

Todo se apoya en lo construido en la función 001 y en la API LGPL de IfcOpenShell 0.9.0, verificada con scripts
reales ([research.md](research.md)).

**Cómo se arma cada parte en el IFC**:
- **Muros con capas**: tipo de muro (`IfcWallType`) con su conjunto de capas, y cada muro con su propia usage, en
  sentido NEGATIVE para la línea de referencia (R2, R3).
- **Esquinas**: `connect_wall` + `regenerate_wall_representation`, que hacen el inglete por capas. El recinto de
  6 × 4 m da exactamente 3,84 m² (R4).
- **Capas en pantalla**: la opción de IfcOpenShell que corta un muro por capas falla siempre en 0.9.0. Por eso el
  motor calcula el prisma de cada capa recortando el perfil del muro por la franja de la capa. Es exacto: la suma de
  las capas da el mismo volumen que OpenCASCADE (R6).
- **Separar**: un muro Básico por capa, con el mismo polígono de esa capa, de modo que nada se mueve. El muro
  original se borra, y Ctrl+Z lo devuelve (R8).
- **Rapidez**: el motor guarda un índice de extremos en memoria, porque buscar los muros vecinos recorriendo el
  piso costaba unos 80 ms con 200 muros. Con el índice, un muro nuevo tarda menos de 20 ms en el motor (R5).

## Contexto técnico

**Lenguaje/versión**: JavaScript (ES2022, módulos) en la ventana y la interfaz; Python 3.14.7 en el motor.

**Dependencias principales**: las mismas de la función 001, sin agregar ninguna (research R14):
- Electron 44.4.5, Three.js 0.186.1 y camera-controls 3.1.2;
- IfcOpenShell 0.9.0 con numpy, y pytest 9.1.1.

**Almacenamiento**: el `.ifc` del usuario (IFC4, metros). Las estructuras y los colores de los materiales quedan en
el IFC.

**Pruebas**:
- `pytest` del motor, con `engine/tests/test_walls.py` nuevo;
- prueba del programa con la ventana oculta, con secciones nuevas;
- prueba manual de [quickstart.md](quickstart.md) parte B.

**Plataforma**: Windows 11 x64, sin conexión a Internet.

**Tipo de proyecto**: aplicación de escritorio (Electron) con un motor local en Python.

**Objetivos de rendimiento**:
- Cada muro aparece en menos de 0,2 s con 200 muros en el piso (SC-006). Medido en el motor: < 20 ms con 211
  muros, más 0,34 ms para las capas (R5).
- Separar un muro: 15,5 ms (R8).
- La vista previa del dibujo no consulta al motor.

**Restricciones**:
- La constitución 4.0.0: IFC real, API verificada y sin código GPL de otros.
- Muros rectos y verticales; solo uniones de extremo (sin T ni cruces).
- La línea de referencia no cambia después de dibujar.

**Escala**: hasta unos 200 muros por piso y 30 pisos; catálogos de decenas de estructuras y materiales.

## Control de la constitución

*Compuerta: se cumple antes de la fase 0 y se vuelve a revisar después del diseño (fase 1).*

| Principio / regla | Cómo lo cumple este plan | Estado |
|---|---|---|
| I. IFC real siempre | Cada muro y cada capa separada es un `IfcWall` real en su piso, con `IfcMaterialLayerSetUsage`. Las estructuras son `IfcWallType` y los colores, estilos de material. Lo que se ve lo calcula el motor desde el IFC (perfil, capas y ubicación; research R6); la única excepción es la vista previa mientras se dibuja. Validación IFC4 con 0 errores verificada en todos los pasos (research R4, R8, R9, R11). | ✅ |
| II. Pensado para quien viene de ArchiCAD | Caja de herramientas, Info Box, estructuras compuestas, línea de referencia, encadenado, Shift, longitud por teclado e imán, todo en español ([contracts/ui.md](contracts/ui.md)). Las diferencias con ArchiCAD están escritas en la especificación: sin T, sin prioridades de capas, línea de referencia fija y extremo recto del vecino de un muro separado (research R10). | ✅ |
| III. Programa propio de escritorio | Órdenes JSON nuevas ([contracts/core_api.md](contracts/core_api.md)). La interfaz no toca el IFC. Herramienta activa, valores del Info Box, selección y vista previa son datos de la interfaz; el índice de extremos vive en el motor, fuera del IFC. | ✅ |
| IV. API verificada, no inventada | Todas las funciones de IfcOpenShell, con firma y archivo:línea, y probadas (research R2-R11). Las de Three.js, con archivo:línea (R12). **Lógica propia justificada**: el recorte de capas, porque la API (`enable-layerset-slicing`) existe pero falla siempre (R6); el índice de extremos, por rendimiento (R5); y la prolongación de cortes de las capas separadas, que la API no tiene (R10). Uniones, regeneración, materiales, tipos y estilos usan la API. | ✅ |
| V. Lógica separada y comprobada | Las reglas viven en el motor (`walls.py`, `materials.py`, `layers.py`). Pruebas del motor y del programa con la ventana oculta (R13). Lista manual en [quickstart.md](quickstart.md). | ✅ |
| VI. Licencia y propiedad del código | Sin dependencias nuevas. Iconos propios. No se leyó ni copió Bonsai (R14). | ✅ |
| Restricciones técnicas | Mismas versiones fijas. Nada fuera de la carpeta del programa. | ✅ |
| Flujo de trabajo: permisos | No hace falta descargar ni instalar nada. Piden permiso: abrir la ventana para la prueba manual, subir los commits y borrar archivos (no se prevé borrar ninguno). | ✅ |

**Resultado**: pasa. Revisión después del diseño: sigue pasando. Los contratos y el modelo de datos no agregan
dependencias, y la lógica propia está justificada en la fila IV.

## Estructura del proyecto

### Documentación (esta función)

```text
specs/002-muros-capas/
├── spec.md              especificación (con aclaraciones)
├── plan.md              este archivo
├── research.md          decisiones verificadas de la fase 0
├── data-model.md        material, estructura, muro, índice, mallas, estado
├── quickstart.md        cómo probar (automático y manual)
├── contracts/
│   ├── core_api.md      órdenes nuevas del motor
│   └── ui.md            caja de herramientas, Info Box, dibujo, selección, diálogo
├── checklists/requirements.md
└── tasks.md             fase 2 (/speckit-tasks)
```

### Código fuente (cambios sobre la función 001)

```text
engine/bimsimple_engine/
├── materials.py      NUEVO: materiales y colores, catálogo de estructuras, apply_structures, contenido de un proyecto nuevo
├── walls.py          NUEVO: crear, editar, borrar y separar muros; clases de muro (R10); índice de extremos (R5); datos del muro
├── layers.py         NUEVO: perfil del cuerpo, recorte por franjas, prismas de capas, prolongación de cortes
├── geometry.py       mallas con groups y datos del muro (los muros editables usan layers.py; el resto, OpenCASCADE)
├── project.py        estado con materials/structures; new_project con el catálogo inicial; descartar el índice
├── storeys.py        editar y borrar pisos descartan el índice
└── commands.py       órdenes nuevas
engine/tests/
├── test_walls.py     NUEVO: muros, capas, separar, catálogo, archivo, rendimiento
└── make_fixtures.py  + IFC de "otro programa": muro con capas POSITIVE, sin capas y con booleano

app/src/main/main.js          menú Opciones > Estructuras compuestas…
app/src/renderer/
├── index.html, styles.css    Info Box, caja de herramientas y diálogo de estructuras
├── icons/arrow.svg, wall.svg NUEVO: iconos propios
├── app.js                    herramienta activa, teclado, órdenes nuevas y selección después de cada respuesta
├── toolbox.js                NUEVO: caja de herramientas
├── infobox.js                NUEVO: Info Box (herramienta y selección)
├── wall-tool.js              NUEVO: cadena, vista previa, imán, Shift, longitud escrita
├── selection.js              NUEVO: elegir en la planta y en el 3D, resaltado
├── structures-dialog.js      NUEVO: diálogo "Estructuras compuestas"
├── meshes.js                 grupos por capa, un material por color, colores en la planta, resaltado
└── viewports.js              punto de la planta bajo el ratón, capa de vista previa, clic sin arrastre en el 3D
app/test/window-test.js       secciones nuevas de la función 002
PRUEBA_MANUAL.md, README.md   sección de muros y estado
```

**Decisión de estructura**:
- Se mantienen las dos piezas de la función 001.
- En el motor, cada tema tiene su módulo: estructuras y materiales, muros, y geometría de capas.
- En la interfaz, cada control tiene su módulo y `app.js` sigue siendo el único que manda órdenes.

## Diseño técnico por pieza

### Motor (`engine/`)
- **Crear**: la receta de research R4, con la búsqueda de vecinos en el índice de R5. No se une con muros
  `custom_ends` ni `locked` (R10).
- **Datos del muro y clases**: según [data-model.md](data-model.md) §3 y §6, y research R10.
- **Capas en pantalla** (`layers.py`), según research R6:
  1. perfil del cuerpo → polígono local;
  2. recorte por la franja de cada capa;
  3. prisma por capa (tapas en abanico) en coordenadas del mundo;
  4. `groups` en el orden de las capas.

  Si un polígono no es convexo, el muro se muestra entero con OpenCASCADE.
- **Separar, cambiar y borrar**: research R8 y R9, una transacción por orden.
- **Catálogo**: research R11. `apply_structures` primero valida todo, después aplica y regenera.
- **Proyecto nuevo**: materiales y estructuras de ejemplo antes de `replace_file` (que vacía el historial).

### Ventana (`app/src/main/`)
- El menú **Opciones** (entre Edición y Ayuda) con "Estructuras compuestas…", que manda la acción `structures` a la
  página. Está desactivado sin proyecto.

### Interfaz (`app/src/renderer/`)
- **Pantalla**: el Info Box arriba y la caja de herramientas a la izquierda de la planta ([contracts/ui.md](contracts/ui.md)).
- **Dibujo** (`wall-tool.js`):
  - el punto bajo el ratón se calcula con `Raycaster` sobre el plano Z = cota del piso;
  - imán a los extremos (de `wall.start`/`wall.end` del piso activo) y a la grilla de 0,10 m;
  - Shift a 45°;
  - longitud escrita;
  - la vista previa es un `ShapeGeometry` de la franja con las capas, dibujado en un grupo aparte que no pertenece a
    ningún piso;
  - cada clic manda `create_wall` y la cadena sigue.
- **Mallas** (`meshes.js`): una malla por elemento, con `addGroup` por capa y un `MeshStandardMaterial` por color en
  el 3D, o `MeshBasicMaterial` en la planta. El resaltado de la selección cambia esos materiales por un azul.
- **Selección** (`selection.js`): `Raycaster` contra las mallas del piso activo en la planta, o de todos en el 3D,
  con clic sin arrastre.
- **Info Box** (`infobox.js`): muestra los valores de la herramienta o de la selección ("varios" si difieren).
  Cada cambio manda una orden.
- **Diálogo de estructuras** (`structures-dialog.js`): trabaja sobre una copia del catálogo y, al Aceptar, manda un
  solo `apply_structures`.

## Pasos que requieren permiso del usuario

| Paso | Cuándo |
|---|---|
| Abrir la ventana del programa para la prueba manual | Al final, si el usuario quiere verla (prueba manual B) |
| Subir los commits a GitHub | Cuando el usuario lo pida |
| Borrar archivos | No se prevé borrar ninguno |

No hay que descargar ni instalar nada.

## Riesgos

1. **IFC de otros programas con muros variados**. Mitigación: tres clases de muro (research R10); lo que no se
   entiende se ve y se conserva, pero no se edita. Hay IFC de prueba para cada clase.
2. **El vecino de un muro separado pierde el inglete si después se lo regenera** (research R10). Mitigación: se
   avisa en los casos límite de la especificación y solo ocurre al cambiar la estructura o el espesor de ese
   vecino.
3. **Capas muy finas (2 cm) son difíciles de elegir con el ratón** a poco zoom. Mitigación: la rueda acerca hacia el
   ratón; se revisa en la prueba manual B5.
4. **Historial de 64 pasos de IfcOpenShell** (función 001): una edición del catálogo con muchos muros es un solo
   paso, pero grande. Mitigación: probado con 202 muros (research R11).
5. **Cambios de IfcOpenShell en versiones futuras** (por ejemplo, si se arregla `enable-layerset-slicing`). Las
   pruebas del motor comparan capas contra OpenCASCADE y detectarían diferencias.

## Seguimiento de complejidad

No hay violaciones de la constitución que justificar. La lógica propia de la fila IV está justificada en research
R5, R6 y R10.
