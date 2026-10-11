# ¿Pueden las librerías de That Open crear y editar modelos IFC hoy?

Investigación para decidir la base tecnológica de BIM Simple. Fecha: 2026-10-11.
Método: solo lectura de código y documentación publicados (GitHub, registro npm, PyPI, docs oficiales) y del
IfcOpenShell 0.9.0 / Bonsai 0.9.0 ya instalados (sin ejecutar nada). No se instaló ni descargó ningún paquete.

**Marcas**: 📄 leído en código fuente (archivo:línea y commit/versión) · 📖 documentación oficial ·
🌐 fuente de terceros · ⚠️ no verificado o inferido.

**Sobre los números de línea de GitHub**: los de los repos de That Open se obtuvieron con la herramienta de
lectura web, que cuenta las líneas por su cuenta; una segunda lectura dio diferencias de hasta ±5 líneas. Se dan
como "≈ l. N" y fijados a un commit. Los números de línea de IfcOpenShell/Bonsai **instalados** son exactos
(leídos en disco).

Commits de referencia (rama `main`, consultados hoy):
- `ThatOpen/engine_web-ifc` → `a7b53a8` (2026-10-09) 📄
- `ThatOpen/engine_fragment` → `2ba7e9d` (2026-10-06, "bump fragments version to 3.4.8") 📄
- `ThatOpen/engine_components` → `8479a7c` (2026-10-06, "bump front version to 3.4.5") 📄

---

## Respuesta corta

- **web-ifc sí escribe IFC4**, pero a bajo nivel: hay que construir **cada entidad a mano** (puntos, ejes,
  perfiles, extrusión, representación, placement, relaciones). No hay ayudas para crear muros, contener en un
  piso, capas de material ni uniones. No valida lo que se escribe.
- **Fragments sí tiene API de edición** (desde 3.2.1, octubre 2025), pero edita el formato propio `.frag`
  (una malla optimizada para ver), **no IFC**. No existe exportador Fragments → IFC.
- **@thatopen/components no tiene herramientas de modelado** (ni muro, ni losa, ni columna). Tiene visor,
  cortes, cotas 2D, proyección de aristas, DXF. El intento de motor de modelado (`engine_clay`) está parado
  desde octubre de 2024.
- **IfcOpenShell** ya tiene, bajo **LGPL** (fuera de Bonsai), casi toda la lógica IFC que hoy usa BIM Simple:
  representación de muros/losas/perfiles, uniones de muros (`connect_wall`) y regeneración con ingletes y capas
  (`regenerate_wall_representation`), mover pisos con hijos, deshacer/rehacer, teselado para mostrar en
  Three.js y plantas SVG (`ifcopenshell.draw`). Lo GPL de Bonsai es sobre todo la **capa interactiva atada a
  Blender**.

**Opinión**: That Open hoy es un excelente **visor/plataforma web**, no un motor de autoría IFC. Para BIM Simple
la combinación con menos trabajo y menos riesgo fuera de Blender es **Three.js (o That Open solo para ver) +
IfcOpenShell en Python como proceso auxiliar**. Ver sección 7 y 8.

---

## 1. Paquetes, estado y licencias

**Decisión**: los cinco paquetes están vivos (releases en las últimas semanas); cuatro son MIT y **web-ifc es
MPL-2.0**, no MIT.

| Paquete | Última versión | Fecha | Licencia | Tamaño desempaquetado | Repo |
|---|---|---|---|---|---|
| `web-ifc` | 0.0.78 | 2026-09-21 | **MPL-2.0** | 24,8 MB (14 archivos, sin dependencias) | ThatOpen/engine_web-ifc |
| `@thatopen/fragments` | 3.4.8 | 2026-10-06 | MIT | 25,1 MB | ThatOpen/engine_fragment |
| `@thatopen/components` | 3.4.9 | 2026-10-06 | MIT | 3,4 MB | ThatOpen/engine_components |
| `@thatopen/components-front` | 3.4.5 | 2026-10-06 | MIT | 0,7 MB | ThatOpen/engine_components |
| `@thatopen/ui` | 3.4.14 | 2026-10-01 | MIT | 0,8 MB | ThatOpen/engine_ui-components |

Evidencia 📄 (registry.npmjs.org, `<paquete>/latest` y objeto `time`):
- web-ifc: 0.0.77 (2026-03-06) → 0.0.78 (2026-09-21): **seis meses sin release** antes de la última. Sigue en
  versión 0.0.x (sin API estable declarada). `main: ./web-ifc-api-node.js`.
- fragments: peerDependencies `three >=0.182.0`, `web-ifc >=0.0.77`. Serie 3.x desde 2025-04-10.
- components: peerDependencies `three`, `web-ifc >=0.0.77`, `camera-controls`, `@thatopen/fragments ~3.4.7`.
- Estrellas GitHub (📄 API de GitHub): web-ifc 1059, components 711, fragments 212, ui 59.

**Producto comercial** 📖/🌐:
- 📄 `ThatOpen/platform_services` (README): cliente y CLI `@thatopen/services` para publicar apps y "cloud
  components" en **That Open Platform**. Cita: "Founding Members get early access to the private beta engine
  libraries (`@thatopen-platform/*-beta`)". O sea: **hay librerías privadas en beta solo para miembros**; no se
  publica cuáles son.
- 🌐 AEC Magazine ("That Open Company raises the stakes", fecha ambigua en la página: 21-jul o 9-sep-2026):
  plataforma en la nube tipo "BIM operating system" (CDE, permisos, versiones, alojamiento de apps). Membresía
  fundadora abierta el 22-jun-2026 con acceso beta de por vida y 3 meses de uso ilimitado; **no se publican
  precios**.
