# Evaluación de la base tecnológica de BIM Simple

**Fecha**: 2026-10-11 · **Para**: Nestor · **Estado**: decidido (ver §9)

Este documento compara las formas posibles de construir BIM Simple y recomienda una. Se basa en:
- la investigación de Blender + Bonsai que ya se hizo para la función 001
  ([research.md](../../specs/001-espacio-trabajo-pisos/research.md));
- cinco investigaciones nuevas, cuyo detalle y fuentes están en [anexos/](anexos/):

| Anexo | Tema |
|---|---|
| [thatopen-modelado.md](anexos/thatopen-modelado.md) | ¿That Open puede crear y editar IFC? IfcOpenShell fuera de Blender. Licencias LGPL y GPL. |
| [thatopen-aplicacion.md](anexos/thatopen-aplicacion.md) | Electron, Tauri o web; vistas; Three.js directo frente a That Open. |
| [librerias.md](anexos/librerias.md) | Catálogo de motores IFC, motores geométricos y pilas posibles, con licencias. |
| [proyectos.md](anexos/proyectos.md) | Editores BIM abiertos en GitHub, cómo están hechos y qué los frenó. |
| [comunidad.md](anexos/comunidad.md) | Qué dicen OSArch, Hacker News y Reddit (unas 45 fuentes). |

Todas las investigaciones solo leyeron documentación y código. No se instaló nada. Los datos de GitHub (estrellas,
fechas, licencias) se consultaron el 2026-10-11.

---

## 1. Respuesta corta

**Recomiendo un programa propio de escritorio, sin Blender**, hecho con tres piezas:

| Pieza | Para qué | Licencia |
|---|---|---|
| **Electron** | La ventana del programa: título, icono, menús, diálogos de Windows | MIT |
| **Three.js** | La gráfica: planta y 3D, dibujo con el ratón | MIT |
| **IfcOpenShell** (en Python, dentro del programa) | El motor BIM: crea y guarda el IFC real, une muros, deshace, genera plantas 2D | LGPL |

Además, **Pascal Editor**, un editor de arquitectura abierto con licencia MIT, sería la principal fuente de ideas y
de código para las herramientas de dibujo y la planta 2D.

**Antes de comprometernos, propongo un prototipo de 1 o 2 sesiones** (requiere tu permiso para descargar unos
300 MB en una carpeta temporal). Sirve para medir lo que no se puede saber leyendo, sobre todo la velocidad.

Por qué, en cinco puntos:
1. **Control total de la interfaz.** Desaparecen los siete límites de Blender (D1–D7): el título y el icono son de BIM
   Simple, la X pregunta "¿Guardar cambios?", no quedan menús de Blender, todo está en español, la lista de pisos
   admite doble clic y se usan los diálogos de Windows.
2. **El motor IFC más maduro que existe**, el mismo que usa Bonsai, pero sin Blender. Ya trae lo difícil: muros con
   capas, uniones en esquina, losas, columnas, deshacer, plantas en SVG, cómputos y validación.
3. **No cierra ninguna puerta de negocio.** Con esta combinación se puede vender cerrado (cumpliendo la LGPL) o
   publicarlo libre. Con Blender solo se puede la segunda.
4. **Pesa un tercio**: entre 500 y 650 MB, frente a 1,5 GB.
5. **Es la combinación que mejor puede llevar adelante un asistente de IA**: lenguajes muy conocidos (TypeScript y
   Python) y recetas IFC que ya verificamos en este proyecto.

---

## 2. La realidad del objetivo "nivel Revit / ArchiCAD / Edificius"

- La comunidad estima que competir con Revit cuesta **unos 10 años y entre 10 y 50 millones de dólares** con un equipo
  grande (Hacker News, ver [comunidad.md](anexos/comunidad.md)).
- **FreeCAD BIM**: lo creó un arquitecto que programa. Lleva desde 2011 y sigue siendo difícil de usar. En 2026 su
  creador dejó de mantenerlo y empezó **LinesCAD**, un programa más pequeño.
