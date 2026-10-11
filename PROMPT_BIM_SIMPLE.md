## Objetivo
Construir "BIM Simple": una extensión de Blender 5.2 que funciona encima de Bonsai y ofrece una interfaz de modelado parecida a ArchiCAD, con caja de herramientas con iconos propios, Info Box de parámetros y navegador de pisos. Con ella se dibujan muros, losas y columnas por piso. La razón es que Blender + Bonsai es demasiado complejo para un arquitecto. El usuario debe poder modelar sin entrar en los menús de Blender ni en los de Bonsai.

## Contexto
- Carpeta del proyecto: C:\Users\Usuario\Documents\SOFTWARE BIM\ (no es repositorio git). Solo contiene .claude\skills, skills-lock.json y este prompt.
- Blender 5.2 instalado en C:\Program Files\Blender Foundation\Blender 5.2\. Las extensiones de usuario están en %APPDATA%\Blender Foundation\Blender\5.2\extensions\.
- Bonsai todavía NO está instalado.
- Windows 11, PowerShell.
- El usuario es arquitecto, conoce ArchiCAD y no quiere aprender Blender.

## Skills de referencia
- En .claude\skills hay skills de Blender (blender-*), Bonsai (bonsai-*) e IfcOpenShell (ifcos-*). Úsalas como guía para la API, la creación de elementos IFC, la estructura espacial, los add-ons, los operadores interactivos y el dibujo en pantalla.
- Fueron escritas para Blender 4.x a 5.1. Todo lo que digan MUST verificarse contra el código de Bonsai instalado y la API de Blender 5.2 antes de usarlo. Si una skill contradice el código instalado, manda el código instalado; anota la diferencia en PLAN.md.

## Arquitectura (ya decidida)
- Extensión de Blender (con blender_manifest.toml) que usa Bonsai mientras corre. Blender aporta el motor gráfico y Bonsai/IfcOpenShell aporta el modelo IFC. La extensión SOLO agrega la interfaz y las herramientas de dibujo.
- Cada elemento MUST ser una entidad IFC real creada con Bonsai o ifcopenshell.api (IfcWall, IfcSlab, IfcColumn), contenida en su IfcBuildingStorey. NUNCA crees mallas sueltas que no existan en el IFC.
- El .ifc resultante MUST abrirse y editarse con la interfaz estándar de Bonsai.
- La lógica que crea elementos MUST estar separada de los operadores interactivos, para que la prueba automática use exactamente las mismas funciones que las herramientas.
- Textos de la interfaz en español con términos de ArchiCAD. Código e identificadores en inglés.

## Comportamiento requerido (MVP)
1. Espacio de trabajo "BIM Simple". La pantalla queda partida en dos: a la izquierda la planta 2D (vista superior ortográfica del piso activo) y a la derecha la vista 3D. Oculta los menús y paneles de Blender que no hacen falta, solo en este espacio de trabajo. Los demás espacios de trabajo de Blender NO se tocan.
2. Caja de herramientas con iconos propios: Flecha (seleccionar), Muro, Losa, Columna.
3. Info Box: muestra los parámetros de la herramienta activa. Esos valores son los que usará el próximo elemento.
   - Muro: espesor 0.20 m, altura = altura del piso, línea de referencia (exterior / centro / interior).
   - Losa: espesor 0.15 m, desfase de cota respecto al piso 0.00 m.
   - Columna: sección rectangular o circular, 0.30 × 0.30 m, altura = altura del piso.
4. Dibujo en la planta:
   - Muro: clic en el inicio y clic en el final. Los muros se encadenan y quedan unidos en las esquinas. Esc o clic derecho termina. Mientras se dibuja: línea de previsualización, la longitud se puede escribir con el teclado, Shift fija ángulos de 0/45/90° y hay imán a los extremos de muros existentes y a la grilla.
   - Losa: un clic por cada vértice del contorno. Se cierra con clic en el primer punto o con Enter.
   - Columna: se coloca con un clic.
   - Todo elemento se crea a la cota del piso activo y queda contenido en ese IfcBuildingStorey.