- 📖 docs.thatopen.com/intro: las librerías son gratuitas y de código abierto y se puede vender lo que se
  construya con ellas.

**Contradicciones**: una fuente de terceros (🌐 skillselion) dice "Fragments + web-ifc, MIT"; el registro npm y
GitHub dicen **web-ifc = MPL-2.0** 📄. La MPL-2.0 es copyleft por archivo: se puede usar en un producto cerrado,
pero las modificaciones a archivos de web-ifc deben publicarse.

**Alternativas**: ninguna dentro de That Open para la parte de autoría (ver 3 y 4).

---

## 2. web-ifc como motor de escritura

**Decisión**: web-ifc puede crear un IFC4 desde cero y guardarlo, pero es una **API de "líneas STEP"**: cada
entidad se arma a mano y no hay ayudas de alto nivel ni validación.

**Métodos de escritura** 📄 `src/ts/web-ifc-api.ts` @ `a7b53a8` (líneas ≈ ±5):

| Método (firma) | ≈ línea | Qué hace |
|---|---|---|
| `CreateModel(model: NewIfcModel, settings?: LoaderSettings): number` | ≈ 634 | Modelo nuevo; escribe cabeceras FILE_DESCRIPTION/FILE_NAME/FILE_SCHEMA; devuelve -1 si el esquema no se admite |
| `interface NewIfcModel { schema: string; name?; description?; authors?; organizations?; authorization? }` | 335-341 | Datos del modelo nuevo |
| `CreateIfcEntity(modelID, type: number, ...args): IfcLineObject` | ≈ 941 | Construye una entidad con el constructor del esquema (`Constructors[schema][type](args)`) |
| `CreateIfcType(modelID, type, value)` | ≈ 968 | Valores tipados (IfcLabel, IfcLengthMeasure…) |
| `CreateIFCGloballyUniqueId(modelID)` | ≈ 954 | GUID nuevo (no existe `CreateIfcGuid`) |
| `WriteLine(modelID, lineObject)` / `WriteLines(modelID, lineObjects)` | ≈ 1037 / ≈ 1025 | Escribe la entidad y, de forma recursiva, las entidades anidadas; asigna expressID si falta |
| `DeleteLine(modelID, expressID)` | ≈ 1015 | Borra una línea |
| `GetLine`, `GetLines`, `GetLineIDsWithType`, `GetMaxExpressID`, `GetNextExpressID` | ≈ 814, 839, 1163, … | Lectura |
| `SaveModel(modelID): Uint8Array` / `SaveModelToCallback(modelID, cb)` | ≈ 688 / ≈ 706 | Exporta el .ifc a un buffer |
| `WriteRawLineData(modelID, data)` | (antes de GetFlatMesh) | Escritura en crudo |

- **No existen** `SaveModelToFile`, `ExportFileAsIFC`, `NewModel` ni `CreateIfcGuid` 📄.
- **Esquemas** 📄 `src/ts/ifc-schema.ts`: `export enum Schemas { IFC2X3, IFC4, IFC4X3 }`. **IFC4 sí se escribe**.
- **Validación**: `WriteLine` rechaza reusar un ID borrado o cambiar el tipo de una línea, pero **no comprueba
  tipos ni reglas WHERE** 📄 (resumen del cuerpo de `WriteLine`).
- **Únicas ayudas de escritura** 📄 `src/ts/helpers/properties.ts`: `setPropertySets(modelID, elementID, psetID)` y
  `setMaterialsProperties(modelID, elementID, materialID)`; solo crean/actualizan las relaciones hacia un pset o
  material **que ya existe**. No crean capas de material.
- Los métodos `CreateExtrusion()`, `CreateSweep()`, `CreateProfile()`, `CreateBooleanOperator()`,
  `CreateArc()`, `CreateAlignment()`, etc. 📄 **no crean entidades IFC**: devuelven objetos del núcleo C++ que
  generan **mallas** (los usa el GeometryEngine de Fragments, ver 3).

**Ejemplos publicados** 📄:
- `examples/nodejs/index.js`: abre `example.ifc` (IFC2X3), modifica unidades y pisos, agrega
  `IfcPropertySingleValue` + `IfcPropertySet` + `IfcRelDefinesByProperties`, `SaveModel` y vuelve a abrir.
  Editar un IFC existente, no crear uno.
- `examples/usage/src/modification.ts` y `exporting.ts`: `GetLine` → cambiar atributo → `WriteLine`;
  `SaveModel`.
- `tests/functional/WebIfcApi.spec.ts`: `CreateModel({schema: IFC2X3})`, crea `IfcCartesianPoint`, un
  `IfcBuildingElementProxy`, `IfcProject` por `WriteRawLineData`, caras sueltas; **ningún test crea
  IfcSite/IfcBuilding/IfcBuildingStorey/IfcWall**.
- `tests/functional/Columns.spec.ts`: **el único ejemplo con geometría extruida en IFC4**: 36 `IfcColumn` con
  `IfcCircleProfileDef` + `IfcExtrudedAreaSolid`. Pero **el IFC resultante no es válido**: no crea IfcProject,
  unidades, contexto, IfcLocalPlacement ni IfcProductDefinitionShape; pasa un `IfcAxis2Placement3D` como
  ObjectPlacement y el sólido directo como Representation. Solo prueba que el motor genera mallas.

**¿Hay un ejemplo Proyecto > Sitio > Edificio > Piso + IfcWall extruido?** No en web-ifc 📄. El único código de
That Open que arma muros IFC es `engine_clay` (abandonado, ver 4).

