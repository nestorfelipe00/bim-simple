# Proyectos abiertos de modelado BIM y arquitectura: qué hay en GitHub y cómo están hechos

Investigación para elegir la base tecnológica de **BIM Simple**.
Datos consultados el **2026-10-11** con la API de GitHub (`gh api`, solo lecturas GET) y lectura de README y código fuente. No se clonó, instaló ni ejecutó nada.

**Marcas usadas:**
- 📄 = verificado en el código o el repositorio
- 📖 = documentación oficial del proyecto (README, sitio)
- 🌐 = fuente de terceros
- ⚠️ = no verificado o inferido

"Último commit" es el último commit de la rama principal. "★" son las estrellas de GitHub en la fecha de consulta.

---

## 1. Tabla resumen

| # | Proyecto | Tipo | Licencia | ★ | Último commit | Stack | Muros con espesor y uniones | Capas | Aberturas | Losas / columnas | Exporta IFC | Planta 2D | Estado | Valor para BIM Simple |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **pascalorg/editor** (Pascal) | Editor web 3D/2D | MIT | 24 784 | 2026-10-11 | TS, React 19, Next 16, Three.js WebGPU, R3F, Zustand, Zundo | Sí, inglete (miter) en cada esquina 📄 | Sí ("assembly") 📄 | Sí, CSG 📄 | Sí / Sí 📄 | Sí, IFC4 con escritor STEP propio (desde 2026-09-30) 📄 | Sí, símbolo por tipo de elemento + láminas PDF 📄 | Muy activo, lo mantiene una empresa | **Muy alto**: base posible o referencia principal |
| 2 | **FreeCAD** (banco BIM) | CAD de escritorio | LGPL-2.1 | 34 137 | 2026-10-11 | C++/Qt, OpenCascade, Python | Sí, con boceto base o fusión 📄⚠️ | Sí (multimateriales) ⚠️ | Sí | Sí / Sí | Sí, vía IfcOpenShell (NativeIFC) 📄 | Sí (planos de sección + TechDraw) 📖 | Activo desde 2011 | Medio: referencia de dominio, no sirve como base web |
| 3 | **Sweet Home 3D** | Diseño de interiores, escritorio | GPL | n/d (está en SourceForge) | v7.5 📖 | Java, Java3D | Sí, cada muro guarda qué muro toca en su inicio y en su fin 📄 | No ⚠️ | Sí | Pisos de habitación / no ⚠️ | No ⚠️ | Sí (planta como parte central) | Activo, prácticamente un solo autor ⚠️ | Medio: referencia de interfaz y de uniones (no se puede copiar código: GPL) |
| 4 | **LTplus-AG/ifc-lite** | Kit IFC web (leer, editar, crear, dibujar en 2D) | MPL-2.0 | 419 | 2026-10-11 | TS + Rust/WASM, WebGPU | Sí (crear muros y unirlos en el IFC) 📄 | Por IFC ⚠️ | Sí 📄 | Sí / Sí 📄 | **Sí, es su núcleo** 📄 | Sí, plantas y secciones SVG cortando mallas 📄 | Muy activo (empezó en 2026-01) | Alto como **librería** IFC y 2D |
| 5 | **hypar-io/Elements** | Librería C# de elementos de edificio | MIT | 420 | 2026-05-26 | C#/.NET, núcleo B-rep/CSG propio | Sí 📄 | ⚠️ | Sí (Opening) 📄 | Sí / Sí 📄 | Sí (IFC4) + DXF + SVG 📄 | SVG/DXF 📄 | Activo y más lento | Medio: buena referencia de modelo de datos |
| 6 | **bimrocket/bimrocket** | Plataforma web de visualización y edición BIM | EUPL-1.1+ / LGPL-3.0+ (doble) 📄 | 99 | 2026-10-09 | JS + Three.js, servidor Java Quarkus | No, solo sólidos CSG genéricos 📄 | No | CSG genérico | Genéricos | Sí (IFC2X3, IFC4, IFC4X3) con escritor propio 📄 | Impresión PDF vectorial 📖 | Activo, un autor principal, lo financia un ayuntamiento | Medio: interfaz en español y catalán, escritor IFC en JS |
| 7 | **ibuilder/massing** | Plataforma AEC web + escritorio (Tauri) | MIT | 122 | 2026-09-24 | Python (FastAPI + IfcOpenShell), TS (That Open) | Sí, según el README 📖⚠️ | ⚠️ | Sí 📖 | Sí 📖 | Sí: el IFC es la fuente de verdad 📖 | Plantas, secciones, láminas PDF/DXF 📖⚠️ | Muy activo (empezó en 2026-06) | Medio: ejemplo de la arquitectura "IfcOpenShell en un servidor" |
| 8 | **cvdlab/react-planner** | Componente web de planta 2D/3D | MIT | 1 480 | 2019-11-03 | JS, React + Redux + Immutable, SVG + Three.js | Espesor sí; uniones mal resueltas 📄 | No | Sí (ThreeBSP) 📄 | Áreas / no | No | SVG 📄 | **Abandonado** | Bajo: caso de estudio |
| 9 | **furnishup/blueprint3d** (y derivados) | Diseño de interiores web | MIT | 1 984 | 2016-07-10 | TS, Three.js, jQuery | Básico 📄 | No | Sí | No | No | Canvas 2D | **Abandonado** (hay copias modernizadas) | Bajo: caso de estudio |
| 10 | **xiangechen/chili3d** | CAD 3D general en el navegador | **AGPL-3.0** | 4 901 | 2026-09-19 | TS, OpenCascade 8 en WASM, Three.js | No es BIM | — | — | — | No (STEP/IGES/BREP/STL) | No | Activo, casi un solo autor | Medio: referencia de deshacer, comandos y núcleo OCCT (no reutilizable por AGPL) |
| 11 | **ThatOpen/engine_clay** | Motor de modelado BIM web | MIT | 74 | 2024-10-09 | TS, Three.js, web-ifc | Sí ⚠️ | ⚠️ | ⚠️ | ⚠️ | Sí (escribe IFC) 📖 | No | **Detenido** desde 2024-10 | Bajo (lo cubre el informe de That Open) |
| 12 | Otros: openPlan3D, arcada, Energy3D, aedifex, ifc5cad, building-editor | Ver §3.12 | MIT / Apache / AGPL | 18–411 | varios | — | — | — | — | — | Ninguno exporta IFC útil, salvo ifc5cad (IFC5) | — | Mezcla de activos y abandonados | Lecciones |

