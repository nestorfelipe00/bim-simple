# Prueba manual de BIM Simple (función 001)

Marca cada casilla cuando el resultado sea el esperado. Si algo falla, anota el número del paso y qué viste.
Es la parte B de la [guía de validación](specs/001-espacio-trabajo-pisos/quickstart.md).

## 0. Antes de empezar

- Abre BIM Simple con el acceso directo **BIM Simple** del Escritorio o del menú Inicio. Antes de instalarlo
  también se puede abrir con `npm --prefix app start` desde la carpeta del proyecto.
- Para probar archivos de otros programas sirven los IFC de prueba de `app\test-output\fixtures\`. Los crea
  la prueba automática (`npm --prefix app test`):
  - `con_elementos.ifc`: 3 pisos con un muro en cada uno;
  - `otro_programa_mm.ifc`: 4 pisos, en milímetros;
  - `no_es_ifc.ifc`: un texto con extensión `.ifc`.

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
