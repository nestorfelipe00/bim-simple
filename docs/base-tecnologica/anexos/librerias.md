# Catálogo de motores y librerías abiertas para un BIM propio

Investigación para elegir la **base tecnológica** de BIM Simple: un programa propio de **modelado** (no un visor)
que trabaje con IFC. Fecha de consulta de **todos** los datos: **2026-10-11**.

**Método.** Solo lecturas: `gh api` (GET) sobre repositorios, versiones y commits; los registros públicos de
npm, PyPI y NuGet (metadatos JSON, sin instalar nada); y documentación oficial. No se clonó, instaló ni ejecutó
código de terceros. Los datos crudos de GitHub están en `repos_data.tsv`, en esta misma carpeta.

**Cómo leer las cifras**
- ★ = estrellas en GitHub.
- **Commits 12 m** = commits en la rama por defecto desde el 2025-10-11 (cabecera `Link` de
  `GET /commits?since=2025-10-11&per_page=1`). Mide actividad, no calidad.
- **Último release** = `releases/latest` en GitHub o, si se indica, la última versión en npm, PyPI o NuGet.
- **Descargas/sem** = descargas en npm del 2026-10-03 al 2026-10-09.

**Marcas**
- 📄 dato sacado del código, del repositorio o de un registro de paquetes;
- 📖 documentación oficial;
- 🌐 fuente de terceros (foros, prensa, resúmenes de búsqueda);
- ⚠️ no verificado o interpretación mía.

La información sobre licencias es **orientativa y no es asesoría legal**. Antes de vender, conviene una revisión
legal (ver §6.3).

That Open (web-ifc, Fragments, Components) y Electron/Tauri los investigan otros agentes. Aquí solo figuran con
sus datos básicos. Las aplicaciones completas se tratan a fondo en `proyectos.md` (otro agente); aquí aparecen
en una tabla breve.

---

## 0. Resumen en 10 líneas

1. **IfcOpenShell 0.9.0** (LGPL-3.0-or-later) sigue siendo el único motor abierto con una **API de modelado**
   completa: 36 módulos en `ifcopenshell.api`, entre ellos `geometry.connect_wall`,
   `regenerate_wall_representation` y `add_door_representation`. Además trae deshacer/rehacer en el propio
   archivo, planos en SVG (`ifcopenshell.draw`), costos (`ifc5d`) e IDS (`ifctester`). Tiene rueda oficial para
   **Python 3.14 en Windows**, así que no hace falta compilar 📄.
2. **Novedad**: desde el **2026-10-10** IfcOpenShell se publica también en **npm** (`ifcopenshell` y
   `@ifcopenshell/wasm`, ambos LGPL). Es el mismo núcleo C++ en WebAssembly, pero la documentación oficial dice
   que la API "está en desarrollo" y solo trae funciones de bajo nivel (`create`/`set`), **sin** el equivalente
   de `ifcopenshell.api` 📄📖.
3. **xBIM** (.NET, CDDL) sirve para leer y escribir IFC, y su licencia permite vender cerrado. Pero su
   geometría solo funciona en Windows (C++/CLI con OCCT 7.6.3) y no tiene API de autoría de alto nivel 📄.
   **GeometryGymIFC** (.NET, MIT) escribe IFC2x3, IFC4 e IFC4.3 📄.
4. **IFC++** está "más o menos archivado" según su propio autor, que recomienda xeoIFC. **xeoIFC** no tiene
   licencia abierta: su conversor pide clave 📄.
5. **ifc-lite** (TS + Rust/WASM, MPL-2.0) crea muros, losas, columnas, puertas y ventanas, une muros y exporta a
   IFC e IFCX. Es muy prometedor, pero nació en **enero de 2026** y casi todo lo escribe una sola persona 📄.
6. **Núcleos geométricos**: para BIM Simple no hace falta un núcleo B-rep propio al principio. Las extrusiones y
   los huecos los resuelve IfcOpenShell, que trae los núcleos OCCT, CGAL y Manifold. Para la vista previa
   interactiva y las uniones en planta alcanzan Three.js, Clipper2 o Shapely y Manifold, todos de licencia
   permisiva 📄.
7. **Trampas de licencia**: xeokit es AGPL (o comercial) 📄. CGAL es GPL o LGPL según el paquete, o comercial
   📄. Bonsai es GPL-3.0, y ahí están los generadores de **cubiertas y escaleras**, que no forman parte de la API
   LGPL 📄. Además, los binarios de IfcOpenShell incluyen piezas que usan CGAL GPL (`svgfill` y el núcleo
   `cgal`). Esto hay que revisarlo antes de vender cerrado ⚠️.
8. **Gráfica**: Three.js (MIT, r186, 20,5 M descargas/sem) es la opción obvia 📄. Babylon.js (Apache-2.0)
   también sirve. Qt 3D quedó fuera de las versiones de Qt desde la 6.8 🌐📖.
9. **IFC5, ahora "IFCX"**: el plan del proyecto se aprobó en agosto de 2026 y pasa a la etapa de financiación y
   ejecución 🌐. El repositorio oficial dice que sus ejemplos son "alpha" y no sirven para producción 📄. Para
   BIM Simple: **IFC4**, con IFC4X3 opcional.
10. **Recomendación** (§6): aplicación de escritorio con interfaz web (TypeScript + **Three.js**) y
    **IfcOpenShell 0.9 en Python** como motor BIM en un proceso local. Es la pila (a). El motor queda detrás de
    una interfaz de "comandos", para poder pasarlo más adelante a IfcOpenShell-WASM sin rehacer el programa.

---

## 1. Motores IFC

