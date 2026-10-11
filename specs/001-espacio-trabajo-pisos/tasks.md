---
description: "Lista de tareas de la función 001: programa BIM Simple y navegador de pisos (Electron + Three.js + IfcOpenShell)"
---

# Tareas: Programa BIM Simple y navegador de pisos

**Entrada**: documentos de diseño en `specs/001-espacio-trabajo-pisos/`, sobre la constitución v3.0.0. Esta lista
**reemplaza** a la que estaba hecha para Blender.

**Requisitos previos**:
- [plan.md](plan.md) y [spec.md](spec.md);
- [research.md](research.md), [data-model.md](data-model.md) y [quickstart.md](quickstart.md);
- los contratos [core_api.md](contracts/core_api.md), [ui.md](contracts/ui.md) y [programa.md](contracts/programa.md).

**Base de código**: el prototipo validado en `docs/base-tecnologica/prototipo/` (`motor/motor.py`, `app/main.js`,
`app/renderer.js`, `app/index.html`) y la verificación de pisos
`docs/base-tecnologica/prototipo/verificaciones/verif_pisos.py`. Se reescriben ordenados y con nombres en inglés,
sin importarlos.

**Pruebas**: se incluyen porque las exige la constitución (Principio V):
- **Motor**: `runtime\python\python.exe -m pytest engine\tests -q`.
- **Programa**: `npm --prefix app test`, que corre Electron con la ventana oculta y escribe
  `app\test-output\resultado.json` y capturas.
- **Manual**: [quickstart.md](quickstart.md), parte B.

**Organización**: por historia de usuario de la especificación (US1 a US4). Cada historia termina con las dos
pruebas automáticas en verde y un commit.

## Formato: `[ID] [P?] [Historia] Descripción`

- **[P]**: se puede hacer en paralelo (otro archivo, sin depender de tareas pendientes).
- **[US1]…[US4]**: historia de usuario de spec.md.
- **⛔ PERMISO**: punto de control. Hay que **detenerse y pedir permiso al usuario** antes de ejecutarlo
  (constitución, "Flujo de trabajo").

## Reglas para todas las tareas

- **APIs**: NUNCA inventar funciones ni opciones de IfcOpenShell, Electron, Three.js ni camera-controls. Usar las
  verificadas en research.md o en el prototipo; si hace falta una nueva, verificarla antes en el código instalado o
  en la documentación oficial y anotarla en research.md (Principio IV).
- **Licencias**: NUNCA copiar código GPL o AGPL (Bonsai, Blender). Toda dependencia nueva necesita permiso y revisar
  su licencia (Principio VI).
- **Idiomas**: textos visibles en español, exactamente como en los contratos. Código, órdenes y campos en inglés.
- **Ventanas**: las pruebas corren con la ventana oculta. Abrir la ventana visible es un ⛔ PERMISO.
- **Commits**: `git commit -F <archivo>`. **No subir nada a GitHub** (`git push`) hasta resolver T056.
- **Errores**: si el mismo error sigue después de 3 correcciones, detenerse y mostrarlo junto con lo que se probó.

---

## Fase 1: Preparación

**Propósito**: carpetas, versiones fijas, icono y entorno de desarrollo.

- [X] T001 Crear las carpetas `app/src/main/`, `app/src/renderer/`, `app/test/`, `app/build/`,
  `engine/bimsimple_engine/`, `engine/tests/` y `tools/`. Agregar a `.gitignore`: `runtime/`, `app/node_modules/`,
  `app/dist/` y `app/test-output/`. `__pycache__/` ya está.
- [X] T002 [P] Crear `engine/requirements.txt` con estas versiones exactas: `ifcopenshell==0.9.0`, `numpy==2.5.4`,
  `shapely==2.2.0`, `isodate==0.7.2`, `lark==1.3.1`, `pyparsing==3.3.3`, `python-dateutil==2.9.0.post0`,
  `six==1.17.0`, `typing_extensions==4.16.0`, `pytest==9.1.1`, `iniconfig==2.3.1`, `pluggy==1.6.0`,
  `packaging==26.3`, `Pygments==2.21.0` y `colorama==0.4.6`. Son las instaladas en el prototipo, con licencias
  revisadas en research R10.
- [X] T003 [P] Crear `app/package.json` con:
  - `"name": "bim-simple"`, `"productName": "BIM Simple"`, `"version": "0.1.0"`, `"private": true`,
    `"license": "UNLICENSED"`, `"main": "src/main/main.js"`;
  - `dependencies` exactas `"three": "0.186.1"` y `"camera-controls": "3.1.2"`;
  - `devDependencies` `"electron": "44.4.5"`;
  - `scripts`: `"start": "electron ."` y `"test": "electron . --test"`.

  Sin `^` ni `~` en las versiones. electron-builder se agrega en T050.
- [X] T004 [P] Crear `tools/make_icon.py`, solo con la biblioteca estándar, a partir de
  `specs/001-espacio-trabajo-pisos/investigacion/scripts/empaquetado_make_ico.py`.
  - Genera `app/build/icon.ico` con 16, 24, 32, 48 y 256 px (research R9): un edificio simple de color.
  - Se ejecuta con el Python del sistema (`python tools/make_icon.py`), y hay que comprobar que el archivo existe.
