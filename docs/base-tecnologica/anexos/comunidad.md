# Qué dice la comunidad: desarrollar software BIM propio con IFC y estándares abiertos

Investigación hecha el 11 de octubre de 2026 para el proyecto **BIM Simple**. Recoge opiniones y experiencias de quienes lo intentaron, no fichas de librerías (de eso se ocupan `librerias.md` y `proyectos.md`).

## Cómo se hizo y qué no se pudo leer

| Fuente | Acceso | Cómo se leyó |
|---|---|---|
| Foro OSArch (community.osarch.org) y osarch.org | Sí | Hilos leídos directamente |
| Hacker News | Sí | Búsqueda en hn.algolia.com y lectura de hilos en news.ycombinator.com |
| Reddit | **Bloqueado** (reddit.com, old.reddit, los espejos tipo Redlib tienen anti-bots) | Solo mediante los archivos públicos `arctic-shift.photon-reddit.com` y `api.pullpush.io`. Funcionaron para subreddits pequeños y para leer hilos concretos por su ID; para r/bim y r/Revit el buscador del archivo devolvió error 422, y pullpush se quedó en límite de peticiones (429). La cobertura de Reddit es **parcial**. |
| Stack Overflow | **Bloqueado** (ni lectura ni búsqueda) | No hay entradas de Stack Overflow. En su lugar se usaron el foro de three.js, el foro de buildingSMART, devtalk.blender.org, Blender Artists y los propios hilos técnicos de OSArch, que es donde de verdad se discuten IfcOpenShell y Bonsai. |

Leyenda: ✅ = hilo leído (o leído su archivo); ⚠️ = solo vi el título o el resumen del buscador, sin poder leer el hilo completo. Los resúmenes son míos; las citas, si las hay, son de pocas palabras.

Nota sobre fechas: el foro OSArch muestra solo mes y año en muchos hilos; así se indica.

---

## (a) Dificultad real de construir un autor BIM

**1. "A medium-term Revit replacement"**, OSArch, abril de 2020 (editado en diciembre de 2021). ✅
https://community.osarch.org/discussion/39
Un arquitecto argentino (joselaks) propone crear desde universidades públicas un BIM libre nuevo, con lo mejor de FreeCAD y Blender y un vínculo vivo 2D-3D. Las respuestas de los desarrolladores son claras:
- bitacovir aconseja empezar por un caso estrecho (por ejemplo, vivienda) en vez de una plataforma completa, y contribuir a lo existente.
- Moult (Bonsai) explica que IFC admite muchísimas formas de representar geometría y que eso hace difícil el motor; propone un flujo de planos aparte (cortar el IFC y sacar SVG) en vez de un programa nuevo.
- yorik (FreeCAD) dice que en software libre no hace falta un "todo en uno" y admite que Revit es muy superior en planos 2D. También dice que la "facilidad de uso" es difícil de definir: Revit parece fácil porque la gente ya lo conoce.
- htlcnn señala que la fuerza real de Revit es la gestión de información (propiedades heredadas y vinculadas), no el modelado.

**2. "A specific BIM software open source?"**, foro buildingSMART (Developers), 23 de marzo de 2020. ✅
https://forums.buildingsmart.org/t/a-specific-bim-software-open-source/2530
El mismo arquitecto argentino plantea la idea. Moult responde que ni FreeCAD ni Blender nacieron para arquitectura, que no ve ventaja en casarse con una sola plataforma, que ambas ya comparten IfcOpenShell, y propone usar el IFC como "archivo-base de datos" que varias herramientas editan por turnos. Sugiere construir herramientas de documentación que lean el IFC y devuelvan los cambios.

**3. "Autodesk criticised by architects"**, Hacker News, 3 de agosto de 2020. ✅ (página muy larga; leída la primera mitad)
https://news.ycombinator.com/item?id=24034211
- Estimaciones de esfuerzo para competir con Revit: user5994461 habla de unos 10 millones de dólares y unos diez años con un equipo grande; IshKebab estima unos 50 millones para llegar a algo usable por empresas.
- neutronicus (trabaja en un competidor): importar/exportar Revit y AutoCAD es imprescindible; los núcleos geométricos son difíciles (Parasolid es propietario; CGAL y OpenCASCADE tienen límites).
- imgabe: el efecto red es el gran obstáculo; los consultores trabajan en Revit y las conversiones a menudo se rompen. Al importar IFC en Revit todo llega como objetos genéricos.
- wappa y Tallasatree: reentrenar personal, perder plantillas y necesitar años de historial antes de que un estudio confíe en el programa.

