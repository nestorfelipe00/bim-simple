# Especificación de la función: Programa BIM Simple y navegador de pisos

**Carpeta**: `specs/001-espacio-trabajo-pisos` (sin rama propia; se trabaja en `main`)

**Creada**: 2026-10-11 · **Revisada**: 2026-10-11 (constitución v3.0.0: programa propio sin Blender)

**Estado**: Implementada (2026-10-11)

**Pedido**: "Espacio de trabajo y navegador de pisos de BIM Simple (primera de tres funciones;
Muro/Info Box y Losa/Columna van en especificaciones aparte). Pantalla partida en planta 2D del
piso activo y vista 3D; menús sobrantes ocultos; proyecto nuevo IFC4 en metros sin reiniciar;
abrir, guardar y guardar como; navegador de pisos con nombre, cota y altura para agregar,
renombrar, borrar y activar pisos." Aclarado después: BIM Simple es un programa propio, sin
Blender, pensado para venderse cerrado. Al cerrar la función (T056), el usuario decidió que sea
software libre bajo GPL-3.0-or-later, como Blender, con el repositorio público.

## Aclaraciones

### Sesión 2026-10-11

- P: ¿Cómo se relacionan la cota y la altura de los pisos? → R: Como en ArchiCAD: la altura es la
  distancia al piso de arriba, y cambiarla desplaza los pisos superiores (FR-016).
- P: ¿Qué pasa al borrar un piso con elementos? → R: Aviso con la cantidad de elementos; si se
  acepta, se borran el piso y sus elementos, y se puede deshacer (FR-017).
- P: ¿Cómo se entra en BIM Simple? → R: Es un programa propio con su icono, que abre directamente
  en su pantalla (FR-001).
- P: ¿Sobre qué base se construye? → R: Programa propio de escritorio, sin Blender (constitución
  v3.0.0, Principio III), validado con un prototipo (`docs/base-tecnologica/prototipo/`).
- P: ¿Cómo se activa un piso? → R: Con doble clic en su fila, como en ArchiCAD. La base nueva lo
  permite (FR-020).
- P: ¿Cómo se navega el 3D? → R: Al estilo ArchiCAD/Revit, como en el prototipo que el usuario
  probó y aprobó (FR-025).
- P: ¿Dónde se informan las licencias que exige la constitución (Principio VI)? → R: En "Ayuda >
  Acerca de BIM Simple" (FR-003), aprobado tras el análisis de coherencia.
- P: ¿Qué pasa con los datos del programa al desinstalar? → R: Se borran también (registros y caché
  en `%APPDATA%\BIM Simple`), para cumplir SC-005; los proyectos del usuario no están ahí.

## Escenarios de usuario y pruebas *(obligatorio)*

### Historia 1: Abrir BIM Simple, empezar un proyecto y guardarlo (Prioridad: P1)

El arquitecto abre BIM Simple desde su acceso directo, como cualquier otro programa. Aparece su
pantalla de trabajo: planta a la izquierda, 3D a la derecha y el panel de BIM Simple. Pulsa
"Nuevo proyecto" y obtiene un proyecto con su edificio y una Planta Baja a cota 0,00. Lo guarda
como archivo `.ifc`.

**Por qué esta prioridad**: sin programa ni proyecto no hay dónde dibujar, y sin guardar no queda
nada. Es lo mínimo que ya sirve: un archivo IFC válido con la estructura del edificio.

**Prueba independiente**: instalar BIM Simple, abrirlo desde el acceso directo, crear un proyecto,
guardarlo y validar el archivo: contiene Proyecto > Sitio > Edificio > Planta Baja a 0,00, pasa la
validación IFC4 y se abre en otro programa BIM.

**Escenarios de aceptación**:

1. **Dado** BIM Simple instalado, **cuando** el usuario lo abre desde su acceso directo,
   **entonces** ve una ventana con el título e icono de BIM Simple, la barra de menús propia en
   español, la planta a la izquierda, la vista 3D a la derecha y el panel de BIM Simple.
2. **Dado** la pantalla sin proyecto, **cuando** pulsa "Nuevo proyecto", **entonces** se crea
   Proyecto > Sitio > Edificio > Planta Baja (cota 0,00, altura 3,00) y la Planta Baja queda activa.
