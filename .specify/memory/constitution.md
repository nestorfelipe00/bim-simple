# Constitución de BIM Simple

## Principios fundamentales

### I. IFC real siempre (NO NEGOCIABLE)

- Cada elemento que dibuja el usuario DEBE ser una entidad IFC real (`IfcWall`, `IfcSlab`,
  `IfcColumn`, etc.) creada con `ifcopenshell.api`.
- Cada elemento DEBE quedar contenido en su `IfcBuildingStorey`, dentro de la jerarquía
  Proyecto > Sitio > Edificio > Piso.
- Lo que se ve en pantalla DEBE salir del IFC (formas calculadas por el motor a partir del
  modelo). NUNCA se dibujan elementos que no existan en el IFC, salvo las vistas previas
  mientras se dibuja.
- Todo `.ifc` que guarde BIM Simple DEBE pasar la validación IFC4 (`ifcopenshell.validate`, con
  reglas EXPRESS) sin errores, y abrirse sin errores en al menos otro programa BIM.

**Por qué:** el valor del producto es un modelo BIM abierto. Si el usuario deja de usar
BIM Simple, su trabajo sigue siendo un IFC válido que cualquier programa BIM puede leer.

### II. Pensado para quien viene de ArchiCAD

- Los textos de la interfaz DEBEN estar en español y usar los términos de ArchiCAD
  (caja de herramientas, Info Box, navegador de pisos, cota, línea de referencia).
- El comportamiento DEBE parecerse al de ArchiCAD: doble clic para activar, menús propios,
  pregunta al cerrar con cambios sin guardar, navegación 3D alrededor del punto señalado.
- Cuando una librería no permita igualar un comportamiento de ArchiCAD, la diferencia DEBE
  quedar escrita en la especificación o en el plan, con la alternativa elegida.
- El código y los identificadores van en inglés.

**Por qué:** el usuario es arquitecto, conoce ArchiCAD y quiere un programa que se sienta
familiar desde el primer día.

### III. Programa propio de escritorio

- BIM Simple es un programa propio para Windows, con su nombre, icono, título de ventana y
  menús. NO usa Blender ni Bonsai.
- Tiene tres piezas con responsabilidades separadas:
  - **ventana** (Electron): menús, diálogos de Windows, cierre con pregunta;
  - **interfaz** (Three.js): planta, 3D, herramientas de dibujo, navegación con
    `camera-controls` al estilo ArchiCAD/Revit;
  - **motor BIM** (IfcOpenShell en Python embebido, como proceso aparte).
- La interfaz y el motor se comunican solo por órdenes JSON (por ejemplo `crear_muro`,
  `deshacer`). La interfaz NUNCA modifica el IFC directamente.
- El IFC es la única fuente de verdad del edificio. Los ajustes de la interfaz (piso activo,
  vista, valores del Info Box) se guardan aparte y nunca contradicen al IFC.
- El programa NO toca otras instalaciones de la computadora (por ejemplo, un Blender instalado).

**Por qué:** da control total de la interfaz sin reescribir el motor IFC. Con el motor detrás
de órdenes, se puede reemplazar (por ejemplo, por IfcOpenShell en WebAssembly) sin rehacer
la interfaz. El prototipo lo validó: unos 30 ms por muro y unos 25 ms por deshacer.

### IV. API verificada, no inventada (NO NEGOCIABLE)

- NUNCA se inventan nombres de funciones, clases u opciones de IfcOpenShell, Electron,
  Three.js, `camera-controls` ni de otras librerías. Todo uso DEBE verificarse en el código
  instalado o en la documentación oficial de la versión fijada, y citarse en el plan con
  archivo y línea, o con su URL.
- Si una skill o una documentación contradice el código instalado, manda el código instalado
  y la diferencia se anota en el plan.
- Antes de escribir lógica BIM propia se DEBE usar la API LGPL de IfcOpenShell cuando exista
  (uniones de muros, capas de materiales, regeneración de muros, teselado, deshacer, planos 2D,
  cómputos, validación).

**Por qué:** las librerías cambian entre versiones. Con todo verificado, una actualización
se detecta con las pruebas y no con errores del usuario.

### V. Lógica separada y comprobada

- La lógica que crea o modifica el modelo DEBE vivir en el motor, en funciones sin interfaz.
- DEBE haber dos pruebas automáticas que salgan con un código distinto de 0 si fallan:
  - la del **motor**, que corre sin interfaz;
  - la del **programa**, que corre con la ventana oculta, recorre las acciones del usuario y
    captura la pantalla.
- Las pruebas DEBEN comprobar el resultado en el IFC guardado y vuelto a abrir: cantidades, piso
  que contiene a cada elemento, espesores, capas, alturas, uniones y validación sin errores.
- Lo que no se puede probar sin ventana (clics, imán, sensación de la navegación) DEBE cubrirse
  con una lista de prueba manual en español.
- Toda afirmación de que algo funciona DEBE ir acompañada de la salida real de la prueba.