**Por qué importa**: para la función 001 habría que escribir a mano unas 40-60 entidades por proyecto nuevo
(unidades, contextos, placements, agregaciones) ⚠️ (estimación), y todas las reglas IFC que hoy resuelve
`ifcopenshell.api`.

---

## 3. Fragments: API de edición y exportación

**Decisión**: hay una API de edición real, pero trabaja sobre `.frag` y **no vuelve a IFC**.

- **Nombre y lugar** 📄 `packages/fragments/src/FragmentsModels/src/edit/editor.ts` (clase `Editor`, se usa como
  `fragments.editor` / `fragments.core.editor`). Métodos: `edit(modelId, actions: EditRequest[], config)`,
  `save(modelId)`, `reset`, `getModelRequests` (historial), `selectRequest` (ir a un estado),
  `createMaterial`, `createLocalTransform`, `createShell`, `createCircleExtrusion`, `createGlobalTransform`,
  `createSample`, `createItem`, `setItem`, `relate`, `unrelate`, `createElements`, `deleteElements`,
  `applyChanges`, `deleteData`, índices. Clase `Element` (`edit/element.ts`): `getMeshes`, `setMeshes`
  (transformaciones, vértices, color), `createSamples`, `deleteSamples`, `delete`.
- **Desde qué versión** 📄 releases de `engine_fragment`: v3.2.1 (2025-10-23) "release edit api"; v3.4.0
  (2026-04-09) trae 7 correcciones de edición ("correct various edit bugs", "correct editing newly created
  elements"…). 🌐 OSArch: la versión 3.2 agregó "Edit API", "History API" (deshacer/rehacer) y "Geometry Engine
  API".
- **Madurez**: un año de vida y correcciones frecuentes; el tutorial `EditApi` aclara que los cambios "no son
  instantáneos" porque el modelo se actualiza en segundo plano 📄. No dice "beta" ni "estable".
- **GeometryEngine** 📄 `packages/fragments/src/GeometryEngine/index.ts`: `getExtrusion`, `getWall`, `getSweep`,
  `getProfile`, `getBooleanOperation`, `getRevolve`, `getArc`, `getClothoid`… Necesita una instancia de
  `WEBIFC.IfcAPI`. `getWall` (`src/wall.ts`) llama a `api.CreateExtrusion()` y devuelve **buffers de malla**;
  `WallData` = start, end, elevation, height, offset, thickness, direction, plano de corte. No hay capas ni
  uniones.
- **Ejemplo "BuildingConfigurator"** 📄 (`FragmentsModels/examples/BuildingConfigurator/example.ts`): edificio
  paramétrico de varias plantas (losas, columnas, muros, escalera, puerta, ventanas) hecho con
  `GeometryEngine` + `editor.createShell` + `createElements`. **Sin clases IFC** (atributo único
  `_category: "test"`), **sin pisos** ni jerarquía espacial, **sin exportar a IFC**.
- **Exportar a IFC**: **no existe**. `Importers/` solo contiene `IfcImporter` (IFC → Fragments) 📄. El README
  dice que incluye "an IfcImporter that works both in the frontend and backend" 📖 y que habrá "more
  importers/exporters" 🌐 (wiki). `editor.save()` + `model.getBuffer()` producen un `.frag` (tutorial `EditApi`) 📄.
  `@thatopen/components` → `IfcLoader` tiene `setup`, `load`, `readIfcFile`, `cleanUp`, `dispose`; **ningún
  método de guardar IFC** 📄.

**Por qué importa**: si se usara Fragments para dibujar, habría **dos modelos** (el IFC en web-ifc y la malla
.frag para ver) que mantener sincronizados a mano, y el Principio I (IFC real siempre) solo se cumpliría por la
parte web-ifc.

---

## 4. @thatopen/components: ¿qué hay de modelado?

**Decisión**: nada de herramientas BIM de autoría en el código publicado.

- `packages/core/src` 📄: `core/` (Clipper, Components, ConfigManager, FastModelPicker, Grids,
  OrthoPerspectiveCamera, Raycasters, ShadowedScene, **SnapResolver**, Viewpoints, Views, Worlds), `fragments/`
  (BoundingBoxer, Classifier, **EdgeProjector**, FragmentsManager, Hider, IfcLoader, ItemsFinder), `drawings/`
  (**DxfManager**, **TechnicalDrawings**), `measurement/`, `openbim/` (BCFTopics, IDSSpecifications).
- `packages/front/src` 📄: `core/` (ClipStyler, Marker, PostproductionRenderer), `fragments/` (Highlighter,
  Hoverer, Mesher, Outliner), `drawings/` (**DrawingEditor**), `civil/`, `measurement/`.
- **Ni muros, ni losas, ni columnas**. Lo más cercano: `SnapResolver` (imán), `EdgeProjector` (proyección 2D de
  aristas visibles/ocultas desde los .frag), `DrawingEditor` (cotas lineales, angulares, llamadas; láminas
  `SheetBoard`/`PaperSpace`; exporta DXF) 📄.
- 📖 docs.thatopen.com/intro: lista "3D+2D modelling and editing" como "work in progress!".
- **engine_clay** 📄: "Lightweight BIM modelling engine". Tenía `SimpleWall` (con `addCorner`/uniones),
  `SimpleSlab`, `SimpleWindow`, `SimpleOpening`, `SimpleCurtainWall`, `Project`, `Site`… y escribía IFC con
  web-ifc (`Model.init()` → `CreateModel({schema: IFC4X3})`). **Último commit: 2024-10-09** ("first working
  version of exportable wall corners"); depende de `web-ifc 0.0.59` y `@thatopen/fragments 2.2.0` (hoy 0.0.78 y
  3.4.8); el paquete `@thatopen/clay` **no está en npm** (404) y el viejo `openbim-clay` quedó en 0.0.5 (2023).
  Útil solo como código de referencia MIT.
- **Hoja de ruta pública**: no se encontró ⚠️. Lo único: las librerías privadas `@thatopen-platform/*-beta`
  para miembros fundadores (contenido desconocido) y 🌐 AEC Magazine: los directivos quieren que "cualquiera
  pueda construir herramientas de autoría", sin fechas.

---

## 5. IfcOpenShell fuera de Blender (navegador y Python local)

**Decisión**: la opción madura es **IfcOpenShell en Python** (pip, igual que el 0.9.0 que BIM Simple ya usa).
En el navegador existe, pero como "technology preview".

**5.1 Pyodide (Python compilado a WebAssembly)**
- 📄 `IfcOpenShell/wasm-wheels` (README): repositorio "centralized, publicly accessible source for
  ifcopenshell wheels" para Pyodide; se instala con `micropip.install(<URL del wheel>)`; se moverán a PyPI
  cuando se acepte el PEP 783.
- 📄 Índice `ifcopenshell.github.io/wasm-wheels`: hay `ifcopenshell-0.9.0-cp313-cp313-pyodide_2025_0_wasm32.whl`
  (la misma versión que el proyecto) y 0.8.4–0.8.6. Tamaño no publicado ⚠️.
- 📖 docs.ifcopenshell.org (Installation, 0.9.1): "technology preview", "This implementation is incredibly
  heavy and will incur a long load time", pero da acceso a toda la API (incluye `ifcopenshell.api`).
- 📄 `src/pyodide/demo-app/README.md` (v0.8.0): demo que dibuja muros poligonales, pone puertas y ventanas,
  abre y guarda .ifc; "Performance of loading and running code is not optimal".
- 🌐 OSArch (ene-2025, actualizado jun-2025): la demo crea muro + puerta + ventana y el IFC abre bien en
  BIMVision; fallos con modelos grandes, en Firefox, y con aberturas no extruidas; el visor de That Open se
  colgaba con modelos de la demo; en jun-2025 se publicaron wheels con "proper exception handling".

**5.2 IfcOpenShell JS/TS (enlaces directos C++ → WebAssembly, sin Python)**
- 📖 docs.ifcopenshell.org/ifcopenshell-js.html (0.9.1): "a work in progress", "The API is subject to change".
- 📖 Installation: la sección npm dice **"TODO"**: no hay paquete publicado; se compila con `nix/build-all.py`.
- 📖 Geometry creation: solo bajo nivel (`new ifcopenshell.File('IFC4')`, `model.create(type)`,
  `entity.set(name, value)`), **sin el equivalente de `ifcopenshell.api`** (que está escrito en Python).
- No sirve hoy para producción.

**5.3 Python local con pip `ifcopenshell`**
- 📄 PyPI: `ifcopenshell 0.9.0` (2026-09-29), wheels Windows `py313-none-win_amd64` de **49,9 MB**; Python
  3.10 a 3.15; dependencias: shapely, numpy, isodate, python-dateutil, lark, pyparsing, typing-extensions.
- 📄 Instalado en esta PC: carpeta `ifcopenshell/` = **151 MB** (todos los esquemas, OpenCASCADE `TK*.dll`,
  núcleos CGAL y Manifold, serializadores glTF/SVG/OBJ…).
- Licencias: ver sección 8.

---

## 6. Ejemplos reales de MODELADO IFC en la web

| Proyecto | Base | Qué hace | Qué tan lejos llegó |
|---|---|---|---|
| Demo IfcOpenShell + Pyodide (wasm.ifcopenshell.org) | IfcOpenShell (Python en WASM) | Muros poligonales, puertas, ventanas, abrir/guardar IFC | Preview técnica; inestable con modelos grandes 📄🌐 |
| `engine_clay` (That Open) | web-ifc | Muros con esquinas, losas, ventanas; exporta IFC4X3 con `SaveModel` (tecla P en el ejemplo) | Abandonado 2024-10, sin piso (`IfcBuildingStorey`) en el ejemplo 📄 |
| BuildingConfigurator (That Open) | Fragments | Edificio paramétrico en malla | No es IFC 📄 |
| ifc-lite (LTplus-AG) | Rust → WASM, MPL-2.0 | Visor, consultas, edición de propiedades con deshacer, `@ifc-lite/create` "Create IFC files from scratch" | 🌐 Muy activo (v20.x, oct-2026); qué elementos crea y si hay modelador interactivo: ⚠️ no verificado |

No se encontró ningún producto público que haga autoría IFC completa (muros con capas y uniones, pisos, planos)
sobre That Open ⚠️ (búsqueda limitada a fuentes oficiales y OSArch).

---

## 7. Conclusión para BIM Simple

Leyenda: **Listo** = existe y se usa tal cual · **Parcial** = existe una base, falta trabajo · **Programar** =
hay que escribirlo nosotros.

| Necesidad | That Open (web-ifc + Fragments + components) | Three.js + IfcOpenShell (Python auxiliar) | Blender + Bonsai (plan actual) |
|---|---|---|---|
| **(a) Función 001** | | | |
| Proyecto IFC4 nuevo en metros con Proyecto > Sitio > Edificio > Piso | Programar (40-60 entidades a mano ⚠️) | Listo (`ifcopenshell.api` project/root/aggregate/unit/context) | Listo (`bim.create_project`) |
| Pisos con cota y altura (`Elevation`, `Qto…GrossHeight`) | Programar | Listo (`pset.add_qto`/`edit_qto`, `attribute.edit_attributes`) | Listo |
| Mover piso **con** sus elementos | Programar (placement relativo) | Listo (`edit_object_placement(..., should_transform_children=True)` 📄 l.33/38) | Listo + sincronizar objetos Blender |
| Abrir / guardar IFC | Listo (`OpenModel`/`SaveModel`) | Listo (`ifcopenshell.open` / `file.write`) | Listo |
| IFC válido (SC-003) | Programar validación (web-ifc no valida) | Listo (`ifcopenshell.validate.validate`, `validate.py:419`; `json_logger` l.91 📄) | Listo |
| Deshacer / rehacer (FR-018) | Parcial (History API solo del .frag; IFC: programar) | Listo en el modelo (`file.undo/redo`, `file.py:548-580` 📄) | Listo |
| Vista planta + 3D, navegador de pisos | Listo (visor, cámaras ortho/persp., clipper) + UI propia | Programar visor Three.js (o usar That Open solo para ver) + UI propia | Listo (Blender) + ocultar Blender |
| Mostrar el IFC | Listo (IfcImporter → .frag) | Listo (`ifcopenshell.geom.iterator` → mallas o glTF) + puente | Listo |
| **(b) Muros / losas / columnas** | | | |
| Muro con espesor por capas de material | Programar todo (IfcMaterialLayerSet, Usage, extrusión) | Listo (`material.*` + `add_wall_representation` + `regenerate_wall_representation`) | Listo (DumbWallGenerator) |
| Uniones en esquina (ingletes, en T) | Programar todo (Clay lo intentó y quedó a medias) | Listo en IFC (`connect_wall`, `connect_path`, `regenerate_wall_representation`) | Listo (DumbWallJoiner) |
| Losa por contorno | Programar (GeometryEngine da malla, no IFC) | Listo (`add_slab_representation(..., polyline=...)`) | Listo |
| Columna rectangular/circular | Programar (patrón de `Columns.spec.ts`, pero válido) | Listo (`add_profile_representation` + perfiles) | Listo |
| Dibujar con el ratón (polilínea, imán, longitud tecleada) | Parcial (`SnapResolver`, raycasters) | Programar en Three.js | Listo (PolylineOperator, GPL) |
| **(c) Planos 2D** | | | |
| Planta con corte, proyección, achurados | Parcial (EdgeProjector: aristas, sin corte; tutorial carga proyección precalculada) | Parcial/Listo (`ifcopenshell.draw` SVG con `auto_floorplan` 📄) | Listo (módulo drawing de Bonsai, GPL) |
| Cotas, textos, láminas | Listo-Parcial (DrawingEditor, SheetBoard, DXF) | Programar (o usar DrawingEditor de That Open) | Listo (Bonsai) |
| Exportar | DXF | SVG (luego PDF) | SVG/PDF |

**Esfuerzo cualitativo comparado con Blender + Bonsai** ⚠️ (estimación):
- **That Open puro**: el mayor. Hay que escribir desde cero un "ifcopenshell.api" en TypeScript (jerarquía,
  materiales, uniones, regeneración de muros, validación, deshacer del IFC) y además mantener sincronizado el
  modelo de visualización. Es lo que That Open intentó con Clay y dejó en 2024. Meses o años para llegar a muros
  con capas y uniones correctas.
- **Three.js + IfcOpenShell (Python auxiliar)**: medio. La lógica IFC ya existe (LGPL). Hay que construir el visor
  (o usar That Open solo para ver), las herramientas de dibujo (polilínea, imán, Info Box), la comunicación
  app ↔ Python y el empaquetado. Es más trabajo que Blender + Bonsai al principio (Blender ya da visor, cámaras,
  selección, imán y deshacer), pero da **control total de la interfaz** y no hay que ocultar Blender.
- **Blender + Bonsai**: el menor para llegar rápido a muros/losas/planos, a costa de pelear con la interfaz de
  Blender y quedar en GPL.

---

## 8. Ampliación: Three.js para la gráfica + IfcOpenShell como motor IFC (sin Blender)

### 8(a) Lógica de modelado LGPL dentro de IfcOpenShell 0.9.0 instalado (fuera de Bonsai)

Ruta: `%APPDATA%\Blender Foundation\Blender\5.2\extensions\.local\lib\python3.13\site-packages\ifcopenshell\`.
Todas las cabeceras citadas dicen en la línea 7: `# it under the terms of the GNU Lesser General Public License
as published by` 📄 (LGPL v3 o posterior). El `METADATA` del paquete declara "GNU Lesser General Public License
v3 or later (LGPLv3+)" 📄. **La carpeta instalada no trae archivo de licencia** (no hay COPYING/LICENSE) 📄:
habría que agregar los textos al distribuir.

| Archivo:línea | Función / clase | Qué resuelve |
|---|---|---|
| `api/geometry/add_wall_representation.py:27` | `add_wall_representation(file, context, length, height, direction_sense, offset, thickness, x_angle, clippings, booleans)` | Cuerpo extruido de un muro recto |
| `api/geometry/create_2pt_wall.py:27` | `create_2pt_wall(file, element, context, p1, p2, elevation, height, thickness, is_si)` | Muro entre dos puntos: llama a `add_wall_representation` (l.69) y `edit_object_placement` (l.87) |
| `api/geometry/connect_wall.py:30` | `connect_wall(file, wall1, wall2, is_atpath=False)` | Calcula si la unión es ATSTART/ATEND/ATPATH con los ejes y llama a `connect_path` (l.58) |
| `api/geometry/connect_path.py:27` | `connect_path(file, relating_element, related_element, relating_connection, related_connection, …)` | Crea `IfcRelConnectsPathElements` (l.72-84) y quita conexiones incompatibles |
| `api/geometry/regenerate_wall_representation.py:41` | `regenerate_wall_representation(file, wall, length, height, angle)` + clase `Regenerator` (l.105) | Regenera el cuerpo según las uniones: "notches, butts, mitres" (l.53-55), capas y prioridades del `IfcMaterialLayerSet`; devuelve `None` si el muro no tiene layer set (l.97-100); crea el contexto Plan/Axis si falta (l.113-118) |
| `api/geometry/add_slab_representation.py:27` | `add_slab_representation(file, context, depth, direction_sense, offset, x_angle, clippings, polyline)` | Losa por contorno (`polyline`) |
| `api/geometry/add_profile_representation.py:54` | `add_profile_representation(file, context, profile, depth, cardinal_point, clippings, placement_zx_axes)` | Columnas/vigas por perfil (rectangular, circular…) |
| `api/geometry/edit_object_placement.py:33` | `edit_object_placement(file, product, matrix, is_si, should_transform_children)` (l.38) | Mover pisos con hijos (receta R12 del proyecto) |
| `util/shape_builder.py` (cabecera l.1-17) | `ShapeBuilder` y utilidades 2D/3D (p. ej. `intersect_x_axis_2d`, usada en `connect_wall.py:47`) | Geometría IFC de bajo nivel |
| `api/root/create_entity.py`, `api/spatial/assign_container.py`, `api/aggregate/assign_object.py`, `api/material/add_material_set.py`, `api/material/add_layer.py`, `api/project/create_file.py`, `validate.py` | (todas con cabecera LGPL en l.7) | Jerarquía, contención en piso, capas de material, archivo nuevo, validación |
| `file.py:548-580` | `set_history_size`, `begin_transaction`, `end_transaction`, `discard_transaction`, `undo`, `redo` | Deshacer/rehacer del modelo IFC |
| `geom/main.py:312, 316, 484` | `settings`, `iterator`, `create_shape(settings, inst, repr=None, geometry_library="opencascade", …)` (l.488) | Teselar a triángulos (vértices, caras, materiales) para mandar a Three.js |
| `geom/main.py:775-790, 804` | `serializers` con `gltf`/`glb`, `obj`, `svg`, `dae`, `usd`… | Exportar mallas a glTF (Three.js lo carga directo con `GLTFLoader`) |
| `draw.py:49, 101` | `draw_settings` (`auto_floorplan=True`, `scale=1/100`, …) y `main(settings, files, iterators, …)` | Plantas/cortes en SVG ("2D drawing generation and serialisation", l.19) |

**Lo GPL de Bonsai** (cabecera l.7: `# it under the terms of the GNU General Public License as published by`
📄, en `bonsai/bim/module/model/wall.py`, `slab.py`, `profile.py`, `polyline.py`, `opening.py`):

