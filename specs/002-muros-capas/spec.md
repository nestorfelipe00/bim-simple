# Especificación de la función: Muros con capas que se pueden separar

**Carpeta**: `specs/002-muros-capas` (sin rama propia; se trabaja en `main`)

**Creada**: 2026-10-11

**Estado**: Implementada (2026-10-12)

**Pedido**: "quiero que los muros funcionen con capas independientes es decir que pueda modelarlos como
muros pero despues tengan la opcion de ser separados en capas diferentes". Es la función 2 del pedido
original (`PROMPT_BIM_SIMPLE.md`, puntos 2 a 4: caja de herramientas, herramienta Muro e Info Box),
ampliada con las capas y su separación.

## Aclaraciones

### Sesión 2026-10-11

- P: ¿Qué queda al "Separar en capas"? → R: Cada capa pasa a ser un muro independiente de una sola capa,
  en el mismo lugar; el muro compuesto deja de existir y se vuelve atrás con Ctrl+Z (FR-021).
- P: ¿Cómo se definen las estructuras compuestas? → R: Como en ArchiCAD: un catálogo con su propio
  diálogo para crearlas, renombrarlas y editarlas, con 3 de ejemplo; si se edita una, cambian todos los
  muros que la usan (FR-015).

## Escenarios de usuario y pruebas *(obligatorio)*

### Historia 1: Dibujar muros en la planta (Prioridad: P1)

El arquitecto elige la herramienta Muro en la caja de herramientas. En el Info Box revisa el espesor, la
altura y la línea de referencia. Dibuja en la planta con un clic al inicio y otro al final, encadenando
muros como en ArchiCAD. Los muros aparecen en la planta y en el 3D, unidos en las esquinas, dentro del
piso activo.

**Por qué esta prioridad**: sin muros no hay capas que separar. Es la herramienta básica de todo el
programa y ya sirve sola: permite dibujar la planta de un edificio y guardarla como IFC.

**Prueba independiente**: con un proyecto de pisos a 0,00, 3,00 y 6,00 y el Piso 1 activo, dibujar 4
muros que cierran un rectángulo de 6 × 4 m, guardar y volver a abrir: hay 4 muros, todos en el Piso 1,
con el espesor y la altura del Info Box, y las cuatro esquinas unidas.

**Escenarios de aceptación**:

1. **Dado** un proyecto abierto, **cuando** el usuario pulsa Muro en la caja de herramientas,
   **entonces** el Info Box muestra los valores del próximo muro: estructura "Básica", espesor 0,20,
   altura igual a la del piso activo y línea de referencia "Exterior".
2. **Dado** la herramienta Muro, **cuando** el usuario hace clic en un punto de la planta y después en
   otro, **entonces** se crea un muro entre los dos puntos y empieza el siguiente muro en el último
   punto.
3. **Dado** un muro empezado, **cuando** el usuario mueve el ratón, **entonces** ve la forma del muro y
   su longitud siguiendo al ratón.
4. **Dado** un muro empezado, **cuando** mantiene Shift, **entonces** la dirección queda fija en un
   múltiplo de 45°.
5. **Dado** un muro empezado, **cuando** escribe 4,5 y pulsa Enter, **entonces** se crea un muro de
   4,50 m en la dirección del ratón.
6. **Dado** el cursor cerca del extremo de un muro existente o de un punto de la grilla, **entonces** el
   cursor se pega a ese punto y lo señala.
7. **Dado** una cadena de muros, **cuando** pulsa Esc o hace clic derecho, **entonces** la cadena
   termina; **cuando** hace clic en el primer punto de la cadena, **entonces** la cadena se cierra y
   termina.
8. **Dado** dos muros encadenados, o un muro que empieza en el extremo de otro, **entonces** la esquina
   queda cerrada, sin huecos ni superposiciones, en la planta y en el 3D.

---

### Historia 2: Muros compuestos por capas (Prioridad: P2)

El arquitecto elige en el Info Box una estructura compuesta, por ejemplo "Muro exterior 30" (revoque,
ladrillo, aislación y revoque). Dibuja el muro como uno solo, pero el muro muestra sus capas en la planta
y en el 3D, cada una con el color de su material.

