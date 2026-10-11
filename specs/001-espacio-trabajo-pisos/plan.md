# Plan de implementación: Programa BIM Simple y navegador de pisos

**Carpeta**: `specs/001-espacio-trabajo-pisos` (sin rama propia; se trabaja en `main`) | **Fecha**: 2026-10-11 | **Especificación**: [spec.md](spec.md)

**Entrada**: especificación de la función en `specs/001-espacio-trabajo-pisos/spec.md`; constitución v2.0.0.

## Resumen

BIM Simple pasa a ser un programa propio para Windows. Funciona así:
- Lleva una **copia sin modificar de Blender 5.2** en modo portable, con su configuración dentro de la
  carpeta del programa.
- Le agrega **Bonsai 0.9.0 py313**, la **extensión BIM Simple** y una **plantilla de aplicación** que lo hace
  arrancar directamente en la pantalla de BIM Simple, en español y sin bienvenida.
- Se instala en `%LOCALAPPDATA%\Programs\BIM Simple\` y se abre con un acceso directo propio.

Al arrancar, la extensión arma en la ventana real la pantalla partida: planta del piso activo a la izquierda
y 3D a la derecha. Oculta la interfaz de Blender y Bonsai y deja solo:
- un menú "Archivo" propio;
- el panel "BIM Simple" con el navegador de pisos.

Toda la lógica de proyecto y pisos vive en `core.py` y usa recetas verificadas de Bonsai/IfcOpenShell.
Algunas corrigen al MVP: mover un piso mueve también sus elementos, y borrar un piso no deja elementos
huérfanos. Las llamadas internas de Bonsai están concentradas en `bonsai_api.py`. La prueba automática usa
las mismas funciones con el Blender del programa en segundo plano. Lo que solo se ve con ventana va a la
prueba manual.

La justificación de cada decisión está en [research.md](research.md), con la evidencia en
[investigacion/](investigacion/).

## Contexto técnico

**Lenguaje/versión**:
- Python 3.13, el que trae Blender 5.2.
- PowerShell 5.1, para el script de armado.

**Dependencias principales**:
- Blender 5.2.0 LTS (copia de `C:\Program Files\Blender Foundation\Blender 5.2`, sin `blender.pdb`).
- Bonsai 0.9.0 `py313` para windows-x64, que incluye IfcOpenShell 0.9.0.
- Sin dependencias pip nuevas. Solo la biblioteca estándar de Python, para el icono.

**Almacenamiento**:
- Archivos `.ifc` (IFC4, metros) elegidos por el usuario.
- Configuración del programa en `<programa>\blender\portable\`.
- `.blend` de sesión oculto en `portable\temp\`.

**Pruebas**:
- Automáticas: `"<programa>\blender\blender.exe" --background --app-template bim_simple --python tests\test_pisos.py`.
  Sale con código distinto de 0 si algo falla y valida el IFC con `ifcopenshell.validate`.
- Manuales en español: [quickstart.md](quickstart.md), parte B.

**Plataforma**: Windows 11 x64, sin permisos de administrador.

**Tipo de proyecto**: programa de escritorio construido sobre Blender, con su extensión, su plantilla y
su script de armado.

**Objetivos de rendimiento**:
- Arranque en menos de 20 s (SC-007). En segundo plano se midieron 5,8–7,1 s.
- Activar un piso en menos de 1 s con 10 pisos (SC-004).

**Restricciones**:
- Ruta del programa corta (base de 90 caracteres o menos) y escribible.
- Aproximadamente 1,5 GB en disco.
- Sin conexión a Internet una vez armado.
- El Blender del usuario no se toca (SC-005).

**Escala**: un usuario y un edificio por proyecto, entre 1 y ~30 pisos. Es la primera de tres funciones.

## Control de la constitución

*Compuerta: se cumple antes de la fase 0 y se vuelve a revisar después del diseño (fase 1).*

| Principio / regla | Cómo lo cumple este plan | Estado |
|---|---|---|
| I. IFC real siempre | Cada piso es un `IfcBuildingStorey` creado por Bonsai (`bim.add_part_to_object`). Borrar un piso borra su contenido: no quedan huérfanos, a diferencia de `delete_container` solo. Mover un piso mueve sus elementos en el IFC y en Blender. La prueba valida IFC4 con reglas EXPRESS. | ✅ |
| II. Pensado para quien viene de ArchiCAD | Interfaz y diálogos en español (idioma `es` del programa y textos propios). Altura de piso como en ArchiCAD (FR-016). Las diferencias que Blender impone están escritas (research.md §E, D1–D7). | ✅ con diferencias documentadas |
| III. Programa propio sobre Blender | Copia portable con configuración propia, plantilla y acceso directo. No se modifica ningún archivo de Blender ni de Bonsai. Los reemplazos de dibujo, paneles y atajos son en tiempo de ejecución, dentro de la copia del programa. El Blender del usuario no se lee ni se escribe: se comprueba con hashes antes y después (SC-005). Única excepción: la caché compartida (D7), que no es preferencia, extensión ni archivo de inicio. | ✅ |
| IV. API verificada | Cada llamada está citada con archivo:línea en research.md e `investigacion/`. Las 13 llamadas internas de Bonsai solo aparecen en `bim_simple/bonsai_api.py`. | ✅ |
| V. Lógica separada y comprobada | `core.py` no importa nada de interfaz, y la prueba usa esas mismas funciones. Lo visual (pantalla, colecciones locales, X, Ctrl+Z real, barra de tareas) va a la prueba manual. | ✅ |
| Restricciones técnicas | Blender 5.2 + Bonsai 0.9.0 py313. IFC4 en metros. Licencias incluidas. Sin pip. Sin archivos ni abstracciones extra (ver estructura). | ✅ |
| Flujo de trabajo: permisos | La implementación se detiene a pedir permiso antes de: descargar Bonsai, instalar el programa en `%LOCALAPPDATA%`, abrir ventanas de Blender, crear accesos directos y borrar archivos. Lista en "Pasos que requieren permiso". | ✅ |

**Resultado**: pasa. No hay violaciones que justificar. Revisión después del diseño: sigue pasando; el
diseño de [data-model.md](data-model.md) y [contracts/](contracts/) no agrega dependencias ni toca nada fuera
de la carpeta del programa.

## Estructura del proyecto

### Documentación (esta función)

```text
specs/001-espacio-trabajo-pisos/
├── spec.md              especificación
├── plan.md              este archivo
├── research.md          decisiones de la fase 0
├── investigacion/       evidencia detallada (informes y scripts verificados)
├── data-model.md        fase 1: entidades, reglas y estados
├── quickstart.md        fase 1: cómo armar, probar y la prueba manual
├── contracts/           fase 1: programa, interfaz y funciones de core.py
├── checklists/requirements.md
└── tasks.md             fase 2 (/speckit-tasks; no lo crea este comando)
```

### Código fuente (raíz del repositorio)

```text
bim_simple/                    extensión de Blender (blender_manifest.toml, id "bim_simple")
├── blender_manifest.toml      Blender ≥ 5.2.0, GPL-3.0-or-later
├── __init__.py                registrar / desregistrar módulos, timers y manejadores
├── bonsai_api.py              ÚNICO módulo que importa bonsai.* o llama bpy.ops.bim.* (Principio IV)
├── core.py                    lógica sin interfaz: proyecto (nuevo/abrir/guardar/cerrar) y pisos
├── props.py                   propiedades de escena: lista espejo de pisos, índice activo, avisos
├── operators.py               operadores bimsimple.* (los que cambian el IFC heredan de tool.Ifc.Operator vía bonsai_api)
├── ui.py                      menú Archivo, lista y panel "BIM Simple"
├── screen.py                  ensure_layout, barra superior, ocultar paneles, planta, colecciones locales
├── keymaps.py                 política de atajos y atajos propios
└── session.py                 .blend de sesión, puente save_pre (X2), recuperación

