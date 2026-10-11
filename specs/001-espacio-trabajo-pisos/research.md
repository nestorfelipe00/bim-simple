# Investigación (fase 0): Programa BIM Simple y navegador de pisos

**Fecha**: 2026-10-11 · **Constitución**: v3.0.0 · **Función**: [spec.md](spec.md) · **Plan**: [plan.md](plan.md)

Este documento reemplaza a la investigación hecha para Blender, que queda como referencia histórica
en [investigacion/](investigacion/). La base de las decisiones es:
- [docs/base-tecnologica/evaluacion.md](../../docs/base-tecnologica/evaluacion.md): por qué
  Electron + Three.js + IfcOpenShell, y sus anexos;
- el prototipo validado ([RESULTADOS.md](../../docs/base-tecnologica/prototipo/RESULTADOS.md)):
  muro ~30 ms, deshacer ~25 ms, IFC válido, título, X y doble clic;
- las verificaciones nuevas de este plan, marcadas con ✅ y con su salida real abajo.

Marcas: ✅ ejecutado y comprobado · 📖 documentación oficial · ⚠️ a comprobar en la implementación.

No queda ningún "NEEDS CLARIFICATION" abierto.

---

### R1. Arquitectura en tres piezas
- **Decisión**:
  - **Ventana**: el proceso principal de Electron.
  - **Interfaz**: la página, con Three.js.
  - **Motor BIM**: Python embebido con IfcOpenShell, como proceso aparte.

  El proceso principal hace de puente: la página pide con `ipcRenderer.invoke` y el proceso
  principal reenvía al motor por stdin/stdout (contrato en [core_api.md](contracts/core_api.md)).
- **Por qué**: es lo que exige el Principio III y lo que validó el prototipo ✅. La comunicación
  agrega menos de 1 ms por orden. Por stdin/stdout no se abren puertos, así que no aparece el aviso
  del Firewall de Windows, y el motor muere con el programa.
- **Alternativas**:
  - HTTP local: hay que manejar puertos, el firewall y otros programas que se conecten.
  - IfcOpenShell en WebAssembly: hoy su API está "en desarrollo" y sin `ifcopenshell.api`; ver
    [librerias.md](../../docs/base-tecnologica/anexos/librerias.md).

### R2. Seguridad y configuración de Electron
- **Decisión** (la misma del prototipo ✅):
  - `contextIsolation: true`, `nodeIntegration: false`, `sandbox: true`;
  - preload con `contextBridge` y una política de seguridad de contenido (CSP) que solo permite
    archivos propios;
  - el título lo controla el proceso principal: se cancela `page-title-updated`;
  - las herramientas de desarrollo solo se abren en modo desarrollo.
- **Por qué**: la página no necesita Node, y así un archivo IFC malicioso no puede ejecutar código
  en la computadora.