3. **Dado** un proyecto nunca guardado, **cuando** pulsa "Guardar IFC", **entonces** se abre el
   diálogo de Windows para elegir carpeta y nombre, y se escribe un archivo `.ifc`.
4. **Dado** un proyecto ya guardado, **cuando** pulsa "Guardar IFC", **entonces** el archivo se
   actualiza en el mismo lugar sin preguntar.
5. **Dado** un proyecto con cambios sin guardar, **cuando** el usuario cierra la ventana con la X,
   **entonces** se le pregunta «¿Guardar cambios antes de cerrar?» con Guardar / No guardar / Cancelar.

---

### Historia 2: Organizar los pisos del edificio (Prioridad: P2)

El arquitecto usa el navegador de pisos para armar la estructura vertical del edificio: agrega
pisos, les cambia el nombre, ajusta cota y altura, y borra los que sobran.

**Por qué esta prioridad**: casi todo edificio tiene más de un piso, y las funciones de dibujo que
vienen después necesitan los pisos ya armados.

**Prueba independiente**: con un proyecto nuevo, agregar dos pisos, renombrarlos, cambiar una
altura, borrar uno, guardar y volver a abrir: la lista muestra los mismos nombres, cotas y alturas.

**Escenarios de aceptación**:

1. **Dado** un proyecto con Planta Baja (0,00; altura 3,00), **cuando** pulsa "Agregar piso
   arriba", **entonces** aparece "Piso 1" a cota 3,00 con altura 3,00, encima en la lista.
2. **Dado** un proyecto con Planta Baja (0,00), **cuando** pulsa "Agregar piso abajo",
   **entonces** aparece "Sótano 1" a cota −3,00 con altura 3,00, debajo en la lista.
3. **Dado** un piso en la lista, **cuando** el usuario le cambia el nombre, **entonces** la lista
   y el IFC muestran el nombre nuevo.
4. **Dado** Planta Baja (0,00; 3,00), Piso 1 (3,00; 3,00) y Piso 2 (6,00; 3,00), **cuando** el
   usuario cambia la altura de la Planta Baja a 3,50, **entonces** el Piso 1 pasa a 3,50 y el
   Piso 2 a 6,50, con sus elementos.
5. **Dado** un piso con elementos, **cuando** el usuario lo borra, **entonces** ve un aviso con la
   cantidad de elementos y, si acepta, se borran el piso y sus elementos.
6. **Dado** cualquiera de las acciones anteriores, **cuando** el usuario pulsa Ctrl+Z,
   **entonces** la acción se deshace; con Ctrl+Y se rehace.

---

### Historia 3: Trabajar en un piso (Prioridad: P3)

El arquitecto activa un piso con doble clic en el navegador. La planta de la izquierda pasa a
mostrar solo ese piso, mientras la vista 3D sigue mostrando el edificio entero. Lo que se dibuje
después queda en ese piso. Recorre el modelo en 3D como en ArchiCAD.

**Por qué esta prioridad**: es la base del trabajo por plantas de ArchiCAD y lo que usarán las
herramientas de dibujo de las funciones siguientes.

**Prueba independiente**: con tres pisos que tengan algún elemento cada uno (por ejemplo, abriendo
un IFC que ya los tenga, porque las herramientas de dibujo llegan en la función 2), activar el
Piso 1: la planta muestra solo los elementos del Piso 1, la vista 3D muestra todos, y un elemento
creado a continuación queda contenido en el Piso 1.

**Escenarios de aceptación**:

1. **Dado** varios pisos, **cuando** el usuario hace doble clic en la fila de un piso,
   **entonces** ese piso queda marcado como activo y es el único activo.
2. **Dado** un piso activo, **entonces** la planta lo muestra visto desde arriba, sin perspectiva,
   y solo con sus elementos; la vista 3D muestra todos los pisos.
3. **Dado** un piso activo, **cuando** se crea un elemento nuevo, **entonces** queda contenido en
   ese piso, a su cota.
4. **Dado** un modelo en la vista 3D, **cuando** el usuario arrastra con el botón izquierdo sobre
   un elemento, **entonces** la vista gira alrededor de ese punto, sin saltos y sin pasar por
   debajo del suelo.