**Por qué esta prioridad**: es lo que pidió el usuario: dibujar muros que ya traen sus capas, como las
estructuras compuestas de ArchiCAD.

**Prueba independiente**: dibujar un muro con una estructura de 3 capas, guardar y abrir el archivo en
otro programa BIM: es un solo muro con 3 capas de material, en el orden y con los espesores definidos, y
su espesor total es la suma de las capas.

**Escenarios de aceptación**:

1. **Dado** la herramienta Muro, **cuando** el usuario elige una estructura compuesta en el Info Box,
   **entonces** el espesor muestra la suma de sus capas, no se puede editar, y el próximo muro usa esa
   estructura.
2. **Dado** un muro compuesto dibujado, **entonces** la planta muestra las líneas que separan sus capas
   y cada capa con el color de su material, y el 3D muestra cada capa con su color.
3. **Dado** un contorno dibujado en sentido horario con línea de referencia "Exterior", **entonces** la
   primera capa de la estructura queda del lado de afuera del contorno.
4. **Dado** el diálogo "Estructuras compuestas", **cuando** el usuario crea una estructura nueva con
   sus capas, **entonces** aparece en la lista del Info Box y se puede dibujar con ella; **cuando**
   edita una estructura que usan muros ya dibujados, **entonces** esos muros cambian sus capas y su
   espesor, y su línea de referencia queda en el mismo lugar.
5. **Dado** un muro compuesto guardado, **cuando** se vuelve a abrir el archivo, **entonces** el muro
   tiene la misma estructura, con las mismas capas, materiales y espesores.

---

### Historia 3: Separar un muro en capas (Prioridad: P3)

El arquitecto selecciona con la Flecha uno o varios muros compuestos y pulsa "Separar en capas". Desde
ese momento cada capa se puede trabajar por separado: por ejemplo, subir el revestimiento exterior hasta
el parapeto o borrar el revoque interior.

**Por qué esta prioridad**: es la parte nueva del pedido. Depende de las historias 1 y 2: hacen falta
muros compuestos para separarlos.

**Prueba independiente**: dibujar un muro de 4 capas y separarlo: quedan 4 muros independientes de una
sola capa, cada uno con el material y el espesor de su capa; nada se mueve en pantalla y el volumen total
no cambia. Ctrl+Z vuelve al muro compuesto. Al guardar y abrir en otro programa BIM, se ven 4 muros.

**Escenarios de aceptación**:

1. **Dado** un muro compuesto, **cuando** el usuario hace clic en él con la Flecha, **entonces** queda
   resaltado en la planta y en el 3D, y el Info Box muestra sus datos y el botón "Separar en capas".
2. **Dado** un muro compuesto seleccionado, **cuando** pulsa "Separar en capas", **entonces** el muro
   compuesto desaparece y en su lugar quedan tantos muros de una sola capa como capas tenía, cada uno
   seleccionable por separado.
3. **Dado** un muro separado, **entonces** cada capa queda en el mismo piso, con la misma altura y la
   misma longitud, y en las esquinas conserva la forma que tenía dentro del muro: en pantalla nada se
   mueve.
4. **Dado** varios muros compuestos seleccionados, **cuando** pulsa "Separar en capas", **entonces** se
   separan todos en un solo paso.
5. **Dado** un muro recién separado, **cuando** pulsa Ctrl+Z, **entonces** vuelve el muro compuesto tal
   como estaba; Ctrl+Y vuelve a separarlo.
6. **Dado** un muro de una sola capa seleccionado, **entonces** "Separar en capas" está desactivado.

---

### Historia 4: Seleccionar, cambiar y borrar muros (Prioridad: P4)

Con la Flecha, el arquitecto selecciona uno o varios muros, incluidas las capas separadas. En el Info Box
les cambia la altura o la estructura, y con Supr los borra. Todo se puede deshacer.

**Por qué esta prioridad**: sin poder cambiar y borrar, separar las capas no sirve para mucho; también
corrige errores de dibujo.