app_template/bim_simple/
└── __init__.py                plantilla de aplicación (register/unregister vacíos)

assets/
├── bim_simple.ico             icono del acceso directo (generado por tools/make_icon.py)
└── LEEME.txt                  qué es, cómo abrir y cómo desinstalar (se copia al programa)

tools/
├── armar_programa.ps1         arma o actualiza el programa en %LOCALAPPDATA%\Programs\BIM Simple
├── configurar_programa.py     corre dentro del Blender del programa: preferencias, userpref y startup.blend de la plantilla
└── make_icon.py               genera assets/bim_simple.ico (biblioteca estándar)

tests/
└── test_pisos.py              prueba automática (blender --background), sale con 1 si falla
```

Fuera de git (en `.gitignore`): `dist/` (zip de la extensión que arma el script) y `__pycache__/`.

**Decisión de estructura**:
- Una sola extensión con módulos separados por responsabilidad: datos de Bonsai (`bonsai_api`), lógica
  (`core`), estado de interfaz (`props`), acciones (`operators`), dibujo (`ui`), pantalla (`screen`), teclado
  (`keymaps`) y cierre (`session`). Es lo mínimo para cumplir los Principios IV y V sin mezclar la lógica con
  la interfaz.
- La plantilla y las herramientas de armado van aparte porque se copian a la carpeta del programa, no a la
  extensión.

**Archivos que quedan del MVP**:
- `PLAN.md` se conserva como referencia de la API de Bonsai.
- `PRUEBA_MANUAL.md` y `README.md` describen el MVP; se **reescriben** al final de esta función para el
  programa nuevo. No se borran.

## Diseño técnico por pieza

### Armado del programa (`tools/armar_programa.ps1`)

Parámetros:
- `-Destino`: por defecto `%LOCALAPPDATA%\Programs\BIM Simple`;
- `-BonsaiZip`: ruta del zip py313;
- `-SoloExtension`: reinstala solo la extensión y la plantilla;
- `-CrearAccesos`: crea los accesos directos.

Cada paso imprime su resultado y el script se detiene ante el primer error.

1. **Requisitos**:
   - `blender.exe --version` del Blender instalado = 5.2.0;
   - el SHA-256 del zip de Bonsai coincide con el publicado;
   - el largo de la ruta de destino es de 90 caracteres o menos.
2. **SC-005**: hash SHA-256 de `%APPDATA%\Blender Foundation\Blender\5.2\config\*` y de
   `extensions\user_default` del usuario, antes de empezar.
3. **Copia de Blender**:
   - `robocopy "<BL>" "<destino>\blender" /E /XF blender.pdb`;
   - crear `blender\portable\` y `blender\portable\temp\`.
4. **Bonsai**: `blender\blender.exe -c extension install-file -r user_default -e <zip>`.
5. **Extensión BIM Simple**:
   - `blender\blender.exe -c extension build --source-dir bim_simple --output-dir dist`;
   - `blender\blender.exe -c extension install-file -r user_default -e dist\bim_simple-<v>.zip`.
6. **Plantilla**: copiar `app_template\bim_simple` a `portable\scripts\startup\bl_app_templates_user\`.
7. **Configuración**: ejecutar `blender\blender.exe --background --python tools\configurar_programa.py -- principal` y
   después `… --app-template bim_simple --python tools\configurar_programa.py -- plantilla`. Preferencias
   según research R5; genera el `startup.blend` de datos de la plantilla.
8. **Archivos propios**: copiar `assets\bim_simple.ico` y `assets\LEEME.txt`; crear `licencias\` con la
   GPL-3.0 de `blender\license\` y los avisos de Blender, Bonsai e IfcOpenShell.
9. **Prueba automática** (`tests\test_pisos.py`) con el Blender del programa; mostrar su salida.
10. **SC-005**: volver a calcular los hashes del paso 2 y mostrar "sin cambios" o la lista de diferencias.
11. **Solo con `-CrearAccesos`**: `BIM Simple.lnk` en el Escritorio y en el menú Inicio (research R6).

`-SoloExtension` hace solo los pasos 5, 6, 7 (parte plantilla), 9 y 10.

### Extensión

- **`bonsai_api.py`**: expone las 13 llamadas internas listadas en `investigacion/ifc.md` §10 y los
  operadores `bim.create_project`, `bim.add_part_to_object`, `bim.load_project` y `bim.save_project`, más la
  base `IfcOperator = tool.Ifc.Operator`. Ningún otro módulo importa `bonsai`.
- **`core.py`**: contrato en [contracts/core_api.md](contracts/core_api.md). Cada función recibe valores en
  metros y convierte con `unit_scale` del archivo. Si una regla no se cumple (FR-016, último piso, nombre
  vacío), lanza `BIMSimpleError` con el mensaje en español.
- **`props.py`**:
  - `BIMSimpleStorey` (`ifc_id`, `name`, `elevation`, `height`).
  - `BIMSimpleProperties` en `Scene`: `storeys`, `active_storey_index` con `update` que llama a
    `core.activate_storey` y a `screen.show_storey_in_plan`, y `notice` para los avisos.
  - `refresh_storeys()` vuelve a llenar la lista desde el IFC. Se llama después de cada operador, en
    `load_post` y en `undo_post`/`redo_post`.
- **`operators.py`**:
  - Proyecto: `bimsimple.new_project`, `open_ifc`, `save_ifc`, `save_ifc_as`, `quit`.
  - Pisos: `add_storey_above`, `add_storey_below`, `edit_storey` (diálogo con nombre, cota y altura),
    `delete_storey` (confirmación con la cantidad de elementos).

  Los que cambian el IFC heredan de `bonsai_api.IfcOperator`: un paso de deshacer por acción, que marca
  `is_dirty`. Contrato en [contracts/ui.md](contracts/ui.md).
- **`ui.py`**:
  - menú `BIMSIMPLE_MT_file` ("Archivo");
  - `BIMSIMPLE_UL_storeys`, con nombre, cota y altura como **texto**, para que el doble clic no renombre;
  - panel `BIMSIMPLE_PT_navigator` en la barra lateral de la vista derecha, `bl_category="BIM Simple"`.
- **`screen.py`**:
  - `ensure_layout(window)` (research R7–R8, R10);
  - reemplazo y restauración de `TOPBAR_HT_upper_bar.draw`;
  - ocultar paneles de Blender (re-registro con `poll` falso; paneles C por `bl_idname`);
  - `show_storey_in_plan(storey)`, que calcula el índice de colección y llama a `object.hide_collection` en la planta.
- **`keymaps.py`**: `apply_keymap_policy()` y los atajos propios (research R9). La lista de desactivación
  vive en una tabla de datos, por keymap, para revisarla fácil.
- **`session.py`**: `.blend` de sesión, puente `save_pre`, carpeta de recuperación y aviso al arrancar
  (research R15, X2). Si X2 no pasa la prueba manual, se cambia a X1 en este mismo módulo.

### Prueba automática (`tests/test_pisos.py`)

Corre con el Blender del programa (research R17) y cubre:
1. Entorno: Blender 5.2, Bonsai 0.9.0, modo portable, preferencias de R5 (idioma, sin bienvenida, Bonsai sin
   espacio "BIM"), plantilla activa.
2. FR-007: proyecto nuevo IFC4 en metros, nombres, Planta Baja 0,00 / 3,00 activa, escena sin objetos
   ajenos. Un segundo "Nuevo" con proyecto abierto también funciona.
3. FR-012 a FR-016: agregar arriba y abajo con sus nombres y cotas; renombrar, incluido un nombre repetido;
   cambiar altura y cota con desplazamiento de los pisos superiores y de los elementos (en Blender y en el
   IFC); rechazos de valores inválidos.
4. FR-017 / FR-021: borrar un piso con elementos (cuenta para el aviso, sin huérfanos, activa el inferior);
   borrar el activo; no borrar el último.
5. FR-018: deshacer y rehacer del lado IFC (simulado como en `investigacion/ifc.md` §7).
6. FR-008 a FR-011: guardar, guardar como, abrir con piso activo más cercano a 0,00, archivo dañado sin tocar
   el proyecto, IFC de otro programa en milímetros, dos edificios, sin pisos, `is_dirty`.
7. FR-019 / SC-002 / SC-003: reabrir con IfcOpenShell (nombres, `Elevation` = ubicación, `GrossHeight`,
   contención) y validar con `express_rules=True` sin errores.
8. FR-003 (lógica): `TOPBAR_HT_upper_bar.draw` reemplazado; paneles de Blender en `VIEW_3D/UI` con `poll`
   falso; después de `keyconfig_init()`, la lista de atajos inactiva y los propios activos; filtro por dueño
   del espacio.
9. FR-022 (lógica): índice de colección elegido para cada piso. SC-004: `activate_storey` + cálculo para 10
   pisos en menos de 1 s.

Los elementos de prueba se crean con la receta verificada (`investigacion/scripts/_recetas.py`), desde el
archivo de prueba y no desde el producto.

## Pasos que requieren permiso del usuario (constitución, flujo de trabajo)

| Paso | Cuándo |
|---|---|
| Descargar `bonsai_py313-0.9.0-windows-x64.zip` del release oficial (~150 MB) y verificar su SHA-256 | Antes del primer armado |
| Crear `%LOCALAPPDATA%\Programs\BIM Simple\`, copiar Blender (830 MB) e instalar Bonsai (~600 MB) | Primer armado |
| Abrir BIM Simple con ventana: prueba manual, arranque (SC-007), título, icono y X | Después de que pase la prueba automática |
| Crear `BIM Simple.lnk` en el Escritorio y en el menú Inicio | Al final |
| Borrar la copia de prueba de Blender que dejó la investigación (842 MB en la carpeta temporal de la sesión) | Cuando el usuario quiera |

## Riesgos

1. **Partes internas de Blender**: reemplazo del dibujo de la barra superior, paneles C reemplazados por
   `bl_idname` y keymaps de fábrica. Una versión nueva de Blender puede cambiarlas. Mitigación: la prueba
   automática comprueba cada una, y la versión de Blender del programa queda fija hasta que se decida
   actualizarla.
2. **13 llamadas internas de Bonsai** (`investigacion/ifc.md` §10). Mitigación: concentradas en
   `bonsai_api.py` y todas ejercitadas por la prueba.
3. **X de la ventana (X2)**: depende del diálogo de Blender y de un `.blend` de sesión. Solo se puede comprobar
   con ventana. Si falla, el plan B es X1 (research R15).
4. **Colecciones locales y Ctrl+Z real**: no se pueden probar en segundo plano; van a la prueba manual.
5. **Barra lateral plegada**: sin flechas ni N, el usuario no podría volver a abrirla. Mitigación:
   `ensure_layout` la vuelve a mostrar en `load_post` y en cada activación de piso.

## Seguimiento de complejidad

No hay violaciones de la constitución que justificar. Las diferencias con la especificación que impone
Blender están en [research.md §E](research.md) (D1–D7) y se revisan en la prueba manual.
