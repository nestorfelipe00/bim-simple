# BIM Simple como programa hecho con That Open (y con Three.js + IfcOpenShell)

Investigación del 2026-10-11. Solo documentación y código fuente publicados: no se instaló ni se ejecutó nada.

**Marcas**: 📄 leído en el código fuente publicado (URL y archivo) · 📖 documentación oficial · 🌐 terceros ·
⚠️ no verificado o inferido (hay que comprobarlo en la prueba práctica).

**Versiones consultadas** (registry.npmjs.org, `latest` al 2026-10-11) 📄:

| Paquete | Versión | Publicada | Licencia | Tamaño npm (sin comprimir) |
|---|---|---|---|---|
| `@thatopen/components` | 3.4.9 | 2026-10-06 | MIT | 3,4 MB |
| `@thatopen/components-front` | 3.4.5 | 2026-10-06 | MIT | 0,7 MB |
| `@thatopen/fragments` | 3.4.8 | 2026-10-06 | MIT | 25,1 MB |
| `@thatopen/ui` | 3.4.14 | 2026-10-01 | MIT | 0,8 MB |
| `web-ifc` | 0.0.78 | 2026-09-21 | **MPL-2.0** | 24,8 MB |
| `three` | 0.186.1 (r186) | 2026-09-24 | MIT | ~23 MB |
| `electron` | 44.7.0 | 2026-10-07 | MIT | runtime win-x64: zip de 158 MB |

`@thatopen/components` 3.4.9 pide como pares `three >=0.182.0`, `web-ifc >=0.0.77`, `camera-controls >=3.1.2` y
`@thatopen/fragments ~3.4.7`. Las rutas de código citadas son de la rama `main` de
github.com/ThatOpen/engine_components y github.com/ThatOpen/engine_fragment, leídas el 2026-10-11 (corresponden a 3.4.x).

---

## Resumen

- **Electron resuelve todo lo que Blender no deja**: título, icono propio en la barra de tareas, menú en español, la X
  interceptada con "Guardar / No guardar / Cancelar", diálogos nativos de Windows, doble clic y caché separada. Desaparecen
  D1–D7. Tauri también puede, pero exige Rust y las herramientas de compilación de C++, que no están instaladas. La web
  sola falla en D5: el navegador muestra su propio aviso genérico.
- **That Open trae casi todo el "visor"**: planos por piso con plano de corte (`Views.createFromIfcStoreys`), rellenos de
  corte por categoría (`ClipStyler`), clasificación por piso, ocultar, resaltar, medir, imán a punto, arista o cara, y grilla.
  Tiene dos límites importantes para BIM Simple:
  1. Un modelo Fragments usa **una sola cámara** y un solo objeto en escena 📄. Para tener planta y 3D lado a lado hay que usar
     dos "worlds" y cargar el modelo dos veces, o dibujar los dos en un solo renderer con *scissor*. No hay ejemplo oficial ⚠️.
  2. **Fragments no exporta IFC** 📖. Guardar IFC exige otro motor: `web-ifc` (bajo nivel) o IfcOpenShell.
- **No trae deshacer general** 📄. Solo el historial de ediciones de Fragments. Se usa el patrón *Command* o las transacciones
  de IfcOpenShell.
- **Opinión**: para un programa que *dibuja* (no solo mira), la base más sólida es **Electron + Three.js + IfcOpenShell en un
  Python embebido**. That Open queda como opcional: su librería de interfaz (`@thatopen/ui`) y, más adelante, la visualización
  de modelos de referencia grandes. Se detalla en la sección 8.

---

## 1. Programa de escritorio o aplicación web

**Decisión**: **Electron**.

**Por qué**: cubre todas las diferencias D1–D7 con API documentadas. Todo se escribe en un solo lenguaje (TypeScript) y ya
están instalados Node.js 24 y npm 11. Es el entorno con más documentación y ejemplos, algo que pesa para un usuario que no
programa y trabaja con ayuda de IA. Su costo es el peso, unos 150 MB comprimidos solo de motor.

**Alternativas**:
- **Tauri 2**: es más liviano (usa el WebView2 de Windows) y técnicamente equivalente. Pero obliga a instalar Rust y las
  Microsoft C++ Build Tools ("Desktop development with C++") y suma un segundo lenguaje (Rust).
- **Solo web, o PWA instalada**: no se instala nada. Pero no se puede interceptar la X con un diálogo propio, cada "Guardar"
  sobre un archivo pide permiso al reabrir la sesión, solo funciona en Chrome o Edge, y los datos viven en el perfil del
  navegador.

### Evidencia: Electron
- **Título e icono**: `win.setTitle(title)` "Changes the title of native window" y `win.setIcon(icon)` (Windows y Linux).
  Además, el evento `page-title-updated` permite impedir que el `<title>` de la página cambie el título 📖
  (electronjs.org/docs/latest/api/browser-window).
- **Grupo propio en la barra de tareas**: `app.setAppUserModelId(id)` "Changes the Application User Model ID" 📖
  (electronjs.org/docs/latest/api/app). La guía del instalador Squirrel también recomienda llamarlo 📖. Es justo lo que impide
  Blender (D2).
- **Menús**: `Menu.setApplicationMenu(menu)`. "On Windows and Linux, the menu will be set as each window's top menu" 📖. Con
  `null` desaparece la barra de menú 📖. Las etiquetas (`label`) las define la aplicación, así que pueden ir en español 📖
  (api/menu-item). La documentación no dice si los `role` traen etiquetas traducidas ⚠️; se evitan usando `click` propio.
- **Interceptar el cierre**: el evento `close` de BrowserWindow se cancela con `event.preventDefault()`. Con `beforeunload` en
  Electron, "returning any value other than `undefined` would cancel the close" 📖. Además, `before-quit` se puede prevenir 📖.