| Pieza | Qué es | Lenguaje | Licencia (SPDX) | ★ | Último release | Commits 12 m | ¿Modela? | IFC | Para qué serviría en BIM Simple |
|---|---|---|---|---|---|---|---|---|---|
| **IfcOpenShell** (núcleo + `ifcopenshell-python`) 📄 | Biblioteca IFC más madura (desde 2011, según su README) | C++ con envoltorio Python | LGPL-3.0-or-later | 2.848 | `ifcopenshell-python-0.9.0` 2026-09-29; `ifcopenshell-v0.9.0` 2026-10-01; PyPI 0.9.0 con rueda `py314-win_amd64` | 4.155 | **Sí** | Lee y escribe IFC2X3 TC1, IFC4 ADD2 TC1, IFC4x1, IFC4x2 e IFC4X3 ADD2. Geometría "extensa" para 2X3 e IFC4 (README) | **Motor del modelo**: proyecto, pisos, muros, losas, columnas, materiales y validación |
| ↳ `ifcopenshell.api` 📄 | API de autoría de alto nivel | Python | LGPL-3.0-or-later | — | (0.9.0) | — | **Sí** | Igual que el núcleo | 36 módulos y unos 417 archivos. Para muros: `geometry.connect_wall`, `connect_path`, `regenerate_wall_representation`, `add_wall_representation`, `add_door_representation`, `add_window_representation`, `add_boolean`, `clip_solid`. También `material`, `spatial`, `type`, `pset`, `drawing`, `cost` |
| ↳ transacciones 📄 | Deshacer/rehacer en el propio archivo | Python | LGPL | — | — | — | — | — | `file.begin_transaction`, `end_transaction`, `undo` y `redo` (`file.py:553-580`). Sirve para el Ctrl+Z del programa propio sin depender de Blender |
| ↳ `ifcopenshell.geom` 📄 | Triangula y evalúa la geometría IFC, incluidos huecos y booleanas | C++ | LGPL-3.0-or-later* | — | — | — | Calcula | — | Pasar los muros con huecos a mallas para Three.js. Núcleos: `opencascade`, `cgal`, `manifold`, `passthrough` (`src/ifcgeom/kernels/`) |
| ↳ `ifcopenshell.draw` 📄 | Plantas y cortes en SVG a partir del IFC | Python (numpy, shapely) + serializador C++ | LGPL-3.0-or-later | — | — | — | Genera 2D | — | Base de **plantas, cortes y láminas** |
| ↳ `ifcpatch`, `ifctester`, `ifc5d`, `ifcedit`, `ifcmcp` 📄 | Recetas de cambios, auditoría IDS, costos, línea de comandos y servidor MCP sobre `ifcopenshell.api` | Python | LGPL-3.0-or-later | — | 0.9.0 (PyPI) | — | `ifcedit`/`ifcmcp`: sí | — | `ifc5d` (`qto.py`: `quantify`, `QtoCalculator`, reglas `IFC4QtoBaseQuantities.json`): **cómputos y costos**. `ifctester`: control de calidad. `ifcmcp`: que un asistente de IA edite el modelo |
| ↳ cubiertas y escaleras 📄 | Generadores paramétricos | Python | **GPL-3.0** (están en Bonsai, no en la API) | — | — | — | — | — | `bonsai/bim/module/model/roof.py` y `stair.py`. **No** se pueden reutilizar en un producto cerrado |
| **IfcOpenShell JS/TS** (`ifcopenshell` y `@ifcopenshell/wasm`, npm) 📄📖 | El núcleo C++ compilado a WASM, para navegador y Node | TS + WASM | LGPL-3.0-or-later | — | npm **0.9.0 del 2026-10-10** (3 versiones); 278 descargas/sem | — | Bajo nivel (`create`/`set`) | Plugins `ifc2x3`, `ifc4`, `ifc4x3_add2`. Núcleo `manifold` disponible | Futuro reemplazo del Python dentro de una app web. **Hoy**: la documentación dice que la API "está en desarrollo y puede cambiar" y la instalación desde npm figura como "TODO" |
| **Bonsai** 📄 | Complemento de Blender para modelar IFC | Python | **GPL-3.0-or-later** | (en IfcOpenShell) | `bonsai-0.9.1-alpha…` 2026-10-10 | — | Sí | Igual que IfcOpenShell | Solo **como referencia** de cómo usar la API. Copiar su código obliga a GPL |
| **xBIM Essentials** 📄 | Lectura y escritura IFC en .NET | C# | CDDL-1.0 (GitHub muestra "Other") | 577 | GitHub 6.0.517 (2025-04-18); **NuGet 6.1.605 del 2026-07-15** (net8.0, net10.0, netstandard2.0/2.1) | 50 | Datos sí; sin API de autoría de alto nivel | IFC2x3, IFC4 ADD2 e IFC4x3 (paquete `Xbim.Ifc4x3` en NuGet) | Base de la pila .NET (b) |
| **xBIM Geometry** 📄 | Motor de geometría de xBIM | C++/CLI con OCCT 7.6.3 | CDDL-1.0 + OCCT (LGPL-2.1 con excepción) | 294 | NuGet `6.3.891-netcore` del 2026-04-01 (net472, net8.0) | 0 en `master`; 49 en `feature/netcore` | Calcula | — | Triangular IFC en .NET. **Solo Windows** (pide el Windows 10 SDK) |
| **GeometryGymIFC** 📄 | Clases IFC para .NET | C# | MIT (GitHub muestra "Other") | 310 | NuGet 26.9.23 del 2026-09-23 (netstandard2.0, net6.0 a net10.0) | 20 | Datos sí | IFC2x3, IFC4, IFC4.3 e IFC4.4 (README) | Escribir IFC en .NET con licencia permisiva |
| **IFC++** (`ifcquery/ifcplusplus`) 📄 | Lectura y escritura IFC con visor | C++ | MIT | 661 | 2.5 (2024-08-09) | 10 | Limitado | — | **Descartado**: su README dice que está "más o menos archivado" |
| **xeoIFC** (`xeofoundry/xeoIFC`) 📄 | Motor IFC en Rust: CLI, DLL y WASM | Rust | **sin licencia abierta** (el conversor pide clave) | 12 | creado 2026-08-24 | — | Autoría "experimental" | IFC2x3 a IFC4.3 | No es abierto. Descartado como base |
| **web-ifc** (That Open) 📄 | Lectura y escritura IFC en WASM | C++→WASM / TS | MPL-2.0 | 1.059 | 0.78 (2026-09-21); 182.810 descargas/sem | 1.151 | Escritura de bajo nivel | ver informe de That Open | ver informe de That Open |
| **@thatopen/components** y **fragments** 📄 | Kit de visor BIM sobre Three.js | TS | MIT | 711 / 212 | v3.4.9 / v3.4.8 (2026-10-06) | 290 / 265 | Sobre todo visor | — | ver informe de That Open |
| **That Open Clay** (`engine_clay`) 📄 | "Motor ligero de modelado BIM" | TS | MIT | 74 | sin releases; último push 2024-10-09 | **0** | Sí (se detuvo) | — | Señal de que That Open no siguió con el modelado |
| **ifc-lite** (`LTplus-AG/ifc-lite`) 📄 | Kit IFC: parser Rust/WASM, render WebGPU, `@ifc-lite/create` y `drawing-2d` | TS + Rust | MPL-2.0 | 419 | v10.3.0 (2026-10-01); `@ifc-lite/parser` 10.792 descargas/sem | **5.122** (creado el 2026-01-10) | **Sí**: muros, losas, columnas, puertas, ventanas, cubiertas y escaleras. `joinWallsInStore` une muros | IFC2X3, IFC4, IFC4X3 e "IFC5 (IFCX)" | Alternativa TS para la pila (d). **Riesgo**: tiene 9 meses y un solo autor principal (3.619 commits) |
| **Hypar Elements** 📄 | "El BIM útil más pequeño": muros, pisos, aberturas y CSG propio | C# | MIT | 420 | GitHub 2.4.0-alpha.8 (2025-06-09); NuGet 2.4.0-alpha.12 (2026-05-26) | 4 | Sí | Exporta IFC (`Elements.Serialization.IFC`) | Referencia de diseño. Actividad casi nula |
| **dotbim** 📄 | Formato mínimo de malla y datos | C# | MIT | 200 | — | 3 | — | No es IFC | No aplica |
| **BIMserver** 📄 | Servidor de modelos IFC | Java | **AGPL-3.0** | 1.761 | v1.5.188 (2025-07-31) | 18 | No (servidor) | ⚠️ IFC2x3/IFC4 | No aplica a un programa de escritorio |
| **Speckle server / connectors** 📄 | Plataforma para intercambiar datos AEC | TS / C# | Apache-2.0, salvo las carpetas "EE" del servidor (licencia Enterprise) | 847 / 66 | 2.31.14 (2026-06-15) / 2026.9.2 (2026-10-09) | 41 / 517 | No | Importa IFC ⚠️ | Posible integración futura. No es motor de modelado |
| **buildingSMART validate** 📄 | Servicio oficial de validación (Django + React + reglas Gherkin) | Python | MIT | 68 | v1.0.5 (2026-09-30) | 383 | No | — | Validar los IFC que exporte BIM Simple (servicio web) |
| **ifc-gherkin-rules** 📄 | Reglas de validación normativa | Python | MIT | 24 | v1.0.5 (2026-09-30) | 163 | No | — | Idem |
| **IDS** e **IFC4.x-development** 📄 | Especificaciones (estándar) | — | **CC BY-ND 4.0** | 324 / 241 | IDS v1.0.0 (2024-06-03) | 36 / 160 | — | — | Se pueden usar, pero no modificar ni redistribuir modificados |
| **IFC5-development** 📄 | Ejemplos y esquema alpha de IFC5 / IFCX | TS/HTML | Sin licencia. El README pide "no crear derivados"; el visor es MIT | 233 | sin releases | 12 | — | IFCX (JSON + composición tipo USD) | Solo seguimiento (ver §1.1) |

