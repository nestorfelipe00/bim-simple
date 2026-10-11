# Lista de calidad de la especificación: Programa BIM Simple y navegador de pisos

**Propósito**: comprobar que la especificación está completa y es clara antes de pasar al plan
**Creada**: 2026-10-11
**Función**: [spec.md](../spec.md)

## Calidad del contenido

- [x] Sin detalles de implementación (lenguajes, frameworks, APIs)
- [x] Centrada en el valor para el usuario y sus necesidades
- [x] Escrita para personas no técnicas
- [x] Todas las secciones obligatorias completas

## Requisitos completos

- [x] No quedan marcas [NEEDS CLARIFICATION]
- [x] Los requisitos se pueden probar y no son ambiguos
- [x] Los criterios de éxito son medibles
- [x] Los criterios de éxito no dependen de la tecnología
- [x] Todos los escenarios de aceptación están definidos
- [x] Los casos límite están identificados
- [x] El alcance está bien delimitado
- [x] Dependencias y supuestos identificados

## Lista para el plan

- [x] Cada requisito funcional tiene criterios de aceptación claros
- [x] Los escenarios cubren los flujos principales
- [x] La función cumple los resultados medibles de los criterios de éxito
- [x] No se filtran detalles de implementación en la especificación

## Notas

- Iteración 1: quedaban 3 marcas [NEEDS CLARIFICATION] (entrada al programa, cota/altura, borrar
  piso con elementos).
- Iteración 2: el usuario respondió las tres. La tercera cambió la arquitectura a programa propio
  construido sobre Blender; se enmendó la constitución a v2.0.0 (Principio III) y se reescribió
  la especificación. Todas las comprobaciones pasan.
- Se mencionan Blender, Bonsai, IFC4 e `IfcBuildingStorey` porque son la plataforma y el estándar
  que exige la constitución, no decisiones de implementación.
- Supuesto a confirmar al revisar: al borrar un piso, los de arriba no bajan (FR-017).
- Iteración 3 (constitución v3.0.0, programa propio sin Blender):
  - se quitaron los requisitos y supuestos propios de Blender (copia de Blender, D1–D7, activar
    con un clic);
  - FR-004 pasa a ser el título de la ventana;
  - FR-020 activa con doble clic;
  - se agregó FR-025 (navegación aprobada en el prototipo);
  - SC-004, SC-005 y SC-007 se ajustaron a la base nueva.

  Todas las comprobaciones siguen pasando.