5. Navegador de pisos: lista con nombre, cota y altura. Permite agregar, renombrar y borrar pisos. Doble clic activa un piso: la planta muestra solo ese piso y los elementos nuevos se crean ahí.

## Fases y puntos de control
Fase 0: investigación, sin escribir todavía el código del producto.
  a. Verifica en la documentación oficial de Bonsai (docs.bonsaibim.org y el repositorio IfcOpenShell en GitHub) qué versión de Bonsai funciona con Blender 5.2 y cómo se instala. Si no es compatible, DETENTE e infórmame.
  b. Dame los pasos para que YO instale Bonsai. No lo instales tú.
  c. Cuando esté instalado, lee el código fuente de Bonsai (empieza por los módulos de modelado de muros, losas, columnas y estructura espacial). Identifica las funciones y operadores reales para: crear el proyecto, crear pisos, crear muros, losas y columnas con capas o perfiles, unir muros, asignar contenedor espacial y guardar el IFC.
  d. Escribe PLAN.md con: la API real encontrada (archivo + nombre de función), cómo vas a mostrar iconos propios en Blender 5.2 (qué formato acepta cada parte de la interfaz), la estructura de archivos y los riesgos. DETENTE y espera mi aprobación.
Fase 1: esqueleto de la extensión, espacio de trabajo y navegador de pisos.
Fase 2: herramienta Muro e Info Box.
Fase 3: Losa y Columna.
Fase 4: prueba completa y checklist manual.
Al terminar cada fase, corre la prueba automática y reporta: "✅ Fase N: [qué quedó hecho] — [salida real de la prueba]".

## Alcance
- Trabaja solo dentro de C:\Users\Usuario\Documents\SOFTWARE BIM\.
- NO modifiques archivos de Bonsai ni de Blender, ni las preferencias o el archivo de inicio de Blender.
- NO modifiques .claude\skills ni skills-lock.json.
- Quedan fuera del MVP: puertas, ventanas, cubiertas, escaleras, cortes, láminas y cómputos. NO los empieces.

## Restricciones
- NUNCA inventes nombres de bpy.ops.bim.* ni de ifcopenshell.api. Usa solo los que verificaste en el código instalado y cita el archivo en PLAN.md.
- Antes de reescribir algo, reutiliza la lógica de Bonsai: uniones de muros, capas de materiales e imanes, si existen.
- No agregues dependencias (pip u otras) sin preguntarme.
- Haz solo lo pedido: nada de funciones, abstracciones ni archivos extra.

## Criterios de aceptación
- [ ] Blender 5.2 arranca con Bonsai y BIM Simple activados, sin errores en la consola.
- [ ] Hay una prueba automática tests/test_mvp.py que se ejecuta con: blender.exe --background --python tests/test_mvp.py. La prueba crea un proyecto con pisos a 0.00, 3.00 y 6.00 m. En el piso 1 dibuja 4 muros que cierran un rectángulo de 6×4 m, una losa sobre ese contorno y una columna. Guarda el .ifc, lo vuelve a abrir con ifcopenshell y comprueba: 3 IfcBuildingStorey, 4 IfcWall, 1 IfcSlab, 1 IfcColumn; cada elemento contenido en el piso correcto; espesor y altura de los muros iguales a los del Info Box; esquinas de muros unidas.
- [ ] El .ifc guardado se abre sin errores en la interfaz estándar de Bonsai.
- [ ] PRUEBA_MANUAL.md: lista de pasos en español para que yo pruebe la interfaz (iconos, dibujo con clics, Shift, longitud con el teclado, cambio de piso).

## Detente y pregúntame antes de
- Instalar o actualizar cualquier software o paquete.
- Enlazar la extensión dentro de la carpeta de extensiones de Blender, la primera vez.
- Borrar cualquier archivo (incluidas carpetas __pycache__, aunque una skill lo indique).
- Cambiar la arquitectura decidida arriba.
- Seguir intentando si el mismo error continúa después de 3 correcciones: muéstrame el error y lo que probaste.

## Evidencia
Cada vez que digas que algo funciona, MUST mostrar la salida real de la prueba o de la consola de Blender. Responde siempre en español.