| Clase (archivo:línea) | Qué agrega sobre lo LGPL |
|---|---|
| `DumbWallGenerator` (`wall.py:1236`) | Decide tipo, capa, insertar desde cursor/polilínea/losa; crea el objeto Blender. La geometría IFC la hace `add_wall_representation` (`wall.py:1412`) |
| `DumbWallJoiner` (`wall.py:1521`) | `unjoin`, `split`, `flip`, `merge`, `extend`, `set_length`, `connect`, `clip`; todo sobre `bpy.types.Object`. La unión IFC la hace `connect_wall` (`wall.py:1847`) y la regeneración `regenerate_wall_representation` (`bonsai/tool/model.py:3153`) |
| `DumbWallAligner` (1143), `DumbWallPlaner` (1441), `DrawPolylineWall` (1019) | Alinear, recalcular, dibujar con polilínea |
| `DumbSlabGenerator` (`slab.py:47`), `DumbSlabPlaner` (198), `DrawPolylineSlab` (859) | Losa: llama a `add_slab_representation` (`slab.py:158`) |
| `DumbProfileGenerator` (`profile.py:51`), `DumbProfileJoiner` (314), `DrawPolylineProfile` (1128) | Columnas/vigas: llama a `add_profile_representation` (`profile.py:159`) |
| `PolylineOperator` (`polyline.py:32`) | Entrada con ratón, imán, longitud/ángulo tecleados, vista previa |

