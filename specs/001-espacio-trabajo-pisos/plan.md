# Plan de implementación: Programa BIM Simple y navegador de pisos

**Carpeta**: `specs/001-espacio-trabajo-pisos` (sin rama propia; se trabaja en `main`) | **Fecha**: 2026-10-11 | **Especificación**: [spec.md](spec.md)

**Entrada**: especificación revisada para la constitución v3.0.0. Este plan **reemplaza** al anterior, que
estaba hecho para Blender. La investigación de Blender queda como referencia histórica en
[investigacion/](investigacion/).

## Resumen

BIM Simple se construye como un **programa propio para Windows** con tres piezas (constitución, Principio III):
- **Ventana**: Electron. Título, menús Archivo y Edición, diálogos de Windows y pregunta al cerrar.
- **Interfaz**: Three.js. Planta del piso activo y 3D lado a lado, navegación al estilo
  ArchiCAD/Revit con `camera-controls`, y el panel "BIM Simple" con el navegador de pisos.
- **Motor BIM**: Python embebido con IfcOpenShell, como proceso aparte. Es dueño del IFC, aplica
  las reglas de pisos, deshace con transacciones y devuelve las formas 3D.

La interfaz manda órdenes JSON y el motor responde con el estado y las mallas. Todo se apoya en el
prototipo validado (muro ~30 ms, deshacer ~25 ms, IFC válido, título, X y doble clic) y en
verificaciones nuevas de las operaciones de pisos con la API LGPL. Se entrega con un instalador por
usuario, sin administrador.

## Contexto técnico

**Lenguaje/versión**:
- JavaScript (ES2022, módulos) en la ventana y la interfaz.
- Python 3.14.7 en el motor.
- PowerShell 5.1 en los scripts de preparación.

**Dependencias principales** (versiones fijas; licencias en [research.md](research.md) R10):
- Electron 44.4.5, Three.js 0.186.1, camera-controls 3.1.2.
- Python embebible 3.14.7, IfcOpenShell 0.9.0 (con numpy, shapely y demás) y pytest 9.1.1.
- Para el instalador: electron-builder 26.17.0 (MIT).

**Almacenamiento**: archivos `.ifc` (IFC4, metros) que elige el usuario. No hay base de datos ni
formato propio.

**Pruebas**:
- `pytest` del motor sin interfaz.
- Prueba del programa con la ventana oculta (`npm --prefix app test`).
- Lista manual de [quickstart.md](quickstart.md).

**Plataforma**: Windows 11 x64, instalación por usuario, sin conexión a Internet.

**Tipo de proyecto**: aplicación de escritorio (Electron) con un motor local en Python.

**Objetivos de rendimiento**:
- Cada acción del navegador se ve en pantalla en menos de 0,2 s con 10 pisos (SC-004); el prototipo
  hizo unos 30 ms.
- Arranque en menos de 10 s (SC-007); el motor estuvo listo en ~0,4 s.

**Restricciones**:
- Versiones fijas, publicadas hace dos semanas o más.
- Sin código GPL o AGPL.
- IfcOpenShell en una carpeta separada y reemplazable.
- Unos 640 MB instalado.
- Rutas cortas (la carpeta del proyecto tiene 36 caracteres).

**Escala**: un usuario, un edificio por proyecto, de 1 a unos 30 pisos y modelos de casas o edificios medianos.

## Control de la constitución

*Compuerta: se cumple antes de la fase 0 y se vuelve a revisar después del diseño (fase 1).*

| Principio / regla | Cómo lo cumple este plan | Estado |
|---|---|---|
| I. IFC real siempre | El motor crea los pisos con `ifcopenshell.api`. Lo que se ve son mallas teseladas del IFC. Cada archivo guardado se valida (IFC4 + EXPRESS) en un proceso aparte; la prueba exige 0 errores. La apertura en otro programa BIM está en la prueba manual. | ✅ |
| II. Pensado para quien viene de ArchiCAD | Español en todo. Doble clic para activar, título propio, pregunta al cerrar y navegación aprobada. Sin diferencias pendientes con la especificación. | ✅ |
| III. Programa propio de escritorio | Las tres piezas, comunicadas solo por órdenes JSON ([core_api.md](contracts/core_api.md)). La interfaz no toca el IFC. Nada de Blender ni Bonsai. | ✅ |
| IV. API verificada | Funciones de IfcOpenShell comprobadas con su firma y su salida real (research R4-R6). APIs de Electron y Three.js usadas en el prototipo o citadas en su documentación oficial. | ✅ |
| V. Lógica separada y comprobada | Las reglas viven en el motor (`engine/`). Hay prueba del motor sin interfaz, prueba del programa con la ventana oculta y lista manual. | ✅ |
| VI. Licencia y propiedad del código | Todas las dependencias revisadas (R10): permisivas, salvo IfcOpenShell (LGPL, carpeta aparte). No se copia código de Bonsai. **Bloqueo R11**: el repositorio de GitHub es público con licencia GPL; no se sube nada hasta que el usuario lo resuelva. **Pendiente antes de vender**: CGAL. | ✅ con bloqueo anotado |
| Restricciones técnicas | Versiones fijas de la constitución. Instalación por usuario. No toca otras instalaciones. | ✅ |
| Flujo de trabajo: permisos | Hay que pedir permiso para: descargar dependencias si no se reutilizan las del prototipo, instalar el programa, crear accesos directos (los crea el instalador), abrir ventanas, borrar archivos obsoletos y cambiar el repositorio y su licencia. Lista en "Pasos que requieren permiso". | ✅ |