- **Bonsai** se sigue declarando en fase alfa después de años de trabajo.
- **Pascal Editor**: una empresa con tres programadores principales llegó en **un año** a muros con capas, aberturas,
  cubiertas, escaleras, planta 2D, láminas y exportación IFC ([proyectos.md](anexos/proyectos.md) §3.1).
- **Los agentes de IA cambiaron la escala.** Proyectos de una o dos personas con IA hicieron miles de commits en
  meses (ifc-lite, Massing). Pero amplitud no es solidez.

**Lo que repite la comunidad**:
- **El hueco más pedido son los planos 2D**, no el modelado 3D. Es lo que separa un juguete de una herramienta
  profesional.
- **Empezar estrecho**: un uso concreto, como vivienda, antes que una plataforma completa. Los proyectos que se
  acotaron sobreviven (Sweet Home 3D); los que prometieron todo se estancaron.
- **No reinventar el motor IFC**: IfcOpenShell es la base común de FreeCAD, Bonsai, LinesCAD y otros.
- **Probar el IFC en dos o tres visores**, no en uno solo.
- **Presentarlo como "sencillo y con IFC limpio"**, no como "otro Revit".

**Consecuencia para BIM Simple**: el objetivo grande guía la elección de la base, pero se avanza por etapas cortas y
probadas:
1. pisos;
2. muros, losas y columnas;
3. puertas y ventanas;
4. **planta 2D y láminas, temprano**;
5. cubiertas y escaleras;
6. cómputos.

---

## 3. Las opciones comparadas

| | **A. Blender + Bonsai** (programa propio, plan actual) | **B. Add-on de Blender a la venta** | **C. Electron + Three.js + IfcOpenShell** ⭐ | **D. Basarse en Pascal Editor** | **E. That Open** | **F. .NET + xBIM** | **G. Web pura** (ifc-lite, IfcOpenShell-JS) |
|---|---|---|---|---|---|---|---|
| **Control de la interfaz** | Parcial (D1–D7) | Menor aún (es el Blender del cliente) | **Total** | Total | Total | Total | Total, pero el navegador limita guardar y cerrar |
| **Motor BIM / IFC** | IfcOpenShell + Bonsai: el más completo | Igual que A | **IfcOpenShell (API LGPL)**: muros, uniones con capas, losas, perfiles, deshacer, plantas SVG, cómputos, validación | Motor propio en TypeScript; el IFC solo al importar y exportar | Muy bueno para **ver**; débil para **crear** IFC | Lee y escribe IFC; **no** tiene API de modelado | Prometedor pero inmaduro |
| **Lo que ya existe** | Casi todo, incluidas cubiertas, escaleras y planos | Igual que A | El motor. Falta: visor, herramientas de dibujo, comunicación y cubiertas/escaleras | Mucho: muros con ingletes y capas, aberturas, losas, cubiertas, escaleras, planta 2D, láminas, IFC | El visor | Casi nada de BIM | Partes sueltas |
| **¿Venderlo cerrado?** | No (GPL) | No: se vende, pero el comprador puede compartirlo | **Sí, cumpliendo la LGPL** (falta confirmar un detalle de CGAL, ver §4) | Sí (MIT) | Sí (MIT + MPL) | Sí | Sí, con condiciones |
| **Tiempo hasta la función 001** | El más corto: el plan está listo | Corto | **Medio**: semanas | Corto si se bifurca; medio si se copian partes | Largo | Muy largo | Largo |
| **Futuro a largo plazo** | Limitado por Blender: tablas, planos, más de 30.000 objetos | Igual | **Bueno** | Atado a una empresa y a una base enorme | Bueno como visor | Lento | Bueno cuando madure |
| **Peso** | ~1,5 GB | ~1,5 GB (Blender del cliente) | **~500–650 MB** | Similar a C | ~350–450 MB | Medio | Liviano |
| **Riesgo principal** | Partes internas de Blender y Bonsai | Licencia y soporte | Velocidad de la comunicación con Python (sin medir) | Una base de unos 4.400 archivos que cambia a diario, en inglés y controlada por una empresa | Escribir el IFC a mano | Escribir todo a mano | APIs que todavía cambian |
| **Veredicto** | Bueno si te sirve que sea libre y quieres velocidad | Pequeño negocio posible, pero no es un programa propio | **Recomendado** | **Cantera de ideas y código**, no base completa | Útil más adelante para ver modelos grandes | No | Revisar en 6 a 12 meses |