**Prueba independiente**: separar un muro de 3 capas, seleccionar solo la capa exterior y cambiar su
altura a 3,60: solo esa capa cambia. Borrar la capa interior: quedan 2. Guardar y volver a abrir: igual.

**Escenarios de aceptación**:

1. **Dado** la Flecha activa, **cuando** el usuario hace clic en un muro, **entonces** solo ese muro
   queda seleccionado; con Shift + clic agrega o quita muros de la selección; un clic en un lugar vacío
   o Esc deja todo sin seleccionar.
2. **Dado** varios muros seleccionados con distinta altura, **entonces** el Info Box muestra la altura
   como "varios"; **cuando** el usuario escribe una altura, **entonces** todos los seleccionados pasan a
   tenerla.
3. **Dado** un muro seleccionado, **cuando** el usuario elige otra estructura en el Info Box,
   **entonces** el muro cambia sus capas y su espesor y su línea de referencia queda en el mismo lugar.
4. **Dado** muros seleccionados, **cuando** pulsa Supr, **entonces** se borran.
5. **Dado** cualquiera de las acciones anteriores, **cuando** pulsa Ctrl+Z, **entonces** se deshace;
   con Ctrl+Y se rehace.

---

### Casos límite

- **Dos clics en el mismo punto**, o un muro de menos de 1 cm: no se crea ningún muro y la cadena sigue.
- **Longitud escrita igual a cero, negativa o que no es un número**: no se acepta y se sigue dibujando.
- **Espesor o altura iguales a cero o negativos**: no se aceptan y se mantiene el valor anterior.
- **Estructura sin capas, o capa de espesor cero o negativo**: no se acepta. Toda estructura tiene al
  menos una capa.
- **Dos estructuras con el mismo nombre**: no se acepta; el diálogo pide otro nombre.
- **Borrar una estructura que usan muros**: no se permite; el diálogo avisa cuántos muros la usan. Una
  estructura sin muros se borra sin preguntar.
- **Editar una estructura que usan muros**: todos esos muros cambian a la vez; se deshace con Ctrl+Z.
- **Separar un muro que tiene una estructura**: la estructura sigue en el catálogo aunque ya no la use
  ningún muro.
- **Cambiar de piso activo mientras se dibuja**: la cadena termina; los muros ya creados quedan en el
  piso donde se dibujaron.
- **Cambiar la altura de un piso después de dibujar sus muros**: los muros conservan su altura; no
  siguen la altura del piso.
- **Mover o borrar un piso con muros**: como en la función 001, los muros se mueven o se borran con su
  piso.
- **Separar un muro unido en una esquina a otro muro compuesto**: el otro muro no cambia; las capas
  separadas conservan la forma que tenían en la esquina. Si después se cambia la estructura o el espesor
  de ese otro muro, su extremo en esa esquina queda recto, como en ArchiCAD cuando se borra un muro de
  una esquina (research R10).
- **Dibujar desde el extremo de una capa separada que tiene su esquina cortada**: el muro nuevo llega a
  tope, sin unirse, para no perder el corte de esa capa (research R10).
- **Dibujar desde una esquina donde ya se unen dos muros**: el muro nuevo llega a tope, sin unirse, y la
  esquina existente no cambia. Cada extremo de un muro admite una sola unión; las uniones en T y los
  cruces llegan después (research R4).
- **Muros de otros programas con capas de material en el IFC**: se ven con sus capas y se pueden
  seleccionar, cambiar y separar. Si su línea de referencia no es exterior, centro ni interior, el Info
  Box la muestra como "Otra" y solo se cambian su altura y, si es de una capa, su material.
- **Muros de otros programas sin capas** (o con formas que BIM Simple no edita, como muros curvos o con
  perfil): se ven y se conservan al guardar; se pueden seleccionar y borrar, pero no separar ni cambiar
  de estructura, y el Info Box lo explica.

## Requisitos *(obligatorio)*

### Requisitos funcionales

**Caja de herramientas e Info Box**