- [X] T005 Crear `tools/setup-dev.ps1`:
  - **`runtime/python`** (si no existe) se arma de una de dos formas:
    - **A**: copiando `%TEMP%\bsproto\python`, después de comprobar `python.exe --version` = 3.14.7 e
      `import ifcopenshell; ifcopenshell.version` = 0.9.0;
    - **B**: con `-Descargar`, bajando `https://www.python.org/ftp/python/3.14.7/python-3.14.7-embed-amd64.zip`,
      verificando el SHA-256 `d297e5ff019966817ad8502465176139f2d3d840fa4ed84b13bed399a6ab1f15` (si no coincide,
      se detiene) e instalando `engine/requirements.txt` con
      `python -m pip install --only-binary=:all: --target runtime/python/Lib/site-packages -r engine/requirements.txt`.
  - En los dos casos escribe `runtime/python/python314._pth` con las líneas `python314.zip`, `.`, `Lib\site-packages`,
    `..\..\engine` (desarrollo) y `..\engine` (programa instalado). El Python embebido ignora `PYTHONPATH` y la
    carpeta actual (research R9, ✅); una ruta que no existe se ignora.
  - Copia `C:\Windows\System32\msvcp140.dll` a `runtime/python/`, junto a los demás DLL de Visual C++ (research R9,
    riesgo 1).
  - **`app/node_modules`**: `npm --prefix app install --no-audit --no-fund` y después
    `node app/node_modules/electron/install.js` (npm 11 no corre ese paso).
  - **Salida**: una línea `OK`/`ERROR` por paso, y al final las versiones de Python, IfcOpenShell, Electron y Three.js.
- [X] T006 ⛔ PERMISO: pedir permiso y ejecutar `powershell -ExecutionPolicy Bypass -File tools/setup-dev.ps1`. Usar
  la opción A (copia del prototipo, ya autorizada); la B solo si el usuario la autoriza. Mostrar la salida real.

---

## Fase 2: Base (bloquea todas las historias)

**Propósito**: el protocolo del motor, la ventana que lo lanza, las vistas vacías y los arneses de prueba.

**⚠️ Ninguna historia puede empezar hasta terminar esta fase.**

- [X] T007 Crear el protocolo del motor en `engine/bimsimple_engine/__init__.py`, `__main__.py` y `commands.py`,
  según [core_api.md](contracts/core_api.md) "Mensajes" y la función `main()` del prototipo:
  - al arrancar, una sola línea `{"id": 0, "ok": true, "result": {"ready": true, "ifcopenshell": …, "import_ms": …}}`;
  - una línea JSON por orden, tolerando el BOM;
  - `sys.stdout` reservado para el protocolo: todo `print` va a stderr;
  - errores esperables con la clase `EngineError` (mensaje en español): `ok: false` y `error`;
  - errores inesperados: `error: "Error interno: …"` y `trace`;
  - el campo `ms` en cada respuesta;
  - orden desconocida: "Orden desconocida: <cmd>";
  - tabla de órdenes en `commands.py`.
- [X] T008 Crear `engine/bimsimple_engine/project.py` con la clase `Project`:
  - **datos**: el `ifcopenshell.file`, `path`, `dirty`, `active_storey_id`;
  - **`transaction(fn)`**: `begin_transaction` / `end_transaction`, y `discard_transaction` si hay error; marca
    `dirty = True`;
  - **`require_project()`**: "No hay ningún proyecto abierto.";
  - **`unit_scale()`**;
  - **`state()`** con la forma exacta de `State` de [core_api.md](contracts/core_api.md): `has_project`, `path`,
    `dirty`, `storeys`, `active_storey_id`, `notice`, `can_undo` (`len(file.history) > 0`) y `can_redo`.
- [X] T009 [P] Crear `engine/bimsimple_engine/geometry.py`, con la orden `meshes(ids=None)` según data-model §5:
  - con `ids`: `ifcopenshell.geom.create_shape(settings, element)`; sin `ids`:
    `ifcopenshell.geom.iterator(settings, file, multiprocessing.cpu_count())`;
  - `settings.set("use-world-coords", True)`, sin `enable-layerset-slicing` (falla con "Unexpected topology",
    RESULTADOS del prototipo);
  - `vertices` en base64 de `float32` y `faces` en base64 de `uint32`;
  - incluye `ifc_class`, `storey_id` (con `ifcopenshell.util.element.get_container`), `existing_ids` y `failures`.
- [X] T010 [P] Crear `engine/tests/conftest.py` con:
  - la fixture `project` (un `Project` nuevo por prueba) y la fixture `run_engine`, que lanza
    `runtime/python/python.exe -m bimsimple_engine` y le manda órdenes reales;
  - **generadores de IFC en `tmp_path`**, con la lógica de
    `specs/001-espacio-trabajo-pisos/investigacion/scripts/make_test_ifcs.py`:
    - `otro_programa_mm`: edificio "Torre" con "Subsuelo" −2,80, "Nivel 0" 0,00, "Nivel 1" 3,20 y "Nivel 2" 6,00,
      en milímetros;
    - `dos_edificios`, `sin_pisos`, `sin_edificio`, `danado` y `no_es_ifc`;
    - `con_elementos`: Planta Baja, Piso 1 y Piso 2 en metros, cada uno con un `IfcWall` hecho con
      `ifcopenshell.api.geometry.create_2pt_wall` + `assign_representation` + `spatial.assign_container`, y un
      `IfcDoor` sin editar en Planta Baja.
  - el módulo `engine/tests/make_fixtures.py` (`python -m tests.make_fixtures <carpeta>`), que escribe los mismos
    archivos para la prueba del programa; y `engine/tests/__init__.py`, para que `tests` se pueda importar como
    paquete.