---

## 2. Cómo se buscó

Se consultó la búsqueda de repositorios de GitHub con:
- términos: `ifc editor`, `bim editor`, `floor plan editor`, `bim authoring`, `ifc authoring`, `parametric building`, `bim threejs`, `ifc quantity takeoff`, `ifc floor plan`, `walls doors windows editor`, `opencascade wasm cad`;
- temas (topics): `bim`, `openbim`, `ifc`, `floorplan`, `bim-authoring` (este último sin resultados);
- nombres concretos: react-planner, blueprint3d, sweethome3d, chili3d, energy3d, BIM-Tools y "revit/archicad alternative".

Después, para los candidatos, se leyeron los metadatos, las cuentas de commits y contribuidores, el README, el árbol de carpetas y archivos clave de código.

Se descartaron:
- **los visores** (xeokit, web-ifc-viewer, BIMsurfer, bldrs Share, Astral3D), porque no crean ni editan modelos;
- **Bonsai/Blender y That Open**, porque los cubren otros agentes;
- **las herramientas de automatización** de Revit y ArchiCAD.

---

## 3. Fichas por proyecto

### 3.1 Pascal Editor — `pascalorg/editor` ⭐ el más relevante

**Datos:**
- Licencia MIT 📄.
- 24 784 ★ y 3 072 bifurcaciones (forks).
- Creado el 2025-10-16; último commit 2026-10-11.
- 1 989 commits y 51 contribuidores. Tres personas concentran la mayoría: wass08 (879), Aymericr (577) y sudhir9297 (257) 📄.
- Lo mantiene una empresa, **Pascal Group Inc.** 📄. Última versión publicada: v1.0.3 (2026-09-24).
- Demo: editor.pascal.app.

**Qué es:** un editor de edificios 3D/2D en el navegador, pensado para "usar primero en local". Se puede ejecutar desde la línea de comandos (`npx @pascal-app/cli editor`) y tiene un servidor MCP para que agentes de IA modelen 📖.

**Qué permite modelar** (📄, según el código):
- **Jerarquía:** Sitio > Edificio > Nivel. Dentro de cada nivel: muros (con puertas y ventanas), losas, cielorrasos, cubiertas, zonas o ambientes, escaneos 3D y guías 2D.
- **Otros tipos de elemento** (carpetas en `packages/nodes/src/`): column, stair, roof, dormer, chimney, skylight, fence, curtain-wall, pipe, gutter, measurement, construction-dimension, cabinet, entre otros.
- **Muros:**
  - **Inglete en las esquinas** (`packages/core/src/systems/wall/wall-mitering.ts`). El punto de unión se calcula intersectando las líneas de las caras. Un límite (`MITER_LIMIT = 10`) cambia a unión a tope cuando dos muros son casi paralelos, para evitar puntas infinitas.
  - Uniones en L y en T, muros curvos, y justificación por cara (a/b).
  - **Capas ("assembly")** (`packages/core/src/schema/assembly.ts`): cada capa tiene un rol (terminación, aislación, estructura, etc.) y un espesor. El espesor total del muro es la suma de las capas del cuerpo. Una sola capa se marca como núcleo estructural.
  - Muchas pruebas automáticas con casos de referencia: `wall-mitering.test.ts`, `wall-layer-bands.test.ts`, `wall-topology.test.ts`…
- **Aberturas:** se recortan del muro con operaciones booleanas usando `three-bvh-csg` 📖.