**Conclusión 8(a)**: lo que **no** se puede copiar a un producto cerrado es la capa de interacción y orquestación
(dibujo con polilínea, imán, gizmos, decidir cuándo unir/partir/extender, sincronizar con Blender). Esa capa
habría que reescribirla igual para Three.js. El "cálculo IFC" que hay debajo (representaciones, uniones,
regeneración con capas, placements, deshacer, teselado, plantas SVG) es LGPL y se puede **usar como librería**.
⚠️ Leer el código GPL para "inspirarse" y reescribirlo parecido es una zona gris de derechos de autor; lo
prudente es no copiar estructura ni código de Bonsai y apoyarse solo en la API LGPL y en la norma IFC.

### 8(b) Cómo correría IfcOpenShell en un programa propio

| | Python local como proceso auxiliar ("sidecar") | IfcOpenShell en WebAssembly (Pyodide) dentro de la app | IfcOpenShell JS/TS nativo |
|---|---|---|---|
| Estado | Maduro: es el mismo `ifcopenshell 0.9.0` de PyPI (2026-09-29) que el proyecto ya prueba 📄 | "technology preview", "incredibly heavy… long load time" 📖 | "work in progress", npm "TODO" 📖 |
| API | Completa (`ifcopenshell.api`, `geom`, `draw`, `validate`) | Completa (misma API Python) 📖 | Solo bajo nivel (`create`/`set`) 📖 |
| Fuente oficial | PyPI + docs.python.org (embeddable) | `IfcOpenShell/wasm-wheels` + docs.ifcopenshell.org | docs.ifcopenshell.org/ifcopenshell-js |
| Tamaño | Wheel 49,9 MB (zip); instalado 151 MB 📄; + Python embebible y numpy/shapely ⚠️ (total estimado 200-250 MB) | Wheel 0.9.0 sin tamaño publicado ⚠️ + runtime de Pyodide ⚠️ | — |
| Riesgos | Dos procesos, comunicación entre ellos, antivirus/firmas en Windows ⚠️ | Carga lenta, memoria, fallos con modelos grandes (🌐 OSArch) | No publicado |