### R3. Motor: proceso, protocolo y reinicio
- **Decisión**:
  - **Lanzamiento**: `child_process.spawn(<python.exe>, ["-u", "-m", "bimsimple_engine"],
    { windowsHide: true })`.
  - **Mensajes**: una línea JSON por mensaje; el motor anuncia que está listo con `id: 0`.
  - **Mallas**: van en base64 (`float32` / `uint32`).
  - **Si el motor se cae**: el evento `exit` del proceso hijo
    ([nodejs.org/api/child_process.html](https://nodejs.org/api/child_process.html), evento `'exit'`
    📖) con un código distinto de 0 y sin pedido de cierre dispara el aviso, un rechazo de las
    órdenes pendientes y el reinicio del motor sin proyecto.
- **Por qué**: el prototipo lo validó ✅: listo en ~0,4 s, importar IfcOpenShell ~0,3 s. Reiniciar
  sin proyecto es simple y seguro, porque el último archivo guardado no se toca (caso límite de la
  especificación).
- **Alternativa**: reabrir el último archivo guardado. Podría confundir si tenía cambios sin
  guardar. Queda para más adelante.

### R4. Operaciones de pisos con la API LGPL de IfcOpenShell (sin Bonsai) ✅
Se verificó en el motor del prototipo (Python 3.14.7, IfcOpenShell 0.9.0):

| Necesidad | Función (firma comprobada) | Resultado |
|---|---|---|
| Crear piso | `root.create_entity` + `aggregate.assign_object` + `geometry.edit_object_placement` + `attribute.edit_attributes(Elevation)` + `pset.add_qto`/`edit_qto(GrossHeight)` | Prototipo ✅ |
| Renombrar | `attribute.edit_attributes(file, product, attributes={"Name": …})` | 0,1 ms; deshacer y rehacer ✅ |
| Mover cota con sus elementos | `geometry.edit_object_placement(file, product, matrix, is_si=True, should_transform_children=True)` + `Elevation` | ✅ (abajo) |
| Altura en cascada (FR-016) | `edit_qto(GrossHeight)` del piso + mover todos los de arriba en Δ | 3,2 ms; deshacer y rehacer ✅ |
| Contar elementos | `util.element.get_decomposition(piso)`, filtrando `IfcElement` sin `IfcFeatureElementSubtraction` | ✅ |
| Borrar piso con elementos | `root.remove_product(file, product)` de cada elemento y después del piso | 2,8 ms; 0 elementos sin piso; deshacer ✅ |
| Deshacer y rehacer | `file.begin_transaction()` / `end_transaction()` / `undo()` / `redo()` (`file.py:548-590`) | ✅ |

Salida real ([verif_pisos.py](../../docs/base-tecnologica/prototipo/verificaciones/verif_pisos.py), 2026-10-11):

```
3. altura de Planta Baja 3,50 (3.2 ms)
   Planta Baja  cota=0.0  altura=3.5  Elevation=0.0  muros=4 z_muros=[0.0]
   Primer piso  cota=3.5  altura=3.0  Elevation=3.5  muros=4 z_muros=[3.5]
   Piso 2       cota=6.5  altura=3.0  Elevation=6.5  muros=1 z_muros=[6.5]
   deshacer → vuelve a 0/3/6 con los muros · rehacer → 0/3,5/6,5
4. elementos en Piso 2: 1 · borrado (2.8 ms); elementos sin piso: 0 · deshacer el borrado → vuelve
5. validación: 0 errores
6. iterador: 8 elementos teselados en 22.2 ms con 16 núcleos
```

- **Por qué no `delete_container` ni el camino de Bonsai**: es GPL (Principio VI), y además dejaba
  huérfanos y no movía los elementos (investigación de Blender, `investigacion/ifc.md` §3-4).

### R5. Abrir IFC de otros programas
- **Decisión**:
  1. Validar el archivo con `ifcopenshell.open` y exigir `IfcProject` **antes** de cerrar el
     proyecto actual (FR-011).
  2. Cambiar de archivo y vaciar el historial.
  3. Activar el piso de cota más cercana a 0,00.
  4. Teselar todos los elementos con `ifcopenshell.geom.iterator(settings, file, núcleos)` y
     `use-world-coords`: 8 elementos en 22 ms ✅.
- **Elementos que BIM Simple no edita** (puertas, proxies…): se muestran y se conservan, porque el
  IFC se guarda entero.
- **Archivos en milímetros**: el motor convierte con `calculate_unit_scale` (comprobado en la
  investigación de Blender sobre IfcOpenShell, `investigacion/ifc.md` §2 ✅).

### R6. Guardar y validar
- **Decisión**:
  - `save_project` escribe con `file.write(path)` y responde enseguida.
  - La **validación** IFC4 completa (`ifcopenshell.validate.validate(..., express_rules=True)`)
    tarda ~1,7 s ✅. Se corre en **un segundo proceso de Python** (`validate_file`) que lanza el
    proceso principal después de guardar, así el motor no se bloquea.
  - El resultado aparece en el panel: "Guardado. Validación IFC4: N errores."
- **Por qué**: en el prototipo, guardar con validación bloqueaba 1,7 s.
- **Requisito**: la validación con reglas EXPRESS necesita `pytest` (MIT) ✅.

### R7. Vistas y navegación ✅ (aprobada por el usuario)
- **Decisión**: la configuración del prototipo:
  - un `WebGLRenderer` con dos zonas de dibujo (`setScissor`);
  - **planta**: `OrthographicCamera` + `MapControls` (sin rotación, `zoomToCursor`);
  - **3D**: `PerspectiveCamera` + `camera-controls` 3.1.2. Botón izquierdo para girar con
    `setOrbitPoint` en el punto bajo el ratón, botón central o derecho para desplazar,
    `dollyToCursor`, `maxPolarAngle` de 88°, `smoothTime` de 0,12;
  - la planta muestra solo el grupo del piso activo;
  - `THREE.Timer` para el movimiento suave (`THREE.Clock` está marcado como obsoleto en r186 ✅).
- En esta función los elementos solo vienen de abrir un IFC, porque el dibujo llega en la
  función 2. Las vistas ya muestran lo que haya.

### R8. Navegador de pisos
- **Decisión**:
  - tabla HTML propia, donde el clic selecciona y el **doble clic** activa (✅ prototipo);
  - "Editar piso…" abre un **diálogo propio en la página**, con campos Nombre, Cota y Altura y
    coma decimal;
  - las confirmaciones (borrar con elementos) usan el diálogo nativo de Windows (`dialog.showMessageBox`).
- **Por qué**: los diálogos nativos no tienen campos de texto 📖
  ([electronjs.org/docs/latest/api/dialog](https://www.electronjs.org/docs/latest/api/dialog)).

### R9. Instalador por usuario
Investigación con lectura de la documentación oficial (electron.build) y del registro npm; no se
instaló nada.

- **Decisión**: **electron-builder 26.17.0**.
  - Fija, publicada el 2026-09-26, licencia MIT; sus 276 dependencias tienen licencias permisivas 📄.
  - La etiqueta `latest` de npm está en la 26.15.3, que tiene un error por el que el instalador
    puede quedar sin el `.exe`. Se corrigió en la 26.15.6 📄.
  - Destino NSIS, con `oneClick: true`, `perMachine: false` (por usuario, sin administrador),
    accesos directos en el Escritorio y el menú Inicio con el nombre "BIM Simple", y desinstalador
    en "Agregar o quitar programas" 📖.
  - Instala en `%LOCALAPPDATA%\Programs\<nombre del paquete>\` 📖.
- **Python y motor fuera del asar**: `extraResources` copia `runtime/python` → `python` y `engine` →
  `engine`, excluyendo `tests` y `__pycache__`. En tiempo de ejecución se encuentran con
  `app.isPackaged ? process.resourcesPath : <carpeta del repositorio>` 📖.
  - `files` debe excluir esas carpetas para no duplicar unos 640 MB.
  - Rutas `from` relativas fuera de `app/` (`../runtime/python`) ⚠️ a comprobar al armar.
- **Icono y barra de tareas**: `appId` = `BIMSimple.BIMSimple`, igual a `app.setAppUserModelId(...)`;
  no se puede cambiar después 📖. El `.ico` lleva 16, 24, 32, 48 y 256 px.
- **Tamaño**: el instalador pesaría unos 170–190 MB ⚠️ (estimado; se mide al armar).
- **Requisitos para armar**: en Windows no hace falta wine, Visual Studio ni Rust. El primer armado
  descarga los binarios de NSIS 📖.
- **Alternativa descartada**: Electron Forge con Squirrel. Squirrel está marcado como obsoleto y tiene
  problemas con nombres con espacio, como "BIM Simple" 📖.
- **Riesgos para probar o resolver**:
  1. **`MSVCP140.dll`**: las DLL de IfcOpenShell la necesitan y ni el Python embebible ni IfcOpenShell
     la traen; en esta computadora ya está en el sistema. Plan: incluirla junto al programa, como
     permite el redistribuible de Visual C++ ⚠️, y **probar en una PC limpia** (Windows Sandbox o
     una máquina virtual) antes de entregar.
  2. **Sin firma digital**: Windows muestra "Windows protegió su PC", y Smart App Control podría
     bloquear el programa. Para el uso propio no bloquea; **antes de vender** hace falta un
     certificado (OV, del orden de US$150–300 al año 📖). Un certificado EV ya no evita el aviso
     desde 2024 📖.
  3. El instalador deja una copia de sí mismo en `%LOCALAPPDATA%\bim-simple-updater`, que el
     desinstalador no borra. Se puede limpiar con un `installer.nsh` ⚠️; hay que comprobarlo para
     cumplir SC-005.
  4. **Datos del programa al desinstalar** (análisis H2): por defecto quedan en
     `%APPDATA%\BIM Simple`, porque `deleteAppDataOnUninstall` vale `false` (anexo, §104). Para
     cumplir SC-005 se usa `deleteAppDataOnUninstall: true`, que solo existe en el instalador de un
     paso; en esa carpeta no hay proyectos del usuario.
- **Dónde encuentra Python al motor** (análisis H1) ✅: el Python embebible con `._pth` arranca
  **aislado**. Comprobado con `sys.flags.isolated = 1` y `safe_path = True`: ignora `PYTHONPATH` y
  la carpeta actual. Por eso el `._pth` lleva **dos** líneas relativas:
  - `..\..\engine`, para desarrollo (`runtime\python` → `engine\` del repositorio);
  - `..\engine`, para el programa instalado (`resources\python` → `resources\engine`).

  Una ruta que no existe se ignora sin error.

- **Resultados medidos** (T050 y T051, 2026-10-11) ✅:
  - `BIM Simple Setup 0.1.0.exe`: **150,4 MB** (menos que lo estimado); instalado ocupa 606 MB. El
    armado tarda unos 3 minutos; el primero bajó 7-Zip, NSIS 3.0.4.1 y nsis-resources 3.4.1. Con
    `electronDist` = `node_modules/electron/dist` no baja Electron otra vez.
  - **Hallazgo**: electron-builder deja fuera de `node_modules` toda carpeta `examples` del primer
    nivel de cada paquete (`app-builder-lib/out/util/NodeModuleCopyHelper.js:24-41`), y la planta usa
    `three/examples/jsm/controls/MapControls.js`. Se agregan `MapControls.js` y `OrbitControls.js`
    con una entrada `from`/`to` en `files`. Sin eso, el programa instalado no cargaba la interfaz.
  - Instalación silenciosa (`/S`) en 26 s, sin administrador: `%LOCALAPPDATA%\Programs\bim-simple`,
    accesos directos "BIM Simple" en el Escritorio y en el menú Inicio, y entrada en "Agregar o
    quitar programas". En modo silencioso no abre el programa al terminar
    (`templates/nsis/installSection.nsh:93-97`).
  - Arranque del programa instalado con la ventana oculta (`--smoke=<archivo>`): interfaz lista
    ("Listo.") en **4,0 s la primera vez y 0,9 s después**, sin errores en la consola; crea un
    proyecto. El motor instalado guarda y valida un IFC con 0 errores. El tiempo con la ventana
    visible (SC-007) queda para la prueba manual.
  - Desinstalar (`Uninstall BIM Simple.exe /S /currentuser`) no deja la carpeta del programa,
    ni `%APPDATA%\BIM Simple`, ni `%LOCALAPPDATA%\bim-simple-updater`, ni los accesos directos, ni
    la entrada del registro (**SC-005** ✅).

- **Pendientes antes de entregar el programa a otros** (T053, anotados al cerrar la función 001):
  1. **Prueba en una PC limpia** (Windows Sandbox o una máquina virtual) para confirmar que el
     programa arranca sin un `MSVCP140.dll` del sistema. Activar Windows Sandbox lo hace el usuario,
     porque pide administrador.
  2. **Firma de código** con un certificado OV (punto 2 de los riesgos).
  3. **CGAL y demás bibliotecas dentro de IfcOpenShell**. La carpeta `ifcopenshell` del paquete 0.9.0
     trae, además del núcleo OpenCASCADE (`TK*.dll`, LGPL-2.1 con excepción) que usa BIM Simple, los
     núcleos `ifcopenshell_geometry_kernel_cgal.dll` y `..._cgalsimple.dll` (CGAL tiene partes
     GPL-3.0), `manifold.dll` (Apache-2.0) y DLL de Boost (BSL-1.0). Su `dist-info` no trae ningún
     texto de licencia. Desde que BIM Simple es GPL-3.0-or-later (R11), las partes GPL de CGAL son
     compatibles con el programa; falta agregar a `licencias/` los textos de CGAL, OpenCASCADE,
     Boost y manifold.
  4. **GEOS** (LGPL-2.1) viene dentro de shapely (`shapely.libs\geos*.dll`): es una DLL aparte y
     reemplazable, y su texto ya está en `licencias/python-paquetes/shapely-2.2.0/LICENSE_GEOS`.

Detalle completo:
[empaquetado-instalador.md](../../docs/base-tecnologica/anexos/empaquetado-instalador.md).

### R10. Licencias (Principio VI) ✅

| Pieza | Versión | Licencia | Uso |
|---|---|---|---|
| Electron | 44.4.5 | MIT | ventana |
| Three.js | 0.186.1 | MIT | gráfica |
| camera-controls | 3.1.2 | MIT | navegación 3D |
| Python embebible | 3.14.7 | PSF-2.0 | motor |
| IfcOpenShell | 0.9.0 | **LGPL-3.0+** | motor IFC (carpeta separada y reemplazable; núcleo OpenCASCADE) |
| numpy | 2.5.4 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 (incluye OpenBLAS, BSD) | IfcOpenShell |
| shapely | 2.2.0 | BSD-3-Clause | IfcOpenShell |
| isodate, lark, pyparsing, python-dateutil, six, typing_extensions | ver `METADATA` | BSD / MIT / Apache-2.0 / PSF | IfcOpenShell |
| pytest (+ iniconfig, pluggy, packaging, Pygments, colorama) | 9.1.1 | MIT / BSD / Apache-2.0 | validación EXPRESS y pruebas |

Todas son permisivas, salvo IfcOpenShell (LGPL), que se usa como permite la constitución. Todas
son compatibles con la GPL-3.0-or-later de BIM Simple (R11). Falta agregar los textos de las
bibliotecas que trae IfcOpenShell (R9, pendiente 3).

### R11. Repositorio público con licencia GPL ✅ (resuelto por el usuario, 2026-10-11)
- **Hallazgo** ✅:
  - `gh api repos/nestorfelipe00/bim-simple` devuelve **`visibility: public`**, con licencia
    detectada GPL-3.0.
  - El archivo `LICENSE` del repositorio es el texto de la GPL-3.0 que se puso para el MVP.
  - En GitHub solo está el commit inicial del MVP; los 12 commits posteriores están **solo en esta
    computadora** (`git rev-list origin/main..main` = 12).
- **Decisión del plan**: no subir nada a GitHub hasta que el usuario decidiera la visibilidad del
  repositorio y la licencia, porque el plan suponía un programa cerrado.
- **Decisión del usuario** (T056, 2026-10-11): "Repositorio público y licencia similar a blender".
  - El repositorio sigue **público**.
  - BIM Simple es **GPL-3.0-or-later**, como Blender. `LICENSE` ya tiene el texto oficial de la
    GPL-3.0 (SHA-256 `3972DC97…6986`) y se conserva.
  - Constitución 4.0.0, Principio VI: el aviso va en "Acerca de", el texto en
    `licencias/bim-simple/GPL-3.0.txt` del instalador y el enlace al código en ambos. Se sigue sin
    copiar código GPL de otros (Blender, Bonsai), para que el autor conserve la opción de cambiar
    la licencia más adelante.

### R12. Pruebas (Principio V)
- **Motor**: `pytest` corriendo con el Python del programa (`runtime/python`). Los IFC de prueba se
  generan en carpetas temporales con IfcOpenShell (lógica de
  `investigacion/scripts/make_test_ifcs.py`), nunca dentro del proyecto.
- **Programa**: Electron con la ventana oculta y un modo de prueba que recorre las acciones,
  captura la pantalla y escribe `resultado.json`. Usa el mismo arnés del prototipo, incluida la
  captura de calentamiento ✅.
- **Manual**: [quickstart.md](quickstart.md), parte B.