**IFC:**
- **Importación** con web-ifc (`packages/ifc-converter`) 📄. Reconstruye muros, uniones, justificación desde `IfcMaterialLayerSetUsage`, ambientes y losas.
- **Exportación IFC4** con un **escritor STEP propio en TypeScript** (`export/step.ts` y `export/scene-to-ifc.ts`, de 1 654 líneas), sin depender de librerías 📄. Escribe `IfcWall`, `IfcSlab`, `IfcColumn`, `IfcDoor`, `IfcWindow`, `IfcOpeningElement` con `IfcRelVoidsElement`/`IfcRelFillsElement`, `IfcMaterialLayerSetUsage` y `IfcSpace`, entre otros.
- La exportación se incorporó recién el **2026-09-30** (PR #984), casi un año después de empezar el proyecto, y tras un pedido de la comunidad (#981) 📄. Es nueva: la validez del IFC no está comprobada ⚠️.

**Planta 2D y láminas:**
- Cada tipo de elemento define **su propia representación en planta** (`def.floorplan(node, ctx)` en `packages/nodes/src/<tipo>/floorplan.ts`). Es decir, **no corta la malla 3D**: es la misma idea que el símbolo de planta de ArchiCAD 📄.
- Hay un editor 2D completo: 97 archivos en `editor-2d` y `floorplan`.
- Exporta PDF vectorial con pdfkit y **láminas con rótulo** (`sheet-export.ts`). El código dice explícitamente que la lámina y el editor 2D usan la misma geometría "para que no puedan diferir" 📄.

**Cómo está armado** (📖📄):
- **Monorepo** (Turborepo) con paquetes separados: `core` (esquemas Zod, estado y sistemas de geometría), `viewer` (render 3D), `editor` (herramientas y paneles), `nodes` (cada tipo de elemento como complemento), `ifc-converter`, `mcp`, `cli`.
- **Modelo de datos:** un **diccionario plano** de nodos (`Record<id, Node>`) con `parentId`, validado con Zod. Es la fuente de verdad; el IFC es solo un formato de importación y exportación.
- **Geometría:** "sistemas" que recalculan solo los nodos marcados como modificados ("dirty") en cada cuadro.
- **Deshacer y rehacer:** middleware **Zundo** sobre Zustand, con historial de 50 pasos. El estado se guarda en IndexedDB. Hay una función para agrupar operaciones en un solo paso (`runAsSingleSceneHistoryStep`) 📄.
- **Un tipo de elemento = una carpeta** con `schema`, `definition`, `renderer` (3D), `floorplan` (2D), `tool`, `panel` (inspector), `parametrics` y `paint`. Es el patrón de complemento que conviene copiar.

**Limitaciones y riesgos:**
- No se encontraron archivos de traducción: interfaz solo en inglés ⚠️. Está orientado a viviendas, con mucho mobiliario.
- La versión "Pascal Next" que muestran como demo **no es código abierto** 📖.
- Lo controla una empresa (el modelo "open core" podría cambiar) ⚠️.
- Es enorme y cambia muy rápido: 4 361 archivos y unos 2 000 commits en un año.
- Tiene un derivado, `TangSY/aedifex` (MIT, que reconoce que "is built upon Pascal Editor") 📄.

**Qué se puede reutilizar (MIT):** todo, conservando el aviso de copyright. En especial `wall-mitering.ts`, el esquema de `assembly`, el escritor `step.ts`/`scene-to-ifc.ts`, el patrón de complemento por tipo de elemento y el canal de planta 2D → PDF.

### 3.2 FreeCAD, banco de trabajo BIM (antes Arch) — `FreeCAD/FreeCAD`, `src/Mod/BIM`

**Datos:**
- Licencia LGPL-2.1 📄; 34 137 ★; último commit 2026-10-11.
- El archivo `ArchWall.py` existe desde **2011-12-12**, con commits de yorikvanhavre 📄.
- El responsable del BIM, **Yorik van Havre, es arquitecto** (su perfil de GitHub dice "architect, freelancer… FreeCAD developer") 📄.
- El banco BIM externo se integró en FreeCAD desde la 1.0 📖.

**Qué permite modelar:**
- Muros, ventanas, escaleras, cubiertas, losas, columnas, vigas, espacios, muros cortina, armaduras y cañerías (módulos `ArchWall.py` de 94 KB, `ArchWindow.py`, `ArchStairs.py`, `ArchRoof.py`, etc.) 📄.
- Los muros pueden salir de un boceto con varios tramos, y tienen ancho, alineación y desplazamiento por tramo 📄.
- El código advierte que **no es "tolerante al renombrado topológico"** con bocetos comunes 📄. Este es el talón de Aquiles conocido de FreeCAD.

**IFC:** módulo `nativeifc` (21 archivos) que usa **IfcOpenShell** y trabaja directamente sobre el IFC 📄.

**2D:** `ArchSectionPlane.py` (67 KB) genera cortes que se llevan a TechDraw para hacer láminas 📄📖.

**Arquitectura:**
- Aplicación de escritorio en C++/Qt con núcleo de geometría OpenCascade (B-rep exacto). La capa BIM está en Python.
- El deshacer usa las transacciones del documento de FreeCAD ⚠️.

**Lección:** a un arquitecto que programa le llevó **más de 13 años**, apoyado en una plataforma CAD completa, llegar a un BIM usable. Y aun así el propio README reconoce una "curva de aprendizaje empinada" 📖.

**Reutilización:** LGPL permite usar FreeCAD como librería, pero no sirve como base de una app web en español. Sirve como referencia de dominio: qué propiedades necesita un muro, cómo representar cortes, cómo mapear a IFC.

### 3.3 Sweet Home 3D

**Datos:**
- Licencia GPL; código en SourceForge 📖. Versión 7.5 según la página de descarga, actualizada el 2025-05-05 📖.
- Java y Java3D (paquetes `model`, `viewcontroller`, `swing` y `j3d` en una copia de 2017, `Vanuan/sweethome3d`) 📄.

**Qué modela:** muros con espesor, puertas, ventanas, habitaciones (pisos) y mobiliario. No exporta IFC ⚠️.

**Uniones:** cada muro guarda una referencia a los muros que tiene en su inicio y en su fin (`wallAtStart`/`wallAtEnd` en `model/Wall.java`). La forma de la esquina se calcula a partir de esa relación 📄.

**Arquitectura:**
- Patrón modelo / vista-controlador con interfaces de vista intercambiables (Swing y Java3D).
- El deshacer usa los `UndoableEdit` de Swing en los controladores ⚠️.

**Lección:** un proyecto prácticamente unipersonal ⚠️, mantenido desde 2006 ⚠️, que tiene éxito porque su **alcance es acotado** (interiorismo) y su interfaz muy simple. Es la mejor referencia de "simple de usar".

**Reutilización:** la GPL obliga a publicar como GPL cualquier obra derivada. Conviene tomar ideas, no código.

### 3.4 IFClite — `LTplus-AG/ifc-lite`

**Datos:**
- Licencia MPL-2.0 📄; 419 ★.
- Creado el 2026-01-10; 5 122 commits en 9 meses. Dos personas principales: louistrue (3 619) y BIMvoice (1 217) 📄.
- 51 paquetes npm y 5 crates de Rust 📖.

**Qué hace:**
- Lee, ve, consulta, edita, valida (IDS) y exporta IFC2X3, IFC4, IFC4X3 e IFC5, todo en el navegador 📖.
- Núcleo en Rust compilado a WASM, con un núcleo CSG de "aritmética exacta" que verifican contra IfcOpenShell 📖.
- **`@ifc-lite/create`** crea IFC4 desde cero 📄📖:
  - muros, losas, columnas, vigas, escaleras, cubiertas, puertas y ventanas que perforan el muro, psets, cantidades y materiales;
  - **uniones de muros** (`joinWallsInStore`, que reescribe ejes y `IfcRelConnectsPathElements`);
  - generación de espacios a partir de muros.
- **`@ifc-lite/mutations`**: edición de propiedades con deshacer 📖.
- **`@ifc-lite/drawing-2d`**: plantas y secciones SVG **cortando mallas**, con rayado de materiales, barridos de puertas, flechas de escalera, escalas de papel y presets gráficos 📖.

**Arquitectura:** el IFC (almacén columnar en memoria) **es** el modelo. Las ediciones son "mutaciones" sobre ese almacén.

**Reutilización:** la MPL-2.0 tiene "copyleft por archivo": se puede usar desde una app con otra licencia, pero los archivos de IFClite que se modifiquen deben publicarse.

**Lugar en BIM Simple:** encaja como **librería de IFC (exportar, validar) y de dibujo 2D a partir del IFC**, no como editor base.

### 3.5 Hypar Elements — `hypar-io/Elements`

**Datos:**
- MIT; 420 ★; 5 579 commits; 33 contribuidores; desde 2018-06.
- Último commit 2026-05-26 📄. Lo desarrolla la empresa Hypar.

**Qué es:** una librería C# "para arquitectos e ingenieros que quieren escribir código que genera edificios" 📖. Incluye `Wall`, `StandardWall`, `WallByProfile`, `Floor`, `Column`, `Beam`, `Opening`, `Space`, entre otros 📄.

**Serialización:** JSON, IFC (paquete `Hypar.IFC4`), DXF, SVG (plantas, secciones, alzados) y glTF 📄.

**Geometría:** un núcleo B-rep/CSG simple que, según ellos, hace "flat stuff with holes in it really well" ("cosas planas con agujeros, y muy bien"). Sostienen que un núcleo industrial es caro y complejo y no hace falta para AEC 📖.

**Lección clave:** decidieron que **su propio modelo de elementos es la fuente de verdad y el IFC un formato de salida**. Argumentan que la ontología fija del IFC dificulta crear tipos propios 📖.

**Reutilización:** como C# no encaja con un stack JS, sirve como referencia de diseño.

### 3.6 BIMROCKET — `bimrocket/bimrocket`

**Datos:**
- Licencia doble EUPL-1.1+ / LGPL-3.0+. Copyright del **Ajuntament de Sant Feliu de Llobregat** 📄.
- 99 ★; 885 commits, de los que 824 son de un solo desarrollador (realor) 📄. Desde 2021.

**Qué permite:**
- Diseño paramétrico con **sólidos CSG genéricos**: extruir, revolucionar, unión, resta, push-pull y perfiles I, L, T, U, Z.
- No tiene herramientas específicas de muro, losa o puerta 📄.
- Entrada y salida de **IFC2X3, IFC4 e IFC4X3_ADD2** con parser y escritor STEP propios en JS (`platform/io/ifc/IFCSTEPExporter.js` y esquemas generados) 📄.
- BCF, IDS y servidor Java con OrientDB/MongoDB 📖.
- **Interfaz en inglés, castellano y catalán** 📖📄.
- No se encontró un deshacer global del modelo: la palabra "undo" solo aparece en las herramientas de medición ⚠️📄.

**Lección:** un solo desarrollador con financiación pública logra en 5 años una plataforma muy completa de visualización y gestión, pero el modelado se queda en CSG genérico, no en BIM de autor.

### 3.7 Massing — `ibuilder/massing`

**Datos:**
- MIT; 122 ★.
- Creado el **2026-06-14**; 2 836 commits en 4 meses. Un humano (ibuilder, 2 634 commits) más cuentas de agentes de IA (`cursoragent` 88, `claude` 34) 📄.

**Qué dice hacer:** autoría IFC en el navegador (muros, losas, columnas, puertas y ventanas paramétricas, muros cortina, armaduras, MEP), documentación de obra (plantas, secciones, alzados, láminas PDF/DXF), cómputos, IDS, BCF y un portal de gestión de obra de 139 módulos 📖. Todo esto **no está verificado** ⚠️.

**Arquitectura** (📄📖):
- Visor web con That Open Fragments.
- **Cada edición es una "receta" de IfcOpenShell que corre en un servidor Python (FastAPI)**. Después se reconvierte el IFC y se republica.
- Aplicación de escritorio con Tauri.
- **Deshacer = una pila de rutas a copias del archivo IFC** (`edit_history.json`), según el docstring de `recipe_log.py` 📄.

**Lección:** confirma la idea "Three.js + IfcOpenShell". También muestra su costo: cada clic recalcula el IFC en un servidor, el deshacer es pesado y hace falta Python en el usuario. El README admite su propio riesgo: "Breadth is the asset; it is also the risk" ("la amplitud es la ventaja y también el riesgo") 📖. Es además un ejemplo de lo que hoy produce una persona con agentes de IA: mucha amplitud y calidad difícil de evaluar.

### 3.8 react-planner — `cvdlab/react-planner` (abandonado)

**Datos:**
- MIT; 1 480 ★.
- 2016-06 → último commit **2019-11-03**; 1 507 commits.
- Tres autores principales del laboratorio CVDLab (académico ⚠️) 📄.

**Arquitectura:**
- React + Redux + Immutable.js. Escena por capas, con vértices, líneas (muros), huecos (aberturas), áreas y objetos.
- Planta en SVG y 3D con Three.js.
- Catálogo de elementos ampliable mediante "factories" 📄.

**Muros:** cada muro es una caja; las aberturas se restan con **ThreeBSP** (CSG) en `wall-factory-3d.js` 📄.

**Deshacer:** `sceneHistory` con estados inmutables (`Project.undo`) 📄.

**Qué lo frenó:**
- El issue #17 "Create new algorithm for wall expansion" (las uniones de muros) está abierto desde **2016-10** 📄.
- En el issue #102 ("Abandoned?", 2018) un autor responde: "We are very busy with other projects" ("estamos muy ocupados con otros proyectos") 📄.
- Nunca exportó IFC.

**Lección:** el estado inmutable hace el deshacer trivial, pero sin un algoritmo serio de uniones y sin IFC se queda en "dibujar habitaciones".

### 3.9 Blueprint3D — `furnishup/blueprint3d` y derivados (abandonado)

**Datos:**
- MIT; 1 984 ★. Creado en 2015-07; último commit **2016-07-10**; solo 107 commits 📄.
- Era el prototipo de una startup. El propio README admite que "was rushed through various prototype stages, and never refactored" ("se hizo apurado en varias etapas de prototipo y nunca se reorganizó") 📖.

**Derivados:** `aalavandhaann/blueprint-js` (591 ★, último commit 2024-11) y `charmlinn/blueprint3d-modern` (157 ★, 2026-05) 📄.

**Lección:** un prototipo apurado, sin pruebas ni un formato de datos bien pensado, se abandona en cuanto se va el equipo. Aun así sigue atrayendo estrellas: **hay demanda de una herramienta simple**.

### 3.10 Chili3D — `xiangechen/chili3d`

**Datos:**
- **AGPL-3.0**; 4 901 ★. Desde 2022-12; 1 247 commits, de los que 1 215 son de un solo autor 📄.

**Qué es:** CAD 3D general con **OpenCascade 8 compilado a WASM** y Three.js 📖.

**Arquitectura:**
- Monorepo con interfaces abstractas (`IShape`, `IShapeFactory`) en `core` e implementación OCCT en `wasm`, de modo que el núcleo geométrico es intercambiable 📖.
- **Transacciones y deshacer/rehacer** en el `core`; comandos; interfaz tipo cinta ("ribbon") estilo Office 📖.
- Traducciones a inglés, chino y portugués de Brasil.

**Lección:** una sola persona puede llegar lejos con OCCT en WASM, pero el resultado es un CAD mecánico, no BIM.

**Reutilización:** la AGPL exige publicar el código de toda la app, incluso si solo se usa como servicio web. **No conviene reutilizar su código**; sí copiar ideas (núcleo detrás de una interfaz, transacciones).

### 3.11 That Open Clay — `ThatOpen/engine_clay`

**Datos:** MIT; 74 ★; 232 commits; último commit **2024-10-09** 📄.

**Qué prometía:** "create and edit IFC geometry and data, as well as create modellers for end users" ("crear y editar geometría y datos IFC, y construir modeladores para usuarios finales") 📖.

**Estado:** sin commits desde hace 2 años. Indica que modelar directamente sobre IFC en la web es difícil incluso para el equipo de web-ifc (detalle en el informe de That Open).

### 3.12 Otros revisados (breve)

- **laanlabs/openPlan3D** (MIT, 202 ★, SvelteKit + Three.js, desde 2026-02, 379 commits):
  - muros, puertas, ventanas, escaleras y ambientes detectados automáticamente;
  - deshacer con operaciones agrupadas;
  - exporta SVG, DXF y PDF con rótulo. **Sin IFC** 📖.
- **mehanix/arcada** (Apache-2.0, 411 ★, React + pixi.js, 86 commits): solo planta 2D de interiores 📄.
- **concord-consortium/energy3d** (MIT, Java): 2012 → último commit 2020-01-10, con 1 891 de sus 3 576 commits de un solo autor 📄. CAD y simulación energética para educación; se detuvo.
- **TangSY/aedifex** (MIT): derivado de Pascal con un asistente de IA 📄.
- **louistrue/ifc5cad** (AGPL, OCCT WASM + Three.js, IFC5): 20 commits en 2 días de 2026-02 y nada más. Prototipo abandonado 📄.
- **baues/building-editor** (MIT): 20 commits; último en 2022-11. Abandonado 📄.
- **⚠️ Alerta:** `ViceAdvocate/ArchiCAD` y `Subash1017/ArchiCAD-Workflow-Tools` ("…2026 Free Trial Full Features") tienen aspecto de cebo de software pirata o malware. **No descargar.**

---

## 4. Generar planos 2D y cómputos a partir de IFC

**Planos 2D.** Hay dos enfoques:

| Enfoque | Cómo funciona | Quién lo usa | Ventaja y límite |
|---|---|---|---|
| **A. Símbolo por tipo de elemento** | Cada elemento sabe dibujarse en planta | Pascal (`def.floorplan`) 📄, Sweet Home 3D, ArchiCAD | Rápido y con convenciones de arquitectura (barridos de puertas, líneas de corte); requiere programar cada tipo |
| **B. Corte de la geometría 3D** | Se corta el modelo con un plano | ifc-lite `drawing-2d` 📄, FreeCAD `ArchSectionPlane` 📄, IfcConvert/Bonsai (otro informe) | Sirve para cualquier modelo IFC y para secciones y alzados; da un resultado más "crudo" |

Lo que mejor funciona es la combinación: **A para plantas, B para secciones y alzados**.

**Cómputos:**
- `ifc-lite schedule` hace tablas de puertas, etc., con salida csv/json/html 📖.
- Massing hace cómputos con respaldo geométrico ⚠️.
- Existen scripts pequeños con IfcOpenShell (`aec-platform/qto`, `bcirilor/ifcqt`), con 0–1 ★ y poca madurez.
- Lo más sólido es calcular las cantidades **desde el modelo propio**: largo, alto, espesor por capa y áreas descontando aberturas. Luego se escriben como `IfcElementQuantity` al exportar.

---

## 5. Lecciones

### 5.1 Qué tan lejos llegaron y cuánto tardaron

| Proyecto | Equipo | Tiempo | Hasta dónde llegó |
|---|---|---|---|
| FreeCAD BIM | 1 arquitecto líder + comunidad | 2011 → hoy (15 años) | BIM completo, pero difícil de usar |
| Sweet Home 3D | ~1 persona ⚠️ | 2006 → hoy | Interiorismo excelente, sin IFC |
| react-planner | 3 académicos | 2016–2019 | Planta y 3D sin uniones buenas ni IFC; abandonado |
| Blueprint3D | Startup | 2015–2016 | Prototipo; abandonado |
| Energy3D | 1 persona | 2012–2020 | Producto educativo; detenido |
| BIMROCKET | 1 persona con financiación municipal | 2021 → hoy | Plataforma de visualización y gestión; modelado CSG genérico |
| Chili3D | 1 persona | 2022 → hoy | CAD general sólido sobre OCCT |
| Pascal | Empresa, 3 personas principales | 1 año | Muros con uniones y capas, losas, cubiertas, escaleras, planta 2D, láminas, IFC de ida y vuelta |
| ifc-lite, Massing | 1–2 personas + agentes de IA ⚠️ | 4–9 meses | 5 000 y 2 800 commits respectivamente |

En los proyectos de 2026, los agentes de IA cambiaron la escala de lo que logran pocas personas. Pero amplitud no es igual a solidez ⚠️.

### 5.2 Qué los frenó

1. **Uniones de muros.** Fue el problema abierto de react-planner (issue de 2016 nunca cerrado). Pascal le dedicó un módulo entero, con límite de inglete y pruebas de referencia. FreeCAD lucha con el renombrado topológico.
2. **Booleanas y aberturas.** Todos los proyectos web usan CSG sobre mallas (ThreeBSP, three-bvh-csg). Sirve para muros rectos con huecos. OCCT en WASM da exactitud, pero suma peso y complejidad (Chili3D, ifc5cad, que se abandonó en 2 días).
3. **IFC.** Ningún editor web de planos exportaba IFC hasta que Pascal lo agregó en 2026-09. Los que hacen IFC "de verdad" (FreeCAD, Massing, ifc-lite) se apoyan en IfcOpenShell o en un núcleo propio de muchos miles de líneas. Un escritor IFC4 acotado son unas **1 650 líneas** en Pascal.
4. **Documentación 2D.** Es la parte que separa un juguete de una herramienta profesional. Solo Pascal, FreeCAD, ifc-lite y Massing la abordan; los planificadores de interiores no.
5. **Falta de modelo de datos y de pruebas.** Blueprint3D lo admite en su propio README. Los proyectos que sobreviven (Pascal, ifc-lite, Elements) tienen miles de pruebas y casos de referencia.
6. **Personas.** Los abandonos (react-planner, Blueprint3D, Energy3D, Clay) coinciden con que el equipo pasó a otros proyectos, más que con un problema técnico concreto ⚠️.

### 5.3 Arquitectura que comparten los proyectos que mejor funcionan

1. **Un modelo de datos propio y paramétrico es la fuente de verdad.** Pascal, Hypar, Sweet Home 3D, react-planner y openPlan3D guardan el muro como inicio, fin, espesor, alto, capas y justificación. El **IFC es un formato de importación y exportación**.
   - La alternativa "el IFC es el modelo" (Bonsai, FreeCAD NativeIFC, Massing, ifc-lite) da fidelidad IFC total, pero cada edición es más cara: Massing reconvierte en un servidor y su deshacer guarda copias del archivo.
2. **La geometría se deriva de los parámetros.** "Sistemas" recalculan solo lo modificado (dirty nodes). Primero se calcula la huella 2D del muro con las esquinas resueltas por intersección de líneas; después se extruye; las aberturas se restan con CSG o se construyen como huecos en el perfil.
3. **Un núcleo "plano con agujeros" alcanza para muros, losas y columnas** (Hypar lo dice explícitamente). OCCT no es necesario al principio.
4. **Cada tipo de elemento es un complemento:** esquema + render 3D + símbolo 2D + herramienta + inspector + mapeo a IFC (Pascal).
5. **Deshacer basado en estado inmutable** (Zustand + Zundo, Redux + Immutable) o en **transacciones y comandos** (Chili3D, Sweet Home 3D). Con un diccionario plano de nodos, el deshacer sale casi gratis.
6. **La lámina usa la misma geometría que el editor 2D**, así nunca se desincronizan (Pascal).
7. **Muchas pruebas con casos de referencia** para las uniones, las aberturas y el IFC (Pascal e ifc-lite tienen decenas de archivos `*.test.ts` solo para muros).

---

## 6. Conclusión para BIM Simple

**1. Existe un proyecto con licencia compatible que ya cubre gran parte de la hoja de ruta: Pascal Editor (MIT).**
Tiene muros con uniones en inglete y capas, aberturas, losas, cielorrasos, cubiertas, escaleras, columnas, niveles, planta 2D con símbolos, láminas PDF e IFC de ida y vuelta. Usa exactamente el stack que sugirió el usuario (Three.js), más React/R3F, Zustand y Zundo. Hay tres caminos posibles:

| Opción | Qué implica | A favor | En contra |
|---|---|---|---|
| **A. Bifurcar (fork) Pascal** | Traducir al español, simplificar la interfaz al estilo ArchiCAD, empaquetar con Electron o Tauri | El camino más rápido a funciones avanzadas | Heredar unos 4 400 archivos de una base que cambia a diario y que controla una empresa; difícil de mantener para una sola persona no programadora |
| **B. Programa propio con la arquitectura de Pascal** *(recomendada)* | Modelo de nodos con Zod + Zustand/Zundo + sistemas de geometría + complementos por tipo de elemento; copiar módulos concretos con su aviso MIT | Código pequeño y entendible, enfocado en el MVP (proyecto, pisos, muros con capas y uniones, losas, columnas); permite traducir Pascal a medida que se avanza | Más lento al principio |
| **C. Programa propio sobre IFClite** | Usar IFClite (MPL-2.0) como librería de exportación, validación y dibujo 2D desde IFC; mantener el modelo propio | Sólido en IFC | IFClite no es un editor de muros: no reemplaza a A ni a B |

Módulos de Pascal que conviene copiar en la opción B: `wall-mitering.ts`, `schema/assembly.ts`, `export/step.ts` y `scene-to-ifc.ts`, el patrón `floorplan.ts` y `sheet-export.ts`.

**2. Usar como referencia, no como base:**
- **FreeCAD BIM:** dominio y mapeo a IFC.
- **Sweet Home 3D:** simplicidad de interfaz y uniones `wallAtStart`/`wallAtEnd`. Solo ideas: es GPL.
- **Hypar Elements:** modelo de datos y la idea de un núcleo "plano con agujeros".
- **BIMROCKET:** escritor IFC en JS e interfaz en español/catalán (licencia EUPL/LGPL).
- **Chili3D:** deshacer con transacciones y núcleo detrás de una interfaz. Solo ideas: es AGPL.

**3. No usar como base:**
- Chili3D, xeokit, ifc5cad (AGPL) y Sweet Home 3D (GPL): por licencia.
- react-planner, Blueprint3D, Clay y building-editor: están abandonados.
- Massing: pesado y con afirmaciones no verificadas.

**4. Sobre "Three.js + IfcOpenShell":**
- Ningún editor web exitoso usa IfcOpenShell en el bucle de edición interactiva. Pascal usa web-ifc para importar y su propio escritor para exportar.
- Massing sí lo usa, pero en un servidor Python con reconversión en cada edición.
- Para BIM Simple, lo más sano es usar IfcOpenShell (o IFClite) **solo para exportar y validar** el IFC, no como modelo vivo.

**5. Riesgo de alcance.** Los proyectos que se acotaron (Sweet Home 3D) sobreviven; los que prometieron todo de entrada se estancaron o dependen de una empresa. El MVP debería quedarse en: proyecto IFC + pisos + muros con capas y uniones + losas + columnas + exportación IFC validada. Recién después, puertas, ventanas, planta 2D y láminas.

---

## 7. Fuentes principales (consultadas el 2026-10-11)

**Pascal Editor:**
- 📄 https://github.com/pascalorg/editor (README; `packages/core/src/systems/wall/wall-mitering.ts`; `packages/core/src/schema/assembly.ts`; `packages/core/src/schema/nodes/wall.ts`; `packages/ifc-converter/README.md` y `src/export/{step,scene-to-ifc}.ts`; `packages/editor/src/lib/floorplan/sheet-export.ts`)
- 📄 issue #981 y PR #984 (fusionado el 2026-09-30)

**FreeCAD:**
- 📄 https://github.com/FreeCAD/FreeCAD/tree/main/src/Mod/BIM (`ArchWall.py`, `nativeifc/`)
- 📖 https://github.com/yorikvanhavre/BIM_Workbench

**Sweet Home 3D:**
- 📖 https://www.sweethome3d.com/download.jsp
- 📄 https://github.com/Vanuan/sweethome3d (`src/com/eteks/sweethome3d/model/Wall.java`)

**IFClite:**
- 📄📖 https://github.com/LTplus-AG/ifc-lite (README; `packages/create/README.md`; `packages/drawing-2d/README.md`)

**Hypar Elements:**
- 📄📖 https://github.com/hypar-io/Elements (README; `Elements.Serialization.IFC.csproj`)

**BIMROCKET:**
- 📄📖 https://github.com/bimrocket/bimrocket (README; `LICENSE.txt`; `bimrocket-webapp/src/main/webapp/platform/io/ifc/`)

**Massing:**
- 📄📖 https://github.com/ibuilder/massing (README; `services/api/src/aec_api/recipe_log.py`)

**react-planner:**
- 📄 https://github.com/cvdlab/react-planner (`src/catalog/factories/wall-factory-3d.js`, `src/class/project.js`; issues #17, #88 y #102)

**Blueprint3D:**
- 📄📖 https://github.com/furnishup/blueprint3d (README; issue #72)

**Chili3D:**
- 📄📖 https://github.com/xiangechen/chili3d

**That Open Clay:**
- 📄📖 https://github.com/ThatOpen/engine_clay

**Otros:**
- 📄 https://github.com/laanlabs/openPlan3D
- 📄 https://github.com/mehanix/arcada
- 📄 https://github.com/concord-consortium/energy3d
- 📄 https://github.com/TangSY/aedifex
- 📄 https://github.com/louistrue/ifc5cad
- 📄 https://github.com/baues/building-editor
