# Constitución de BIM Simple

## Principios fundamentales

### I. IFC real siempre (NO NEGOCIABLE)

- Cada elemento que dibuja el usuario DEBE ser una entidad IFC real (`IfcWall`, `IfcSlab`,
  `IfcColumn`, etc.) creada con Bonsai o con `ifcopenshell.api`.
- Cada elemento DEBE quedar contenido en su `IfcBuildingStorey`, dentro de la jerarquía
  Proyecto > Sitio > Edificio > Piso.
- NUNCA se crean mallas de Blender sueltas que no existan en el IFC.
- El `.ifc` guardado DEBE abrirse y editarse sin errores con la interfaz estándar de Bonsai.

**Por qué:** el valor del producto es un modelo BIM abierto. Si el usuario deja de usar
BIM Simple, su trabajo sigue siendo un IFC válido que cualquier programa BIM puede leer.

### II. Pensado para quien viene de ArchiCAD

- Los textos de la interfaz DEBEN estar en español y usar los términos de ArchiCAD
  (caja de herramientas, Info Box, navegador de pisos, cota, línea de referencia).
- Cada función DEBE poder usarse de principio a fin sin abrir menús ni paneles de Blender
  o de Bonsai.
- Cuando Blender no permita igualar un comportamiento de ArchiCAD, la diferencia DEBE quedar
  escrita en la especificación o en el plan, con la alternativa elegida.
- El código, los identificadores y los nombres de operadores van en inglés. Los operadores y
  herramientas propios usan el prefijo `bimsimple.` para no chocar con los `bim.*` de Bonsai.

**Por qué:** el usuario es arquitecto, conoce ArchiCAD y no quiere aprender Blender.

### III. Programa propio construido sobre Blender

- BIM Simple es un programa propio: se abre desde su acceso directo, con su nombre e icono, y
  muestra directamente la interfaz de BIM Simple. El usuario NUNCA necesita ver ni usar la
  interfaz de Blender.
- Por dentro, Blender aporta el motor gráfico y Bonsai/IfcOpenShell aporta el modelo IFC, tal
  como se publican: NUNCA se modifica su código. BIM Simple solo agrega interfaz y herramientas
  de dibujo.
- El programa lleva su propia copia de Blender y de Bonsai, con configuración aparte. Un Blender
  instalado en la misma computadora NO se toca: ni sus preferencias, ni sus extensiones, ni su
  archivo de inicio.
- Los datos del edificio viven únicamente en el IFC. Las propiedades propias de BIM Simple
  solo guardan ajustes de la interfaz (valores del Info Box, piso activo).

**Por qué:** el usuario quiere un programa propio, sin la interfaz de Blender, que aproveche su
motor gráfico y Bonsai en lugar de reescribirlos. Usar copias sin modificar permite
actualizarlas reemplazando solo la copia incluida.

### IV. API verificada, no inventada (NO NEGOCIABLE)

- NUNCA se inventan nombres de `bpy.ops.bim.*`, de `ifcopenshell.api` ni de `bpy`. Toda
  llamada DEBE verificarse en el código instalado (Bonsai 0.9.0, Blender 5.2) y citarse en el
  plan con archivo y línea.
- Si una skill o una documentación contradice el código instalado, manda el código instalado
  y la diferencia se anota en el plan.
- Antes de escribir lógica propia se DEBE reutilizar la de Bonsai cuando exista (uniones de
  muros, capas de materiales, imán, polilínea, longitud tecleada).
- Las llamadas a clases internas de Bonsai que no son API pública (por ejemplo
  `DumbWallGenerator`) DEBEN concentrarse en un solo módulo.

**Por qué:** Bonsai publica versiones casi a diario y sus clases internas pueden cambiar.
Con todo verificado y concentrado en un lugar, una actualización se detecta con la prueba
y se arregla en un solo archivo.

### V. Lógica separada y comprobada

- La lógica que crea o modifica elementos DEBE estar en funciones sin interfaz, separadas de
  los operadores interactivos.
- La prueba automática DEBE usar exactamente esas mismas funciones, correr con
  `blender.exe --background --python tests/...` y salir con un código distinto de 0 si falla.
- La prueba DEBE comprobar el resultado en el IFC guardado y vuelto a abrir con IfcOpenShell:
  cantidades, piso que contiene a cada elemento, espesores, alturas y uniones.
- Lo que no se puede probar sin ventana (clics, imán, iconos, teclas) DEBE cubrirse con una
  lista de prueba manual en español.
- Toda afirmación de que algo funciona DEBE ir acompañada de la salida real de la prueba o de
  la consola de Blender.

**Por qué:** la prueba ejercita el mismo camino que las herramientas, y el usuario puede
confirmar cada avance sin leer el código.

## Restricciones técnicas

- El programa incluye Blender 5.2 LTS (Python 3.13) y funciona en Windows 11.
- Bonsai 0.9.0, paquete `py313` (el paquete `py311` se instala pero no carga en Blender 5.2).
  Actualizar Blender o Bonsai requiere permiso del usuario y correr la prueba automática antes.
- Proyectos nuevos en IFC4, con unidades métricas en metros.
- Se entrega como programa para Windows que incluye Blender, Bonsai y la extensión BIM Simple
  (con `blender_manifest.toml`). Licencia GPL-3.0-or-later, igual que Blender y Bonsai; el
  paquete incluye las licencias de ambos.
- NO se agregan dependencias (pip u otras) sin permiso del usuario.
- Solo se hace lo pedido: nada de funciones, abstracciones ni archivos extra. Cada función
  nueva entra por su propia especificación (`/speckit-specify`).
- Se trabaja solo dentro de la carpeta del proyecto. NO se modifican `.claude/skills` ni
  `skills-lock.json`.

## Flujo de trabajo

- Cada función sigue el orden de Spec Kit: especificación → aclaraciones (si hay dudas) →
  plan → tareas → implementación. El plan DEBE pasar el control de esta constitución antes
  de escribir código.
- Se DEBE pedir permiso al usuario antes de:
  - instalar o actualizar cualquier software o paquete;
  - borrar cualquier archivo, incluidas las carpetas `__pycache__`;
  - cambiar la arquitectura descrita en el Principio III;
  - descargar Blender o Bonsai para la copia del programa;
  - crear accesos directos en el escritorio o en el menú Inicio;
  - abrir ventanas de Blender (las pruebas corren en segundo plano).
- Si el mismo error sigue después de 3 correcciones, el trabajo se DETIENE y se muestra el
  error junto con lo que se probó.
- Al cerrar cada fase de tareas se corre la prueba automática y se informa su salida real.
- Las respuestas al usuario son siempre en español.

## Gobernanza

- Esta constitución manda sobre cualquier otra práctica, skill o documento del proyecto.
- Las enmiendas las puede proponer cualquiera, pero solo entran con la aprobación explícita
  del usuario. Cada enmienda queda registrada en un commit.
- Versionado semántico: MAJOR cuando se quita o redefine un principio; MINOR cuando se agrega
  un principio o sección, o se amplía una regla; PATCH para correcciones de redacción.
- Cada `plan.md` DEBE incluir el control de constitución. Una excepción solo se acepta si queda
  justificada en la tabla de complejidad del plan y el usuario la aprueba.
- Los requisitos originales están en `PROMPT_BIM_SIMPLE.md`. La investigación de API del MVP
  anterior (`PLAN.md`, etiqueta git `mvp-original`) es punto de partida, pero cada llamada se
  vuelve a verificar según el Principio IV.

**Versión**: 2.0.0 | **Ratificada**: 2026-10-11 | **Última enmienda**: 2026-10-11