- [X] T011 Crear `engine/tests/test_engine.py` con las pruebas del protocolo, usando `run_engine`:
  - el mensaje `id 0` con `ready`;
  - el texto exacto de una orden desconocida;
  - el texto exacto de una orden sin proyecto: "No hay ningún proyecto abierto.";
  - una línea con BOM se acepta;
  - toda respuesta tiene `ms`.
- [X] T012 Crear `app/src/main/engine.js`:
  - lanza Python (desarrollo: `<repo>/runtime/python/python.exe`; instalado:
    `path.join(process.resourcesPath, "python", "python.exe")`) con `["-u", "-m", "bimsimple_engine"]` y
    `windowsHide: true`;
  - `request(cmd, args)` devuelve una Promise asociada por `id`; `ready()` espera el mensaje `id 0`;
  - stderr va a `%APPDATA%\BIM Simple\logs\engine.log`;
  - **si el motor se cae** (evento `exit` sin pedido de cierre): rechaza las órdenes pendientes, avisa a la ventana
    con el texto exacto de [ui.md](contracts/ui.md) "Motor detenido" y lo reinicia;
  - `stop()` para el cierre normal.
- [X] T013 [P] Crear `app/src/preload.js` con `contextBridge.exposeInMainWorld("bim", …)`:
  - órdenes: `engine(cmd, args)`;
  - diálogos: `openIfc()`, `saveIfcAs()`, `confirmDelete(nombre, n)`, `askSaveChanges()`;
  - avisos y menú: `onMenu(fn)`, `onNotice(fn)`, `onState(fn)`;
  - para la prueba: `capture(nombre)` y `finishTest(resultado)`.

  Nada de Node en la página.
- [X] T014 Crear `app/src/main/main.js`:
  - `app.setAppUserModelId("BIMSimple.BIMSimple")`;
  - ventana 1400 × 860 con `contextIsolation`, `nodeIntegration: false`, `sandbox: true` e icono
    `app/build/icon.ico`; se cancela `page-title-updated`;
  - **título** según FR-004 / [ui.md](contracts/ui.md), a partir del `State` de cada respuesta;
  - **menú** "Archivo", "Edición" y "Ayuda" con los textos y atajos exactos de [ui.md](contracts/ui.md); Deshacer y
    Rehacer activos según `can_undo` / `can_redo`. El menú propio reemplaza al de Electron, así que no hay
    herramientas de desarrollo a la vista;
  - **cierre**: `close` con `preventDefault` si `dirty`, y `dialog.showMessageBox` con el título "BIM Simple", el
    mensaje «¿Guardar cambios antes de cerrar?», el detalle "Si no los guardas, se perderán." y los botones
    Guardar / No guardar / Cancelar. La misma pregunta (`askSaveChanges`) la usan Nuevo proyecto y Abrir IFC…;
  - **modo `--test`**:
    - ventana oculta con `backgroundThrottling: false`;
    - la consola de la página en `app/test-output/consola.txt`;
    - capturas con `webContents.capturePage()`;
    - al final, `resultado.json` y `app.exit(código)`.

    En este modo, **todos** los diálogos nativos (pregunta de guardar, confirmar borrado, Acerca de) se reemplazan
    por uno que registra el título y el mensaje en `resultado.json` y responde lo que diga una **cola de respuestas**
    que arma el arnés (por defecto, "No guardar" o "Borrar").
- [X] T015 [P] Crear `app/src/renderer/index.html` y `styles.css` con la pantalla de [ui.md](contracts/ui.md):
  - planta | 3D | panel de ~290 px;
  - CSP `default-src 'self'`;
  - import map para `three`, `three/addons/` y `camera-controls`, desde `../../node_modules/…`.

  Estilos a partir del prototipo.
- [X] T016 [P] Crear `app/src/renderer/viewports.js` a partir del prototipo (research R7):
  - un `WebGLRenderer` con dos zonas (`setScissor`);
  - **planta**: `OrthographicCamera` + `MapControls` con `enableRotate=false`, `zoomToCursor=true` y
    `mouseButtons {LEFT:-1, MIDDLE:PAN, RIGHT:-1}`;
  - **3D**: `PerspectiveCamera` + `CameraControls` (botón izquierdo ROTATE con `setOrbitPoint` en el punto bajo el
    ratón; Mayús + botón central ROTATE; central y derecho TRUCK; rueda DOLLY con `dollyToCursor`;
    `maxPolarAngle` 88°; `smoothTime` 0,12; `draggingSmoothTime` 0,06);
  - `THREE.Timer` en el ciclo de dibujo;
  - funciones `setStoreyGroups(map)`, `setActiveStorey(id)` (la planta muestra solo ese grupo) y `fit()` (Encuadrar);
  - para la prueba: `debugVisiblePlanStoreys()`.
- [X] T017 [P] Crear `app/src/renderer/meshes.js`: decodifica `vertices` y `faces` de base64; crea `Mesh` con
  `EdgesGeometry`, agrupados por `storey_id`; quita por `deleted_ids` o los que no estén en `existing_ids`.
- [X] T018 Crear `app/src/renderer/app.js`:
  - un solo despachador de órdenes que reemplaza el estado con cada respuesta;
  - pide las mallas que cambiaron (`changed_ids`) o todas (después de nuevo, abrir, deshacer y rehacer);
  - muestra los errores en el área de mensajes;
  - al arrancar espera el `ready` del motor;
  - con `?test=1`, carga `app/test/window-test.js`.
