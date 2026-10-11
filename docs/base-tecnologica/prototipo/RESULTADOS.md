# Prototipo de comprobación: Electron + Three.js + IfcOpenShell

**Fecha**: 2026-10-11 · **Decisión que valida**: [evaluacion.md](../evaluacion.md) §9 (opción C)

## Qué se armó

Un programa mínimo en una carpeta temporal (`%TEMP%\bsproto`), que no toca el proyecto, Blender ni el sistema.

| Pieza | Versión | Origen | Licencia |
|---|---|---|---|
| Electron | 44.4.5 (2026-09-23) | npm; el instalador verifica las sumas de control | MIT |
| Three.js | 0.186.1 (2026-09-24) | npm | MIT |
| Python embebible | 3.14.7 | python.org, SHA-256 verificado (`d297e5ff…1f15`) | PSF |
| IfcOpenShell | 0.9.0, con numpy, shapely y pytest (pytest lo pide la validación completa) | PyPI, ruedas binarias | LGPL-3.0+ |

El código está en [app/](app/) (ventana e interfaz) y en [motor/motor.py](motor/motor.py) (motor BIM).

- **Motor**: un proceso de Python que recibe órdenes de a una por línea, en formato JSON (`crear_muro`, `deshacer`,
  …), y responde igual.
- **El IFC es la única fuente de verdad.** Cada orden que lo cambia es una transacción de IfcOpenShell, es decir, un
  paso de deshacer.
- **Licencias**: solo se usa la API LGPL de IfcOpenShell, nada de Bonsai, y el núcleo geométrico OpenCASCADE, no
  CGAL.

## Prueba automática

La ventana corre oculta, ejecuta los pasos, captura la pantalla y comprueba el cierre. Los resultados completos están
en [resultados/resultado.json](resultados/resultado.json).

| Paso | Motor | Total con el dibujo en pantalla |
|---|---|---|
| Arranque del motor (desde que abre el programa) | — | **414–425 ms** |
| Nuevo proyecto (Proyecto > Sitio > Edificio > Planta Baja, tipo de muro con 3 capas) | 89 ms | 93 ms |
| Agregar piso arriba | 4 ms | 6 ms |
| Recinto de 4 muros unidos en las esquinas | 63 ms | 100 ms |
| Un muro unido en esquina a otro | 24 ms | **32 ms** |
| Muro encadenado | 21 ms | 27 ms |
| Deshacer (Ctrl+Z) | 14 ms | **25 ms** |
| Rehacer | 18 ms | 35 ms |
| Guardar IFC + validación completa IFC4 (con reglas EXPRESS) | 1.675 ms | 1.676 ms |

**Otras comprobaciones**

| Comprobación | Resultado |
|---|---|
| Validación del IFC guardado | **0 errores** |
| Doble clic en un piso del navegador | Lo activa (no se podía en Blender) |
| Título de la ventana | `* prueba_prototipo.ifc — BIM Simple` (en Blender no se podía cambiar) |
| Cerrar con la X habiendo cambios | Pregunta **«¿Guardar cambios antes de cerrar?»** con Guardar / No guardar / Cancelar, y cierra según la respuesta (en Blender no se podía interceptar) |

**Revisión independiente del IFC** (`resultados/prueba_prototipo.ifc`):
- IFC4 en METRE, con Proyecto > Sitio > Edificio > 3 pisos.
- `Elevation` igual a la cota de la ubicación, y `GrossHeight` 3,00 en cada piso.
- 10 muros del tipo "Muro 0,20", con `IfcMaterialLayerSetUsage` y 3 capas (Revoque 0,02 + Ladrillo 0,16 +
  Revoque 0,02).
- 9 uniones `IfcRelConnectsPathElements`.
- 0 muros sin piso.

**Capturas**:
- [planta baja](resultados/captura_planta_baja.png): planta con los muros unidos en inglete, y 3D.
- [piso 1](resultados/captura_piso_1.png): la planta muestra solo el piso activo y el 3D, todo el edificio.

## Conclusiones

1. **La velocidad no es un problema.** Un muro tarda unos 30 ms de punta a punta y deshacer, unos 25 ms. Se siente
   instantáneo: el umbral de percepción ronda los 100 ms. La comunicación con Python suma menos de 1 ms.
2. **Los límites de Blender desaparecen**: título propio, pregunta al cerrar con la X, doble clic, menú propio en
   español, diálogos de Windows.
3. **IfcOpenShell sin Blender hace lo difícil**: uniones en inglete con capas, deshacer y validación. Lo hace con la
   API LGPL, que permite vender cerrado (salvo el punto de CGAL, que sigue pendiente).

## Problemas encontrados y cómo se resuelven

| Problema | Solución en el programa real |
|---|---|
| La opción de IfcOpenShell que corta el muro por capas (`enable-layerset-slicing`) falla con "Unexpected topology" | Cada muro se muestra como un sólido. Las capas en planta se dibujarán desde los datos de las capas, como hace ArchiCAD con el rayado de corte. |
| La validación completa tarda 1,7 s | Validar en segundo plano después de guardar, sin bloquear al usuario. |
| npm 11 no ejecutó el paso que descarga el programa de Electron | El script de armado ejecuta `node node_modules/electron/install.js`. |
| La captura de una ventana oculta devuelve el cuadro anterior | Solo afecta a las pruebas automáticas: se toma una captura de calentamiento. |

## Peso

En disco, sin optimizar:

| Pieza | Peso |
|---|---|
| Electron | 369 MB |
| Python + IfcOpenShell + dependencias | 271 MB |
| Three.js | 23 MB (en el programa final se empaqueta en ~1 MB) |
| **Total estimado del programa** | **~640 MB** (contra ~1,5 GB con Blender) |

## Sin probar todavía

- La experiencia con la mano de un usuario: dibujar con clics, el imán y Mayús. Están programados en el prototipo,
  pero solo se pueden probar con la ventana visible.
- El instalador.
- Modelos grandes.