\* El README de IfcOpenShell marca con asterisco `ifcgeom`, `ifcconvert`, `ifcparse` y `serializers` sin
explicar el motivo. `src/svgfill/README.md` declara que depende de "CGAL 2D Arrangements — GPL" 📄. Interpreto
que los binarios precompilados pueden llevar código GPL a través de CGAL ⚠️. Ver §6.3.

### 1.1 Estado de IFC5 / IFCX (octubre de 2026)
- La última versión oficial sigue siendo **IFC 4.3.2.0**, publicada también como **ISO 16739-1:2024** 🌐 (resumen
  de buildingsmart.org; la página respondió 403 a la descarga directa).
- En 2025 se consultó el plan del proyecto **"IFC 5 Core"**. Según buildingSMART, el resultado fue 44 a favor y 22
  en contra (≈67 %), por encima del umbral del 65 % 🌐.
- En 2026 el proyecto pasó a llamarse **"IFCX – Core & Modularisation"**. La votación del plan final cerró el
  **2026-08-07**, y un anuncio del **2026-08-26** dice que el plan "pasó la siguiente fase" y que se entra en la
  etapa de **financiación y ejecución** 🌐.
- En el foro OSArch (29 y 31 de agosto de 2026), un participante estimó de **5 a 10 años** hasta que IFCX sirva
  para trabajo real 🌐. Es una opinión, no un dato.
- `buildingSMART/IFC5-development`: "IFC 5 alpha Examples… preliminary… not suitable for production use" 📄.
- **Implementaciones**: ifc-lite tiene `Ifc5Exporter` 📄. En el árbol de IfcOpenShell v0.9.0 no encontré ninguna
  ruta `ifcx` ⚠️ (la búsqueda fue solo por nombre de archivo).