---

### Historia 4: Abrir un IFC existente (Prioridad: P4)

El arquitecto abre un `.ifc` hecho antes con BIM Simple o con otro programa BIM, trabaja sobre sus
pisos y lo guarda con otro nombre.

**Por qué esta prioridad**: permite retomar el trabajo de otro día y recibir modelos de terceros;
se apoya en las historias anteriores.

**Prueba independiente**: abrir un IFC con tres pisos hecho en otro programa: la lista muestra sus
tres pisos con nombre, cota y altura; "Guardar IFC como…" crea un archivo nuevo y deja el original
sin cambios.

**Escenarios de aceptación**:

1. **Dado** la pantalla de BIM Simple, **cuando** el usuario elige "Abrir IFC…" y un archivo
   válido, **entonces** el navegador muestra sus pisos y queda activo el de cota más cercana a 0,00.
2. **Dado** un proyecto con cambios sin guardar, **cuando** elige "Nuevo proyecto", "Abrir IFC…" o
   "Salir", **entonces** se le pregunta Guardar / No guardar / Cancelar antes de seguir.
3. **Dado** un archivo dañado o que no es IFC, **cuando** intenta abrirlo, **entonces** ve un
   mensaje en español y el proyecto que tenía abierto sigue intacto.
4. **Dado** un proyecto abierto, **cuando** elige "Guardar IFC como…", **entonces** se escribe un
   archivo nuevo y los siguientes "Guardar IFC" van a ese archivo.

---

### Casos límite

- **Borrar el último piso**: no se permite; el proyecto siempre tiene al menos un piso.
- **Borrar el piso activo**: pasa a estar activo el piso inmediatamente inferior, o el superior si
  no hay ninguno debajo.
- **Nombre vacío**: no se acepta y se mantiene el nombre anterior. Se permiten nombres repetidos.
- **Dos pisos a la misma cota**: no puede ocurrir (FR-016).
- **Cota negativa** (sótanos): permitida.
- **Altura cero o negativa**: no se acepta y se mantiene el valor anterior.
- **IFC con varios edificios**: el navegador muestra los pisos del primer edificio y avisa que hay
  más edificios.
- **IFC sin edificio o sin pisos**: el navegador queda vacío con un mensaje explicativo; el modelo
  se ve igual en la vista 3D.
- **IFC con elementos que BIM Simple no edita** (puertas, ventanas, otros): se muestran en las
  vistas y se conservan al guardar.
- **El motor deja de responder**: el programa avisa en español, no se pierde el último archivo
  guardado y ofrece reiniciar el motor.
- **Abrir un `.ifc` con doble clic en el Explorador de Windows**: fuera de esta función; los
  archivos se abren desde "Abrir IFC…".

## Requisitos *(obligatorio)*

### Requisitos funcionales

**Programa y pantalla**

- **FR-001**: BIM Simple se abre como un programa propio, con su nombre e icono, desde un acceso
  directo en el escritorio y en el menú Inicio, y muestra directamente su pantalla de trabajo.
- **FR-002**: La pantalla se divide en dos vistas: a la izquierda la planta (vista desde arriba,
  sin perspectiva, solo del piso activo) y a la derecha la vista 3D con todo el edificio.
- **FR-003**: En la pantalla se ven: la barra de menús propia (Archivo, Edición y Ayuda), las dos
  vistas y el panel "BIM Simple" (datos del proyecto, navegador de pisos y acciones). No hay menús
  ni paneles ajenos a BIM Simple. La caja de herramientas propia llega con la función 2.
  - "Ayuda > Acerca de BIM Simple" muestra la versión, la licencia de BIM Simple (GPL-3.0-or-later,
    con el enlace a su código), las librerías que usa con sus licencias
    (IfcOpenShell bajo LGPL-3.0, con el enlace a su código fuente) y dónde están los textos de
    licencia (constitución, Principio VI).
- **FR-004**: El título de la ventana muestra el nombre del archivo, o "Proyecto sin guardar",
  seguido de "BIM Simple", con un asterisco cuando hay cambios sin guardar.