**4. "Autodesk criticised by 35 named architects (2020)"**, Hacker News, 13 de agosto de 2022. ✅
https://news.ycombinator.com/item?id=32446907
- analog31: el trabajo pesado es codificar conocimiento de dominio arcano, y los usuarios se resisten a cambiar de flujo.
- HellDunkel: un CAD en el navegador es viable, pero un núcleo geométrico es más difícil que un motor de videojuegos.
- aothms (IfcOpenShell) presenta BlenderBIM como alternativa en desarrollo que busca financiación.
- Se mencionan startups web (Arcol, Snaptrude, Qonic, Modumate) y Renga como posibles retadores.

**5. "FreeCAD BIM development news"**, Hacker News, 31 de octubre de 2020. ✅
https://news.ycombinator.com/item?id=24951311
- person8645 (arquitecto): lo primero es la interoperabilidad; si el intercambio de datos funciona, un sustituto no necesita igualar todo Revit de golpe. Prefiere ArchiCAD por su apuesta por IFC. Cambiar de programa en un solo proyecto puede duplicar los costes del estudio.
- kls (usa ArchiCAD): estos programas se manejan con el teclado; cambiar destruye la memoria muscular.
- Se critican de FreeCAD la interfaz poco pulida, la dispersión en "workbenches" y la falta de tramas SVG para la documentación 2D.

**6. Comentario de fsloth en "Blender 5.0"**, Hacker News, aprox. noviembre de 2025. ✅
https://news.ycombinator.com/item?id=46001824
Antes de escribir geometría hay que decidir quién es el usuario experto y qué produce (planos, modelos de coordinación, fabricación). Para AEC, importar y exportar IFC es obligatorio. En una respuesta añade que los conceptos de gráficos y geometría se comparten entre juegos, VFX y CAD, pero las capas propias del dominio son la mayor parte del código y de la complejidad.

**7. "Show HN: I've spent nearly 5y on a web app that creates 3D apartments" (Roometron)**, Hacker News, 7 de agosto de 2024. ✅
https://news.ycombinator.com/item?id=41180504
Un desarrollador web en solitario, con Three.js, tardó casi cinco años en llegar a beta con una app que pasa planos a apartamentos 3D. El hilo (694 puntos, 200 comentarios) se centró en la puesta en marcha: errores al subir PDF, cobros incorrectos, falta de un proyecto de ejemplo y de una pantalla de guía. Lección: el producto tardó mucho más de lo previsto y los fallos de incorporación del usuario pesaron más que la parte 3D.

**8. "Thoughts on using IFC.js and IfcOpenShell in combination?"**, OSArch, agosto de 2022. ✅
https://community.osarch.org/discussion/1089/thoughts-on-using-ifc-js-and-ifcopenshell-in-combination
Moult distingue entre crear geometría por código (fácil con IfcOpenShell) y una edición geométrica cómoda para el usuario, que exige un esfuerzo de interfaz enorme. Es la frase que mejor resume la dificultad de un autor BIM.

**9. "Problems with learning Bonsai and Blender"**, OSArch, marzo de 2025. ✅
https://community.osarch.org/discussion/2838/problems-with-learning-bonsai-and-blender
Un usuario nuevo no consigue modelar ni un proyecto simple: vídeos viejos o muy específicos y documentación que no explica cómo empezar. Moult reconoce que Bonsai sigue en **alfa**: los fundamentos aún cambian y hay zonas inestables o sin documentar. Es decir, tras años de desarrollo y con un equipo activo, el autor BIM libre más avanzado aún no se considera terminado.

**10. "Is native IFC good for Bonsai in the long run"**, OSArch, febrero de 2025. ✅
https://community.osarch.org/discussion/2767/is-native-ifc-good-for-bonsai-in-the-long-run
Moult enumera partes del IFC nativo que Bonsai todavía no implementa: capas de muro, MEP, tipos agregados y alineaciones. Da idea del tamaño del estándar.

**11. Yorik van Havre, "Hi again" (anuncio de LinesCAD)**, blog, 15 de mayo de 2026. ✅
https://yorik.uncreated.net/?blog%2F2026%2F2026-001-hi-again
El creador del BIM de FreeCAD empieza un programa nuevo, ligero, BIM y 2D, con IFC como modelo. Él mismo enumera lo difícil: que el visor sea rápido, deshacer/rehacer, copiar/pegar, varios documentos abiertos, un árbol de objetos rápido, importar/exportar DXF con velocidad (sospecha que hará falta C++) y empaquetar para Windows y macOS.