**Cómo se distribuye el sidecar en Windows**:
- 📖 docs.python.org ("The embeddable package"): "It is intended for acting as part of another application,
  rather than being directly accessed by end-users". No incluye pip ni tkinter; "Third-party packages should be
  installed by the application installer alongside the embedded distribution".
- 📖 Electron Packager, opción `extraResource`: copia archivos a la carpeta `resources` de la app; en tiempo de
  ejecución se llega con `process.resourcesPath`. La app Electron lanza `python.exe` de esa carpeta y conversa
  por stdin/stdout (JSON) o por un puerto local ⚠️ (patrón habitual, no hay un "modo sidecar" oficial en
  Electron).
- 📖 Tauri v2 tiene sidecars oficiales (`bundle.externalBin`) y menciona "Python CLI applications or API servers
  bundled using `pyinstaller`" como caso de uso. Alternativa más liviana que Electron ⚠️.
- Todo queda en una carpeta propia del programa (igual que la idea actual de "copia propia de Blender"):
  instalar = copiar; desinstalar = borrar carpeta ⚠️.

**Recomendación 8(b)**: para un programa de escritorio en Windows, **sidecar Python**. Pyodide solo si algún día
hace falta correr 100 % dentro de un navegador.

### 8(c) LGPL-3.0 y un programa cerrado (no es asesoría legal)