- **FR-001**: La caja de herramientas propia, vertical y a la izquierda de la planta, tiene iconos
  propios para **Flecha** (seleccionar) y **Muro**, con su nombre al pasar el ratón. Hay una sola
  herramienta activa y se distingue a simple vista. Al abrir o crear un proyecto queda activa la Flecha.
  Losa y Columna llegan con la función 3.
- **FR-002**: El **Info Box**, una barra horizontal debajo de los menús como en ArchiCAD, muestra los
  valores que usará el próximo elemento de la herramienta activa. Con la Flecha y muros seleccionados,
  muestra y cambia los valores de la selección.
- **FR-003**: Valores del Muro en el Info Box:
  - estructura: "Básica" o una estructura compuesta;
  - material y espesor, editables solo en la Básica (en una compuesta, el espesor es la suma de sus
    capas);
  - altura;
  - línea de referencia: Exterior, Centro o Interior.

  Valores por defecto: Básica, material "Hormigón", espesor 0,20, altura igual a la del piso activo y
  línea de referencia Exterior. Las medidas se muestran en metros con dos decimales y se escriben con
  coma o con punto.
- **FR-004**: Los valores que el usuario cambia para la herramienta se mantienen para los muros
  siguientes mientras el programa esté abierto. Mientras el usuario no cambie la altura, la altura es la
  del piso activo.

**Dibujo**

- **FR-005**: Un muro se dibuja con un clic en el inicio y otro en el final. Los muros se encadenan: el
  final de uno es el inicio del siguiente.
- **FR-006**: Mientras se dibuja se ve la forma del muro con su espesor y su longitud, siguiendo al
  ratón.
- **FR-007**: Escribir un número y pulsar Enter crea el muro con esa longitud en la dirección del ratón.
- **FR-008**: Con Shift, la dirección del muro queda fija en un múltiplo de 45° respecto de los ejes de
  la planta.
- **FR-009**: Imán: a menos de 10 píxeles, el cursor se pega a los extremos de los muros del piso activo
  y, si no hay ninguno cerca, a los puntos de la grilla. La planta muestra una grilla con líneas cada
  1,00 m y el imán de la grilla actúa cada 0,10 m. El punto de imán se señala en pantalla.
- **FR-010**: La cadena termina con Esc o con clic derecho, o se cierra y termina con un clic en su
  primer punto. La herramienta Muro sigue activa.
- **FR-011**: Los muros encadenados, y los que empiezan o terminan en el extremo de otro muro, quedan
  unidos en la esquina, sin huecos ni superposiciones, en la planta y en el 3D. En los muros compuestos,
  todas las capas se cortan en la misma esquina.
- **FR-012**: La línea de referencia es la línea que se dibuja:
  - con **Exterior**, es la cara exterior del muro: la primera capa la toca y el muro crece hacia la
    derecha del sentido de dibujo;
  - con **Interior**, es la cara interior: la última capa la toca y el muro crece hacia la izquierda;
  - con **Centro**, es el eje del muro.

  Así, un contorno dibujado en sentido horario queda con la primera capa afuera en los tres casos.
- **FR-013**: Cada muro es un muro IFC real (`IfcWall`) contenido en el piso activo, con la base a la
  cota del piso y la altura, el espesor y las capas del Info Box.
- **FR-014**: Cada muro creado se deshace con Ctrl+Z y se rehace con Ctrl+Y, también desde el menú
  Edición.

**Estructuras compuestas y materiales**

- **FR-015**: Una estructura compuesta tiene un nombre y una lista ordenada de capas, de exterior a
  interior. Cada capa tiene material y espesor mayor que cero, y toda estructura tiene al menos una
  capa. Su espesor es la suma de sus capas. Las estructuras forman un **catálogo**, como en ArchiCAD:
  - el diálogo "Estructuras compuestas" se abre desde el menú **Opciones > Estructuras compuestas…** y
    desde un botón junto a la lista de estructuras del Info Box;
  - en él se crean, duplican, renombran y borran estructuras, y en cada una se agregan, quitan y
    reordenan capas y se cambian su material y su espesor, viendo el espesor total;
  - los nombres no se repiten; una estructura que usan muros no se puede borrar;
  - al aceptar los cambios de una estructura, todos los muros que la usan cambian sus capas y su
    espesor, con su línea de referencia en el mismo lugar; es un solo paso de deshacer;
  - un proyecto nuevo trae 3 estructuras de ejemplo (Supuestos).
