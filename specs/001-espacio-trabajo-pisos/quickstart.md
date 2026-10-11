# Guía de validación: Programa BIM Simple y navegador de pisos

Sirve para comprobar de punta a punta que la función 001 cumple la [especificación](spec.md):
- la parte A es automática y la corre el asistente;
- la parte B es la prueba manual, con la ventana visible (requiere permiso para abrirla).

Contratos: [programa.md](contracts/programa.md), [ui.md](contracts/ui.md) y
[core_api.md](contracts/core_api.md). Datos: [data-model.md](data-model.md).

## Requisitos previos

- Windows 11, Node.js 24 y npm 11. Ya están instalados.
- El entorno de desarrollo armado con `tools/setup-dev.ps1` (ver [plan.md](plan.md)).
  - Prepara `runtime/python` (Python 3.14.7 embebible con IfcOpenShell 0.9.0 y sus dependencias,
    en las versiones de `engine/requirements.txt`) y `app/node_modules`.
  - Puede copiar los archivos ya verificados del prototipo (`%TEMP%\bsproto`) en lugar de
    descargarlos de nuevo.
  - **Si hace falta descargar, requiere permiso.**

## A. Pruebas automáticas

1. **Prueba del motor**, sin interfaz:

   ```bash
   runtime/python/python.exe -m pytest engine/tests -q
   ```

   Resultado esperado: todas las pruebas pasan (`N passed`) y el comando sale con código 0.
   Cubre:
   - proyecto nuevo (FR-007);
   - pisos: agregar arriba y abajo, nombres, editar cota y altura con desplazamiento de los
     superiores y sus elementos, rechazos, borrar con elementos, piso activo (FR-012 a FR-021);
   - deshacer y rehacer (FR-018);
   - abrir IFC de otros programas (milímetros, varios edificios, sin pisos, dañado, no IFC) y
     guardar como (FR-008 a FR-011);
   - reabrir y validar sin errores (FR-019, SC-002, SC-003);
   - tiempo de cada orden con 10 pisos (SC-004).

2. **Prueba del programa**, con la ventana oculta:

   ```bash
   npm --prefix app test
   ```

   Resultado esperado: el resumen termina con `RESULTADO: TODO OK`, código 0, y capturas en
   `app/test-output/`. Cubre:
   - título (FR-004) y menús (FR-003);
   - nuevo, agregar pisos, editar y borrar desde el panel;
   - doble clic que activa un piso (FR-020);
   - la planta muestra solo el piso activo (FR-022, comprobado sobre la escena);
   - deshacer y rehacer desde el menú;
   - guardar y validar;
   - cierre con cambios: pregunta y no cierra hasta responder (FR-010);
   - reinicio del motor si se detiene.

3. **Instalador** (requiere permiso para instalar y crear accesos directos):

   ```bash
   npm --prefix app run dist
   ```

   Genera `app/dist/BIM Simple Setup <versión>.exe`. Después de instalarlo:
   - existen los accesos directos;
   - el programa abre;
   - "Agregar o quitar programas" lo desinstala sin dejar nada en la computadora (SC-005).

## B. Prueba manual (con ventana)

Abrir **BIM Simple** desde su acceso directo. Marcar cada punto y anotar lo que no coincida.

### B1. Arranque y pantalla (FR-001 a FR-006, SC-007)
- [ ] Desde el doble clic hasta poder pulsar "Nuevo proyecto" pasan menos de 10 s (cronometrar).
- [ ] La ventana y la barra de tareas muestran el icono y el título de BIM Simple.
- [ ] Solo hay menús Archivo y Edición; a la izquierda la planta, al centro el 3D y a la derecha el panel.

### B2. Proyecto (FR-007 a FR-011)
- [ ] Nuevo proyecto: "Planta Baja", 0,00 / 3,00, activa.
- [ ] Ctrl+S en un proyecto nuevo abre el diálogo de Windows; después, Ctrl+S guarda sin preguntar.
- [ ] Guardar IFC como… crea otro archivo, y el siguiente Ctrl+S guarda en ese.
- [ ] Abrir IFC… con un archivo de texto renombrado a `.ifc`: aparece el mensaje en español y el proyecto abierto sigue igual.
- [ ] Abrir un IFC de otro programa con varios pisos: se ven sus pisos y elementos, y queda activo el más cercano a 0,00.
- [ ] El IFC guardado se abre sin errores en otro programa BIM (por ejemplo, un visor IFC gratuito) (SC-003).

### B3. Pisos (FR-012 a FR-019)
- [ ] Agregar piso arriba dos veces: "Piso 1" a 3,00 y "Piso 2" a 6,00, el más alto arriba en la lista.
- [ ] Agregar piso abajo: "Sótano 1" a −3,00.
- [ ] Editar piso… sobre Planta Baja, altura 3,50: Piso 1 pasa a 3,50 y Piso 2 a 6,50, también en el 3D.
- [ ] Editar piso… con una cota menor que la del piso de abajo: mensaje y nada cambia.
- [ ] Borrar un piso con elementos (abriendo un IFC que los tenga): avisa cuántos son; Cancelar no borra.

### B4. Piso activo y navegación (FR-020 a FR-025)
- [ ] El doble clic en un piso lo activa al instante; un clic solo lo selecciona.
- [ ] La planta muestra solo el piso activo; el 3D, todo el edificio.
- [ ] 3D: el botón izquierdo gira alrededor del punto señalado, sin saltos; la rueda acerca hacia el ratón; no se puede pasar por debajo del suelo.
- [ ] Planta: la rueda acerca hacia el ratón y el botón central desplaza; no rota.

### B5. Deshacer y salir (FR-010, FR-018)
- [ ] Agregar piso → Ctrl+Z → desaparece; Ctrl+Y → vuelve.
- [ ] Cambiar una altura → Ctrl+Z → todo vuelve a su cota.
- [ ] Cerrar con la X habiendo cambios: «¿Guardar cambios antes de cerrar?»; Cancelar sigue en el programa; Guardar guarda y cierra.
