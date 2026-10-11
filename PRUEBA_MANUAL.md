# Prueba manual de BIM Simple

Marca cada casilla cuando el resultado sea el esperado. Si algo falla, anota el número del paso y qué viste.

## 0. Antes de empezar

- [ ] Abre Blender 5.2. La ventana abre sin mensajes de error.
- [ ] En **Edit > Preferences > Add-ons** aparecen activados **Bonsai** y **BIM Simple**.

## 1. Proyecto nuevo y espacio de trabajo

1. En cualquier vista 3D, pulsa **N** para abrir la barra lateral y elige la pestaña **BIM Simple**.
2. Pulsa **Nuevo proyecto**.

- [ ] Arriba se activa el espacio **BIM Simple**.
- [ ] A la izquierda está la planta ("Top", vista desde arriba). A la derecha, la vista 3D.
- [ ] En la barra lateral de la derecha se ve el navegador **Pisos** con `Planta Baja +0,00 3,00`.
- [ ] Tus otros espacios de trabajo (Layout, Modeling…) siguen igual que antes.

## 2. Caja de herramientas e iconos

- [ ] La barra de la izquierda muestra solo 4 iconos: **Flecha, Muro, Losa, Columna**. No aparecen las herramientas de Blender ni las de Bonsai.
- [ ] Al dejar el ratón sobre cada icono aparece su nombre en español.
- [ ] En otro espacio de trabajo (por ejemplo Layout), la barra muestra todas las herramientas de siempre.

## 3. Navegador de pisos

- [ ] Pulsa **+**: se abre un cuadro con Nombre, Cota y Altura. La cota propuesta queda encima del piso más alto. Crea **Piso 1** a 3,00 con altura 3,00.
- [ ] **Un clic** sobre Piso 1 lo activa: la planta queda vacía, porque muestra solo ese piso.
- [ ] Un clic sobre Planta Baja vuelve a mostrar lo de la Planta Baja.
- [ ] **Doble clic sobre el nombre** permite renombrarlo.
- [ ] **−** pide confirmación y borra el piso seleccionado con todo su contenido. Con un solo piso, el botón queda desactivado.

## 4. Muro

Con la Planta Baja activa, elige la herramienta **Muro**.

- [ ] El **Info Box** (barra sobre la vista) muestra: Espesor 0,20 · 🔗 Altura 3,00 (piso) · Referencia Exterior.
- [ ] En la planta, **clic** en el inicio y **clic** en cada esquina. Mientras mueves el ratón se ven la línea de vista previa y las cotas.
- [ ] Mantén **Shift**: el tramo queda fijo en 0°, 45° o 90°.
- [ ] Apunta el ratón en una dirección, escribe **5** y pulsa **Enter**: el tramo mide exactamente 5,00 m en esa dirección.
- [ ] **Clic en el primer punto** cierra el contorno; **Esc** o **clic derecho** terminan. Los muros quedan unidos en las esquinas y en el 3D miden 3,00 de alto.
- [ ] Cambia la Referencia a **Centro** y dibuja otro muro: la línea dibujada queda en el eje del muro.
- [ ] Quita el candado 🔗 de la altura, escribe 2,50 y dibuja: el muro mide 2,50.

## 5. Losa

Elige la herramienta **Losa**.

- [ ] El Info Box muestra: Espesor 0,15 · Desfase 0,00.
- [ ] Haz clic en cada vértice. Un **clic en el primer punto** cierra el contorno y crea la losa; **Enter** también la crea.
- [ ] En el 3D, la **cara superior** de la losa queda a la cota del piso, debajo de los muros.

## 6. Columna

Elige la herramienta **Columna**.

- [ ] El Info Box muestra: Rectangular · Ancho 0,30 · Largo 0,30 · 🔗 Altura 3,00 (piso).
- [ ] **Un clic** coloca la columna centrada en ese punto.
- [ ] Cambia a **Circular**: aparece Diámetro. Coloca otra columna y comprueba que es redonda.

## 7. Trabajar en otro piso

- [ ] Activa **Piso 1** y dibuja un muro: en el 3D aparece a cota 3,00, encima de la Planta Baja.
- [ ] En la planta solo se ve lo del Piso 1.

## 8. Guardar y abrir

- [ ] **File > Guardar IFC**: elige un nombre `.ifc` y guarda.
- [ ] Cierra Blender, ábrelo de nuevo y usa **File > Abrir IFC…** con ese archivo. Se ve todo igual y el navegador muestra los pisos.
- [ ] Cambia al espacio **BIM** de Bonsai: los pisos, muros, losas y columnas aparecen en la interfaz estándar de Bonsai.

## 9. Deshacer y rehacer

- [ ] Dibuja un muro y pulsa **Ctrl+Z**: el muro desaparece.
- [ ] **Ctrl+Shift+Z** lo devuelve.

## Diferencias conocidas con ArchiCAD

- **Activar un piso:** se hace con **un clic**. Las listas de Blender no detectan doble clic, que aquí sirve para renombrar.
- **La planta se ve desde arriba, sin plano de corte a 1,20 m.** Con el corte, Blender ocultaba la vista previa y las cotas de dibujo. Como solo se ve el piso activo, el resultado es casi igual.
- **Atajos de Bonsai:** en modo Objeto siguen activos (G mover, X / Supr borrar, Tab…).
- **Teclas del dibujo:**
  - Escribir un número fija el largo (D).
  - **Tab** cambia entre largo, ángulo, X e Y.
  - **C** cierra el contorno.
  - **Retroceso** quita el último punto.
  - **M** cambia el tipo de imán.
- **Versión de Bonsai:** BIM Simple usa partes internas de Bonsai 0.9.0. Conviene no actualizar Bonsai sin correr antes `tests/test_mvp.py`.
