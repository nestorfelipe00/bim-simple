# Guía de validación: Muros con capas que se pueden separar

Cómo comprobar que la función 002 funciona de punta a punta:
- **Parte A**: pruebas automáticas, sin abrir ventanas.
- **Parte B**: prueba manual con la ventana visible. Abrirla requiere permiso del usuario.

Los detalles están en [spec.md](spec.md), [data-model.md](data-model.md) y [contracts/](contracts/).

## Requisitos

- La función 001 implementada y el entorno armado (`runtime/python`, `app/node_modules`). Ver `README.md`.
- No hace falta descargar nada nuevo (research R14).

## A. Pruebas automáticas

1. **Motor**, sin interfaz:

   ```bash
   runtime/python/python.exe -m pytest engine/tests -q -p no:cacheprovider
   ```

   Esperado: `N passed`, con las pruebas de la función 001 y las nuevas de `engine/tests/test_walls.py`
   (research R13).

| Comprueba | Resultado esperado |
|---|---|
| Recinto Básico 6 × 4, sentido horario, Exterior | 4 muros en el piso activo, 4 uniones y 3,84 m² en planta (SC-002) |
| Líneas de referencia | Exterior [−T, 0], Centro [−T/2, T/2] e Interior [0, T] en Y local (research R3) |
| Recinto "Muro exterior 30" | La suma de las capas es igual al volumen de cada muro |
| Separar un muro de 4 capas | 4 muros de una capa con el mismo material y espesor; el volumen no cambia (< 0,1 %); los vecinos no cambian; Ctrl+Z y Ctrl+Y (SC-003) |
| Cambiar altura, estructura, material y espesor; borrar | Según [data-model.md](data-model.md) §3 |
| Catálogo | Crear, duplicar, renombrar, borrar y editar capas; errores exactos de [core_api.md](contracts/core_api.md) |
| Guardar y volver a abrir | Muros, capas, materiales, uniones y estructuras iguales (diferencia < 1 mm; SC-004) |
| Validación IFC4 con reglas EXPRESS | 0 errores (SC-005) |
| 200 muros en el piso + 1 nuevo | < 0,2 s en el motor (SC-006) |
| IFC de otro programa | Clase `regenerable`, `custom_ends` o `locked` según research R10 |

2. **Programa**, con la ventana oculta:

   ```bash
   npm --prefix app test
   ```

   Esperado: `RESULTADO: TODO OK`. Las secciones nuevas de la función 002 son:
   - **Dibujar**: Muro, 4 clics y clic en el primer punto → 4 muros cerrados; con Shift, longitud escrita
     (`4,5` + Enter) e imán al extremo.
   - **Compuestos**: elegir "Muro exterior 30" → el espesor del Info Box es 0,30 y está desactivado; las mallas
     tienen 4 grupos con los colores del catálogo.
   - **Separar**: con la Flecha, clic en un muro → Info Box con "1 muro seleccionado" → "Separar en capas" →
     4 muros seleccionados; Ctrl+Z.
   - **Cambiar y borrar**: altura 3,60 en una capa → solo esa cambia; Supr.
   - **Estructuras**: Opciones > Estructuras compuestas… → nueva de 3 capas → Aceptar → aparece en el Info Box;
     nombre repetido → error exacto.
   - Capturas en `app/test-output/` para revisar la planta y el 3D.

## B. Prueba manual (con ventana)

Se agrega a `PRUEBA_MANUAL.md` como sección nueva. Abrir el programa:

```bash
npm --prefix app start
```

### B1. Caja de herramientas e Info Box (FR-001 a FR-004)
- [ ] A la izquierda de la planta están **Flecha** y **Muro** con iconos propios; al pasar el ratón dicen su nombre.
- [ ] Debajo de los menús está el Info Box. Con Muro muestra Estructura "Básica", Material "Hormigón", Espesor
      0,20, Altura igual a la del piso y Línea de referencia Exterior.

### B2. Dibujar (FR-005 a FR-012, SC-001, SC-002)
- [ ] Con el cronómetro: dibuja un rectángulo de 6 × 4 m en sentido horario, sin ayuda, en **menos de 1 minuto**.
- [ ] Las cuatro esquinas quedan cerradas, sin huecos ni superposiciones, en la planta y en el 3D.
- [ ] Mientras dibujas ves el muro con su espesor y la longitud junto al cursor.
- [ ] Shift fija 0°, 45° o 90°. Escribir `4,5` + Enter crea un muro de 4,50 m.
- [ ] El imán se pega a los extremos de los muros y a la grilla, y lo marca.
- [ ] Esc o clic derecho terminan la cadena. Un clic en el primer punto la cierra.

### B3. Muros compuestos (FR-015 a FR-018, SC-007)
- [ ] En Estructura elige "Muro exterior 30": el espesor pasa a 0,30. El muro muestra sus 4 capas con colores en
      la planta y en el 3D, con el revoque exterior afuera del recinto.
- [ ] Con el cronómetro: Opciones > Estructuras compuestas… → crea una estructura de 3 capas y dibuja un muro con
      ella, en **menos de 2 minutos** (SC-007).
- [ ] Cambia el espesor de una capa de esa estructura: los muros que la usan cambian.

### B4. Separar en capas (FR-019 a FR-022, SC-003)
- [ ] Con la Flecha, haz clic en un muro compuesto: se ve azul y el Info Box ofrece "Separar en capas".
- [ ] Un clic en "Separar en capas": en pantalla nada se mueve, y ahora cada capa se selecciona por separado.
- [ ] Ctrl+Z vuelve el muro compuesto; Ctrl+Y lo separa otra vez.

### B5. Cambiar y borrar (FR-023 a FR-027)
- [ ] Selecciona solo la capa exterior y cambia su altura a 3,60: solo esa capa sube.
- [ ] Shift + clic agrega y quita muros de la selección; con dos alturas distintas, el Info Box dice "varios".
- [ ] Supr borra lo seleccionado; Ctrl+Z lo devuelve.

### B6. Archivo y otro programa (FR-028, SC-004, SC-005)
- [ ] Guarda, cierra y vuelve a abrir: todo está igual.
- [ ] Abre el IFC en otro programa BIM (por ejemplo IFC Studio Desktop o Revit): los muros compuestos se ven con
      sus capas y materiales, y las capas separadas, como muros independientes.