- **FR-016**: Cada material tiene nombre y color. BIM Simple trae una lista inicial: Hormigón, Ladrillo,
  Bloque de hormigón, Revoque, Aislación, Placa de yeso y Madera. En el diálogo "Estructuras compuestas"
  se pueden agregar materiales con nombre y color; los nombres no se repiten.
- **FR-017**: En la planta, cada muro compuesto muestra las líneas que separan sus capas y cada capa
  rellena con el color de su material. En el 3D, cada capa se ve con el color de su material.
- **FR-018**: Las capas se guardan en el IFC como capas de material del muro, en orden, con su material
  y su espesor, de modo que otro programa BIM muestra las mismas capas. La estructura compuesta queda
  guardada con su nombre, compartida por los muros que la usan, y reaparece al volver a abrir el
  archivo.

**Separar en capas**

- **FR-019**: "Separar en capas" está disponible en el Info Box cuando hay seleccionado al menos un muro
  de dos o más capas. Se hace con un clic desde la selección y separa todos los muros compuestos
  seleccionados en un solo paso.
- **FR-020**: Cada capa separada queda en el mismo piso, con la misma base, altura, inicio y final que
  el muro original, exactamente donde estaba la capa, y conserva en las esquinas la forma que tenía.
  Cada capa conserva su material y su espesor. La suma de los volúmenes de las capas es igual al volumen
  del muro original.
- **FR-021**: Al separar, cada capa pasa a ser un **muro independiente** de estructura Básica, con el
  material y el espesor de su capa, y el muro compuesto deja de existir. Cada muro nuevo es un muro IFC
  real contenido en el piso, que se selecciona, cambia y borra por su cuenta (Historia 4). Volver a unir
  capas en un muro compuesto no forma parte de esta función; se vuelve atrás con Ctrl+Z.
- **FR-022**: Separar se deshace con Ctrl+Z, que devuelve el muro compuesto tal como estaba.

**Selección y cambios**

- **FR-023**: Con la Flecha, un clic sobre un muro, en la planta o en el 3D, lo selecciona. Shift + clic
  lo agrega a la selección o lo quita. Un clic en un lugar vacío o Esc deja todo sin seleccionar. Los
  muros seleccionados se resaltan en las dos vistas.
- **FR-024**: Con muros seleccionados, el Info Box muestra su estructura, espesor, altura y línea de
  referencia. Si los seleccionados tienen valores distintos, el campo muestra "varios". Lo que el usuario
  cambia se aplica a todos los seleccionados.
- **FR-025**: Se puede cambiar la altura y la estructura de los muros seleccionados y, en los de
  estructura Básica, también su material y su espesor. Al cambiar la estructura o el espesor, la línea
  de referencia queda en el mismo lugar y el muro cambia sus capas y su espesor.
- **FR-026**: Supr borra los muros seleccionados.
- **FR-027**: Cambiar y borrar muros se deshace con Ctrl+Z y se rehace con Ctrl+Y.

**Archivo y compatibilidad**

- **FR-028**: Al guardar y volver a abrir, cada muro reaparece con la misma posición, espesor, altura,
  estructura, capas, materiales, uniones y piso.
- **FR-029**: Los muros que BIM Simple no puede editar se ven y se conservan sin cambios al guardar
  (casos límite).

**Textos**

- **FR-030**: Todos los textos visibles de esta función están en español y usan los términos de
  ArchiCAD: caja de herramientas, Flecha, Muro, Info Box, estructura compuesta, capa, material, línea de
  referencia, Separar en capas. La barra de menús suma el menú **Opciones** (entre Edición y Ayuda), con
  "Estructuras compuestas…".

### Entidades clave

- **Muro**: tramo recto y vertical entre un inicio y un final, contenido en un piso. Tiene altura, línea
  de referencia y una estructura (Básica o compuesta). Puede estar unido en sus extremos a otros muros.