**Resultado**: pasa. Revisión después del diseño: sigue pasando. El protocolo, el modelo de datos y
los contratos no agregan dependencias ni tocan nada fuera de la carpeta del programa.

## Estructura del proyecto

### Documentación (esta función)

```text
specs/001-espacio-trabajo-pisos/
├── spec.md              especificación (revisada para v3.0.0)
├── plan.md              este archivo
├── research.md          decisiones de la fase 0 (reemplaza a la de Blender)
├── data-model.md        entidades, reglas y estados
├── quickstart.md        cómo probar (automático y manual)
├── contracts/
│   ├── core_api.md      protocolo del motor (órdenes JSON)
│   ├── ui.md            ventana, menús, pantalla, navegación
│   └── programa.md      instalación, carpetas, accesos directos, licencias
├── investigacion/       referencia histórica (Blender)
├── checklists/requirements.md
└── tasks.md             fase 2 (/speckit-tasks)
```

### Código fuente (raíz del repositorio)

```text
app/                              programa Electron (ventana + interfaz)
├── package.json                  versiones fijas; scripts start / test / dist; configuración de electron-builder
├── package-lock.json
├── src/
│   ├── main/
│   │   ├── main.js               ventana, título, menús, diálogos, cierre con pregunta
│   │   ├── engine.js             lanza el motor, órdenes con id, rechaza pendientes y reinicia si se cae
│   │   └── validator.js          valida el IFC guardado en un proceso aparte
│   ├── preload.js                puente seguro (contextBridge)
│   └── renderer/
│       ├── index.html, styles.css
│       ├── app.js                arranque, estado, órdenes, mensajes
│       ├── viewports.js          escena, planta + 3D, cámaras, navegación, encuadrar
│       ├── meshes.js             mallas del motor agrupadas por piso
│       └── storey-panel.js       panel: proyecto, navegador, botones, diálogo Editar piso
├── test/window-test.js           prueba del programa con la ventana oculta
└── build/icon.ico                icono (lo genera tools/make_icon.py)

engine/                           motor BIM (Python)
├── requirements.txt              dependencias con versiones exactas
├── bimsimple_engine/
│   ├── __main__.py               bucle del protocolo (stdin/stdout)
│   ├── commands.py               tabla de órdenes, errores en español
│   ├── project.py                nuevo, abrir, guardar, validar, estado
│   ├── storeys.py                listar, agregar, editar, contar, borrar, activar
│   └── geometry.py               teselado a mallas (iterador)
└── tests/
    ├── conftest.py               IFC de prueba generados en carpetas temporales
    └── test_engine.py            prueba del motor

tools/
├── setup-dev.ps1                 arma runtime/python (desde el prototipo o descargando, con permiso) y app/node_modules
└── make_icon.py                  genera app/build/icon.ico (biblioteca estándar)

runtime/                          (fuera de git) Python embebible + IfcOpenShell para desarrollo y empaquetado
```

Fuera de git (en `.gitignore`): `runtime/`, `app/node_modules/`, `app/dist/`, `app/test-output/` y `__pycache__/`.

**Decisión de estructura**:
- Dos carpetas de nivel superior, `app/` y `engine/`, que reflejan las dos piezas que se
  comunican por el protocolo. La ventana y la interfaz comparten `app/` porque las empaqueta Electron.
- El motor es un paquete de Python que se ejecuta con `python -m bimsimple_engine`.
- El código anterior basado en Blender ya no existe en el árbol (se borró en `feae67c`).
- El prototipo queda en `docs/` como referencia y no se importa: se reescribe ordenado, con nombres
  en inglés (constitución, Principio II).