- **Consecuencia para BIM Simple**: trabajar en **IFC4** (ADD2 TC1), dejar IFC4X3 como opción y, si algún día hace
  falta, agregar IFCX como **exportación**. El modelo interno no debe depender del formato del archivo.

---

## 2. Núcleos geométricos

Para el arquitecto, en una frase: un **muro IFC** es un perfil extruido; una **puerta o ventana** abre un hueco
(`IfcOpeningElement`) que se **resta** del muro; y la **unión en esquina** recorta los extremos de los muros. Las
dos primeras cosas ya las calcula IfcOpenShell (`ifcopenshell.geom` + `geometry.connect_wall`). El núcleo propio
solo hace falta para la **vista previa en vivo** mientras se dibuja, y más adelante para formas libres.

| Pieza | Tipo | Lenguaje / forma de uso | Licencia | ★ | Último release | Commits 12 m | ¿Sirve en Windows sin compilar? | Para qué en BIM Simple |
|---|---|---|---|---|---|---|---|---|
| **Open CASCADE (OCCT)** 📄 | Núcleo B-rep industrial: booleanas, cortes, STEP | C++ | **LGPL-2.1** + "Open CASCADE exception 1.0" (`OCCT_LGPL_EXCEPTION.txt`) | 2.984 | V8.0.1 (2026-07-30) | 426 | A través de envoltorios ya compilados | Ya va dentro de IfcOpenShell (núcleo `opencascade`). No hace falta usarlo directamente |
| **pythonocc-core** 📄 | OCCT para Python (SWIG) | Python | LGPL-3.0 | 1.983 | 8.0.1.1 (2026-10-05) | 110 | **Solo con conda**: en PyPI la última es la 0.16 | Pila (c) |
| **OCP** / `cadquery-ocp` 📄 | OCCT para Python (pybind11) | Python | Apache-2.0 (el envoltorio; OCCT sigue LGPL) | 205 | PyPI `cadquery-ocp` 8.0.1.1.0 (2026-10-05) con rueda **cp314-win_amd64** | 28 | **Sí, con pip** | Pila (c), alternativa a pythonocc |
| **CadQuery** 📄 | CAD paramétrico por código sobre OCP | Python | Apache-2.0 | 5.913 | v2.8.0 (2026-06-20) | 80 | Sí (con pip) | Referencia; no es BIM |
| **opencascade.js** 📄 | OCCT compilado a WASM | JS/WASM | LGPL-2.1-only | 934 | npm 1.1.1 (**2020-09-27**); último push 2023-08-15 | **0** | — | **Descartado** (detenido) |
| **replicad** (+ `replicad-opencascadejs`) 📄 | API amable sobre OCCT-WASM | TS | MIT (el núcleo WASM es LGPL-2.1-only) | 697 | npm 1.1.0 (2026-09-04); 28.679 descargas/sem | 85 | Sí (npm) | Formas libres en la web (cubiertas complejas) si algún día hace falta |
| **brepjs** (+ `occt-wasm`) 📄 | CAD B-rep para la web | TS | Apache-2.0 | 116 | 20.4.0 (2026-10-09); creado 2026-02-01 | 2.419 | Sí (npm) | Alternativa a replicad. Muy nuevo |
| **Manifold** 📄 | Booleanas robustas de mallas | C++ con versiones WASM y Python | **Apache-2.0** | 2.345 | v3.5.4 (2026-09-25); `manifold-3d` 151.113 descargas/sem; PyPI `manifold3d` con rueda cp314-win | 288 | **Sí** | Vista previa de huecos en vivo (en la web). Además es un núcleo de IfcOpenShell |
| **CGAL** 📄 | Geometría computacional: booleanas exactas, esqueleto recto, arreglos 2D | C++ | **GPL-3.0-or-later o LGPL-3.0-or-later según el paquete**, más licencia comercial de GeometryFactory (`Installation/LICENSE`) | 6.072 | v6.2.1 (2026-09-04) | 3.138 | No (hay que compilar) | **Evitar usarlo directamente** si se va a vender cerrado |
| **three-bvh-csg** 📄 | Booleanas rápidas sobre Three.js | JS | MIT | 948 | 0.0.18 (2026-02-17); 145.884 descargas/sem | 157 | Sí | Vista previa de huecos. Su README dice "experimental, in progress" y exige mallas cerradas |
| **three-csg-ts** 📄 | Booleanas BSP para Three.js | TS | MIT | 587 | último push 2024-05-28 | 0 | Sí | **Descartado** (sin mantenimiento) |
| **JSCAD** (`@jscad/modeling`) 📄 | Modelado sólido por código (CSG) | JS | MIT | 3.255 | npm 2.13.0 (2026-02-22) | 13 | Sí | Poco útil para BIM |
| **Truck** 📄 | Núcleo B-rep moderno | Rust | Apache-2.0 | 1.592 | sin releases | 254 | **No** (no hay Rust en la PC) | No por ahora |
| **Fornjot** 📄 | Núcleo B-rep | Rust | 0BSD | 2.553 | v0.49.0 (2024-03-21); **archivado** | — | — | Descartado |
| **Clipper2** 📄 | Uniones, recortes y desfases de **polígonos 2D** | C++, C# y Delphi; en JS `clipper2-js` (BSL, 2024-01-01) y `clipper2-wasm` 0.4.0 (2026-05-18) | **BSL-1.0** | 2.502 | 2.0.1 (2025-12-19) | 52 | Sí | **Uniones de muros en planta**, sombreado de capas y desfases |
| **Shapely** (sobre GEOS) 📄 | Geometría 2D en Python | Python / C | BSD-3-Clause (GEOS: LGPL-2.1) | 4.521 / 1.513 | shapely 2.2.0 con rueda cp314-win | — | Sí | Lo usa `ifcopenshell.draw`. Uniones 2D del lado Python |
| **earcut** 📄 | Triangulación de polígonos | JS | ISC | 2.601 | v3.2.4 (2026-09-28) | 66 | Sí | Rellenos de losas y sombreados en Three.js |