- [X] T019 Crear el arnés de `app/test/window-test.js`:
  - pasos con nombre, `ok`, `ms` y error;
  - una captura de calentamiento antes de la primera, porque la ventana oculta devuelve un cuadro viejo;
  - `resultado.json` con los pasos, las capturas y `RESULTADO: TODO OK` o `N FALLAS`, que termina con código 1;
  - **regla SC-004**: un paso del navegador de pisos (agregar, editar, borrar, activar, deshacer, rehacer) que tarde
    más de 200 ms, desde la orden hasta el redibujo, cuenta como falla;
  - la sección "Entorno":
    - el motor listo en menos de 10 s (SC-007);
    - los textos de los menús según [ui.md](contracts/ui.md);
    - al arrancar no hay proyecto, la tabla está vacía con "No hay ningún proyecto abierto" y no hay mallas en
      la escena (FR-006).
- [X] T020 Ejecutar `runtime\python\python.exe -m pytest engine\tests -q` y `npm --prefix app test`. Mostrar la
  salida real: la base pasa. Hacer commit de las fases 1 y 2.

**Punto de control**: el programa arranca con la ventana oculta, el motor responde y las pruebas base pasan.

---

## Fase 3: Historia 1. Abrir BIM Simple, empezar un proyecto y guardarlo (P1) 🎯 MVP

**Objetivo**: pantalla de BIM Simple, proyecto nuevo con Planta Baja, guardar y guardar como, título y pregunta al cerrar.

**Prueba independiente**: nuevo proyecto → guardar → el IFC tiene Proyecto > Sitio > Edificio > Planta Baja a 0,00 y
pasa la validación IFC4.

### Pruebas de la Historia 1

- [X] T021 [US1] En `engine/tests/test_engine.py`, agregar las pruebas de la Historia 1:
  - **`new_project`**: el archivo es `IFC4` con unidad `METRE` y nombres "Proyecto", "Sitio", "Edificio",
    "Planta Baja"; la Planta Baja tiene `elevation` 0,0, `height` 3,0 (`GrossHeight`) y está activa;
    `dirty=False`; `can_undo=False`;
  - un segundo `new_project` deja un solo piso;
  - **`save_project(path)`**: el archivo existe, `state.path` es esa ruta y `dirty=False`;
  - `save_project()` sin ruta y sin ruta previa devuelve "Elige dónde guardar el proyecto.";
  - **`validate_file`** del archivo guardado devuelve 0 errores.

### Implementación de la Historia 1

- [X] T022 [US1] En `engine/bimsimple_engine/storeys.py`:
  - `create_storey(project, name, elevation, height)`: `root.create_entity("IfcBuildingStorey")` +
    `aggregate.assign_object` + `geometry.edit_object_placement` (Z = cota) + `attribute.edit_attributes(Elevation)`
    + `pset.add_qto("Qto_BuildingStoreyBaseQuantities")` + `edit_qto(GrossHeight)`;
  - `list_storeys(project)` según data-model §3: cota =
    `ifcopenshell.util.placement.get_storey_elevation(piso) × escala`; «Altura: distancia al piso de arriba; para
    el más alto, `Qto_BuildingStoreyBaseQuantities.GrossHeight`, o 3,00 si no existe»; `elements` = cantidad de
    `IfcElement` sin aberturas; orden de mayor a menor cota, con empate por nombre;
  - `notice(project)`, con los textos exactos de [core_api.md](contracts/core_api.md).
- [X] T023 [US1] En `engine/bimsimple_engine/project.py`:
  - **`new_project`**, con la receta del prototipo pero **sin** el tipo de muro (es de la función 2):
    `ifcopenshell.api.project.create_file("IFC4")`; unidades SI LENGTHUNIT, AREAUNIT, VOLUMEUNIT y PLANEANGLEUNIT;
    contextos Model/Body/MODEL_VIEW y Plan/Axis/GRAPH_VIEW; Sitio y Edificio con su ubicación; Planta Baja con
    `create_storey`; la activa; vacía `history`/`future`; `dirty=False`;
  - **`save_project(path=None)`**: `file.write`, fija `path` y `dirty=False`;
  - **`validate_file(path)`**: `ifcopenshell.validate.json_logger()` +
    `validate(path, logger, express_rules=True)`, y devuelve la cantidad de errores y los 5 primeros mensajes.

  Registrar las órdenes en `commands.py`.
- [X] T024 [P] [US1] Crear `app/src/main/validator.js`. Después de cada guardado lanza un **segundo** motor
  (`python -m bimsimple_engine`), le manda `validate_file` y lo cierra; envía a la página "Guardado. Validación IFC4:
  N errores." (research R6).
- [X] T025 [US1] Crear `app/src/renderer/storey-panel.js` (primera parte):
  - **sin proyecto**: "No hay ningún proyecto abierto" y los botones Nuevo proyecto / Abrir IFC…;
  - **con proyecto**: nombre del archivo o "Proyecto sin guardar" y "• Cambios sin guardar";
  - `notice`;
  - tabla Piso | Cota | Altura con dos decimales y coma decimal, el activo con "●" y fondo resaltado;
  - área de mensajes.