**Por qué:** las pruebas ejercitan el mismo camino que las herramientas, y el usuario puede
confirmar cada avance sin leer el código.

### VI. Licencia y propiedad del código (NO NEGOCIABLE)

- BIM Simple se venderá como programa cerrado; quizás se abra más adelante. Por eso:
  - NUNCA se copia ni se importa código con licencia GPL o AGPL: Blender, Bonsai, Chili3D,
    xeokit, Sweet Home 3D y similares. Se puede estudiar cómo se comportan, pero no copiar
    su código ni su estructura.
  - El código con licencias permisivas (MIT, BSD, Apache), como Pascal Editor, Three.js o
    `camera-controls`, se puede reutilizar conservando sus avisos de copyright.
  - IfcOpenShell (LGPL) se distribuye como carpeta separada y sin modificar, con sus textos de
    licencia y un aviso en "Acerca de", y el usuario debe poder reemplazarlo. Si alguna vez se
    modifica, esos cambios se publican bajo LGPL.
  - Se usa el núcleo geométrico OpenCASCADE de IfcOpenShell. Antes de la primera venta se DEBE
    aclarar si sus binarios incluyen partes GPL de CGAL.
- Toda dependencia nueva DEBE tener su licencia revisada y anotada en el plan antes de usarla.

**Por qué:** una sola copia de código GPL obligaría a publicar todo BIM Simple. Revisar cada
licencia al entrar es mucho más barato que limpiar el producto después.

## Restricciones técnicas

- Windows 11, instalación por usuario y sin permisos de administrador.
- Versiones fijas, publicadas hace al menos dos semanas. Hoy son:

  | Pieza | Versión | Detalle |
  |---|---|---|
  | Electron | 44.4.5 | |
  | Three.js | 0.186.1 | |
  | `camera-controls` | 3.1.2 | |
  | Python embebible oficial | 3.14.7 | Con su SHA-256 verificado |
  | IfcOpenShell | 0.9.0 | Con sus dependencias: numpy, shapely; pytest para la validación completa |

  Actualizar cualquiera requiere permiso del usuario y correr las pruebas automáticas antes.
- Proyectos nuevos en IFC4, con unidades métricas en metros.
- NO se agregan dependencias (npm, pip u otras) sin permiso del usuario y sin revisar su licencia
  (Principio VI).
- Solo se hace lo pedido: nada de funciones, abstracciones ni archivos extra. Cada función nueva
  entra por su propia especificación (`/speckit-specify`).
- Se trabaja dentro de la carpeta del proyecto. El entorno de desarrollo (`runtime/` con Python e
  IfcOpenShell, `app/node_modules/`) vive en el proyecto y se excluye de git. Las descargas sueltas
  y las copias de prueba van en una carpeta temporal de ruta corta. NO se modifican
  `.claude/skills` ni `skills-lock.json`.

## Flujo de trabajo

- Cada función sigue el orden de Spec Kit: especificación → aclaraciones (si hay dudas) →
  plan → tareas → implementación. El plan DEBE pasar el control de esta constitución antes
  de escribir código.
- Se DEBE pedir permiso al usuario antes de:
  - instalar, actualizar o descargar cualquier software o paquete;
  - borrar cualquier archivo, incluidas las carpetas `__pycache__`;
  - cambiar la arquitectura descrita en el Principio III;
  - crear accesos directos en el escritorio o en el menú Inicio;
  - abrir ventanas del programa (las pruebas corren con la ventana oculta).
- Si el mismo error sigue después de 3 correcciones, el trabajo se DETIENE y se muestra el
  error junto con lo que se probó.
- Al cerrar cada fase de tareas se corren las pruebas automáticas y se informa su salida real.
- Los commits se hacen con `git commit -F <archivo>`, porque PowerShell 5.1 rompe los mensajes
  con comillas.
- Las respuestas al usuario son siempre en español.

## Gobernanza

- Esta constitución manda sobre cualquier otra práctica, skill o documento del proyecto.
- Las enmiendas las puede proponer cualquiera, pero solo entran con la aprobación explícita
  del usuario. Cada enmienda queda registrada en un commit.
- Versionado semántico: MAJOR cuando se quita o redefine un principio; MINOR cuando se agrega
  un principio o sección, o se amplía una regla; PATCH para correcciones de redacción.
- Cada `plan.md` DEBE incluir el control de constitución. Una excepción solo se acepta si queda
  justificada en la tabla de complejidad del plan y el usuario la aprueba.
- Referencias:
  - Los requisitos originales están en `PROMPT_BIM_SIMPLE.md`.
  - La decisión de la base tecnológica y su evidencia, en `docs/base-tecnologica/`.
  - La investigación hecha sobre Blender (`PLAN.md`, etiqueta git `mvp-original`,
    `specs/001-espacio-trabajo-pisos/investigacion/`) sirve como referencia del
    comportamiento IFC. Su código de Bonsai NO se reutiliza (Principio VI).

**Versión**: 3.0.1 | **Ratificada**: 2026-10-11 | **Última enmienda**: 2026-10-11