**Archivos obsoletos por el cambio de base** (borrarlos requiere permiso):
- `specs/001-espacio-trabajo-pisos/contracts/programa.md` se **reescribe** con el contrato nuevo.
- `PLAN.md`, `PRUEBA_MANUAL.md` y `README.md` describen el MVP sobre Blender. `README.md` y
  `PRUEBA_MANUAL.md` se reescriben al final de la función. `PLAN.md` queda como referencia histórica,
  salvo que el usuario prefiera borrarlo.
- `LICENSE` (GPL-3.0): se reemplaza solo con aprobación del usuario (research R11).

## Diseño técnico por pieza

### Motor (`engine/`)
- Implementa el protocolo de [core_api.md](contracts/core_api.md) con las recetas verificadas en
  research R4-R6.
- Mantiene el `file` de IfcOpenShell, la ruta, la bandera de cambios y el piso activo.
- Cada orden que cambia el IFC se envuelve en `begin_transaction` / `end_transaction`, y en caso
  de error, `discard_transaction`.
- Las reglas FR-012 a FR-021 viven en `storeys.py`, tal como están en [data-model.md](data-model.md) §3-4.
- Las mallas se calculan con `ifcopenshell.geom` (núcleo OpenCASCADE): `create_shape` para pocos
  elementos y `iterator` para todos.

### Ventana (`app/src/main/`)
- **Ventana**: 1400 × 860, `backgroundColor`, y las opciones de seguridad de research R2. El menú en
  español sale de una plantilla con los atajos de [ui.md](contracts/ui.md).
- **Cierre**: `close` con `preventDefault` mientras haya cambios. Después, `dialog.showMessageBox`
  con Guardar / No guardar / Cancelar. "Salir" del menú pasa por el mismo camino.
- **`engine.js`**:
  - lanza el motor (desarrollo: `runtime/python/python.exe`; instalado: `process.resourcesPath`, R9);
  - asocia cada respuesta a su orden por `id`;
  - registra stderr en un archivo de log de la carpeta de datos del usuario;
  - si el motor termina inesperadamente, avisa y lo reinicia.
- **`validator.js`**: después de cada guardado, lanza un segundo Python con `validate_file` y manda el
  resultado a la página.

### Interfaz (`app/src/renderer/`)
- `viewports.js`: el código del prototipo, ordenado (research R7). Los grupos por piso se muestran
  u ocultan en cada dibujo de la planta.
- `storey-panel.js`: la tabla con clic y doble clic, los botones con su estado activo o inactivo y
  el diálogo "Editar piso" (research R8).
- `app.js`: un solo punto que manda las órdenes. Con cada respuesta reemplaza el estado y pide las
  mallas que cambiaron (`changed_ids`/`deleted_ids`) o todas (nuevo, abrir, deshacer, rehacer).

### Instalador
Ver research R9 y [programa.md](contracts/programa.md). `npm --prefix app run dist` arma el instalador
con el Python embebido y el motor como recursos extra, fuera del asar.

## Pasos que requieren permiso del usuario

| Paso | Cuándo |
|---|---|
| Armar `runtime/python` y `app/node_modules`: copiando del prototipo (ya autorizado) o descargando de nuevo | Al empezar la implementación |
| Descargar electron-builder (npm) | Antes de armar el instalador |
| Abrir la ventana del programa para la prueba manual | Al terminar cada historia, si el usuario quiere verla |
| Instalar el programa con su instalador (crea accesos directos) | Al final |
| Hacer privado el repositorio de GitHub y reemplazar `LICENSE` | **Antes de subir cualquier commit** (R11) |
| Borrar archivos obsoletos (`PLAN.md` u otros) | Solo si el usuario lo pide |

## Riesgos

1. **Diálogo "Editar piso" propio**: es HTML, no un diálogo nativo. Mitigación: contrato de textos en
   [ui.md](contracts/ui.md) y prueba del programa.
2. **El motor se cae**: se pierden los cambios sin guardar. Mitigación: reinicio automático y aviso;
   más adelante, autoguardado.
3. **Tamaño (~640 MB) y SmartScreen sin firma de código**: ver research R9. No bloquea el uso propio;
   hay que resolverlo antes de vender.
4. **`MSVCP140.dll` en una PC limpia** (research R9): se incluye junto al programa y hay que probar
   la instalación en una PC limpia (Windows Sandbox o una máquina virtual) antes de entregarlo.
5. **CGAL dentro de IfcOpenShell**: pendiente legal antes de la primera venta (Principio VI).
6. **Repositorio público con GPL** (R11): bloqueo antes de subir commits.

## Seguimiento de complejidad

No hay violaciones de la constitución que justificar.