- [X] T026 [US1] En `app/src/main/main.js`:
  - **Archivo > Nuevo proyecto**: pregunta si hay cambios y llama a `new_project`;
  - **Guardar IFC**: `save_project`; si responde "Elige dónde guardar el proyecto.", sigue como Guardar como;
  - **Guardar IFC como…**: `dialog.showSaveDialog` con el filtro "Modelo IFC" (`*.ifc`) y `save_project(path)`;
  - **Salir**: igual que la X;
  - después de guardar, `validator.js`; actualizar el título.
- [X] T027 [US1] En `app/src/main/main.js`, el menú **Ayuda > Acerca de BIM Simple**: `dialog.showMessageBox` con el
  título "Acerca de BIM Simple", el botón "Cerrar" y el **texto exacto** de [ui.md](contracts/ui.md) (versión,
  IfcOpenShell 0.9.0 bajo LGPL-3.0 con el enlace https://github.com/IfcOpenShell/IfcOpenShell, Electron, Three.js y
  camera-controls bajo MIT, Python bajo PSF, y la carpeta «licencias»). La versión sale de `app.getVersion()`.
  Es el aviso de licencias que exige la constitución (Principio VI) y FR-003.
- [X] T028 [US1] En `app/test/window-test.js`, sección "Historia 1":
  - Nuevo proyecto → la tabla muestra "● Planta Baja | 0,00 | 3,00" y el título es "Proyecto sin guardar — BIM Simple";
  - guardar como en `app/test-output/prueba.ifc` → el título es "prueba.ifc — BIM Simple" y aparece el mensaje de
    validación con 0 errores;
  - Ayuda > Acerca de → el diálogo registrado contiene "LGPL-3.0" y el enlace de IfcOpenShell;
  - captura `h1`.

  La pregunta al cerrar o al hacer Nuevo con cambios se prueba en la Historia 2 (T035), porque en la Historia 1
  todavía no hay ninguna acción que deje cambios sin guardar.
- [X] T029 [US1] Ejecutar las dos pruebas automáticas y mostrar la salida real; todas pasan. Hacer commit.

**Punto de control**: la Historia 1 funciona y se prueba sola.

---

## Fase 4: Historia 2. Organizar los pisos del edificio (P2)

**Objetivo**: agregar arriba y abajo, editar nombre, cota y altura con la regla de ArchiCAD, borrar, deshacer y rehacer.

**Prueba independiente**: proyecto nuevo → dos pisos → renombrar → cambiar una altura → borrar uno → guardar y
reabrir: mismos nombres, cotas y alturas.

### Pruebas de la Historia 2

- [X] T030 [US2] En `engine/tests/test_engine.py`, agregar las pruebas de la Historia 2:
  - **Escenarios** 1 a 5 de spec.md, con los valores exactos: "Piso 1" a 3,00 y "Sótano 1" a −3,00; altura de
    Planta Baja 3,50 → Piso 1 a 3,50 y Piso 2 a 6,50.
  - **Con `con_elementos`**:
    - los muros se mueven con su piso (Z del mundo);
    - borrar un piso con elementos: `count_storey_elements` es correcto, quedan 0 `IfcElement` sin contenedor y se
      activa el piso inferior.
  - **Rechazos con su texto exacto**: cota menor o igual que la del piso de abajo, altura 0, nombre vacío, borrar el
    único piso.
  - **Nombres repetidos**: se permiten.
  - **Deshacer y rehacer**: después de cada acción, el estado vuelve a ser idéntico.
  - **Guardar y reabrir** con `ifcopenshell.open`: `Elevation` = cota de la ubicación, `GrossHeight` correcto,
    validación 0 errores (FR-019, SC-002, SC-003).
  - **Tiempo**: cada orden con 10 pisos tarda menos de 50 ms en el motor (base para SC-004).

### Implementación de la Historia 2

- [X] T031 [US2] En `engine/bimsimple_engine/storeys.py`, implementar cada orden en **una** transacción, con las
  recetas de research R4 (`verif_pisos.py`) y estas reglas de data-model §3:
  - **`add_storey_above`**: «Cota = cota del más alto + su altura. Altura = la del más alto. Nombre "Piso N"
    (N = pisos con cota > 0 contando el nuevo).»
  - **`add_storey_below`**: «Cota = cota del más bajo − 3,00. Altura 3,00. Nombre "Sótano N" (N = pisos con
    cota < 0 contando el nuevo).»
  - **`edit_storey(id, name?, elevation?, height?)`**:
    - Aplica solo lo que viene. Nombre «No vacío».
    - Altura: «Si es el más alto, solo `GrossHeight`. Si no, Δ = nueva − actual: todos los pisos de arriba se
      mueven Δ con sus elementos y `GrossHeight(i)` = nueva.» Altura «Mayor que 0».
    - Cota: «Se rechaza si es menor o igual que la del piso de abajo. Δ = nueva − actual: el piso *i* y todos los
      de arriba se mueven Δ con sus elementos. `GrossHeight` del piso de abajo = nueva distancia.»
    - Para mover se usa
      `ifcopenshell.api.geometry.edit_object_placement(…, is_si=True, should_transform_children=True)` +
      `Elevation`.
    - Devuelve `changed_ids`, con los pisos y elementos movidos.
  - **`count_storey_elements(id)`**.
  - **`delete_storey(id)`**: «Se rechaza si es el único». `ifcopenshell.api.root.remove_product` de cada elemento y
    después del piso; activa el inferior o, si no hay, el superior; devuelve `deleted_ids`.

  Textos de error exactos de [core_api.md](contracts/core_api.md).