**Conclusión del bloque**: no hace falta elegir un núcleo B-rep ahora. La geometría "de verdad" (la que queda en
el IFC) la calcula IfcOpenShell. La de "mientras dibujo" se arma con Three.js más Clipper2 (en planta) y
Manifold o three-bvh-csg (huecos en 3D). Todas tienen licencia permisiva.

---

## 3. Gráfica 3D y 2D

### 3.1 Motores 3D

| Pieza | Lenguaje | Licencia | ★ | Último release | Commits 12 m | ¿Para modelar? | Comentario |
|---|---|---|---|---|---|---|---|
| **Three.js** 📄 | JS | MIT | 116.217 | r186 (2026-09-24); npm 0.186.1, **20.521.334 descargas/sem** | 2.185 | Sí: es una librería de render; las herramientas las pone uno | Estándar de facto. That Open, Pascal, Chili3d y massing lo usan. Ejemplo oficial de IfcOpenShell-JS con Three.js (`examples/threejs.html`) 📄 |
| **React Three Fiber** 📄 | TS | MIT | 32.851 | v9.8.1 (2026-09-24) | 129 | Sí | Three.js en React. Lo usa Pascal Editor |
| **Babylon.js** 📄 | TS | Apache-2.0 | 26.153 | 9.30.0 (2026-10-08); 369.374 descargas/sem | 1.764 | Sí | Alternativa sólida, con menos ecosistema BIM |
| **xeokit SDK** 📄 | JS | **AGPL-3.0, o licencia comercial** (README: "Need a commercial license?… proprietary or closed-source") | 945 | v2.6.114 (2026-09-02) | 1.094 | Visor | **Evitar** si se vende cerrado sin pagar licencia |
| **iTwin.js** 📄 | TS | MIT | 733 | release/5.14.2 (2026-10-06) | 1.011 | Sí, sobre su formato iModel | Plataforma de Bentley. No es IFC nativo ⚠️ |
| **Helix Toolkit** 📄 | C# | MIT | 2.283 | v3.1.2 (2025-11-25); NuGet `HelixToolkit.Wpf` 3.1.2 (net8.0-windows) | 71 | Visor y escenas | Pila .NET. Variantes WPF, WPF.SharpDX, **Avalonia.SharpDX** y WinUI.SharpDX (DirectX 11, Windows) |
| **VTK** / **vtk-js** 📄 | C++ / JS | BSD-3-Clause | 3.212 / 1.538 | vtk-js v37.4.1 (2026-10-03) | 5.558 / 364 | Visualización científica | Poco adecuado para un CAD de arquitectura ⚠️ |
| **Visualización de OCCT** (AIS/V3d) | C++ (en OCCT) | LGPL-2.1 + excepción | — | — | — | Sí | Es la que usa FreeCAD a través de Coin3D ⚠️. Pila (c) |
| **Qt 3D** 🌐📖 | C++ | LGPL/GPL/comercial | — | — | — | — | **Fuera de las versiones de Qt desde la 6.8** (lista de Qt, marzo de 2024). Su sucesor es Qt Quick 3D. No usar |

### 3.2 Planos 2D, láminas y DXF/PDF

| Pieza | Lenguaje | Licencia | ★ | Último release | Commits 12 m | Uso en BIM Simple |
|---|---|---|---|---|---|---|
| **`ifcopenshell.draw`** 📄 | Python + C++ | LGPL-3.0-or-later (con la duda de CGAL, §1) | — | 0.9.0 | — | **Plantas y cortes en SVG** directamente desde el IFC. Es lo que usa Bonsai para sus planos |
| **`@ifc-lite/drawing-2d`** 📄 | TS | MPL-2.0 | — | (ifc-lite 10.3.0) | — | Equivalente en TS. No lo evalué en detalle ⚠️ |
| **ezdxf** 📄 | Python | MIT | 1.463 | PyPI 1.4.4 (2026-05-14) | 122 | Exportar las láminas a **DXF** |
| **ACadSharp** 📄 | C# | MIT | 879 | v3.8.0 (2026-09-21) | 1.223 | Leer y escribir **DXF y DWG** en .NET |
| **netDxf** 📄 | C# | MIT | 1.148 | v3.0.1 (2023-10-11); **archivado** | 0 | Descartado |
| **@tarikjabiri/dxf** 📄 | TS | MIT | — | npm 2.9.0 (2026-09-15) | — | Escribir DXF en JS |
| **dxf-writer** 📄 | JS | MIT | — | npm 1.18.4 (2022-11-07); 21.924 descargas/sem | — | Sencillo y sin novedades desde 2022 |
| **maker.js** 📄 | TS | Apache-2.0 | 2.038 | npm `makerjs` 0.19.2 (2026-01-27) | 36 | Dibujo 2D paramétrico con salida SVG, DXF y PDF |
| **jsPDF** + **svg2pdf.js** 📄 | JS | MIT | 31.308 / — | 4.2.1 (2026-03-17) / 2.8.1 (2026-08-31) | — | **Láminas en PDF** a partir del SVG |
| **pdf-lib** 📄 | TS | MIT | 8.654 | npm 1.17.1 (2021-11-06) | — | Funciona, pero no tiene versiones nuevas desde 2021 |

---

## 4. Aplicaciones abiertas de referencia (resumen; el detalle está en `proyectos.md`)