> Esto **no es asesoría legal**. Resume el texto de la licencia; antes de vender, consultar a un abogado.

Lo que dice la LGPL v3 📄 (`COPYING.LESSER` del repo IfcOpenShell, tag v0.8.0):
- Un programa que **usa** la librería por su interfaz es una "Application"; junto con la librería forman un
  "Combined Work" que **se puede distribuir con licencia propia (cerrada)** si se cumple la sección 4.
- Sección 4, obligaciones típicas:
  1. Aviso visible de que se usa IfcOpenShell y de que está bajo LGPL.
  2. Incluir copias de la GPL v3 y de la LGPL v3.
  3. Si el programa muestra avisos de copyright (p. ej. "Acerca de"), incluir el de IfcOpenShell.
  4. Permitir que el usuario **reemplace la librería** por una versión modificada: o se usa un mecanismo de
     librería compartida (opción 1) o se entrega lo necesario para volver a combinarla (opción 0). Con Python:
     distribuir `ifcopenshell` como **carpeta separada y sin modificar**, no fundida en un ejecutable cerrado.
  5. "Installation Information" solo cuando la GPL §6 lo exigiría (productos de consumo con bloqueo).
  - Los términos propios no pueden prohibir modificar la parte de la librería ni la ingeniería inversa para
    depurar esas modificaciones.
- Si se **modifica** el código de IfcOpenShell, esas modificaciones deben publicarse bajo LGPL.
- **Bonsai es GPL v3+**: no se puede copiar ni importar sus módulos en un producto cerrado ⚠️ (importarlo
  formaría una obra combinada GPL).

Dependencias que viajan con IfcOpenShell (revisar una por una):
- OpenCASCADE (`TK*.dll`): "LGPL 2.1 with an additional exception" 📖 (occt3d.com).
- CGAL (`ifcopenshell_geometry_kernel_cgal*.dll`): 📖 cgal.org: el núcleo es LGPL, pero "most higher-level
  geometric algorithms" son **GPL** (con licencia comercial de GeometryFactory). ⚠️ No se verificó qué paquetes
  CGAL usa IfcOpenShell. Mitigación posible: usar el núcleo OpenCASCADE (`create_shape` usa
  `geometry_library="opencascade"` por defecto, `geom/main.py:488` 📄) y no distribuir las DLL de CGAL; a
  confirmar con un abogado.
- Manifold, numpy, shapely: licencias ⚠️ no verificadas en esta sesión.
- web-ifc (si se usa para ver): MPL-2.0, copyleft por archivo 📄.

**Choque con la constitución actual**: hoy dice "Licencia GPL-3.0-or-later, igual que Blender y Bonsai" y el
Principio III se basa en Blender. Pasar a Three.js + IfcOpenShell y/o a producto cerrado requiere **enmienda**
aprobada por el usuario.

---

## Prueba práctica propuesta (para que el usuario la autorice)

Dos pruebas cortas que crean **el mismo** archivo y se validan igual, para comparar esfuerzo real.

**Común a ambas**: crear proyecto IFC4 en metros → Sitio → Edificio → 3 pisos (Planta Baja 0,00 / Piso 1 3,00 /
Piso 2 6,00, con `GrossHeight` 3,00) → un muro de 5,00 × 0,20 × 3,00 m con una capa de material, contenido en
la Planta Baja → guardar `prueba.ifc`.

