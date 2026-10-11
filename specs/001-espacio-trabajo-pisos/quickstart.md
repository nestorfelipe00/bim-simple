# Guía de validación: Programa BIM Simple y navegador de pisos

Sirve para comprobar de punta a punta que la función 001 cumple la [especificación](spec.md). La parte A
es automática y la corre el asistente. La parte B es la prueba manual con ventana, la hace el usuario o el
asistente con su permiso.

Contratos de referencia: [programa.md](contracts/programa.md), [ui.md](contracts/ui.md) y
[core_api.md](contracts/core_api.md). Datos: [data-model.md](data-model.md).

## Requisitos previos

- Windows 11 con Blender 5.2.0 instalado en `C:\Program Files\Blender Foundation\Blender 5.2`.
- El zip `bonsai_py313-0.9.0-windows-x64.zip`, descargado del release oficial de Bonsai 0.9.0. Su SHA-256
  tiene que coincidir con el publicado. **La descarga requiere permiso.**
- Unos 2 GB libres en `%LOCALAPPDATA%`.

## A. Armado y prueba automática

1. Primer armado (instala en `%LOCALAPPDATA%\Programs\BIM Simple`; **requiere permiso**):

   ```bash
   powershell -ExecutionPolicy Bypass -File tools/armar_programa.ps1 -BonsaiZip "C:\Users\Usuario\Downloads\bonsai_py313-0.9.0-windows-x64.zip"
   ```

   **Resultado esperado**:
   - una línea `OK` por paso;
   - la prueba automática termina con `RESULTADO: TODO OK`;
   - el control SC-005 dice `Blender del usuario sin cambios`;
   - el código de salida es 0.

2. Después de cambiar el código de la extensión o de la plantilla (rápido, sin volver a copiar Blender):

   ```bash
   powershell -ExecutionPolicy Bypass -File tools/armar_programa.ps1 -SoloExtension
   ```

3. Correr solo la prueba automática:

   ```bash
   "%LOCALAPPDATA%\Programs\BIM Simple\blender\blender.exe" --background --app-template bim_simple --python tests/test_pisos.py
   ```

   La prueba cubre lo que se puede comprobar sin ventana; la lista está en [plan.md](plan.md), sección
   "Prueba automática". Si algo falla, sale con código 1 y muestra el detalle.

4. Accesos directos, al final y **con permiso**:

   ```bash
   powershell -ExecutionPolicy Bypass -File tools/armar_programa.ps1 -SoloExtension -CrearAccesos
   ```

## B. Prueba manual (con ventana)

Abrir **BIM Simple** desde su acceso directo. Marcar cada punto y anotar lo que no coincida.

### B1. Arranque y pantalla (FR-001 a FR-006, SC-007)
- [ ] Desde el doble clic hasta poder pulsar "Nuevo proyecto" pasan menos de 20 s (cronometrar).
- [ ] No aparece ninguna ventana negra (consola) ni la pantalla de bienvenida de Blender.
- [ ] Planta a la izquierda y 3D a la derecha, sin el cubo ni nada en la escena.
- [ ] Arriba solo dice "Archivo". No hay pestañas de espacios de trabajo, barra de estado ni encabezados en las vistas.
- [ ] A la derecha, la barra lateral muestra solo "BIM Simple", sin pestañas.
- [ ] No se puede dividir la pantalla arrastrando desde las esquinas. Al pasar el ratón por los bordes no aparecen flechas.
- [ ] Anotar el título de la ventana y el icono de la barra de tareas (diferencias D1 y D2).

### B2. Proyecto (FR-007 a FR-011)
- [ ] Archivo > Nuevo proyecto: aparece "Planta Baja", cota 0,00, altura 3,00, marcada como activa.
- [ ] Guardar IFC (Ctrl+S) en un proyecto nuevo: pide carpeta y nombre (explorador en español) y guarda.
- [ ] Volver a guardar: no pregunta nada.
- [ ] Guardar IFC como…: crea otro archivo, y el siguiente Ctrl+S guarda en ese.
- [ ] Abrir IFC… con un archivo de texto renombrado a `.ifc`: aparece el mensaje en español y el proyecto abierto sigue igual.
- [ ] Abrir un IFC de otro programa con varios pisos: la lista muestra sus pisos, y queda activo el más cercano a 0,00.
- [ ] Con cambios sin guardar, Nuevo proyecto pregunta Guardar / No guardar / Cancelar, y Cancelar no hace nada.

