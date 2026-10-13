# Prueba manual de BIM Simple (funciones 001 y 002)

Marca cada casilla cuando el resultado sea el esperado. Si algo falla, anota el número del paso y qué viste.
Son las partes B de las guías de validación de la [función 001](specs/001-espacio-trabajo-pisos/quickstart.md)
(secciones 1 a 6) y de la [función 002](specs/002-muros-capas/quickstart.md) (sección 7).

## 0. Antes de empezar

- Abre BIM Simple con el acceso directo **BIM Simple** del Escritorio o del menú Inicio. Antes de instalarlo
  también se puede abrir con `npm --prefix app start` desde la carpeta del proyecto.
- Para probar archivos de otros programas sirven los IFC de prueba de `app\test-output\fixtures\`. Los crea
  la prueba automática (`npm --prefix app test`):
  - `con_elementos.ifc`: 3 pisos con un muro en cada uno;
  - `otro_programa_mm.ifc`: 4 pisos, en milímetros;
  - `no_es_ifc.ifc`: un texto con extensión `.ifc`;
  - `muros_otro_programa.ifc`: muros como los haría otro programa (uno con capas, uno sin capas y uno recortado).

## 1. Arranque y pantalla

- [ ] Ten un cronómetro listo. Desde el doble clic en el acceso directo hasta que se puede pulsar
  **Nuevo proyecto** pasan menos de 10 segundos.
- [ ] La ventana y la barra de tareas muestran el icono de BIM Simple y el título "BIM Simple".
- [ ] Arriba solo están los menús **Archivo**, **Edición** y **Ayuda**.
- [ ] A la izquierda está la **planta**, al centro la **vista 3D** y a la derecha el panel **BIM Simple**.
- [ ] **Ayuda > Acerca de BIM Simple** muestra la versión, que BIM Simple es software libre bajo la GPL-3.0 o
  posterior (con el enlace a su código), las licencias de las librerías (IfcOpenShell bajo LGPL-3.0, con el
  enlace a su código) y dónde están los textos de las licencias.

## 2. Proyecto

- [ ] **Tiempo para armar un proyecto**: sin ayuda y con el cronómetro, crea un proyecto, arma tres pisos con
  sus cotas y guárdalo. Tiene que llevar menos de 3 minutos.
- [ ] **Clics por acción**: nuevo, abrir, guardar, agregar, editar, borrar y activar se hacen con 2 clics como
  máximo desde la pantalla principal, sin contar lo que se escribe.
- [ ] **Archivo > Nuevo proyecto** muestra un solo piso, **Planta Baja**, con cota 0,00, altura 3,00 y marcado
  con ●.
- [ ] El título dice "Proyecto sin guardar — BIM Simple".
- [ ] **Ctrl+S** en un proyecto nuevo abre el diálogo de Windows para elegir dónde guardar. Después de
  guardar, el título muestra el nombre del archivo y un nuevo **Ctrl+S** guarda sin preguntar.
- [ ] Al guardar aparece abajo, en el panel, "Guardado. Validación IFC4: 0 errores.".
- [ ] **Archivo > Guardar IFC como…** crea otro archivo, y el siguiente Ctrl+S guarda en ese.
- [ ] **Archivo > Abrir IFC…** con `no_es_ifc.ifc` muestra «No se pudo abrir «no_es_ifc.ifc»: no es un
  archivo IFC válido.» y el proyecto abierto sigue igual.
- [ ] **Abrir IFC…** con `otro_programa_mm.ifc` muestra 4 pisos (Subsuelo −2,80, Nivel 0 0,00, Nivel 1 3,20 y
  Nivel 2 6,00) y deja activo **Nivel 0**.
- [ ] El IFC que guardaste se abre sin errores en otro programa BIM, por ejemplo un visor IFC gratuito o
  ArchiCAD.

## 3. Pisos

Empieza con un proyecto nuevo.

- [ ] **Agregar piso arriba** dos veces: aparecen "Piso 1" a 3,00 y "Piso 2" a 6,00. El más alto queda
  arriba en la lista.
- [ ] **Agregar piso abajo**: aparece "Sótano 1" a −3,00.
- [ ] Un clic en **Planta Baja** y **Editar piso…**: cambia la altura a 3,50 (con coma) y pulsa Aceptar.
  Piso 1 pasa a 3,50 y Piso 2 a 6,50.
- [ ] **Editar piso…** en Piso 1 con cota 0,00: aparece «La cota debe ser mayor que la del piso de abajo
  («Planta Baja», 0,00 m).» y nada cambia.
- [ ] Abre `con_elementos.ifc`, selecciona **Piso 2** y pulsa **Borrar piso**. Aparece «El piso «Piso 2»
  tiene 1 elemento. Se borrarán junto con el piso.». Con **Cancelar** no se borra nada; con **Borrar**
  desaparecen el piso y su muro, también en el 3D.
- [ ] Con un solo piso, el botón **Borrar piso** queda desactivado.

## 4. Piso activo y navegación

Con `con_elementos.ifc` abierto:

- [ ] Un clic en un piso solo lo selecciona (fondo de color). El **doble clic** lo activa al instante: pasa a
  tener ● y la etiqueta de la planta dice "Planta — <nombre del piso>".
- [ ] La planta muestra solo el muro del piso activo; el 3D muestra todo el edificio.
- [ ] **Vista 3D**:
  - [ ] el botón izquierdo gira alrededor del punto que señalas, sin saltos;
  - [ ] el botón central o el derecho desplazan la vista;
  - [ ] la rueda acerca hacia donde está el ratón;
  - [ ] no se puede girar por debajo del suelo.
- [ ] **Planta**: la rueda acerca hacia el ratón, el botón central desplaza y la vista no gira.
- [ ] **Encuadrar** centra la planta en el piso activo y el 3D en todo el edificio.

## 5. Deshacer y salir

- [ ] Agrega un piso y pulsa **Ctrl+Z**: el piso desaparece. **Ctrl+Y** lo devuelve.
- [ ] Cambia una altura y pulsa **Ctrl+Z**: todos los pisos vuelven a su cota.
- [ ] Con cambios sin guardar, el título empieza con "* " y el panel dice "• Cambios sin guardar".
- [ ] Cierra con la **X** habiendo cambios: aparece «¿Guardar cambios antes de cerrar?».
  - [ ] **Cancelar** te deja en el programa.
  - [ ] **Guardar** guarda y cierra.
  - [ ] **No guardar** cierra sin guardar.

## 6. Instalación (solo con el instalador)

- [ ] El instalador no pide permiso de administrador.
- [ ] Quedan los accesos directos **BIM Simple** en el Escritorio y en el menú Inicio.
- [ ] Desinstalar desde **Configuración > Aplicaciones > Aplicaciones instaladas** (Agregar o quitar programas) no deja
  carpetas de BIM Simple en `%LOCALAPPDATA%\Programs`, `%APPDATA%` ni `%LOCALAPPDATA%`.

## 7. Muros con capas (función 002)

Empieza con **Archivo > Nuevo proyecto**.

### 7.1 Caja de herramientas e Info Box
- [ ] A la izquierda de la planta están la **Flecha** y el **Muro**, con iconos propios. Al pasar el ratón dicen
  "Flecha (seleccionar)" y "Muro".
- [ ] Al crear el proyecto queda activa la Flecha y arriba dice «Nada seleccionado…».
- [ ] Un clic en **Muro**: el Info Box muestra Estructura "Básica", Material "Hormigón", Espesor 0,20, Altura 3,00
  (la del piso) y Línea de referencia **Exterior**.

### 7.2 Dibujar
- [ ] **Tiempo**: con el cronómetro y sin ayuda, dibuja un rectángulo de 6 × 4 m en sentido horario en **menos de
  1 minuto**: un clic en cada esquina y un clic en la primera para cerrarlo.
- [ ] Las 4 esquinas quedan cerradas, sin huecos ni superposiciones, en la planta y en el 3D. Los muros quedan
  hacia adentro del rectángulo.
- [ ] Mientras dibujas ves el muro con su espesor (en azul) y su longitud junto al cursor.
- [ ] Con **Shift** el muro queda a 0°, 45° o 90°.
- [ ] Escribe `4,5` y pulsa **Enter**: se crea un muro de 4,50 m en la dirección del ratón.
- [ ] Cerca del extremo de un muro el cursor se pega a él y muestra un cuadradito; cerca de la grilla, una crucecita.
- [ ] **Esc** o el **clic derecho** terminan la cadena. La herramienta Muro sigue activa.
- [ ] La vista previa sigue al ratón sin retraso.

### 7.3 Muros compuestos
- [ ] En **Estructura** elige "Muro exterior 30": el espesor pasa a 0,30 y no se puede escribir.
- [ ] Dibuja un rectángulo: se ven las 4 capas con sus colores en la planta y en el 3D, con el revoque exterior
  hacia afuera.
- [ ] **Tiempo**: con el cronómetro, abre **Opciones > Estructuras compuestas…**, crea una estructura de 3 capas y
  dibuja un muro con ella en **menos de 2 minutos**.
- [ ] En el mismo diálogo, cambia el espesor de una capa de "Muro exterior 30" y pulsa Aceptar: los muros que la usan
  cambian. **Ctrl+Z** los devuelve.
- [ ] Ponle a una estructura el nombre de otra que ya existe: aparece «Ya existe una estructura llamada «…».» y el
  diálogo sigue abierto.

### 7.4 Separar en capas
- [ ] Con la **Flecha**, un clic en un muro compuesto lo pone azul y el Info Box dice "1 muro seleccionado" y ofrece
  **Separar en capas**.
- [ ] Un clic en **Separar en capas**: en pantalla nada se mueve, pero ahora cada capa se elige por separado.
- [ ] **Ctrl+Z** vuelve el muro compuesto y **Ctrl+Y** lo separa otra vez.

### 7.5 Cambiar y borrar
- [ ] Elige solo la capa exterior (acerca con la rueda si es muy fina) y cambia su altura a 3,60: solo esa capa sube.
- [ ] **Shift + clic** agrega y quita muros de la selección. Con dos alturas distintas, la altura dice "varios".
- [ ] **Supr** borra lo elegido y **Ctrl+Z** lo devuelve.
- [ ] Elige un muro y cámbiale la Estructura: cambia su espesor y su línea de referencia queda en el mismo lugar.
- [ ] Abre `muros_otro_programa.ifc`: el "Muro sin capas" se puede elegir y borrar, pero el Info Box avisa que viene
  de otro programa y no deja cambiarlo.

### 7.6 Archivo y otro programa
- [ ] Guarda, cierra y vuelve a abrir: muros, capas, colores, uniones y estructuras están igual.
- [ ] Abre el IFC guardado en otro programa BIM (IFC Studio Desktop, Revit u otro): los muros compuestos se ven con
  sus capas y materiales, y las capas separadas, como muros independientes.