---

## 4. La recomendación en detalle (opción C)

### Cómo se reparte el trabajo

```text
┌──────────────────── Programa BIM Simple (Electron) ─────────────────────┐
│  Ventana, título, icono, menú "Archivo", diálogos de Windows,           │
│  la X pregunta "¿Guardar cambios?"                                      │
│                                                                         │
│  Interfaz (TypeScript + Three.js)                                       │
│   · planta del piso activo y 3D, lado a lado                            │
│   · navegador de pisos, Info Box, herramientas de dibujo                │
│   · vista previa instantánea mientras se dibuja                         │
└──────────────┬──────────────────────────────────────────────────────────┘
               │ órdenes simples: "crear piso", "crear muro", "deshacer"…
               ▼
┌──────────────── Motor BIM (Python + IfcOpenShell, dentro del programa) ─┐
│  el IFC real es la única verdad · uniones y capas · deshacer            │
│  devuelve las formas 3D a la interfaz · guarda y valida el IFC          │
│  más adelante: plantas 2D en SVG, cómputos                              │
└─────────────────────────────────────────────────────────────────────────┘
```

- La **interfaz** nunca toca el IFC: le manda **órdenes** al motor. Así, cuando IfcOpenShell funcione completo dentro
  del navegador (hoy está "en desarrollo"), se cambia el motor sin rehacer la interfaz.
- El **IFC es la fuente de verdad**, como dice el Principio I de la constitución. Abrir y editar un IFC de otro
  programa (Historia 4 de la función 001) funciona sin perder lo que BIM Simple no entiende.

### Lo que se reutiliza de lo ya hecho
- **La especificación 001** casi entera. Sobra lo que era de Blender: FR-004 y SC-005, y las diferencias D1–D7.
- **Los principios I, II, IV y V** de la constitución.
- **Las recetas IFC verificadas** (research.md §C). La mayoría ya son `ifcopenshell.api`, que es LGPL. Las que usaban
  funciones internas de Bonsai (GPL), como renombrar un piso o el piso activo, se reescriben con `ifcopenshell.api`;
  son operaciones simples.

### Lo que hay que construir y antes no hacía falta
- El visor con planta y 3D, el imán, la longitud por teclado y los ángulos fijos. En Blender venían hechos.
- La comunicación entre la interfaz y el motor.
- El instalador del programa.
- **Más adelante**, los generadores de **cubiertas y escaleras**: en Bonsai son GPL y no se pueden copiar a un programa
  que se venda cerrado.

### Riesgos, sin maquillar
1. **La velocidad de cada edición no está medida.** Cada muro va de la interfaz al motor y vuelve. Debería tardar
   milisegundos, porque es local y Bonsai hace lo mismo dentro de Blender, pero hay que medirlo. Mientras se arrastra
   el muro, la vista previa se calcula en la interfaz, sin esperar al motor.
2. **No hay un precedente publicado exacto** de un programa BIM con Electron + Three.js + IfcOpenShell. Lo más
   parecido:
   - Massing, que corre IfcOpenShell en un servidor y es más lento;
   - LinesCAD, que usa Qt en lugar de Electron.
3. **Un detalle de licencia por confirmar.** Los binarios de IfcOpenShell incluyen piezas que usan **CGAL**, que en
   parte es GPL. Antes de vender cerrado hay que preguntarlo a los mantenedores o usar solo el núcleo OpenCASCADE, que
   es el que IfcOpenShell usa por defecto. No es asesoría legal: para vender, conviene un abogado.
4. **Más trabajo al principio que con Blender.** Es el precio del control total.

### Cómo aprovechar Pascal Editor (MIT)
- **Copiar ideas y partes de código, con su aviso de licencia**:
  - el cálculo de ingletes en las esquinas, para la vista previa;
  - el esquema de capas del muro;
  - **cada tipo de elemento en su carpeta** (3D, símbolo 2D, herramienta, panel);
  - **símbolos de planta por tipo de elemento**, como ArchiCAD;
  - exportación de láminas PDF.