- **FR-005**: La instalación se hace en un solo paso, sin permisos de administrador, y crea los
  accesos directos. Para desinstalar basta con borrar la carpeta del programa y sus accesos
  directos. El programa no modifica nada fuera de su carpeta y de los archivos que guarda el
  usuario; otros programas instalados (por ejemplo, Blender) no cambian.
- **FR-006**: El programa arranca sin proyecto y con las vistas vacías; solo se muestran elementos
  que existen en el IFC abierto.

**Proyecto**

- **FR-007**: "Nuevo proyecto" crea un proyecto IFC4 en metros con la jerarquía Proyecto > Sitio >
  Edificio > Planta Baja (cota 0,00, altura 3,00) y deja la Planta Baja activa.
- **FR-008**: "Abrir IFC…" abre un archivo `.ifc` existente, muestra sus pisos y elementos y
  activa el piso de cota más cercana a 0,00.
- **FR-009**: "Guardar IFC" escribe en el archivo actual; si el proyecto nunca se guardó, actúa
  como "Guardar IFC como…", que abre el diálogo de Windows y escribe un archivo `.ifc`.
- **FR-010**: Si hay cambios sin guardar, "Nuevo proyecto", "Abrir IFC…", "Salir" y cerrar la
  ventana con la X preguntan antes «¿Guardar cambios antes de cerrar?» con Guardar / No guardar /
  Cancelar.
- **FR-011**: Si un archivo no se puede abrir, se muestra un mensaje en español que dice por qué,
  y el proyecto abierto no cambia.

**Navegador de pisos**

- **FR-012**: El navegador lista los pisos del edificio ordenados por cota, el más alto arriba,
  con nombre, cota y altura en metros con dos decimales. El piso activo se distingue a simple
  vista.
- **FR-013**: "Agregar piso arriba" crea un piso encima del más alto, con cota = cota del más alto
  + su altura, la misma altura que él y nombre "Piso N", donde N es la cantidad de pisos con cota
  mayor que 0,00 contando el nuevo.
- **FR-014**: "Agregar piso abajo" crea un piso debajo del más bajo, con cota = cota del más bajo
  − 3,00, altura 3,00 y nombre "Sótano N", donde N es la cantidad de pisos con cota menor que
  0,00 contando el nuevo.
- **FR-015**: El usuario puede cambiar el nombre, la cota y la altura de cualquier piso desde el
  navegador. Al moverse un piso, sus elementos se mueven con él.
- **FR-016**: Como en ArchiCAD, la altura de un piso es la distancia hasta el piso de arriba:
  - Cambiar la altura de un piso desplaza, en la misma medida, todos los pisos de arriba con sus
    elementos. El piso más alto no tiene ninguno encima, así que su altura se guarda tal cual.
  - Cambiar la cota de un piso desplaza ese piso y todos los de arriba en la misma medida. La
    altura del piso de abajo pasa a ser la nueva distancia entre ambos.
  - No se acepta una cota igual o menor que la del piso de abajo; los pisos nunca se superponen.
- **FR-017**: Al borrar un piso que contiene elementos aparece un aviso con la cantidad de
  elementos que se borrarán. Si el usuario acepta, se borran el piso y sus elementos. Un piso
  vacío se borra sin preguntar. Los pisos de arriba no se mueven: el piso de abajo pasa a tener
  como altura la distancia hasta el siguiente.
- **FR-018**: Agregar, renombrar, cambiar cota o altura y borrar pisos se pueden deshacer con
  Ctrl+Z y rehacer con Ctrl+Y, también desde el menú Edición.
- **FR-019**: Cada piso es un piso IFC real (`IfcBuildingStorey`) dentro del edificio. Su nombre,
  cota y altura quedan guardados en el IFC y reaparecen iguales al volver a abrirlo.

**Piso activo y vistas**

- **FR-020**: El usuario activa un piso con **doble clic** en su fila del navegador, como en
  ArchiCAD. Un clic simple solo lo selecciona para editarlo o borrarlo.
- **FR-021**: Siempre hay exactamente un piso activo mientras haya un proyecto abierto.
- **FR-022**: La planta muestra solo los elementos del piso activo; la vista 3D muestra todos los
  pisos.
- **FR-023**: Todo elemento que se cree a continuación (con las herramientas de las funciones
  siguientes) queda contenido en el piso activo.