- [X] T032 [US2] En `engine/bimsimple_engine/project.py`, las órdenes `undo` y `redo` (`file.undo()` /
  `file.redo()`):
  - `dirty=True`;
  - si el piso activo dejó de existir, pasa al de cota más cercana a 0,00;
  - textos "No hay nada que deshacer." / "No hay nada que rehacer.".
- [X] T033 [US2] En `app/src/renderer/storey-panel.js`:
  - **un clic** selecciona la fila;
  - **botones**: Agregar piso arriba, Agregar piso abajo, Editar piso… y Borrar piso, que se desactivan según
    [ui.md](contracts/ui.md);
  - **Editar piso…**: diálogo HTML con Nombre, Cota (m) y Altura (m), que acepta coma decimal y manda **un solo**
    `edit_storey` con lo que cambió;
  - **Borrar piso**: si `count_storey_elements > 0`, `bim.confirmDelete` muestra el diálogo nativo «El piso «X»
    tiene N elementos. Se borrarán junto con el piso.» con [Borrar] / [Cancelar].
- [X] T034 [US2] En `app/src/main/main.js`, la confirmación de borrado (`dialog.showMessageBox`) y Edición >
  Deshacer / Rehacer (Ctrl+Z / Ctrl+Y). En `app/src/renderer/app.js`, actualizar las mallas con `changed_ids` /
  `deleted_ids`.
- [X] T035 [US2] En `app/test/window-test.js`, sección "Historia 2":
  - agregar arriba dos veces y abajo una → la tabla tiene 4 filas en el orden correcto;
  - editar la Planta Baja con altura 3,50 desde el diálogo → los valores de la tabla;
  - una cota inválida → el mensaje exacto y la tabla sin cambios;
  - borrar "Sótano 1";
  - Deshacer y Rehacer desde el menú → la tabla;
  - **pregunta por cambios sin guardar (FR-010)**:
    - con cambios, Archivo > Nuevo proyecto y la respuesta "Cancelar" en la cola → se registró «¿Guardar cambios
      antes de cerrar?» y la tabla no cambió;
    - con cambios, cerrar la ventana y la respuesta "No guardar" → se registró la pregunta y la ventana se cerró
      (último paso de la prueba);
  - captura `h2`.
- [X] T036 [US2] Ejecutar las dos pruebas automáticas y mostrar la salida real. Hacer commit.

**Punto de control**: las Historias 1 y 2 funcionan.

---

## Fase 5: Historia 3. Trabajar en un piso (P3)

**Objetivo**: doble clic activa un piso; la planta muestra solo ese piso; navegación al estilo ArchiCAD/Revit.

**Prueba independiente**: con `con_elementos`, doble clic en "Piso 1" → es el único activo, la planta muestra solo
sus elementos y el 3D muestra todos.

### Pruebas de la Historia 3

- [X] T037 [US3] En `engine/tests/test_engine.py`:
  - `activate_storey` cambia `active_storey_id` sin tocar `dirty` ni `can_undo`;
  - siempre hay exactamente uno activo (FR-021): después de borrar el activo y después de deshacer;
  - `meshes()` de `con_elementos` devuelve cada muro con su `storey_id`.

### Implementación de la Historia 3

- [X] T038 [US3] En `engine/bimsimple_engine/storeys.py`, la orden `activate_storey(id)`: «Activar no cambia el IFC
  ni marca cambios»; el piso tiene que existir. Registrarla en `commands.py`.
- [X] T039 [US3] En `app/src/renderer/storey-panel.js`, el **doble clic** en una fila manda `activate_storey`
  (FR-020). Debajo de la tabla, la ayuda "Doble clic en un piso para activarlo.".
- [X] T040 [US3] En `app/src/renderer/viewports.js` y `app.js`:
  - al cambiar el piso activo, `setActiveStorey(id)` y la etiqueta "Planta — <piso>";
  - el botón **Encuadrar** llama a `fit()`;
  - la primera vez que aparecen elementos, encuadre automático.
- [X] T041 [US3] En `app/test/window-test.js`, sección "Historia 3":
  - antes de la ventana, generar los IFC de prueba con
    `runtime\python\python.exe -m tests.make_fixtures app\test-output\fixtures` (desde `engine/`);
  - abrir `con_elementos.ifc`;
  - `dblclick` en "Piso 1" → activo "Piso 1" y `debugVisiblePlanStoreys()` = [Piso 1];
  - el 3D muestra los 3 grupos;
  - la activación tarda menos de 0,2 s (SC-004);
  - **borrar un piso con elementos (FR-017)**: seleccionar "Piso 2" y pulsar Borrar piso, con "Cancelar" en la
    cola → se registró «El piso «Piso 2» tiene 1 elemento. Se borrarán junto con el piso.» y no se borró nada;
    repetir con "Borrar" → el piso y su muro desaparecen de la tabla y de la escena;
  - captura `h3`.
- [X] T042 [US3] Ejecutar las dos pruebas automáticas y mostrar la salida real. Hacer commit.

**Punto de control**: las Historias 1 a 3 funcionan.

---

## Fase 6: Historia 4. Abrir un IFC existente (P4)

**Objetivo**: abrir archivos de BIM Simple o de otros programas sin perder el proyecto actual si el archivo no sirve.

**Prueba independiente**: abrir `otro_programa_mm.ifc` → 4 pisos con sus cotas; "Guardar IFC como…" no toca el original.

### Pruebas de la Historia 4