| Aplicación | Cómo está hecha | Licencia | ★ | Inicio → hoy | Estado (2026-10) | Lección para BIM Simple |
|---|---|---|---|---|---|---|
| **FreeCAD**, banco **BIM** 📄🌐 | C++ y Python, núcleo **OCCT**, interfaz **Qt**; IFC con IfcOpenShell (carpeta `src/Mod/BIM/nativeifc`) | LGPL-2.1 | 34.137 | Empezó en **2001** 🌐. Arch ya existía en 2012 (commit del 2012-12-18) 📄. **1.0 en noviembre de 2024** 🌐. 1.1.4 el 2026-09-28 📄 | El repositorio tuvo 5.242 commits en 12 meses, 348 de ellos en `src/Mod/BIM` 📄 | Más de 20 años y una comunidad grande para llegar a 1.0. La pila (c) funciona, pero es lenta de construir |
| **Bonsai** (antes BlenderBIM) 📄🌐 | Python sobre Blender + IfcOpenShell | GPL-3.0-or-later | — | Ya existía en 2020 (premio buildingSMART 2020) 🌐. Pasó a llamarse Bonsai en la v0.8.0 (septiembre de 2024) 🌐 | 0.9.x, todavía "alpha" | La mejor referencia de **cómo usar `ifcopenshell.api`** para modelar |
| **Sweet Home 3D** 📖 | Java + Java 3D | GPL (texto GPL-2.0 enlazado) | — | Versión 7.5 (página de descarga actualizada en 2025-05) | Estable; sin IFC | Interfaz sencilla de "dibujar muros en planta" |
| **Pascal Editor** 📄 | TS, React Three Fiber, WebGPU, estado en Zustand; **importa** IFC con web-ifc (`packages/ifc-converter`) | MIT | 24.784 | Creado el **2025-10-16**; v1.0.3 el 2026-09-24 | 1.989 commits en 12 meses | Modelo propio (no IFC) y una interfaz muy pulida en menos de un año. Licencia MIT: se puede estudiar y reutilizar |
| **Chili3d** 📄 | TS + **OCCT 8.0 en WASM** + Three.js | **AGPL-3.0** | 4.901 | 2022-12-31 → 0.7.1 (2026-09-19) | Activo; sigue antes de la 1.0 tras casi 4 años | Demuestra que OCCT-WASM y Three.js funcionan juntos. Su licencia impide copiar código para un producto cerrado |
| **massing** 📄 | **That Open + IfcOpenShell + Three.js + FastAPI + Tauri** | MIT | 122 | Creado el 2026-06-14 | 2.836 commits; un autor con agentes de IA (`cursoragent`, `claude`) | Prueba reciente de la combinación "web + IfcOpenShell en Python local" que recomiendo en §6 |
| **bimrocket** 📄 | JS sobre Three.js ⚠️; visor y editor web con backend | EUPL-1.1+ o LGPL-3.0+ | 99 | 2021 → hoy (Ajuntament de Sant Feliu de Llobregat) | 162 commits en 12 meses | Editor IFC web mantenido por una entidad pública |
| **ifc5cad** (`louistrue`) 📄 | TS + Three.js + OpenCascade, autoría IFC5 | AGPL-3.0 | 36 | 2026-02-19 → 2026-02-21 | Experimento | — |
| **open-3d-studio** (OpenAEC) 📄 | TS sobre That Open, "IFC como salida nativa" | MIT | 2 | 2026-07 → 2026-08 | Experimento | — |
| **react-planner** / **blueprint3d** 📄 | JS / TS, planta 2D → 3D | MIT | 1.480 / 1.984 | sin cambios desde 2024-04 / 2021-01 | Abandonados | Los editores "de planta" sin IFC se quedan cortos y se abandonan |

---

## 5. Pilas posibles para un programa de escritorio propio

Supuestos: el usuario no programa y un asistente de IA escribe el código. La PC tiene Windows 11, Node 24,
npm 11, .NET 10, Python 3.14 y Git, pero **no** tiene Rust ni compiladores C++.

### 5.1 Tabla comparativa