- **No** usarlo como base entera:
  - tiene unos 4.400 archivos y cambia a diario;
  - lo controla una empresa;
  - su interfaz está solo en inglés;
  - trata el IFC como algo secundario (su exportación IFC tiene dos semanas y no está validada).
- **Puedes mirar su demo** en `editor.pascal.app` para ver ideas de interfaz. La versión de la demo ("Next") no es la
  abierta.

---

## 5. Sobre vender un add-on de Blender

- **Se puede vender, pero solo con licencia GPL.** Así lo dice la página de licencias de Blender para todo código que
  use su API. El comprador recibe el código y puede compartirlo. Además, BIM Simple usa Bonsai, que también es GPL.
- **En la práctica** existe un mercado de add-ons pagos: la gente paga por comodidad, actualizaciones y soporte. Es un
  negocio posible, pero el código no se puede proteger.
- **Y no es un programa propio**: sigue siendo Blender, con todos sus límites.

---

## 6. Qué cambiaría en el proyecto si eliges la opción C

1. **Constitución v3.0.0**:
   - Principio III: "programa propio de escritorio, sin Blender: Electron + Three.js + motor IfcOpenShell";
   - restricciones técnicas;
   - licencia, según lo que decidas.
2. **Especificación 001**: ajustes menores, porque desaparecen los requisitos y diferencias propios de Blender.
3. **Plan 001**: se rehace. La investigación de Blender queda como referencia, y las recetas IFC pasan a
   `ifcopenshell.api` puro.
4. **Lo ya guardado en git no se pierde**: el MVP (`mvp-original`), la constitución v2.0.0 y el plan para Blender
   quedan en el historial por si se vuelve a esa opción.

---

## 7. Próximo paso propuesto: prototipo de comprobación (requiere tu permiso)

| | |
|---|---|
| **Dónde** | Una carpeta temporal, fuera del proyecto. Se borra al terminar. |
| **Qué se descarga** | Electron y Three.js con npm (~250 MB); Python embebible oficial (~10 MB); IfcOpenShell 0.9.0 y sus dependencias (~60 MB). |
| **Qué debe mostrar** | Una ventana **"BIM Simple"** con su icono y el menú "Archivo" en español; planta y 3D lado a lado; crear un proyecto con 3 pisos y dos muros con capas unidos en esquina desde el motor; ver las formas en las dos vistas; Ctrl+Z; guardar un IFC que pase la validación; cerrar con la X y que pregunte "¿Guardar cambios?". |
| **Qué se mide** | Tiempo de cada edición (objetivo: que se sienta instantáneo), tiempo de arranque y peso total. |
| **Después** | Con los números en la mano decides: opción C, volver a Blender o esperar. |

---

## 8. Decisiones que te tocan

1. **Base**: ¿programa propio (C, recomendado) o seguir con Blender (A)?
2. **Licencia**: ¿venderlo cerrado, publicarlo libre o decidir más adelante? La opción C sirve para las tres.
3. **Prototipo**: ¿autorizas las descargas del §7 en una carpeta temporal?

---

## 9. Decisiones del usuario (2026-10-11)

1. **Base**: programa propio (opción C), "aunque cueste más al principio".
2. **Licencia**: venderlo **cerrado**, con la posibilidad de abrirlo más adelante. Consecuencias:
   - no se copia código GPL (Bonsai, Blender) ni AGPL;
   - se cumple la LGPL de IfcOpenShell;
   - antes de vender hay que aclarar lo de CGAL (§4, riesgo 3).
3. **Prototipo**: autorizado, con las descargas del §7 en una carpeta temporal fuera del proyecto.

La constitución (v3.0.0) y el plan de la función 001 se actualizan con los resultados del prototipo.

**Resultado del prototipo** ([prototipo/RESULTADOS.md](prototipo/RESULTADOS.md)): la opción C queda confirmada.
- Un muro unido en esquina tarda ~30 ms de punta a punta y deshacer ~25 ms.
- El IFC guardado pasa la validación IFC4 completa sin errores.
- Funcionan el título propio, la pregunta al cerrar con la X y el doble clic en la lista.
- Peso estimado: ~640 MB.