### B3. Pisos (FR-012 a FR-019)
- [ ] Agregar piso arriba dos veces: "Piso 1" a 3,00 y "Piso 2" a 6,00, el más alto arriba en la lista.
- [ ] Agregar piso abajo: "Sótano 1" a −3,00.
- [ ] Editar piso… sobre Planta Baja, altura 3,50: Piso 1 pasa a 3,50 y Piso 2 a 6,50.
- [ ] Editar piso… con una cota menor que la del piso de abajo: mensaje y nada cambia.
- [ ] Renombrar un piso con el mismo nombre que otro: se acepta tal cual, sin agregar " 2".
- [ ] Borrar un piso que tiene elementos (hacen falta elementos: abrir un IFC que los tenga): avisa cuántos se borrarán; Cancelar no borra y Borrar los quita de las dos vistas.
- [ ] Con un solo piso, "Borrar piso" está desactivado.

### B4. Piso activo (FR-020 a FR-023, SC-004)
- [ ] Con un IFC que tenga elementos en varios pisos, un clic en un piso lo marca activo **al instante**.
- [ ] La planta muestra solo los elementos de ese piso; la vista 3D, todo el edificio.
- [ ] La planta no rota con el botón central; solo se desplaza y hace zoom.

### B5. Deshacer (FR-018)
- [ ] Agregar piso → Ctrl+Z: desaparece de la lista y de las vistas. Ctrl+Mayús+Z: vuelve.
- [ ] Cambiar la cota de un piso con elementos → Ctrl+Z: piso y elementos vuelven a su cota.
- [ ] Borrar un piso con elementos → Ctrl+Z: vuelven el piso y sus elementos.
- [ ] Renombrar → Ctrl+Z: vuelve el nombre anterior.
- [ ] Nuevo proyecto → Ctrl+Z: **no** reaparece el proyecto anterior.
- [ ] Después de cada caso, guardar y volver a abrir: el archivo coincide con lo que se veía.

### B6. Atajos (casos límite)
- [ ] Tab, F3, F4, Mayús+A, T, N, Ctrl+Espacio, Mayús+F1 a F12 y el clic derecho sobre la vista no hacen nada.
- [ ] Ctrl+N, Ctrl+O, Ctrl+S, Mayús+Ctrl+S y Ctrl+Q hacen lo del menú Archivo.
- [ ] Anotar qué aparece con clic derecho **sobre un botón** del panel (diferencia D3).

### B7. Salir (FR-010)
- [ ] Ctrl+Q sin cambios: cierra sin preguntar.
- [ ] Ctrl+Q con cambios: «¿Guardar cambios antes de cerrar?», con Guardar, No guardar y Cancelar. Cancelar sigue en el programa; Guardar guarda el IFC y cierra.
- [ ] La X de la ventana con cambios en un proyecto guardado: aparece la pregunta y "Guardar" actualiza **el `.ifc`** (comprobar la fecha del archivo).
- [ ] La X con cambios en un proyecto nunca guardado: "Guardar" deja una copia de recuperación, y al volver a abrir el programa se ofrece abrirla.
- [ ] Si alguna de las dos pruebas de la X falla, se pasa al plan B (X1, research R15) y se anota.

### B8. El Blender del usuario (FR-004, SC-005)
- [ ] Con BIM Simple abierto, abrir también el Blender normal: los dos funcionan.
- [ ] El Blender normal se ve igual que antes (mismo idioma, sus extensiones, su archivo de inicio).
- [ ] El control SC-005 del script de armado dijo "sin cambios".