| | **(a) App web de escritorio + Three.js + IfcOpenShell (Python local)** | **(b) .NET (WPF/Avalonia) + xBIM + Helix Toolkit** | **(c) Qt/PySide6 + OCCT (pythonocc/OCP) + IfcOpenShell** (como FreeCAD) | **(d) Web pura: Three.js + web-ifc/That Open o ifc-lite + IfcOpenShell-WASM** |
|---|---|---|---|---|
| **Piezas y licencias** | Electron (MIT) o Tauri (Apache-2.0/MIT); Three.js (MIT); IfcOpenShell y sus herramientas (LGPL-3.0+); Python incrustado (PSF); Clipper2 (BSL), Manifold (Apache) | WPF (MIT) o Avalonia (MIT); xBIM Essentials y Geometry (CDDL-1.0) con OCCT (LGPL-2.1 + excepción); Helix (MIT); GeometryGymIFC (MIT); ACadSharp (MIT) | PySide6 (LGPL-3.0, o GPL, o Qt comercial); pythonocc (LGPL-3.0) u OCP (Apache-2.0 sobre OCCT LGPL); IfcOpenShell (LGPL) | Three.js (MIT); web-ifc (MPL-2.0); That Open (MIT); ifc-lite (MPL-2.0); `ifcopenshell` npm (LGPL-3.0+) |
| **¿Se puede vender cerrado?** | **Sí, cumpliendo LGPL**: IfcOpenShell queda como paquete Python aparte y reemplazable, con aviso de licencia y su código fuente disponible. **Pendiente**: CGAL GPL dentro de los binarios de IfcOpenShell ⚠️ | **Sí**. CDDL y MPL obligan a publicar solo los archivos de esas librerías que uno modifique. La excepción de OCCT facilita el uso. Es la pila más "limpia" para vender cerrado | **Sí, cumpliendo LGPL** (Qt, OCCT, pythonocc e IfcOpenShell enlazados dinámicamente). Misma duda de CGAL si se usa IfcOpenShell | **Sí**: MIT y MPL son por archivo. Con LGPL en WASM hay que poder **reemplazar el `.wasm`** (servirlo como archivo aparte) ⚠️ |
| **Madurez del motor BIM** | **Alta**: la API de autoría más completa (36 módulos, uniones de muros, puertas, ventanas, planos, costos, IDS, deshacer) 📄. Las recetas ya se verificaron en este proyecto (research.md §C). Faltan cubiertas y escaleras (en Bonsai, GPL) | **Media** para datos y **baja** para autoría: no hay API de muros, uniones ni planos; hay que escribirlo todo. Geometría solo en Windows | **Alta** en geometría (OCCT) y en IFC (la misma API que en (a)) | **Media-baja** para modelar: Clay está parado; ifc-lite tiene 9 meses y un autor; IfcOpenShell-JS salió el 2026-10-10 y no tiene `api` |
| **Madurez de la gráfica** | **Alta** (Three.js) | Media (Helix con DirectX 11; Avalonia.SharpDX solo en Windows) | Media: el visor de OCCT o Coin3D es potente pero anticuado, y Qt 3D está descartado | **Alta** (Three.js / That Open) |
| **Cuánto hay que programar** ⚠️ | **Medio**: interfaz y herramientas de dibujo en TS, el puente TS↔Python (JSON por stdio o HTTP local) y el empaquetado de Python. Casi toda la lógica BIM ya existe | **Alto**: muros con capas, uniones, huecos, planos y cómputos, todo a mano en C# | **Alto**: interfaz Qt a mano, visor OCCT y empaquetado pesado (Qt + OCCT + Python) | **Alto hoy** (falta la API de autoría en TS). **Medio** si ifc-lite o IfcOpenShell-JS maduran |
| **¿Qué tan bien la lleva un asistente de IA?** ⚠️ | **Muy bien**: TS/Three.js y Python/ifcopenshell abundan en los datos de entrenamiento. Ya hay habilidades `ifcos-*` en este entorno, `ifcedit`/`ifcmcp` y la experiencia de este proyecto | Bien en C#, pero xBIM tiene pocos ejemplos de autoría y XAML es verboso | Regular: la API de OCCT es enorme y difícil, y las depuraciones visuales son lentas | Bien en TS. **Mal** con APIs nuevas y casi sin documentar (IfcOpenShell-JS: "API subject to change"; instalación por npm: "TODO") |
| **¿Se instala en esta PC sin compilar?** | **Sí**: `ifcopenshell` 0.9.0 tiene rueda `py314-win_amd64` y `shapely`/`manifold3d` tienen cp314-win 📄. Electron: npm. Tauri **necesita Rust** para compilar el programa ⚠️ (ver informe Electron/Tauri) | **Sí** (NuGet y .NET 10) | **Sí** con `cadquery-ocp` y `PySide6` (ruedas cp314/abi3-win) 📄; pythonocc solo con conda | **Sí** (npm) |
| **Multiplataforma** | Sí (Windows, macOS y Linux) | WPF solo Windows; Avalonia sí, pero Helix.SharpDX y xBIM Geometry atan a Windows | Sí | Sí, incluso en el navegador |

### 5.2 Variantes de la pila (a)
- **(a1) Electron + Node + Python como proceso hijo.** Es la más común y está mejor documentada. El instalador
  ocupa más espacio.
- **(a2) Python + pywebview (BSD-3, 6.098 ★, 6.2.1 del 2026-04-15) + página web con Three.js** 📄. Un solo
  proceso Python que muestra la interfaz web en WebView2 (el motor de Edge que trae Windows) ⚠️. Es más simple:
  no hace falta Node para ejecutar el programa, aunque sí para construir la interfaz.
- **(a3) Tauri + "sidecar" Python.** Es lo que usa massing 📄. Exige Rust en la máquina de compilación (aquí no
  hay).

---

## 6. Recomendación razonada

### 6.1 Qué elegir
**Pila (a): interfaz web de escritorio (TypeScript + Three.js) + IfcOpenShell 0.9 en Python como motor BIM
local.** Primero (a1) con Electron, o (a2) si el informe de Electron/Tauri lo aconseja. El "motor" se diseña
como un **servicio de comandos** (`crear_piso`, `crear_muro`, `unir_muros`, `insertar_puerta`, `deshacer`,
`exportar_planta`…) que recibe y devuelve JSON. La interfaz no sabe si detrás hay Python o WASM.

**Por qué:**
1. **Es el único motor con API de autoría completa y probada**, y es la misma que ya validó este proyecto con
   Bonsai (R11 a R16). Las recetas de `ifcopenshell.api` se reutilizan casi tal cual **sin Blender** 📄.
2. **La licencia permite vender cerrado.** El código propio no toca nada GPL: ni Blender, ni Bonsai, ni CGAL
   usado directamente. IfcOpenShell es LGPL y queda como paquete aparte, que es el caso más simple de cumplir.
   Three.js y Electron son MIT.
3. **Cubre casi toda la hoja de ruta**: muros con capas (`material`), uniones (`geometry.connect_wall`), huecos,
   puertas y ventanas (`add_door/window_representation`), planos (`ifcopenshell.draw` → SVG → PDF con jsPDF y
   svg2pdf, o DXF con ezdxf), cómputos (`ifc5d/qto.py`: `quantify`, `QtoCalculator` 📄) y validación
   (`ifcopenshell.validate`, `ifctester`). **Excepción**: los generadores de **cubiertas y escaleras** no están en
   `ifcopenshell.api`. Están en Bonsai (`bonsai/bim/module/model/roof.py` y `stair.py`), que es GPL 📄. Si se
   vende cerrado, esos dos generadores hay que escribirlos desde cero (se puede estudiar cómo lo hace Bonsai, pero
   no copiar su código).
4. **Es la mejor para trabajar con IA**: lenguajes y librerías muy conocidos, herramientas MCP oficiales
   (`ifcmcp`) y nada que compilar en esta PC.
5. **Tiene salida al futuro**: cuando IfcOpenShell-JS madure (mismo núcleo C++, núcleo Manifold en WASM), el
   servicio de comandos se puede mover dentro de la app y desaparece el Python incrustado. Si ifc-lite se
   consolida, también se podría enchufar como motor alternativo.