- **Estructura compuesta**: nombre y lista ordenada de capas, de exterior a interior. La comparten los
  muros que la usan.
- **Catálogo de estructuras compuestas**: las estructuras del proyecto, con nombres únicos. Se guarda en
  el IFC con el proyecto.
- **Capa**: material y espesor dentro de una estructura.
- **Material**: nombre y color.
- **Herramienta activa**: Flecha o Muro. El Info Box muestra sus valores para el próximo elemento.
- **Selección**: los muros elegidos con la Flecha. El Info Box muestra y cambia sus valores.

## Criterios de éxito *(obligatorio)*

### Resultados medibles

- **SC-001**: Un arquitecto que conoce ArchiCAD dibuja, sin ayuda y la primera vez, 4 muros que cierran
  un rectángulo de 6 × 4 m con las esquinas unidas, en menos de 1 minuto.
- **SC-002**: En un rectángulo de 6 × 4 m dibujado en sentido horario con línea de referencia Exterior y
  muros de 0,20 m, la superficie de los muros en la planta es 3,84 m² (6 × 4 − 5,60 × 3,60), con una
  diferencia menor al 0,1 %: las esquinas no tienen huecos ni superposiciones.
- **SC-003**: Separar en capas los muros seleccionados toma 1 clic. Después de separar, cada capa
  conserva su material y su espesor (diferencia menor a 1 mm) y la suma de los volúmenes es igual al
  volumen del muro original (diferencia menor al 0,1 %).
- **SC-004**: El 100 % de los muros reaparecen iguales al cerrar y volver a abrir el archivo
  (diferencia menor a 1 mm en posición, espesor y altura; mismas capas y materiales).
- **SC-005**: Todo archivo guardado pasa la validación del esquema IFC4 sin errores y se abre en al
  menos otro programa BIM, que muestra los muros con sus capas y materiales.
- **SC-006**: Cada muro aparece en la planta y en el 3D en menos de 0,2 segundos después del clic, en un
  piso con 200 muros. La forma del muro sigue al ratón sin retraso visible mientras se dibuja.
- **SC-007**: Un arquitecto que conoce ArchiCAD crea en el catálogo una estructura de 3 capas y dibuja un
  muro con ella en menos de 2 minutos, sin ayuda.

## Supuestos

- Usuario: arquitecto que conoce ArchiCAD. Depende de la función 001: proyecto, pisos, piso activo,
  deshacer y guardar.
- La base del muro está a la cota del piso. Su altura es un número fijo: no queda ligada al piso de
  arriba. El desfase inferior y la unión con el piso de arriba llegan después.
- Muros rectos, verticales y de espesor constante. Quedan fuera: muros curvos, inclinados o con perfil,
  puertas y ventanas, uniones en T y cruces (un muro puede llegar a otro, pero no se recortan), y
  prioridades de capas en las uniones como en ArchiCAD: en esta función todas las capas se cortan en la
  misma esquina.
- Quedan fuera: mover, estirar, copiar y girar muros, y cambiar la línea de referencia de un muro ya
  dibujado.
- La planta sigue siendo una vista desde arriba sin plano de corte (función 001). Los colores de cada
  capa entran en esta función; los rayados de material llegan con los planos 2D.
- Estructuras de ejemplo: "Muro exterior 30" (Revoque 0,02 · Ladrillo 0,20 · Aislación 0,05 · Revoque
  0,03), "Tabique 15" (Revoque 0,015 · Ladrillo 0,12 · Revoque 0,015) y "Muro de hormigón 25" (Hormigón
  0,20 · Aislación 0,05).
- Cada capa separada lleva como nombre el del muro original seguido de su material. Su línea de
  referencia es Exterior, sobre su propia cara exterior.
- Las estructuras de ejemplo se agregan a los proyectos nuevos. Un IFC abierto de otro programa trae las
  suyas, si tiene; las de ejemplo se pueden crear a mano en el catálogo.
- Cada muro dibujado es un paso de deshacer.