- **Diálogo de tres botones**: `dialog.showMessageBox(win, { buttons: ['Guardar','No guardar','Cancelar'], cancelId: 2,
  defaultId: 0, noLink: true })` 📖 (api/dialog). Los botones son libres. `cancelId` decide qué pasa con Esc.
- **Abrir y guardar**: `dialog.showOpenDialog` y `dialog.showSaveDialog` con `filters`, `defaultPath`, `title` y
  `buttonLabel` 📖. Son los diálogos nativos de Windows, en el idioma de Windows ⚠️ (la documentación no lo dice).
- **Instalador**:
  - Electron Forge es la herramienta oficial 📖 (tutorial-packaging): `npm run make` y `@electron-forge/maker-squirrel`, que
    genera `{appName} Setup.exe` y se describe como "no-prompt, no-hassle, no-admin" 📖 (electronforge.io). También existen
    makers AppX/MSIX y WiX.
  - Alternativa de terceros: **electron-builder** con NSIS 📖 (app-builder-lib 26.15.3, `nsisOptions.d.ts`): `oneClick`
    (por defecto `true`), `perMachine` (por defecto `false`, es decir, por usuario y sin permisos de administrador),
    `allowToChangeInstallationDirectory`, `installerLanguages`, `deleteAppDataOnUninstall`.
  - Firmar el instalador es opcional, pero sin firma Windows SmartScreen advierte ⚠️ 📖 ("so it does not trigger the security
    checks").
- **Tamaño**: `electron-v44.7.0-win32-x64.zip` pesa 158.293.649 bytes 📄 (release de GitHub). Instalado ocuparía unos
  300–400 MB ⚠️ y el instalador comprimido unos 100–130 MB ⚠️. Se pueden quitar los idiomas de Chromium que no se usan ⚠️.
- **Licencia**: MIT 📄 (github.com/electron/electron/LICENSE).
- **Seguridad**: la lista oficial pide `contextIsolation`, sandbox, validar el emisor del IPC y no usar `file://` sino un
  protocolo propio (`protocol.handle`) 📖 (tutorial/security, api/protocol).

### Evidencia: Tauri 2
- **Requisitos en Windows**: Microsoft C++ Build Tools con "Desktop development with C++", Rust con la cadena MSVC (`rustup`)
  y WebView2, que "is already installed on Windows 10 (from version 1803 onward)" 📖 (v2.tauri.app/start/prerequisites).
- **Cierre**: `onCloseRequested`, con un ejemplo que usa `event.preventDefault()` 📖 (reference/javascript/api/namespacewindow).
- **Diálogo de tres botones**: desde el plugin de diálogos 2.4.0, `message(..., { buttons: { yes:'Guardar', no:'No guardar',
  cancel:'Cancelar' } })`. El tipo `MessageDialogButtonsYesNoCancel` admite etiquetas propias 📖
  (reference/javascript/dialog).
- **Instalador**: NSIS (`-setup.exe`) o MSI (WiX v3). Por defecto instala por usuario y sin permisos de administrador.
  WebView2 en modo `downloadBootstrapper` suma 0 MB 📖 (distribute/windows-installer).
- **Tamaño**: un programa mínimo "can be less than 600KB" 📖 (v2.tauri.app/start).
- **Licencia**: "MIT or MIT/Apache 2.0 where applicable" 📄 (README de tauri-apps/tauri).
- **Python como proceso aparte**: está documentado como *sidecar* ("Python CLI applications or API servers bundled using
  `pyinstaller`") 📖 (develop/sidecar).

### Evidencia: solo web, o PWA
- **Guardar sobre el archivo**: `showSaveFilePicker` es "experimental", solo funciona en HTTPS y "Transient user activation
  is required" 📖 (MDN). Funciona en Chromium (Chrome y Edge), no en Firefox ni Safari 📖
  (developer.chrome.com/docs/capabilities/web-apis/file-system-access). Tras cerrar todas las pestañas del sitio, "they will be
  re-prompted for access to the files" 📖.
- **Doble clic en un `.ifc`**: solo con la PWA instalada (`file_handlers`, Chrome y Edge 102 o posterior) 📖.
- **Sin conexión**: un *service worker* sirve los recursos desde la caché (Cache Storage) 📖 (web.dev/learn/pwa).
- **Ventana propia**: la PWA en modo `standalone` muestra "an OS-standard window without any browser navigation UI" y el título
  sale del `<title>` 📖 (web.dev/learn/pwa/app-design).
- **Salir con cambios**: los navegadores "Only show a generic browser-specified string… cannot be controlled by the webpage
  code" 📖 (MDN, `beforeunload`). Es decir, no hay Guardar / No guardar / Cancelar.

### Qué diferencias D1–D7 desaparecen

| # | Diferencia en Blender | Electron | Tauri 2 | Web o PWA |
|---|---|---|---|---|
| D1 | Título "… - Blender 5.2.0 LTS" | ✅ `setTitle` 📖 | ✅ `setTitle` 📖 | ✅ en la PWA instalada (`<title>`) 📖; en una pestaña se ve además el navegador |
| D2 | Icono de Blender en la barra de tareas | ✅ `icon` + `setAppUserModelId` 📖 | ✅ icono propio ⚠️ | ⚠️ la PWA instalada tiene icono propio, pero el proceso es del navegador |
| D3 | Menús y área de Blender que no se pueden quitar | ✅ el menú es 100 % propio o no hay menú 📖 | ✅ | ⚠️ los atajos del navegador (Ctrl+W, F5, Ctrl+P…) siguen activos |
| D4 | Explorador de archivos de Blender | ✅ diálogo nativo de Windows 📖 | ✅ nativo 📖 | ⚠️ selector nativo, pero con avisos de permiso y solo en Chromium 📖 |
| D5 | La X no se puede interceptar | ✅ `close` + `showMessageBox` 📖 | ✅ `onCloseRequested` + `YesNoCancel` 📖 | ❌ solo el aviso genérico del navegador 📖 |
| D6 | Las listas no distinguen el doble clic | ✅ evento `dblclick` del DOM ⚠️ | ✅ ⚠️ | ✅ ⚠️ |
| D7 | Caché compartida con el Blender del usuario | ✅ carpeta propia (`app.getPath('userData')`) ⚠️ | ✅ ⚠️ | ⚠️ los datos quedan en el perfil del navegador y se borran al limpiar datos |

---

## 2. Dos vistas lado a lado (planta 2D + 3D) con That Open

**Decisión**: se puede, con **dos *worlds*** (escena + cámara + renderer cada uno): uno 3D con `OrthoPerspectiveCamera` en
perspectiva y uno de planta. Para la planta hay dos caminos: abrir en ese world un plano generado con
`Views.createFromIfcStoreys`, o poner su cámara en `projection.set("Orthographic")` + `set("Plan")`. El modelo se **carga dos
veces**, una por world. No hay tutorial oficial de vistas lado a lado ⚠️: es la primera cosa que hay que comprobar.

**Por qué hay que cargarlo dos veces**:
- `FragmentsModel` tiene **una sola cámara**: `useCamera(camera)` reemplaza a `currentCamera`, y con ella se calculan el
  *culling* y el nivel de detalle 📄 (engine_fragment `FragmentsModels/src/model/view-manager.ts` y `fragments-model.ts`).
- Tiene **un solo** `object = new THREE.Object3D()` 📄. En Three.js un objeto pertenece a una sola escena.
- `Views.open(id)` "Ensures that no more than one view is opened in the same world at a time" y cambia la cámara de *ese* world
  📄 (engine_components `packages/core/src/core/Views/index.ts`). Dentro de un solo world, la vista se alterna entre 3D y
  planta; no se ven las dos a la vez.
- La visibilidad (`setVisible`, `toggleVisible`) es por modelo 📄. Con dos copias, la planta puede mostrar solo el piso activo
  y el 3D todo (FR-022). Esto juega a favor.

**Alternativas**:
- **Un solo renderer con *scissor*** (dos cámaras sobre la misma escena, como el ejemplo oficial de three.js
  `webgl_multiple_views`). Ahorra memoria, pero las cámaras de That Open no están pensadas para eso y el *culling* de Fragments
  seguiría a una sola cámara ⚠️. 🌐 Una demo de la comunidad dice que dibujar Fragments con otro `WebGLRenderer` falla y usa
  scissor sobre el renderer principal (no pude ubicar la fuente exacta; no verificado).
- **Planta como dibujo 2D de líneas** con `EdgeProjector` (líneas visibles y ocultas, basado en `three-edge-projection`) 📖, o
  con `TechnicalDrawings` y sus *viewports* en papel 📖. Sirve para láminas, no para editar en vivo.

**Evidencia** (nombres reales de la versión actual):
- `Worlds.create<OBC.SimpleScene, OBC.OrthoPerspectiveCamera, OBC.SimpleRenderer>()`. El manager guarda varios worlds en
  `list` y los actualiza a todos en `update()` 📄 (`core/Worlds/index.ts`).
- `Views`, con estos métodos 📄 (`core/Views/index.ts`):
  - `create(normal, point, config)`, `createFromPlane(plane, config)` y `createElevations({combine})`;
  - `async createFromIfcStoreys(config)`, que hace "one view per IFC building storey" con un plano a la cota del piso más un
    `offset` (por defecto 0,25);
  - `open(id)`, `close(id)`, `hasOpenViews`, y `Views.defaultRange = 15`.
- `View`: cámara propia `OrthoPerspectiveCamera` en `"Orthographic"` + `"Plan"`, `plane`, `farPlane`, `range` ("how far from the
  plane the second cut will be made"), `distance` y `flip()` 📄 (`core/Views/src/view.ts`). Es decir, **tiene plano de corte y
  profundidad de vista**, como ArchiCAD.
- Tutorial `ClipStyler` (front) 📖: `views.createFromIfcStoreys({ storeyNames: [/03/], world, offset: 1 })` y luego
  `clipStyler.createFromView(planView, { items: { Walls: { style: "Blue", … } } })`. El estilo combina `linesMaterial`
  (`LineMaterial` con grosor) y `fillsMaterial`: es el **relleno de muros cortados por categoría**. No hay rayados (hatch) 📖.
- `Clipper` (core): `clipper.create(world)`, `createFromNormalAndCoplanarPoint`, `delete`, `deleteAll()` y
  `config.visible/color/opacity/size` 📖.
- `OrthoPerspectiveCamera`: modos `Orbit`, `FirstPerson` y `Plan` ("for navigating 2d plans (blocking the orbit)"), y
  `projection.set("Perspective" | "Orthographic")` 📖.
- No existe un componente llamado `Plans`, `FloorPlans` ni `EdgesClipper` en la versión actual. El árbol del repositorio tiene
  `Views`, `Clipper`, `ClipStyler`, `EdgeProjector`, `TechnicalDrawings` y `DrawingEditor` 📄.
- La especificación 001 dice "planta sin plano de corte". Con That Open, el corte viene incluido y su altura es un parámetro
  (`offset`), así que se puede reconsiderar.

---

## 3. Pisos, selección, medición, imán y grilla

**Decisión**: That Open cubre lo necesario para **ver y medir**. Para **dibujar muros** (clics, longitud por teclado, ángulos
fijos) hay piezas (raycast con imán, `GeometryEngine.getWall`, editor de Fragments), pero la herramienta de dibujo hay que
escribirla.

**Por qué**:
- El imán existe a **punto, arista y cara**. No hay punto medio, perpendicular, intersección ni bloqueo de ángulo 📄.
- `DrawingEditor` gestiona clic → herramienta → máquina de estados, pero para anotaciones (cotas, ángulos, llamadas) 📖. No
  modela.

**Alternativas**: escribir el imán y las restricciones sobre `THREE.Raycaster` y `three-mesh-bvh` (ver la sección 8).

**Evidencia**:
- **Pisos**:
  - `classifier.byIfcBuildingStorey({ classificationName: "Levels" })`. Los grupos se leen con
    `classifier.list.get(c).get(g).get()`, que devuelve un `ModelIdMap` 📖 (tutorial Classifier).
  - `hider.isolate(modelIdMap)` y `hider.set(visible, modelIdMap)` 📖 (tutorial Hider). Hider actúa sobre todos los modelos
    del `FragmentsManager` ⚠️. Con dos copias conviene usar `planModel.setVisible(ids, visible)` directamente 📄.
  - Nombre y cota del piso: `Views.createFromIfcStoreys` ya lee el nombre y la elevación de cada piso 📄. También
    `model.getSpatialStructure()` y `getItemsOfCategories()` 📖 (tutorial EditApi).
- **Selección y resaltado**:
  - `components.get(OBF.Highlighter)`, `highlighter.setup({ world, selectMaterialDefinition })`, estilo `"select"`, Ctrl+clic
    para sumar a la selección, `events.select.onHighlight/onClear`, `styles.set`, `highlightByID` y `clear` 📖.
  - También existen `Hoverer` y `Outliner` 📄 (árbol `packages/front/src/fragments`).
  - Hubo un fallo: con fondo de color y dos o más modelos, el resaltado solo funcionaba en el último cargado. Se corrigió en
    `components-front` 3.4.5 (2026-10-06) 📄 (issue #808, cerrado). Para BIM Simple importa, porque se cargan dos modelos.
    Con 3.4.4, el arreglo provisorio es pasar el color de fondo al renderer y dejar el fondo de la escena en `null`.
- **Raycast**: `components.get(OBC.Raycasters).get(world).castRay()` 📖. En Fragments, `raycastWithSnapping(data)` con
  `data.snappingClasses` devuelve `point`, `normal`, `snappedEdgeP1/P2`, `snappingClass`, etc. 📄
  (`model/raycast-manager.ts`).
- **Imán**: `SnapResolver` (core) con `SnapClass` `POINT` (vértice), `LINE` (punto más cercano en una arista) y `FACE`, en
  orden de prioridad POINT > LINE > FACE, `maxDistance = 1` y `precision` 📄 (`core/SnapResolver/src/snap-resolver.ts`).
  Según sus comentarios, lo usan las mediciones y el `Hoverer`.
- **Medir**: `LengthMeasurement`, `AreaMeasurement`, `AngleMeasurement` y `VolumeMeasurement`. Por ejemplo,
  `measurer.snappings = [FRAGS.SnappingClass.POINT]` (o `LINE`), `units`, `rounding`, `mode` y `create()` con doble clic 📖.
- **Grilla**: `components.get(OBC.Grids).create(world)`, `grid.config.visible/color/primarySize/secondarySize`, y
  `grid.three.position.y = cota del piso` 📖. No dice si se ve bien con cámara ortogonal ⚠️.
- **Modelado**:
  - `FRAGS.GeometryEngine` con `getExtrusion`, `getWall`, `getSweep` y `getBooleanOperation`;
    `fragments.core.editor.createElements` 📖 (tutorial BuildingConfigurator).
  - Esos elementos **no son entidades IFC** ("`_category: { value: "test" }`") 📖.
  - El editor ofrece `edit`, `createElements`, `deleteElements`, `applyChanges`, `save` y `reset` 📄 (`src/edit/editor.ts`).

---

## 4. Interfaz: `@thatopen/ui` (BUI) y español

**Decisión**: sirve **`@thatopen/ui`** (componentes web hechos con Lit, MIT) o HTML/CSS común. Todo puede estar en español,
porque los textos los pone la aplicación.

**Por qué**:
- La librería trae `bim-grid` para la distribución de pantalla, con plantillas de áreas CSS con nombre, áreas redimensionables
  y agrupación en `bim-tabs` o `bim-panel` 📄 (`packages/core/src/components/Grid`).
- `bim-viewport` es un contenedor que emite `resize` 📄.
- `bim-table` tiene datos jerárquicos, `selectableRows`, `dataTransform`, `headersTransform`, `queryString` y los eventos
  `dataselected`/`datadeselected` 📄.
- Hay además `Button`, `ContextMenu`, `Dropdown`, `Modal`, `NumberInput`, `TextInput`, `Toolbar`, `Tabs`, `Tooltip` y
  `Selector` 📄.
- No tiene archivos de idioma 📄, pero casi no trae textos fijos. En `bim-table` solo quedan "Grouped By: " (si se agrupa) y
  "Indentation" (al exportar a CSV) 📄. El mensaje de "sin datos" va en una ranura (`slot="missing-data"`) que define la
  aplicación 📄.

**Alternativas**:
- Los componentes ya armados de `@thatopen/ui-obc` (por ejemplo `tables.spatialTree`) traen textos en inglés ("Spatial
  Tree", "Search...") 📖. Para el navegador de pisos conviene una `bim-table` propia con las columnas Nombre, Cota y Altura,
  editable y con doble clic.
- React, Svelte o HTML simple también sirven. BUI no depende de Three.js.

**Menús**: el menú Archivo puede ser el nativo de Electron (sección 1) o uno HTML (`bim-context-menu`).

---

## 5. Deshacer y rehacer

**Decisión**: That Open **no trae un deshacer general**. No hay componente de historial en el árbol de `engine_components` 📄.
Se usa el **patrón *Command***: cada acción es un objeto con `hacer()` y `deshacer()`, en dos pilas, con Ctrl+Z y
Ctrl+Shift+Z. Si el motor IFC es IfcOpenShell, se usan sus transacciones.

**Por qué**: lo que existe solo cubre las ediciones de la geometría Fragments.
- Editor de Fragments: `getModelRequests(modelId)` devuelve `requests` y `undoneRequests`; `selectRequest(modelId, index)`
  pone el modelo "in the state it was after the request was applied"; y `edit(modelId, actions, { removeRedo })` 📄
  (`src/edit/editor.ts`). No hay métodos `undo()` ni `redo()` 📄.
- IfcOpenShell: `file.begin_transaction()`, `end_transaction()`, `discard_transaction()`, `undo()` y `redo()` 📄
  (IfcOpenShell `v0.8.0`, `ifcopenshell-python/ifcopenshell/file.py`). Son las mismas transacciones que usa Bonsai.

**Alternativas**:
- Guardar una copia completa del estado en cada paso (simple, pero gasta más memoria).
- Usar el historial de Fragments, que no cubre el IFC.

---

## 6. Rendimiento

**Decisión**: no hay cifras oficiales ⚠️. Hay que medir en la prueba práctica: tiempo de conversión del IFC, memoria y tiempo
de cambio de piso (SC-004 pide menos de 1 s).

**Evidencia**:
- La documentación dice "designed to handle millions of elements in seconds", sin datos de prueba 📖 (README de
  engine_fragment).
- "Loading IFC models at runtime is too slow for production." Recomiendan convertir una vez y guardar `.frag` 📖 (tutorial
  IfcLoader). Para BIM Simple, que trabaja sobre el `.ifc`, esto significa convertir cada vez que se abre.
- Fragments trabaja en un *worker* y carga por *tiles* según la cámara (LOD y *culling*) 📄 (`lod-manager`,
  `virtual-tiles-controller`).
- 🌐 Una guía de terceros habla de 0,8–2 GB de memoria para modelos de 100.000–500.000 elementos (no verificado).
- **Cuidado sin conexión**: `FragmentsModels.getWorker()` **descarga el worker de unpkg** 📄 y `IfcLoader.autoSetWasm`
  descarga `web-ifc` de unpkg 📄. En un programa de escritorio hay que incluir `worker.mjs` y `web-ifc.wasm` y pasar su ruta
  local: el constructor acepta `workerURL` 📄, y `setup({ autoSetWasm: false, wasm: { path, absolute: false } })` 📄.
- **Arranque**: Electron arranca en unos 1–3 s ⚠️. Más la conversión del IFC. Muy por debajo de los 20 s de SC-007 ⚠️.

---

## 7. Conclusión: la función 001 con cada base

Esfuerzo: **B** = bajo (horas), **M** = medio (días), **A** = alto (semanas). Son estimaciones ⚠️.

| Parte de la función 001 | Blender + Bonsai (plan actual) | That Open + Electron | Three.js + IfcOpenShell + Electron (sección 8) |
|---|---|---|---|
| Pantalla partida planta + 3D | ✅ hecho con trucos (R7) | M: dos worlds y el modelo cargado dos veces ⚠️ | M: un renderer con *scissor*, dos cámaras 📖 |
| Planta solo del piso activo, sin perspectiva | ✅ (R10) | B–M: `createFromIfcStoreys` + `setVisible` + `ClipStyler` 📄📖 | M: `Layers` o visibilidad por pasada + `clippingPlanes` 📖; relleno de corte con *stencil* = A |
| Navegador de pisos (editar, doble clic) | ⚠️ sin doble clic (D6) | B: tabla propia | B: tabla propia |
| Abrir IFC | ✅ | B: `IfcLoader` (convierte con web-ifc) | M: IfcOpenShell abre; geometría con `geom.iterator` → mallas Three.js |
| Crear y editar pisos y guardar IFC | ✅ (`ifcopenshell.api`) | **A**: Fragments no exporta IFC; hay que mantener el IFC con `web-ifc` (`WriteLine`, `SaveModel`), sin API de alto nivel | B–M: `ifcopenshell.api`, ya probado en este proyecto |
| Preguntar al salir, también con la X | ⚠️ parcial (D5) | B ✅ | B ✅ |
| Todo en español | ⚠️ quedan piezas de Blender | ✅ | ✅ |
| Icono y título propios | ❌ (D1, D2) | B ✅ | B ✅ |
| Deshacer y rehacer (FR-018) | ✅ (Bonsai) | M–A: patrón *Command* sobre web-ifc | M: transacciones de IfcOpenShell + refrescar las vistas |
| Peso instalado | ~1,5 GB | ~350–450 MB ⚠️ | ~500–650 MB ⚠️ |
| Licencias | GPL (Blender, Bonsai) | MIT + MPL-2.0 (web-ifc) | MIT + LGPL-3.0+ (IfcOpenShell) + PSF (Python) |

**Recomendación del contenedor**: **Electron**, no Tauri ni web.
- Tauri ahorra peso, pero exige instalar Rust y las Build Tools (varios GB) y sumar Rust. En cuanto se embebe Python con
  IfcOpenShell, el ahorro relativo es menor.
- La web sola no cumple FR-010 con la X (D5), pide permisos para guardar y depende de Chrome o Edge.

---

## 8. Three.js propio + IfcOpenShell (con o sin That Open)

### 8a. Three.js directo o Three.js + `@thatopen/components`

**Decisión**: **Three.js directo como base del visor y del modelado**, con IfcOpenShell como única fuente de verdad del IFC.
That Open queda como opcional: su librería `@thatopen/ui`, que no depende de Fragments, y más adelante su visor para modelos de
referencia grandes.

**Por qué**:
- Casi todo lo que aporta That Open está construido **sobre Fragments**: `Classifier`, `Hider`, `Highlighter`, `Views`,
  `ClipStyler`, `SnapResolver` y las mediciones trabajan con modelos del `FragmentsManager` 📄📖. Fragments se genera desde el
  IFC con `web-ifc`, no con IfcOpenShell.
- Usar That Open junto a IfcOpenShell obliga a uno de estos dos caminos:
  1. Reconvertir el IFC a Fragments después de cada cambio. Es lento: "the time-consuming part is the conversion process" 📖.
  2. Duplicar cada cambio en el editor de Fragments.
- Los dos caminos usan **dos motores de geometría distintos** (web-ifc y el de IfcOpenShell), que pueden no coincidir ⚠️.
- Para un programa que dibuja, lo importante es actualizar **un elemento** al instante con la **misma geometría** que se
  guarda. IfcOpenShell → mallas → Three.js lo da de forma directa.

**Qué aporta That Open por encima de Three.js, y cuánto cuesta hacerlo solo con Three.js**:

| Necesidad | That Open | Solo Three.js (r186, MIT 📄) | Costo sin That Open |
|---|---|---|---|
| Leer IFC | `IfcLoader` + web-ifc → Fragments 📖 | IfcOpenShell `geom.iterator`: `verts` y `faces` en listas planas, "faces are always triangles", varios núcleos 📖 → `BufferGeometry` | M |
| Modelos muy grandes (LOD, *culling*, *workers*) | Fragments 📄 | No hay; el *frustum culling* básico sí está en Three.js | A si hiciera falta; para casas y edificios medianos no hace falta ⚠️ |
| Clasificar y aislar por piso | `Classifier`, `Hider` 📖 | Agrupar mallas por piso (`THREE.Group`) y `visible`; o `Layers`: "an object must share a layer with a camera to be visible" (32 capas) 📖 | B |
| Planta ortogonal | `Views` + cámara `Plan` 📄 | `OrthographicCamera`: "an object's size … stays constant regardless of its distance" 📖 + `MapControls` ("bird's eye perspective") 📖 | B |
| Planta y 3D a la vez | Dos worlds, modelo cargado dos veces ⚠️ | Un `WebGLRenderer` con `setViewport`, `setScissor` y `setScissorTest(true)` por cámara 📄 (ejemplo `webgl_multiple_views`). Comparte la memoria de la GPU | B–M |
| Plano de corte | `Clipper`, `View.range` 📄 | `renderer.clippingPlanes` (global, se puede cambiar antes de dibujar cada vista ⚠️) o `material.clippingPlanes` + `localClippingEnabled` 📄 (`webgl_clipping`) | B |
| Relleno de corte (poché) | `ClipStyler` 📖 | Técnica de *stencil* (ejemplo `webgl_clipping_stencil` ⚠️ no leído) o calcular la sección en Python | M–A |
| Seleccionar y resaltar | `Highlighter`, `Hoverer`, `Outliner` 📖 | `THREE.Raycaster` + cambio de material; acelerado con `three-mesh-bvh` (That Open ya depende de él 📄; licencia MIT ⚠️) | B–M |
| Imán (punto, arista, cara) | `SnapResolver` 📄 | Propio: vértices y aristas del elemento tocado, grilla, ángulo | M, pero el bloqueo de ángulo y la longitud por teclado hay que escribirlos igual |
| Medir | `LengthMeasurement` y otras 📖 | Propio, con líneas + `CSS2DRenderer` para textos ⚠️ | B–M |
| Controles de cámara | `OrthoPerspectiveCamera` (camera-controls) 📖 | `OrbitControls`, `MapControls` 📖 o `camera-controls` (MIT 📄) | B |
| Grilla | `Grids` 📖 | `GridHelper` o una grilla propia | B |
| Interfaz | `@thatopen/ui` 📄 | Igual: BUI se puede usar sin el resto de That Open | — |

**Licencias**: Three.js MIT 📄; That Open MIT 📄; web-ifc MPL-2.0 📄; IfcOpenShell "LGPLv3+" 📄 (clasificador en PyPI). Usada
como proceso aparte y sin modificar, la LGPL permite un programa propio, siempre que se entreguen su licencia y el acceso a su
código ⚠️ (no es asesoramiento legal). Bonsai (GPL) deja de usarse.

### 8b. Arquitectura recomendada para Windows

```
┌──────────── Electron ─────────────────────────────────────────────┐
│ Proceso principal (Node.js)                                       │
│  · ventana, título, icono, menú Archivo, diálogos, X → "¿Guardar?"│
│  · lanza python.exe embebido (child_process.spawn, windowsHide)   │
│  · puente: ipcMain.handle  ⇄  stdin/stdout del Python (JSON)      │
│                                                                   │
│ Proceso de la ventana (Chromium, sin Node)                        │
│  · Three.js: planta (ortogonal) + 3D en un renderer con scissor   │
│  · panel BIM Simple y navegador de pisos (BUI o HTML)             │
│  · llama a window.bimSimple.* (preload + contextBridge)           │
└───────────────────────────────────────────────────────────────────┘
                 │ stdin/stdout, una línea JSON por mensaje
┌────────────── Python 3.13 embebido + IfcOpenShell 0.9.0 ──────────┐
│ ifcopenshell.api: proyecto, pisos, muros…  · transacciones=Ctrl+Z │
│ ifcopenshell.geom.iterator → mallas por elemento → Three.js       │
│ guardar .ifc · validar IFC4                                       │
└───────────────────────────────────────────────────────────────────┘
```

**Decisión**: canal **stdin/stdout con un mensaje JSON por línea**, del proceso principal de Electron al `python.exe` embebido.

**Por qué**:
- No abre puertos, así que no aparece el aviso del Firewall de Windows ⚠️ ni hay que gestionar puertos ocupados.
- El proceso muere con el programa.
- `child_process.spawn(command, args, options)` redirige por defecto stdin, stdout y stderr a *pipes*
  (`['pipe','pipe','pipe']`), y `windowsHide` "Hide[s] the subprocess console window" 📖 (nodejs.org/api/child_process).

**Alternativas**:
- **HTTP o WebSocket local** en `127.0.0.1`. Es más fácil de depurar con un navegador, pero hay que gestionar el puerto, y la
  conexión podría alcanzarla otro programa local ⚠️.
- **`utilityProcess`**: no sirve para Python. "creates a child process with Node.js and Message ports enabled" y su
  `modulePath` es un *script* de Node 📖 (api/utility-process). La documentación del modelo de procesos sugiere
  `UtilityProcess` en vez de `child_process.fork` **para procesos Node** 📖. Para Python, lo que corresponde es
  `child_process.spawn` desde el proceso principal ⚠️.
- **Mallas grandes**: JSON con números es lento. Conviene enviar los vértices como binario (`Float32Array` en base64, o
  mensajes con largo + bytes) ⚠️.

**¿Es un patrón documentado?**
- En **Electron no hay una guía específica para Python** ⚠️ (no la encontré). Las piezas sí están documentadas:
  - procesos hijos desde el proceso principal, que "can … use all of Node.js APIs" 📖 (tutorial/process-model);
  - IPC entre ventana y proceso principal: *Pattern 2*, `ipcRenderer.invoke` / `ipcMain.handle` + `contextBridge` 📖
    (tutorial/ipc);
  - incluir archivos extra en el paquete: `extraResource` de Electron Packager / Forge 📖, o `extraResources` en
    electron-builder;
  - ubicarlos al ejecutar con `process.resourcesPath` 📖.
- **Tauri sí lo documenta** como *sidecar* con Python y PyInstaller 📖.

**Python embebido en Windows**:
- El paquete oficial "embeddable" es "a ZIP file containing a minimal Python environment … intended for acting as part of
  another application" 📖 (docs.python.org/3/using/windows.html §4.2).
- Queda "(almost) fully isolated" del sistema (variables, registro, paquetes instalados) 📖.
- No trae pip ni tkinter 📖. El archivo `._pth` "is intended for embedders to modify" 📖: ahí se agrega la carpeta con los
  paquetes.
- Tamaño: `python-3.13.10-embed-amd64.zip` pesa 10,4 MB 📄 (python.org).
- Paquetes: IfcOpenShell 0.9.0 pide `requires_python <3.16,>=3.10`, y la rueda `py313-none-win_amd64` pesa 49.865.978 bytes
  📄 (PyPI). Sus dependencias son `shapely`, `numpy`, `isodate`, `python-dateutil`, `lark`, `pyparsing` y
  `typing-extensions` 📄.
- Al **armar** el programa (no en la computadora del usuario), las ruedas se descomprimen en `python\Lib\site-packages`. Como
  una rueda es un ZIP, se puede hacer sin pip ⚠️, o con `pip install --target` desde un Python completo 3.13.

**Tamaño final aproximado** ⚠️ (hay que medirlo):
- Electron: 300–400 MB.
- Python embebido: unos 25 MB.
- IfcOpenShell + numpy + shapely: 150–250 MB.
- Código de la aplicación con Three.js: menos de 10 MB.
- **Total instalado: 500–650 MB. Instalador comprimido: 180–250 MB.** Blender + Bonsai pesan unos 1,5 GB.

**Instalación**: por usuario y sin permisos de administrador, con NSIS (`oneClick`, `perMachine: false`) 📖 o Squirrel 📖.
Para desinstalar se borra la carpeta. Nada toca el Blender del usuario: desaparecen FR-004, SC-005 y D7.

---

## 9. Prueba práctica propuesta (requiere tu autorización)

Son dos pruebas independientes. Ninguna toca el proyecto ni Blender, no instala nada en Windows y se borran eliminando su
carpeta. Las versiones van **fijas** y con más de 2 semanas de publicadas.

### Prueba A: ventana Electron con dos vistas de un IFC y panel de pisos (solo npm)

- **Carpeta**: `%TEMP%\bim-simple-prueba-electron\`, nueva y vacía.
- **Qué se instala** (`npm install` local en esa carpeta, con versiones exactas):

  | Paquete | Versión | Publicada | Nota |
  |---|---|---|---|
  | `electron` | 44.4.4 | 2026-09-22 | |
  | `three` | 0.185.0 | r185, 2026-07-01 | |
  | `camera-controls` | 3.1.2 | | |
  | `@thatopen/components` | 3.4.8 | 2026-07-24 | |
  | `@thatopen/components-front` | 3.4.4 | 2026-07-23 | Con el arreglo provisorio del issue #808 |
  | `@thatopen/fragments` | 3.4.7 | 2026-07-23 | |
  | `@thatopen/ui` | 3.4.11 | 2026-08-28 | |
  | `web-ifc` | 0.0.77 | 2026-03-06 | |
  | `vite` | 8.x | | Una versión con más de 2 semanas; la fecha se confirma antes de instalar ⚠️ |

- **Descarga y espacio** ⚠️:
  - Unos 250 MB de descarga, de los cuales 151–158 MB son el ZIP de Electron.
  - Unos 450–550 MB en `node_modules`.
  - Electron deja una copia de su ZIP en `%LOCALAPPDATA%\electron\Cache` ⚠️, que también se puede borrar.
  - Tarda unos minutos.
- **IFC de ejemplo**: un `.ifc` con 2 o 3 pisos guardado con el MVP de Bonsai, o `school_str.ifc` del repositorio de
  engine_fragment (`resources/ifc/`) 📄. El worker de Fragments y `web-ifc.wasm` se sirven **locales** (sin unpkg) para
  comprobar que funciona sin conexión.
- **Qué mostraría**:
  1. Una ventana con el título "BIM Simple — prueba", un icono propio en la barra de tareas (no agrupado con Blender) y un menú
     **Archivo** en español: Abrir IFC…, Guardar IFC como… y Salir.
  2. A la izquierda, la **planta** ortogonal del piso activo (`Views.createFromIfcStoreys` + `ClipStyler` con muros
     rellenos). A la derecha, el **3D** completo. Cada vista con su propio world y su copia del modelo.
  3. Un panel **Pisos** (`bim-table`) con Nombre, Cota y Altura. Un clic o un **doble clic** activa el piso y la planta cambia.
  4. Al cerrar con la **X** con un "cambio" simulado: "¿Guardar los cambios?" con **Guardar / No guardar / Cancelar**.
  5. "Guardar IFC como…" con el diálogo nativo de Windows. Escribe una copia con `web-ifc` (`SaveModel`).
  6. Medidas en pantalla: tiempo de arranque, tiempo de conversión del IFC, memoria (`process.getProcessMemoryInfo` ⚠️), tiempo
     de cambio de piso (SC-004) y si el resaltado funciona en las dos vistas.
- **Qué decide**: si el doble world con dos copias del modelo de That Open funciona bien, que es el mayor ⚠️ de este informe,
  y cómo se siente un programa propio frente a Blender.

### Prueba B (opcional): Electron + Three.js + IfcOpenShell en Python embebido

- **Carpeta**: `%TEMP%\bim-simple-prueba-python\`, nueva y vacía.
- **Qué se descarga** (no es npm):
  - `python-3.13.10-embed-amd64.zip` de python.org (10,4 MB) 📄;
  - la rueda `ifcopenshell-0.9.0-py313-none-win_amd64.whl` de PyPI (49,9 MB) 📄 y las de sus 7 dependencias (unos 30 MB ⚠️).
  - Se descomprimen sin instalar nada. Total unos 250 MB ⚠️.
  - De npm se reutilizan `electron` y `three` de la prueba A (o se instalan igual).
- **Qué mostraría**:
  1. La misma ventana con planta y 3D, pero dibujada con **Three.js puro**: un renderer con *scissor*, `OrthographicCamera` +
     `MapControls` a la izquierda y `PerspectiveCamera` + `OrbitControls` a la derecha.
  2. Las mallas vienen del Python (`ifcopenshell.geom.iterator`) por stdin/stdout.
  3. Panel de pisos con datos de `ifcopenshell`. Botón "Agregar piso arriba" que usa `ifcopenshell.api`. Ctrl+Z que deshace
     con las transacciones de IfcOpenShell. "Guardar IFC" escribe el archivo.
  4. Medidas: arranque del Python, tiempo de geometría y tiempo de ida y vuelta de un comando.
- **Qué decide**: si la arquitectura de la sección 8b es fluida (el tiempo del puente Python ↔ ventana) y cuánto pesa de
  verdad.

---

## Fuentes principales

- That Open:
  - código: github.com/ThatOpen/engine_components (`packages/core/src/core/{Views,Worlds,SnapResolver}`,
    `packages/front/src/...`); github.com/ThatOpen/engine_fragment (`FragmentsModels/index.ts`, `src/model/*.ts`,
    `src/edit/editor.ts`); github.com/ThatOpen/engine_ui-components (`Grid`, `Viewport`, `Table`);
  - tutoriales: docs.thatopen.com/Tutorials/… (Worlds, Views, Clipper, ClipStyler, Classifier, Hider, Raycasters, Grids,
    OrthoPerspectiveCamera, IfcLoader, EdgeProjector, Highlighter, LengthMeasurement, DrawingEditor, MultiDrawingViewports,
    EditApi, EditElements, BuildingConfigurator, SpatialTree);
  - issues #808 y #810 de engine_components.
- npm: registry.npmjs.org (versiones, fechas, licencias y tamaños de los paquetes citados).
- web-ifc: `src/ts/web-ifc-api.ts` (`CreateModel`, `WriteLine`, `SaveModel`).
- Electron: electronjs.org/docs/latest (api/browser-window, api/dialog, api/menu, api/menu-item, api/app, api/utility-process,
  api/protocol, api/process, tutorial/process-model, tutorial/ipc, tutorial/security, tutorial/tutorial-packaging,
  tutorial/distribution-overview); electronforge.io (makers, Squirrel.Windows); electron.github.io/packager; releases de
  github.com/electron/electron; app-builder-lib `nsisOptions.d.ts`.
- Tauri: v2.tauri.app (start, start/prerequisites, plugin/dialog, reference/javascript/dialog, namespacewindow,
  distribute/windows-installer, develop/sidecar).
- Web: developer.mozilla.org (`showSaveFilePicker`, `beforeunload`); developer.chrome.com (File System Access, File Handling);
  web.dev/learn/pwa.
- Three.js: threejs.org/docs (`Layers`, `OrthographicCamera`, `MapControls`); ejemplos `webgl_multiple_views.html` y
  `webgl_clipping.html` en github.com/mrdoob/three.js; LICENSE.
- Python e IfcOpenShell: docs.python.org/3/using/windows.html; python.org (3.13.10); pypi.org (ifcopenshell 0.9.0);
  docs.ifcopenshell.org (geometry processing); IfcOpenShell `file.py` (v0.8.0); nodejs.org/api/child_process.