**Cómo se reparte el trabajo:**
- **Three.js**: dibujo interactivo. La vista previa del muro mientras se arrastra se calcula en TS (Clipper2 para
  las esquinas en planta y Manifold o three-bvh-csg para los huecos). Al soltar el ratón se manda **un** comando
  al motor.
- **IfcOpenShell**: guarda la verdad del modelo y su deshacer (`begin_transaction`/`undo`), y devuelve las mallas
  definitivas (`ifcopenshell.geom`) y los planos (`ifcopenshell.draw`).

### 6.2 Alternativas, por orden
1. **(d) Web pura**, en **6 a 12 meses**, si IfcOpenShell-JS publica una API de autoría o ifc-lite demuestra que
   se sostiene con más de un autor. La migración desde (a) es barata si se respeta el servicio de comandos.
2. **(b) .NET** solo si la prioridad absoluta es una licencia sin ninguna duda para vender cerrado **y** se
   acepta escribir a mano toda la lógica BIM (uniones, planos, cómputos). Es el camino más largo.
3. **(c) Qt + OCCT**: no. Repite el camino de FreeCAD (más de 20 años) con la interfaz más costosa de construir
   y la geometría más difícil para una IA.

**Qué evitar**: xeokit (AGPL), CGAL usado directamente (GPL), Qt 3D (fuera de las versiones de Qt),
opencascade.js (detenido desde 2023), three-csg-ts (sin cambios desde 2024), netDxf y Fornjot (archivados),
IFC++ (archivado de hecho), xeoIFC (no es abierto), y copiar código de Bonsai (GPL) o Chili3d (AGPL) dentro de
un producto cerrado. Con FreeCAD (LGPL), lo que se copie o modifique sigue siendo LGPL.

### 6.3 Pendientes antes de decidir la licencia de BIM Simple
1. **CGAL dentro de IfcOpenShell** ⚠️: confirmar con los mantenedores (foro OSArch o issue) si las ruedas de PyPI
   enlazan CGAL GPL (`svgfill` y el núcleo `cgal`) y qué implica para un producto cerrado. Si molesta, las
   alternativas son: (i) no usar las funciones que dependen de CGAL; (ii) compilar IfcOpenShell sin CGAL, lo que
   requiere compiladores; (iii) publicar BIM Simple como libre.
2. **Cumplir LGPL en la práctica**: aviso de licencias en "Acerca de", el código fuente de las versiones LGPL
   usadas (o un enlace), que el usuario pueda reemplazar la librería y no prohibir la ingeniería inversa
   necesaria para eso ⚠️ (resumen general, no asesoría legal).
3. **Si se decide publicarlo libre (GPL)**, se abre la puerta a reutilizar código de Bonsai, y la pila (a) sigue
   siendo válida.

---

## 7. Fuentes (consultadas el 2026-10-11)
- Repositorios (API de GitHub; datos crudos en `repos_data.tsv`): IfcOpenShell/IfcOpenShell (README, AGENTS.md,
  `docs/ifcopenshell-js*.rst`, `src/ts/*/package.json`, `src/*/pyproject.toml`, `src/svgfill/README.md`,
  `src/ifcgeom/kernels/`, `src/ifcopenshell-python/ifcopenshell/file.py` y `api/`), xBimTeam/XbimEssentials y
  XbimGeometry (README, LICENCE.md), ifcquery/ifcplusplus (README), xeofoundry/xeoIFC (README),
  LTplus-AG/ifc-lite (README, `packages/create/README.md`), ThatOpen/*, buildingSMART/* (README y LICENSE),
  GeometryGym/GeometryGymIFC, hypar-io/Elements, Open-Cascade-SAS/OCCT (`OCCT_LGPL_EXCEPTION.txt`),
  CGAL/cgal (`Installation/LICENSE`), elalish/manifold, gkjohnson/three-bvh-csg (README), xeokit/xeokit-sdk
  (README), helix-toolkit/helix-toolkit (README), pascalorg/editor (README, `packages/ifc-converter`),
  xiangechen/chili3d (README), ibuilder/massing (README), FreeCAD/FreeCAD (`src/Mod/BIM`), OpenAEC-Foundation.
- Registros: registry.npmjs.org y api.npmjs.org (descargas), pypi.org/pypi/*/json, api.nuget.org (v3).
- Documentación oficial: [docs.ifcopenshell.org](https://docs.ifcopenshell.org/ifcopenshell-js.html),
  [Sweet Home 3D – descarga](https://www.sweethome3d.com/download.jsp) y
  [historial](https://www.sweethome3d.com/history.jsp),
  [Qt – Scene3D obsoleto](https://doc.qt.io/QT-6/qtquick-scene3d-qmlmodule-obsolete.html).
- Terceros: [buildingSMART – IFC](https://www.buildingsmart.org/standards/bsi-standards/industry-foundation-classes/)
  (vía buscador; 403 al descargar), [IFCX Core project update](https://www.buildingsmart.org/ifcx-core-modularisation-project-update/),
  [IFC X Final Project Plan voting](https://www.buildingsmart.org/ifc-x-core-modularisation-final-project-plan-voting/),
  [OSArch – IFCX Core Project Update](https://community.osarch.org/discussion/3587/ifcx-core-project-update-by-buildingsmart),
  [Lista de Qt – retiro de Qt 3D](https://lists.qt-project.org/pipermail/development/2024-March/045127.html),
  [FreeCAD 1.0 (pixls.us)](https://discuss.pixls.us/t/freecad-1-0-new-features-and-the-larger-picture/46690),
  [Bonsai v0.8.0 (BlenderNation)](https://www.blendernation.com/2024/09/01/bonsai-previously-blenderbim-add-on-v0-8-0-adds-blender-4-2-and-much-more/).