**Textos**

- **FR-024**: Todos los textos visibles de esta función (título de la ventana, menús, botones,
  columnas, mensajes, confirmaciones y "Acerca de") están en español y usan los términos de
  ArchiCAD: piso, cota, altura, navegador.

**Navegación**

- **FR-025**: Navegación al estilo ArchiCAD/Revit:
  - En la vista 3D:
    - el botón izquierdo, o Mayús + botón central, gira alrededor del punto del modelo bajo el
      ratón;
    - el botón central o el derecho desplazan;
    - la rueda acerca y aleja hacia el ratón;
    - el movimiento es suave;
    - la vista no pasa por debajo del suelo ni se da vuelta.
  - En la planta: la rueda acerca y aleja hacia el ratón y el botón central desplaza; la planta
    no rota.
  - "Encuadrar" lleva cada vista a mostrar el modelo completo: la planta, el piso activo; el 3D,
    el edificio.

### Entidades clave

- **Programa BIM Simple**: la aplicación con su icono y accesos directos. Tiene una interfaz y un
  motor BIM que trabaja sobre el IFC.
- **Proyecto**: el archivo IFC abierto. Contiene un sitio, que contiene el edificio. Tiene un
  archivo de destino (vacío si nunca se guardó) y un estado "con cambios sin guardar".
- **Edificio**: contiene los pisos. BIM Simple trabaja con un edificio por proyecto.
- **Piso**: nombre, cota (metros, puede ser negativa) y altura (metros, mayor que cero; distancia
  al piso de arriba). Contiene elementos del modelo.
- **Piso activo**: el piso que muestra la planta y que recibe los elementos nuevos. Uno por
  proyecto.

## Criterios de éxito *(obligatorio)*

### Resultados medibles

- **SC-001**: Un arquitecto que nunca usó BIM Simple abre el programa, crea un proyecto, arma tres
  pisos con sus cotas y lo guarda en menos de 3 minutos, sin ayuda.
- **SC-002**: El 100 % de los pisos creados o modificados reaparecen con el mismo nombre, cota y
  altura al cerrar y volver a abrir el archivo.
- **SC-003**: Todo archivo guardado por BIM Simple pasa la validación del esquema IFC4 sin errores
  y se abre sin errores en al menos otro programa BIM.
- **SC-004**: Cada acción del navegador de pisos (agregar, editar, borrar, activar, deshacer) se
  ve reflejada en pantalla en menos de 0,2 segundos en un proyecto de 10 pisos.
- **SC-005**: Después de instalar, usar y desinstalar BIM Simple, no queda ningún cambio en la
  computadora fuera de los archivos que el usuario guardó.
- **SC-006**: Cada acción de esta función (nuevo, abrir, guardar, agregar, renombrar, cambiar cota
  o altura, borrar y activar piso) se hace con un máximo de 2 clics desde la pantalla principal,
  más la escritura de nombres o números cuando corresponda.
- **SC-007**: Desde el doble clic en el acceso directo hasta poder pulsar "Nuevo proyecto" pasan
  menos de 10 segundos.

## Supuestos

- Usuario: arquitecto que conoce ArchiCAD. Solo Windows 11.
- El archivo de trabajo es el `.ifc`; no hay un formato propio de proyecto.
- Altura por defecto de un piso: 3,00 m. Nombres por defecto: "Planta Baja", "Piso N", "Sótano N".
- Al borrar un piso, los de arriba no bajan (FR-017). Se eligió así para que borrar nunca mueva
  elementos de otros pisos; si en ArchiCAD funciona distinto y se prefiere ese comportamiento, se
  cambia en el plan.
- En esta función la planta es una vista desde arriba **sin plano de corte**. El corte a una
  altura, como en ArchiCAD, y el rayado por capas de material llegan con la función de planos 2D.
- La navegación aprobada es la del prototipo (`docs/base-tecnologica/prototipo/`).
- Fuera de esta función: herramientas de dibujo (muro, losa, columna), Info Box, iconos de la caja
  de herramientas, asociar archivos `.ifc` al programa, puertas, ventanas, cubiertas, escaleras,
  cortes, láminas y cómputos.