**Prueba A: web-ifc (That Open)** — requiere permiso para instalar un paquete npm.
- Carpeta temporal: `C:\Users\Usuario\AppData\Local\Temp\claude\C--Users-Usuario-Documents-SOFTWARE-BIM\8ee48afe-f54b-49d7-bef6-78f94e89b071\scratchpad\research\thatopen\prueba-webifc\`
- Instalar: `npm install web-ifc@0.0.78` (un solo paquete, sin dependencias, 24,8 MB desempaquetado). Node.js
  24.19.0 ya está instalado en `C:\Program Files\nodejs\` (comprobado sin ejecutarlo).
- Script `crear.mjs`: `Init()` → `CreateModel({schema: "IFC4"})` → `CreateIfcEntity` para unidades
  (`IfcSIUnit`, `IfcUnitAssignment`), contexto + subcontexto Body, `IfcProject`, `IfcSite`, `IfcBuilding`, 3
  `IfcBuildingStorey` con `IfcLocalPlacement` encadenados, `IfcRelAggregates`, el muro (`IfcRectangleProfileDef`
  → `IfcExtrudedAreaSolid` → `IfcShapeRepresentation` → `IfcProductDefinitionShape`), `IfcMaterial`,
  `IfcMaterialLayer`, `IfcMaterialLayerSet`, `IfcMaterialLayerSetUsage`, `IfcRelAssociatesMaterial`,
  `IfcRelContainedInSpatialStructure`, cantidades de piso → `WriteLine` → `SaveModel` → escribir archivo →
  reabrir con `OpenModel` y contar entidades.
- Medir: líneas de código necesarias, cantidad de entidades escritas a mano.

**Prueba B: IfcOpenShell (línea base)** — no instala nada; usa el IfcOpenShell 0.9.0 ya instalado, corriendo
`blender.exe --background --python` (sin ventanas) o el Python de Blender.
- Mismo resultado con `ifcopenshell.api` (`project.create_file`, `root.create_entity`, `aggregate.assign_object`,
  `spatial.assign_container`, `material.add_material_set`/`add_layer`, `geometry.create_2pt_wall`,
  `pset.add_qto`), y además una segunda pared unida con `connect_wall` + `regenerate_wall_representation` para
  ver la esquina.

**Validación (igual para A y B)**:
1. `ifcopenshell.validate.validate(ruta, json_logger(), express_rules=True)` sin errores de nivel `error`
   (receta R16 del proyecto).
2. Reabrir con IfcOpenShell y comprobar: 1 proyecto, 1 sitio, 1 edificio, 3 pisos con `Elevation` 0/3/6, el muro
   contenido en Planta Baja, layer set de 0,20 m.
3. Opcional, con permiso para abrir ventana: abrir `prueba.ifc` en Bonsai.

Tiempo estimado: A, 1-2 h (escribir entidades a mano); B, 15-30 min ⚠️.

---

## Fuentes principales

- npm: https://registry.npmjs.org/web-ifc , /@thatopen/fragments , /@thatopen/components ,
  /@thatopen/components-front , /@thatopen/ui
- https://github.com/ThatOpen/engine_web-ifc (src/ts/web-ifc-api.ts, src/ts/ifc-schema.ts,
  src/ts/helpers/properties.ts, examples/, tests/functional/WebIfcApi.spec.ts, Columns.spec.ts)
- https://github.com/ThatOpen/engine_fragment (FragmentsModels/src/edit/editor.ts, element.ts,
  elements-helper.ts, examples/EditApi, examples/BuildingConfigurator, GeometryEngine/, Importers/, releases)
- https://github.com/ThatOpen/engine_components (packages/core/src, packages/front/src, IfcLoader,
  TechnicalDrawings, DrawingEditor, EdgeProjector)
- https://github.com/ThatOpen/engine_clay , https://github.com/ThatOpen/platform_services
- https://docs.thatopen.com/intro
- https://osarch.org/2025/10/23/that-open-engine-3-2-open-modeling/ ,
  https://osarch.org/2026/04/09/that-open-engine-3-4-native-2d-drawings/ ,
  https://osarch.org/2026/06/06/that-open-platform-founding-member-launch/
- 🌐 https://aecmag.com/features/that-open-company-raises-the-stakes/
- https://github.com/IfcOpenShell/wasm-wheels , https://ifcopenshell.github.io/wasm-wheels/
- https://docs.ifcopenshell.org/ifcopenshell-python/installation.html ,
  https://docs.ifcopenshell.org/ifcopenshell-js.html (+ installation, geometry_creation)
- https://github.com/IfcOpenShell/IfcOpenShell (src/pyodide/demo-app/README.md, COPYING.LESSER, tag v0.8.0)
- 🌐 https://community.osarch.org/discussion/comment/23503
- https://pypi.org/pypi/ifcopenshell/0.9.0/json
- https://docs.python.org/3/using/windows.html , https://electron.github.io/packager/main/interfaces/Options.html ,
  https://v2.tauri.app/develop/sidecar/
- https://www.cgal.org/license.html , https://occt3d.com/open-cascade-technology/index.html
- 🌐 https://github.com/LTplus-AG/ifc-lite , https://docs.rs/crate/ifc-lite-core/5.0.0
- Local (solo lectura): IfcOpenShell 0.9.0 y Bonsai 0.9.0 en
  `%APPDATA%\Blender Foundation\Blender\5.2\extensions\.local\lib\python3.13\site-packages\`