**12. "If a new open source, cross platform BIM software were developed, what features do you want in V1?"**, r/askarchitects, 17 de marzo de 2026. ✅ (leído por el archivo arctic-shift)
https://www.reddit.com/r/askarchitects/comments/1rw5gg2/
El autor dice que BlenderBIM y el BIM de FreeCAD aún no están listos para el trabajo diario. Lo que piden los arquitectos para una V1: el nivel de Revit LT en modelado y planos, trabajo colaborativo sobre un mismo modelo, control fino de grosores de línea y una interfaz amable ("que no parezca una cabina de avión"). Un comentario duda de que una V1 así sea alcanzable. La misma pregunta en r/architecture (junio de 2025, https://www.reddit.com/r/architecture/comments/1lecadq/) fue retirada por los moderadores.

**13. "Looking for Advisor for our startup" (Open Monolith)**, r/architectureph, 24 de diciembre de 2025. ✅ (archivo arctic-shift)
https://www.reddit.com/r/architectureph/comments/1puoj0d/
Una startup busca asesor para una alternativa libre a Revit con IA. El comentario más útil (diegstah) hace las preguntas incómodas: qué hace mejor que Revit, cómo atraerá a quien ya usa AutoCAD o Revit sin integración, si los contratistas e ingenieros podrán abrir los archivos y en qué formato guarda. Los fundadores admiten que la integración está sin resolver.

**14. "I'm building a lightweight, offline-first BIM tool from scratch…" (Northsill)**, r/bim, 23 de septiembre de 2026. ✅ (archivo; publicación luego retirada)
https://www.reddit.com/r/bim/comments/1wnrt8e/
Un desarrollador en solitario hace un BIM de escritorio en C++ con Open CASCADE (uniones de muros automáticas, hojas y tablas). Cero comentarios. Ejemplo de que anunciar una herramienta nueva en r/bim no basta para conseguir probadores.

**15. "The Future of FreeCAD BIM After Yorik's Stepping Down"**, blog FCB Lounge, 9 de septiembre de 2026, y su hilo en r/FreeCAD (10 de septiembre de 2026). ✅
https://fcblounge.blogspot.com/2026/09/the-future-of-freecad-bim-after-yorik.html
https://www.reddit.com/r/FreeCAD/comments/1wccofq/
El creador del banco BIM de FreeCAD deja de mantener FreeCAD (el artículo apunta a la nueva política sobre IA como motivo principal). El BIM de FreeCAD queda en manos de un grupo pequeño de voluntarios. Riesgo clásico: dependencia de pocas personas.

---

## (b) Comparación de motores IFC

**1. "XBIM or IFC++ ?"**, OSArch, abril de 2020. ✅
https://community.osarch.org/discussion/41
Para un proyecto de presupuestos (5D) a partir de IFC, Moult recomienda IfcOpenShell: lo usan FreeCAD, Blender y BIMServer, es multiplataforma y tiene bindings de Python. Ve a xBIM técnicamente a la par, pero más ligado a Windows y a aplicaciones propietarias. IFC++ le parece menos completo.

**2. "Thoughts on using IFC.js and IfcOpenShell in combination?"**, OSArch, agosto de 2022. ✅
https://community.osarch.org/discussion/1089/thoughts-on-using-ifc-js-and-ifcopenshell-in-combination
- Moult: IFC.js (hoy That Open) es fuerte en visualización web y débil en autoría; IfcOpenShell es fuerte en autoría de datos, y Bonsai añade la autoría geométrica.
- Entonces IFC.js no tenía atributos inversos, necesarios para editar relaciones en el grafo IFC.
- xeokit usa IfcOpenShell y es más rápido que IFC.js una vez preprocesado, pero su conversión es de un solo sentido.
- Como todo Bonsai se construye primero en IfcOpenShell, un frontal web que hable con un servidor local es posible.
- Ve a IFC.js por delante en marketing.

**3. "Discussion about IFC.js"**, OSArch, enero a septiembre de 2021. ✅
https://community.osarch.org/discussion/426/
Fase temprana: el propio autor (agviegas) dice que aún completan lo básico de un visor; hay geometrías mal mostradas y falta guía para no programadores. Útil como historia: That Open empezó como visor.

**4. "Bug on IfcWalls connections when exporting IFC from BlenderBIM to IFC.js"**, OSArch, octubre de 2022. ✅
https://community.osarch.org/discussion/1197/bug-on-ifcwalls-connections-when-exporting-ifc-from-blenderbim-to-ifc-js
Muros unidos a inglete en BlenderBIM se ven mal en IFC.js, pero bien en Solibri, Trimble Connect y Revit. Moult lo atribuye a web-ifc y abre una incidencia. Lección: dos motores pueden dibujar distinto el mismo IFC; hay que probar en varios visores.

**5. "Updated IfcOpenShell+pyodide demo app wasm.ifcopenshell.org"**, OSArch, enero de 2025 (actualizado en junio de 2025). ✅
https://community.osarch.org/discussion/2701/updated-ifcopenshell-pyodide-demo-app-wasm-ifcopenshell-org
IfcOpenShell completo corriendo en el navegador vía Pyodide/WASM, con descarga de unos 10 MB. Un usuario creó un muro con ventana y puerta y lo abrió sin problemas en BIMVision. Pero un modelo grande no cargó, en Firefox las aberturas no cortaban los muros, y el visor de That Open se colgó con modelos salidos de la demo. aothms lo llama un "teaser" y reconoce que el manejo de excepciones en WASM aún no está resuelto.

**6. "BlenderBIM – add-on for beautiful, detailed, and data-rich OpenBIM with Blender"**, Hacker News, 14 de marzo de 2024. ✅
https://news.ycombinator.com/item?id=39700448
- Moult: el modelado se hace con una interfaz propia que actualiza el IFC; Blender solo muestra los triángulos; la geometría se procesa con IfcOpenShell sobre OpenCASCADE; un edificio necesita menos precisión que la fabricación mecánica.
- epaulson: Blender funciona como capa de interfaz y de dibujo, con todo guardado en IfcOpenShell; algunas operaciones de Blender pueden desincronizar el IFC (ha mejorado).
- Un usuario no técnico (pzs) usó BlenderBIM para recorrer la reforma de su casa, aunque al importar el IFC del arquitecto se perdieron puertas, ventanas y medidas de muros.
- ptrott2017 comenta que las "Blender Apps" están en la hoja de ruta a largo plazo pero sin prioridad.

**7. "Bonsai Viewer is coming"**, osarch.org, 29 de mayo de 2026. ✅
https://osarch.org/2026/05/29/bonsai-viewer-is-coming/
El equipo de Bonsai empieza un visor de coordinación aparte de Blender, porque Blender no está optimizado como visor rápido. Menciona trabajo en rendimiento, soporte web y soporte TypeScript de IfcOpenShell. Es una señal de hacia dónde va IfcOpenShell: más allá de Python y de Blender.

**8. "Arcol simplifies building design with browser-based modeling"**, Hacker News, 2 de junio de 2025. ✅
https://news.ycombinator.com/item?id=44160358
El fundador confirma su pila: Three.js para dibujar, un núcleo geométrico propio en Rust compilado a WASM y React para la interfaz; copian los búferes de geometría del heap de WASM a JavaScript. No hablan de IFC; exportan a Revit y glTF. Muestra el coste de ir 100 % web con autoría: escribieron su propio núcleo.

**9. "Arcol's Parametric Geometry Engine"**, Hacker News, 3 de febrero de 2023. ✅
https://news.ycombinator.com/item?id=34642588
El motor es un grafo paramétrico al estilo Grasshopper, oculto al usuario, que dibuja muros y coloca ventanas a mano. Afirman una lista de espera de más de 15.000 personas tras las cartas abiertas contra Revit.

**10. Hilos del foro de three.js sobre aberturas y CSG.** ⚠️ (solo resumen del buscador)
- "How to create window and door openings in the wall?" (2020): https://discourse.threejs.org/t/how-to-create-window-and-door-openings-in-the-wall/20473 — se recomienda extruir formas con agujeros en vez de usar booleanas.
- "Performance CSG": https://discourse.threejs.org/t/performance-csg/31820 — una intersección con una malla de unos 550.000 vértices agotó la memoria del navegador; para formas simples la extrusión siempre es más rápida que la CSG.
- "How to make a hole in the wall?": https://discourse.threejs.org/t/how-to-make-a-hole-in-the-wall/21475 — la booleana tardaba demasiado con muros de muchos polígonos.

**11. Recomendación del autor de IfcPlusPlus.** ⚠️ (resumen del buscador)
https://github.com/ifcquery/ifcplusplus
El repositorio, archivado, recomienda web-ifc para proyectos nuevos por su ligereza y por funcionar en WASM.

---

## (c) Web frente a escritorio

**1. Comentario de un equipo de AutoCAD en "Ask HN: Is there still a place for native desktop apps?"**, Hacker News, 17 de mayo de 2020. ✅
https://news.ycombinator.com/item?id=23212285
Consiguieron correr AutoCAD 2D en WebAssembly, pero no fue una simple recompilación. El ratón en el navegador va con retraso frente al nativo, Revit está demasiado atado a Windows para portarlo, el 3D con WebGL fue lo más fácil, y el límite real son los modelos enormes que superan la memoria del navegador.

**2. "Qonic vs Revit vs Forma vs Motif"**, r/bim, 8 de octubre de 2026 (18 comentarios). ✅ (archivo arctic-shift)
https://www.reddit.com/r/bim/comments/1x0rmj2/
- Preocupa qué pasa con tu trabajo si desaparece el proveedor de una herramienta web.
- Qonic promete, pero está lejos de reemplazar a Revit, sobre todo en documentación (hojas de planos).
- Consejo práctico (Merusk): asegurarse de poder exportar todos los datos, tener plan de migración y presupuesto para reentrenar.
- Nadie ha resuelto bien el trabajo colaborativo, ni local ni en la nube.

**3. Arcol (HN 2023 y 2025, ver sección b).** ✅ La web resuelve acceso sin instalar y colaboración en tiempo real, pero el producto se limita a diseño temprano y viabilidad, y exporta a Revit para el resto.

**4. Interfaz web junto a Blender.** ✅
- "Blender BIM UI and workflow", OSArch, octubre de 2022 a febrero de 2023: https://community.osarch.org/discussion/1173/ — Moult dice que Blender es muy malo para hojas de cálculo, diagramas de Gantt, gestión de incidencias BCF y maquetación de planos 2D, y que preferiría hacer esas herramientas fuera de Blender. Un usuario con 25 años de ArchiCAD pide una interfaz distinta a la estándar de Blender; otro dice que, tras un año, tareas rápidas en Revit o ArchiCAD le llevan mucho más en BlenderBIM.
- "Web-based UI integration with Blender", OSArch, noviembre de 2025: https://community.osarch.org/discussion/3224/web-based-ui-integration-with-blender — Bonsai ya trae una interfaz web integrada (planos, costes, hojas de cálculo).
- "What about showing the drawings in Blender's 3D space?" (página 2), OSArch, enero de 2026: https://community.osarch.org/discussion/2625/what-about-showing-the-drawings-in-blenders-3d-space/p2 — se pide una app de maquetación tipo Layout de SketchUp, local y en navegador. Moult confirma que la integración web existe para lo que la interfaz de Blender no puede hacer, pero que faltan las pantallas, y pide librerías de snapping y dibujo SVG.

**5. Límites de Blender con modelos grandes: "How to Open Large IFC Files in Bonsai?"**, OSArch, marzo de 2025. ✅
https://community.osarch.org/discussion/2821/how-to-open-large-ifc-files-in-bonsai
Moult: lo que importa es el número de objetos, no el tamaño del archivo. Blender suele sufrir por encima de unos 30.000 objetos y se vuelve inutilizable hacia 60.000-80.000; Bonsai aún no sirve para editar gráficamente modelos muy grandes (enlazar sí). Fusionar modelos lo empeora.

**6. LinesCAD: escritorio con Python + Qt + Coin3D + IfcOpenShell.** ✅
- Anuncio en OSArch, mayo de 2026: https://community.osarch.org/discussion/3456/announcing-linescad
- Noticia: https://osarch.org/2026/05/15/linescad-announced/
Yorik elige escritorio, Python y Qt, y quita OpenCASCADE y C++, apoyándose solo en IfcOpenShell para la geometría. Motivo declarado: FreeCAD es lento con archivos grandes y Bonsai queda lejos de un flujo de "dibujo" sencillo. Cada objeto IFC se refleja en la escena 3D, así que mover un piso mueve su contenido. Comentarios en el hilo: semhustej coincide con el diagnóstico; paullee pregunta por la compatibilidad (será vía IFC); zoomer critica las herramientas 2D de FreeCAD y tuvo que pasarse a un programa propietario; isain pide una biblioteca compartida de componentes IFC.

---

## (d) Licencias y modelos de negocio

**1. "That Open Company"**, OSArch, julio a octubre de 2023 (seguimiento en diciembre de 2024). ✅
https://community.osarch.org/discussion/1551
El hilo más claro sobre modelos de negocio en BIM libre:
- agviegas (That Open): el núcleo será siempre libre y con licencia MIT; los servicios de pago para desarrolladores y estudiantes financian el desarrollo.
- Moult: el software libre es una postura ética, no un medio, y habla de "openwashing". Critica decisiones a puerta cerrada y documentación tras registro.
- cvillagrasa: valora mucho la licencia MIT y señala que los add-ons GPL pueden ahuyentar a usuarios comerciales; pide aclarar qué seguirá abierto.
- doia sospecha de un plan de "crear comunidad y monetizar después".
- Varios piden colaboración real con IfcOpenShell; se percibe "solo de entrada".

**2. "Yet another discussion about the GPL... this time about add-ons (again)"**, Blender Artists, 3-4 de junio de 2019. ✅
https://blenderartists.org/t/yet-another-discussion-about-the-gpl-this-time-about-add-ons-again/1163319
Vender add-ons GPL es legal, pero el comprador puede redistribuirlos. stephen_leger (autor de Archipack, add-on de arquitectura) dice que las donaciones no pagan las facturas; otros cuentan que compran aunque existan copias gratis, como forma de apoyo. BD3D observa que los add-ons financiados por donación acaban siendo proyectos de fin de semana.

**3. Reglas oficiales de Blender y tiendas.** ⚠️ (resumen del buscador)
- FAQ de Blender: https://www.blender.org/support/faq/ — se puede vender un add-on si se entrega con su código bajo GPL; un script que llama a la API de Blender (`bpy`) debe ser GPL al distribuirse.
- Blender Market (Superhive), "How to Sell GPL Software": https://support.blendermarket.com/article/289-how-to-sell-gpl-software-the-license-basics — se vende el soporte y el mantenimiento más que el código.
- La plataforma oficial de extensiones solo admite add-ons GPL-3.0-or-later (o compatibles): https://docs.blender.org/manual/es/dev/advanced/extensions/licenses.html

**4. Programa propio sobre Blender.** ✅ / ⚠️
- "Creating custom UI for Blender for a project (for a customer) instead of developing new software", devtalk.blender.org, febrero de 2021 (✅): https://devtalk.blender.org/t/creating-custom-ui-for-blender-for-a-project-for-a-customer-instead-of-developing-new-software/17472 — es viable pero no fácil; se recomiendan las Application Templates; un usuario se queja de que la documentación no enseña a crear una desde cero.
- Propuesta "Blender Apps", code.blender.org, noviembre de 2022 (⚠️): https://code.blender.org/2022/11/blender-apps/ — versiones de Blender a medida para una tarea; su código seguiría bajo GPL. En HN (2024) se comenta que siguen sin prioridad.
- "Custom UI for Blender 2.8 Addons", Blender Artists (⚠️): https://blenderartists.org/t/custom-ui-for-blender-2-8-addons/1141881 — los widgets disponibles para add-ons son limitados; las salidas (código C, un programa aparte por socket, PyQt incrustado) son engorrosas o inestables.

**5. "Bonsai Licensing Explained: Is It Really Free Forever?"**, r/bim, 8 de febrero de 2025. ✅ (texto leído en el archivo; la publicación fue borrada)
https://www.reddit.com/r/bim/comments/1ikl64j/
Explica que IfcOpenShell es LGPL y Bonsai GPL, que la licencia difícilmente puede cambiarse y que el proyecto vive de donaciones, con posibles negocios de soporte y servicios. Ojo: la wiki de OSArch lista Bonsai como LGPL-3.0, mientras otras fuentes dicen GPL-3.0-or-later para los add-ons de Blender; conviene que el informe de librerías lo confirme en el repositorio oficial.

**6. GPL de LinesCAD y choque con FreeCAD.** ✅
- Blog de Yorik (mayo de 2026): elige GPL porque es una aplicación de usuario final, poco probable que se use como librería, y quiere asegurar desde el principio que siga siendo libre.
- Hilo de r/FreeCAD (septiembre de 2026, ver a.15): DesignWeaver3D y semhustej señalan que la GPL-3.0 de LinesCAD (y de OpenCAD Studio) es incompatible con la licencia de FreeCAD (LGPL), lo que impide compartir código entre ellos.

**7. Licencias como protección del usuario (HN 2020, ver a.3).** ✅ tomxor propone licencias libres para proteger a los estudios; nitrogen menciona el depósito del código fuente (escrow); dreamcompiler duda que los inversores acepten cláusulas que dificulten una venta.

**8. That Open: negocio descrito por la propia empresa y medios.** ⚠️ (resumen del buscador)
- https://opensource.construction/projects/that-open-company/ y AEC Magazine (https://aecmag.com/features/that-open-company-raises-the-stakes/): empresa con ánimo de lucro, librerías MIT, ingresos por cursos, consultoría y desarrollo a medida; rechazó capital riesgo. La plataforma de pago se presenta como un "sistema operativo BIM" (CDE en la nube, permisos, versiones).

---

## (e) Consejos para empezar (lo que repite la comunidad)

1. **Empezar estrecho.** Un caso de uso concreto (vivienda) antes que una plataforma completa. Fuente: bitacovir en OSArch 39 (✅).
2. **Definir primero el usuario y lo que produce** (planos, coordinación, cantidades). Fuente: fsloth en HN (✅).
3. **Interoperabilidad desde el primer día**: IFC de entrada y salida, y DWG/DXF si se quiere convivir con estudios reales. Fuentes: person8645 y neutronicus en HN (✅); Yorik pone DXF como objetivo de LinesCAD (✅).
4. **No reinventar el lector IFC ni el motor geométrico**: IfcOpenShell es la base común de FreeCAD, Bonsai, LinesCAD y xeokit. Fuentes: OSArch 41 y 1089 (✅).
5. **Construir sobre lo existente o al menos ser compatible con ello.** Moult y yorik insisten en colaborar con Bonsai y FreeCAD mediante IFC en vez de duplicar. Fuentes: OSArch 39 y buildingSMART 2530 (✅).
6. **Mantener el IFC nativo y guardar lo propio en psets que respeten el esquema.** Bonsai guarda escaleras, barandillas y planos como JSON en psets `bbim_`; la comunidad propone convenciones compartidas entre Bonsai y FreeCAD. Fuente: OSArch 2767 (✅).
7. **Probar el IFC generado en varios visores** (BIMVision, Solibri, That Open, Revit). Fuentes: OSArch 1197 y 2701 (✅).
8. **Proyecto pequeño, comprensible y medido.** Principios del manifiesto de LinesCAD: documentar cada cambio, medir antes y después de cada cambio, bajo consumo de recursos. Fuente: blog de Yorik (✅).
9. **Cuidar la incorporación del usuario**: proyecto de ejemplo, pantalla de guía, botón claro para probar. Fuente: Roometron en HN (✅).
10. **Para aprender IfcOpenShell**: ejemplos de código de la documentación y de la wiki de OSArch, y el tutorial IfcOpenHouse. ⚠️ (comentarios de OSArch vistos solo por resumen: https://community.osarch.org/discussion/comment/18938/ y https://wiki.osarch.org/index.php?title=IfcOpenShell_code_examples).

---

## (f) Errores comunes

| Error | Qué pasa | Fuente |
|---|---|---|
| Hacer un muro como un cubo con la clase IfcWall | En IFC el muro se define por su eje y sus capas de material; el cubo "funciona" pero no es un muro bien formado | OSArch "Creat Wall Blender BIM missing operators" ⚠️ https://community.osarch.org/discussion/1964/ |
| Mover la ventana y olvidar la abertura | La ventana y el hueco (IfcOpeningElement) son entidades distintas; hay que mover las dos | OSArch "ifcopenshell (Python): change wall and window geometries" ⚠️ https://community.osarch.org/discussion/comment/17922/ |
| Crear la abertura sin la relación correcta | Sin IfcRelVoidsElement el hueco se ve en algunos visores pero no se reconoce como abertura; se aconseja hacerla algo más gruesa que el muro para evitar errores numéricos | OSArch "IfcOpenShell: Create openings in walls with arbitrary shapes" ⚠️ https://community.osarch.org/discussion/1246 |
| Usar booleanas de Blender en vez de las de IFC | Los modificadores de Blender no pasan al IFC; Bonsai genera el muro desde su eje con IfcOpenShell | OSArch "BlenderBIM: Simple modification of geometry in existing IFC" ⚠️ https://community.osarch.org/discussion/713 |
| Booleanas CSG en el navegador sobre mallas pesadas | Lentitud o cuelgue por memoria; mejor extruir perfiles con huecos | Foro three.js ⚠️ (ver b.10) |
| Confiar en un solo visor | Cada motor puede dibujar distinto las uniones y aberturas | OSArch 1197 ✅ |
| Demasiados objetos en Blender | Por encima de unos 30.000 empieza a sufrir; 60.000-80.000 inutilizable | OSArch 2821 ✅ |
| Librería web sin atributos inversos | No se pueden hacer ediciones que recorran relaciones del IFC | OSArch 1089 ✅ (estado de 2022) |
| Inventar un formato propio "casi IFC" | Se pierde la interoperabilidad, que es la razón de usar IFC | OSArch 2767 ✅ |
| Tutoriales que quedan viejos | La interfaz cambia y los menús ya no coinciden; el usuario nuevo se pierde | OSArch 2838 ✅ |
| Depender de una sola persona | El BIM de FreeCAD perdió a su creador como mantenedor | FCB Lounge y r/FreeCAD ✅ |
| Fricción de pago y de primer uso | Los usuarios se van antes de ver el valor | HN Roometron ✅ |
| Desarrolladores que nunca fueron usuarios | Un comentario sobre CAD electrónico lo señala como causa de malas herramientas | HN, comentario de "specialist" ⚠️ (solo fragmento) https://news.ycombinator.com/item?id=27424327 |
| Compatibilidad entre versiones de Blender | Add-ons de arquitectura (Archipack) se rompían con versiones nuevas de Blender | OSArch ⚠️ https://community.osarch.org/discussion/comment/12931/ |

---

## Qué aprendemos para BIM Simple

Lo que sigue es mi lectura de las fuentes; donde es inferencia mía lo digo.

1. **La meta "nivel Revit/ArchiCAD" es enorme, y la comunidad lo dice sin rodeos.** Las cifras de HN (10 millones y diez años, o 50 millones) son conjeturas, pero los hechos van en la misma línea: Bonsai, con un equipo activo y años de trabajo, se declara todavía en alfa (marzo de 2025), y el creador del BIM de FreeCAD empieza de cero algo más pequeño (2026). Para BIM Simple, el camino realista es el que ya marca el MVP: pocos elementos (pisos, muros, losas, columnas) muy bien hechos, en vez de abarcar mucho.

2. **El hueco más citado no es el 3D, son los planos.** Desde 2020 (hilo argentino) hasta 2026 (r/askarchitects, Qonic en r/bim), lo que falta en las herramientas libres y web es la documentación 2D: hojas, grosores de línea y vínculo modelo-plano. Para un arquitecto que viene de ArchiCAD, ese es el punto que decidirá si usa el programa.

3. **Nadie en la comunidad recomienda escribir un lector IFC ni un núcleo geométrico propio.** IfcOpenShell es la base común (FreeCAD, Bonsai, LinesCAD, xeokit, el futuro Bonsai Viewer). That Open/web-ifc tiene buena fama para ver modelos en la web y solo desde la versión 3.2 de octubre de 2025 ofrece API de edición; hay poca experiencia publicada de autoría con ella (fuente: noticia de osarch.org, https://osarch.org/2025/10/23/that-open-engine-3-2-open-modeling/, ⚠️ solo resumen). xBIM es razonable solo si se elige .NET en Windows.

4. **Blender + Bonsai es el camino más corto hasta algo que funciona, pero tiene techo de interfaz.** Los propios desarrolladores de Bonsai dicen que la interfaz de Blender es mala para tablas, Gantt, BCF y maquetación de planos, y por eso hicieron una interfaz web aparte y empiezan un visor fuera de Blender. Hay además un límite práctico de objetos (unos 30.000) y la GPL es obligatoria para todo código que use `bpy`. Inferencia: si BIM Simple sigue en Blender, conviene que la lógica (crear muros, losas, pisos) viva en funciones de IfcOpenShell separadas de la interfaz de Blender, como hace Bonsai, para poder cambiar de "carcasa" más adelante.

5. **Si se quiere programa propio, el precedente más cercano es LinesCAD**, no Electron. Yorik eligió Python + Qt + Coin3D + IfcOpenShell, GPL, y su lista de dificultades (visor rápido, deshacer/rehacer, copiar/pegar, árbol de objetos, DXF, instaladores) es una buena lista de trabajo para estimar la opción (b). No encontré en la comunidad experiencias publicadas de un autor BIM con Electron + Three.js + IfcOpenShell; el ejemplo web más serio (Arcol) tuvo que escribir su propio núcleo en Rust/WASM, y IfcOpenShell en el navegador vía Pyodide sigue siendo una demostración pesada.

6. **Web frente a escritorio.** La web gana en acceso sin instalar y en colaboración; pierde en modelos grandes (memoria del navegador), en la latencia del ratón para dibujo preciso y en confianza ("¿y si el proveedor desaparece?"). Inferencia: para un arquitecto que trabaja solo o en un estudio pequeño, escritorio es más seguro al principio; la web puede venir después como visor o para compartir.

7. **Licencias y negocio.** Cualquier código que use Blender (`bpy`) es GPL: se puede vender, pero el comprador puede redistribuirlo, así que el negocio real es soporte, actualizaciones, formación o servicios. IfcOpenShell es LGPL, lo que permite un programa propio con código cerrado si se enlaza como librería aparte (resumen del buscador; conviene verificarlo con el informe de librerías). That Open es MIT, lo más permisivo, pero en OSArch hay desconfianza sobre su modelo y su colaboración con el resto. Para un arquitecto que no programa, la opción de menos riesgo legal es asumir GPL desde el principio y ganar dinero con servicios, no con la venta de copias.

8. **Para no repetir errores conocidos:** muros por eje y capas (no cubos), aberturas con su relación IFC y con la ventana como relleno, nada de booleanas de Blender, IFC probado en dos o tres visores, psets propios que respeten el esquema, y tutoriales atados a una versión concreta del programa.

9. **El factor humano pesa tanto como la técnica.** Los proyectos libres dependen de pocas personas (FreeCAD BIM en 2026), los anuncios de herramientas nuevas en Reddit apenas reciben respuesta (Northsill, Open Monolith) y los arquitectos preguntan primero por compatibilidad con Revit y ArchiCAD. Inferencia: BIM Simple gana si se presenta como "ArchiCAD en español, sencillo, que guarda IFC limpio que abre cualquiera", y no como "un Revit nuevo".