- [X] T043 [US4] En `engine/tests/test_engine.py`:
  - **`otro_programa_mm`**: 4 pisos con cotas −2,80 / 0,00 / 3,20 / 6,00 y alturas por distancia; activo "Nivel 0";
    `dirty=False`;
  - **`dos_edificios`, `sin_pisos` y `sin_edificio`**: `notice` con su texto exacto;
  - **`danado` y `no_es_ifc`**: el texto exacto del error, y el proyecto abierto antes sigue igual (misma ruta y
    mismos pisos);
  - **guardar como** sobre un archivo abierto deja el original sin cambios (hash);
  - **`con_elementos`**: después de abrir y guardar, se conservan la puerta y los muros (misma cantidad de `IfcElement`).

### Implementación de la Historia 4

- [X] T044 [US4] En `engine/bimsimple_engine/project.py`, la orden `open_project(path)` según research R5:
  1. `ifcopenshell.open` en `try`, exigiendo `IfcProject`; si falla, `EngineError` con el texto exacto, **sin tocar**
     el proyecto abierto;
  2. reemplaza el archivo, `path`, `dirty=False`, y vacía el historial;
  3. activa el piso de cota más cercana a 0,00.
- [X] T045 [US4] En `app/src/main/main.js`, **Archivo > Abrir IFC…**: pregunta si hay cambios, abre
  `dialog.showOpenDialog` con el filtro "Modelo IFC" (`*.ifc`) y llama a `open_project`. En `app.js`, pide todas las
  mallas, encuadra y muestra el error si lo hay.
- [X] T046 [US4] En `app/test/window-test.js`, sección "Historia 4":
  - abrir `otro_programa_mm.ifc` → 4 filas, activo "Nivel 0";
  - abrir `danado.ifc` → el mensaje exacto y la tabla sin cambios;
  - **pregunta por cambios sin guardar (FR-010)**: agregar un piso; Archivo > Abrir IFC… con "Cancelar" en la cola →
    se registró la pregunta y la tabla no cambió; repetir con "No guardar" → se abre el archivo elegido;
  - captura `h4`.
- [X] T047 [US4] Ejecutar las dos pruebas automáticas y mostrar la salida real. Hacer commit.

**Punto de control**: las cuatro historias pasan las pruebas automáticas.

---

## Fase 7: Cierre, instalador y prueba manual

**Propósito**: robustez, instalador, prueba con ventana, documentos y el bloqueo del repositorio.

- [X] T048 En `app/test/window-test.js`, sección "Motor detenido":
  - terminar el proceso del motor con un gancho de prueba de `engine.js`;
  - comprobar que aparece el aviso exacto de [ui.md](contracts/ui.md), que el motor vuelve a estar listo sin proyecto
    y que las órdenes posteriores funcionan.

  Ejecutar y mostrar la salida.
- [X] T049 [P] ⛔ PERMISO (solo para descargar el texto de la LGPL-3.0): crear `app/build/licencias/` con los textos
  de licencia de Electron (MIT), Three.js (MIT), camera-controls (MIT), Python (`runtime/python/LICENSE.txt`) y las
  dependencias de Python (`*.dist-info`).
  - Para IfcOpenShell, los textos GPL-3.0 y LGPL-3.0. El de GPL-3.0 es el `LICENSE` actual del repositorio; el de
    LGPL-3.0 se descarga de https://www.gnu.org/licenses/lgpl-3.0.txt después de pedir permiso.
  - Agregar `app/build/LEEME-licencias.txt`, que dice que BIM Simple usa IfcOpenShell bajo LGPL y dónde está su
    código fuente.
- [X] T050 ⛔ PERMISO: pedir permiso para descargar electron-builder y ejecutar
  `npm --prefix app install --save-dev --save-exact electron-builder@26.17.0`. Agregar a `app/package.json`:
  - el script `"dist": "electron-builder --win"`;
  - el bloque `"build"` de research R9 / [programa.md](contracts/programa.md):
    - `appId: "BIMSimple.BIMSimple"`, `productName: "BIM Simple"`, `files` que excluyan `test/`;
    - `extraResources`: `../runtime/python` → `python` y `../engine/bimsimple_engine` → `engine/bimsimple_engine`,
      sin `__pycache__`;
    - `win.target: nsis x64`, con el icono `build/icon.ico`;
    - `nsis`: `oneClick: true`, `perMachine: false`, `createDesktopShortcut: true`,
      `createStartMenuShortcut: true`, `shortcutName: "BIM Simple"`, `packElevateHelper: false`,
      `differentialPackage: false`, **`deleteAppDataOnUninstall: true`** (borra `%APPDATA%\BIM Simple` al
      desinstalar, para SC-005);
    - `include: build/installer.nsh`, que borra `%LOCALAPPDATA%\bim-simple-updater` al desinstalar.
  - El motor instalado se encuentra por la línea `..\engine` del `._pth` (T005). **No** usar `PYTHONPATH` ni `cwd`:
    el Python embebido los ignora (research R9, ✅).
- [X] T051 ⛔ PERMISO: ejecutar `npm --prefix app run dist`, medir el tamaño de `app\dist\BIM Simple Setup 0.1.0.exe`
  y **pedir permiso para instalarlo**. Después de instalar, comprobar y mostrar:
  - la ruta de instalación y los dos accesos directos;
  - que arranca, con permiso para abrir la ventana (SC-007 cronometrado);
  - que se desinstala desde "Agregar o quitar programas" sin dejar `%LOCALAPPDATA%\Programs\…`, ni
    `%APPDATA%\BIM Simple`, ni `%LOCALAPPDATA%\bim-simple-updater` (SC-005).
- [ ] T052 ⛔ PERMISO: pedir permiso para abrir BIM Simple con ventana y hacer con el usuario la parte B de
  [quickstart.md](quickstart.md) (B1 a B5): arranque, Acerca de, proyecto, el tiempo de SC-001, los clics de SC-006,
  pisos, navegación, deshacer, salir, y abrir el IFC en otro programa BIM (SC-003). Anotar los resultados en el mensaje de commit de T057 y corregir lo que falle, con su
  prueba automática.
- [X] T053 Anotar en `specs/001-espacio-trabajo-pisos/research.md` (R9) los pendientes **antes de vender**:
  - la prueba en una PC limpia (Windows Sandbox o una máquina virtual; activar Windows Sandbox lo hace el usuario,
    porque pide administrador) para confirmar `MSVCP140.dll`;
  - la firma de código;
  - aclarar CGAL.
- [X] T054 [P] Reescribir `README.md`:
  - qué es BIM Simple;
  - requisitos (Windows 11, Node.js 24);
  - cómo preparar el entorno (`tools/setup-dev.ps1`), correr las pruebas y armar el instalador;
  - la estructura `app/` + `engine/`, el método Spec Kit (`.specify/`, `specs/`) y la licencia
    ("Todos los derechos reservados", pendiente de T056).
- [X] T055 [P] Reescribir `PRUEBA_MANUAL.md` como la lista de prueba manual para el usuario: la parte B de
  [quickstart.md](quickstart.md) en lenguaje simple y con casillas.
- [ ] T056 ⛔ BLOQUEO R11 (decisión del usuario): **antes de cualquier `git push`**, el usuario tiene que:
  1. hacer privado el repositorio `nestorfelipe00/bim-simple`, él mismo o autorizando
     `gh repo edit nestorfelipe00/bim-simple --visibility private --accept-visibility-change-consequences`;
  2. aprobar el reemplazo de `LICENSE` por el aviso "Copyright (c) 2026 Nestor Torres. Todos los derechos
     reservados."

  Solo después, y con permiso, se suben los commits.
- [ ] T057 Marcar la especificación como implementada (`**Estado**: Implementada` en [spec.md](spec.md)), comprobar
  que todas las tareas de este archivo están marcadas y hacer el commit final con los resultados de T052.

---

## Dependencias y orden de ejecución

### Dependencias entre fases

- **Fase 1 (Preparación)**: sin dependencias. T006 necesita permiso.
- **Fase 2 (Base)**: depende de la Fase 1. **Bloquea todas las historias.**
- **Fases 3 a 6 (US1 a US4)**: dependen de la Fase 2.
  - US2, US3 y US4 usan la pantalla y el panel de US1 para verse, pero sus pruebas del motor son independientes.
  - US3 y US4 usan `con_elementos`, `otro_programa_mm` y los demás de T010.
- **Fase 7**: depende de todas las historias. T049 (texto LGPL), T050, T051 y T052 necesitan permiso. T056 bloquea
  cualquier subida.

### Dentro de cada historia

- Primero las pruebas del motor, después el motor, después la ventana y la interfaz, después la sección de la prueba
  del programa, y por último las dos pruebas y el commit.
- Varias tareas tocan los mismos archivos (`storeys.py`, `project.py`, `main.js`, `storey-panel.js`,
  `test_engine.py`, `window-test.js`), así que dentro de una historia van **en orden**.

### Oportunidades de paralelo

- **Fase 1**: T002, T003 y T004.
- **Fase 2**: T009, T010, T013, T015, T016 y T017 (archivos distintos), después de T007 y T008 para el motor.
- **Fase 3**: T024 (`validator.js`) en paralelo con T022 y T023.
- **Fase 7**: T049, T054 y T055.

## Ejemplo de paralelo: Fase 2

```text
Tarea: "T009 [P] Mallas en engine/bimsimple_engine/geometry.py"
Tarea: "T010 [P] IFC de prueba en engine/tests/conftest.py"
Tarea: "T015 [P] Pantalla en app/src/renderer/index.html y styles.css"
Tarea: "T016 [P] Vistas en app/src/renderer/viewports.js"
Tarea: "T017 [P] Mallas en app/src/renderer/meshes.js"
```

## Estrategia de implementación

### MVP primero (solo la Historia 1)

1. Fases 1 y 2, con el permiso de T006.
2. Fase 3 (US1).
3. **Detenerse y validar**: las dos pruebas en verde. Si el usuario quiere, prueba manual B1-B2 (requiere permiso
   para abrir la ventana).

### Entrega incremental

Cada historia termina con las dos pruebas completas en verde (las anteriores siguen pasando) y un commit. Después
US2 → US3 → US4 → Fase 7 (instalador y prueba manual).

## Notas

- Puntos ⛔: T006 (entorno), T049 (descarga del texto LGPL), T050 (electron-builder), T051 (armar e instalar), T052
  (ventana y prueba manual) y T056 (repositorio y licencia, decisión del usuario).
- **FR-023** (los elementos nuevos quedan en el piso activo) se verifica en la función 002, que trae las herramientas
  de dibujo. En esta función se exige que el motor mantenga `active_storey_id` (T037) para que esas herramientas lo usen.
- Nada de esta función toca otras instalaciones (constitución, Principio III).
- No borrar archivos sin permiso. `PLAN.md` (referencia histórica del MVP) solo se borra si el usuario lo pide.
