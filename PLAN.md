# PLAN — BIM Simple (Fase 0)

Estado: **MVP terminado (Fases 0 a 4)**. Plan aprobado; los cambios hechos durante la implementación están anotados en D5, D7 y Riesgos. Prueba automática: `tests/test_mvp.py`. Prueba manual: `PRUEBA_MANUAL.md`.

## 1. Entorno verificado

| Qué | Resultado | Cómo se comprobó |
|---|---|---|
| Blender | 5.2.0 LTS, Python 3.13.13 | `blender.exe --background` |
| Bonsai | 0.9.0 estable, versión `py313` para Windows x64, instalado en `extensions\user_default\bonsai` | La versión py311 instalada antes no cargaba (sin IfcOpenShell). Se reemplazó por `bonsai_py313-0.9.0-windows-x64.zip`; su SHA-256 coincide con el publicado en GitHub. |
| Bonsai activo | Sí, IfcOpenShell 0.9.0 importa y hay 1.310 operadores `bpy.ops.bim` | Script en `--background` |
| Compatibilidad | La tienda de extensiones de Blender publica Bonsai 0.9.0 para "Blender 5.1 y posteriores" | extensions.blender.org |

Rutas de código citadas abajo, relativas a
`%APPDATA%\Blender Foundation\Blender\5.2\extensions\.local\lib\python3.13\site-packages\`.

## 2. API real encontrada

Columna **Probado**: ✅ = ejecutado en Blender 5.2 sin ventana en esta fase, con resultado comprobado en el IFC guardado. 📖 = leído en el código, todavía sin ejecutar.

### Proyecto y guardado
| Necesidad | Función / operador | Archivo:línea | Probado |
|---|---|---|---|
| Crear proyecto (IFC4, metros, Proyecto > Sitio > Edificio > 1 piso) | `bpy.ops.bim.create_project()` | `bonsai/bim/module/project/operator.py:137` | ✅ |
| **No usar**: borra la sesión entera | `bim.new_project` llama a `bpy.ops.wm.read_homefile()` | `bonsai/bim/module/project/operator.py:98` | 📖 |
| Archivo IFC vivo | `tool.Ifc.get()` | `bonsai/tool/ifc.py:72` | ✅ |
| Guardar | `tool.Ifc.get().write(ruta)` (prueba) · `bpy.ops.bim.save_project(filepath=...)` (interfaz) | `ifcopenshell/file.py:880` · `bonsai/bim/module/project/operator.py:1976` | ✅ · 📖 |
| Deshacer en operadores propios | Heredar de `tool.Ifc.Operator` e implementar `_execute` | `bonsai/tool/ifc.py:400` | 📖 |

### Pisos (IfcBuildingStorey)
| Necesidad | Función / operador | Archivo:línea | Probado |
|---|---|---|---|
| Crear piso bajo el edificio | `bpy.ops.bim.add_part_to_object("EXEC_DEFAULT", element=<id edificio>, part_class="IfcBuildingStorey", part_name=...)` | `bonsai/bim/module/aggregate/operator.py:348` | ✅ |
| Cota del piso | `obj.matrix_world[2][3] = z` + `bonsai.core.geometry.edit_object_placement(tool.Ifc, tool.Geometry, tool.Surveyor, obj=obj)` | `bonsai/core/geometry.py:31` | ✅ |
| Atributo `Elevation` (Bonsai no lo escribe) | `ifcopenshell.api.attribute.edit_attributes(f, product=piso, attributes={"Elevation": z})` | `ifcopenshell/api/attribute/edit_attributes.py:26` | ✅ |
| Renombrar | `tool.Spatial.edit_container_name(piso, nombre)` | `bonsai/tool/spatial.py:605` | ✅ |
| Borrar | `bonsai.core.spatial.delete_container(tool.Ifc, tool.Spatial, tool.Geometry, piso)`. El operador `bim.delete_container` depende de la fila elegida en la lista de Bonsai, así que no sirve. | `bonsai/core/spatial.py:158` | 📖 |
| Piso activo (destino de los elementos nuevos) | `tool.Spatial.set_default_container(piso)` / `tool.Root.get_default_container()` | `bonsai/tool/spatial.py:1282` · `bonsai/tool/root.py:139` | ✅ |
| Mostrar solo un piso | `bpy.ops.bim.set_container_visibility(container=id, mode="ISOLATE")`. Afecta a todas las vistas. | `bonsai/bim/module/spatial/operator.py:494` | 📖 |
| Altura del piso | Cantidad estándar IFC `Qto_BuildingStoreyBaseQuantities.GrossHeight`, con `ifcopenshell.api.pset.add_qto` + `edit_qto`. Para pisos intermedios, valor por defecto = cota del piso siguiente − cota propia. | `ifcopenshell/api/pset/` | 📖 |

Resultado comprobado: Planta Baja a 0,00, Piso 1 a 3,00 y Piso 2 a 6,00, los tres bajo "My Building". Un muro creado con el Piso 1 activo quedó contenido en el Piso 1 a cota 3,00.

### Muros
| Necesidad | Función / operador | Archivo:línea | Probado |
|---|---|---|---|
| Tipo de muro con espesor | `root.create_entity(IfcWallType)` → `material.add_material_set(IfcMaterialLayerSet)` → `add_material` → `add_layer` → `edit_layer(LayerThickness)` → `assign_material` | `ifcopenshell/api/material/` | ✅ |
| Crear 1 muro (inicio, largo, ángulo, altura) | `DumbWallGenerator(tipo)`: se rellenan `file, layers, body_context, axis_context, container, container_obj, width, height, length, rotation, location, x_angle` y se llama `create_wall()`. Es el mismo patrón que usa Bonsai en `wall.py:2674-2694`. | `bonsai/bim/module/model/wall.py:1236`, `:1380` | ✅ |
| Unir esquinas | `DumbWallJoiner().connect(muro1, muro2)` | `bonsai/bim/module/model/wall.py:1840` | ✅ |
| Línea de referencia exterior / centro / interior | `tool.Model.offset_wall(obj, "EXTERIOR"\|"CENTER"\|"INTERIOR")` + `tool.Model.recreate_wall(element, obj)` | `bonsai/tool/model.py:3115`, `:3138` | 📖 |
| Leer el espesor de un tipo | `tool.Model.get_material_layer_parameters(tipo)` | `bonsai/tool/model.py:788` | ✅ |
| Dibujo interactivo de Bonsai (referencia) | `bim.draw_polyline_wall`, modal, hereda de `PolylineOperator` | `bonsai/bim/module/model/wall.py:1019` | 📖 |

Resultado comprobado: 4 muros de 0,20 × 3,00 m forman el rectángulo de 6 × 4 m, con 4 uniones `IfcRelConnectsPathElements`, `IfcMaterialLayerSetUsage` y contenidos en su piso. Los volúmenes medidos encajan sin huecos.

### Losas
| Necesidad | Función / operador | Archivo:línea | Probado |
|---|---|---|---|
| Tipo de losa con espesor | La misma receta que el muro, con `IfcSlabType` | `ifcopenshell/api/material/` | ✅ |
| Losa desde el contorno | Se cargan los puntos en `scene.BIMPolylineProperties.insertion_polyline[0].polyline_points` y se llama `DumbSlabGenerator(tipo).generate("POLYLINE")`. Después, `tool.Polyline.clear_polyline()`. Requiere piso activo. | `bonsai/bim/module/model/slab.py:47` | ✅ |
| Desfase vertical | `ifcopenshell.api.material.edit_layer_usage(..., {"OffsetFromReferenceLine", "DirectionSense"})` + `DumbSlabPlaner().regenerate_from_occurence(element, usage)` | `bonsai/bim/module/model/slab.py:241` | 📖 |

Resultado comprobado: losa de 6 × 4 m y 0,15 m de espesor, contenida en su piso. Con la configuración por defecto queda **sobre** la cota del piso (z 0,00 a 0,15). Ver la decisión D4.

### Columnas
| Necesidad | Función / operador | Archivo:línea | Probado |
|---|---|---|---|
| Tipo de columna con perfil rectangular o circular | `profile.add_parameterized_profile("IfcRectangleProfileDef"\|"IfcCircleProfileDef")` → `profile.edit_profile` → `material.add_material_set(IfcMaterialProfileSet)` → `add_profile` → `assign_profile` → `assign_material` | `ifcopenshell/api/profile/`, `ifcopenshell/api/material/` | ✅ (rectangular) |
| Crear columna en un punto | Se fijan `tool.Model.get_model_props().extrusion_depth` y `scene.cursor.location`, y se llama `DumbProfileGenerator(tipo).generate()`. Bonsai pone `extrusion_depth` a 42 m por defecto, así que siempre hay que fijarlo. | `bonsai/bim/module/model/profile.py:51` | ✅ |
| Cambiar la altura | `DumbProfileJoiner().set_depth(obj, metros)` | `bonsai/bim/module/model/profile.py:357` | 📖 |

Resultado comprobado: columna de 0,30 × 0,30 × 3,00 m centrada en el punto, con `IfcMaterialProfileSetUsage` y contenida en su piso.

### Ayudas de dibujo de Bonsai
| Pieza | Archivo:línea | Se puede reutilizar |
|---|---|---|
| `PolylineOperator`: clics, imán, longitud con el teclado (Tab cambia entre largo, ángulo, X, Y), previsualización con cotas | `bonsai/bim/module/model/polyline.py:32` | Sí, como clase base de nuestro operador; es lo que hace el propio `bim.draw_polyline_wall`. Está atada a `BIMPolylineProperties` y a los dibujadores de Bonsai. |
| Interpretar el largo tecleado (métrico, fórmulas) | `tool.Polyline.validate_input` en `bonsai/tool/polyline.py:344` | Sí |
| Imán (extremos, aristas, grilla, ejes) | `tool.Snap` en `bonsai/tool/snap.py:204` | Sí, dentro de una vista 3D |
| **Shift para fijar 0/45/90°** | **No existe en Bonsai.** Bonsai usa A para fijar ejes y Shift + rueda para pasos de ángulo. | Hay que agregarlo |

### Caja de herramientas, Info Box e iconos
| Pieza | Archivo:línea | Conclusión |
|---|---|---|
| Patrón de herramienta de Bonsai: `BimTool(WorkSpaceTool)`, `bl_icon` = ruta absoluta sin ".dat", `bl_keymap`, `draw_settings` | `bonsai/bim/module/model/workspace.py:59`, `:98` | Copiamos este patrón |
| Registro: `bpy.utils.register_tool(cls, after=..., separator=..., group=...)` | `bonsai/bim/module/model/__init__.py:311` · Blender `scripts/modules/bpy/utils/__init__.py:1066` | Igual |
| Formato de icono de herramienta | Blender `scripts/startup/bl_ui/space_toolsystem_common.py:241`: solo acepta archivos `.dat` de triángulos, nunca PNG | Ver D1 |
| Formato `.dat`, descifrado en 3 iconos reales | Encabezado `VCO\0`, tamaño 255×255, origen (0,0), N vértices × (x,y) en bytes, N colores RGBA. Triángulos = N/3. | Generamos los nuestros con un script |
| Info Box | Blender dibuja `draw_settings` de la herramienta activa en la barra horizontal sobre la vista (`TOOL_HEADER`) | Es el lugar del Info Box de ArchiCAD |
| Selección estándar para la Flecha | `tool.Blender.get_default_selection_keypmap()` | `bonsai/tool/blender.py:936` |

## 3. Decisiones de diseño

**D1. Caja de herramientas e iconos.** Cuatro herramientas propias (`WorkSpaceTool`) en la barra izquierda de la vista: Flecha, Muro, Losa y Columna. Usan el prefijo `bimsimple.` para no chocar con las herramientas `bim.*` de Bonsai. Los iconos son `.dat` dibujados por nosotros (formas planas simples, estilo ArchiCAD) y los genera `tools/make_icons.py` a partir de listas de triángulos. Si alguna vez hace falta un icono PNG en un panel, se carga con `bpy.utils.previews`.

**D2. Info Box.** Los parámetros de la herramienta activa se dibujan en `draw_settings`, que aparece como barra horizontal sobre la vista. Los valores se guardan en propiedades de la escena de BIM Simple, y cada elemento nuevo usa el tipo IFC que corresponde a esos valores: por ejemplo, un muro de 0,20 m usa el tipo "Muro 0.20" y se crea si no existe.

**D3. Dibujo.** Nuestro operador interactivo hereda de `PolylineOperator` de Bonsai, como hace `bim.draw_polyline_wall`. Así reutiliza el imán, la longitud tecleada y la previsualización. Le agregamos Shift para 0/45/90°, y al terminar llama a nuestras funciones de creación (las mismas que usa la prueba). **Plan B**, si heredar de Bonsai choca con sus dibujadores internos: un operador propio con dibujo `gpu` e imán simple (grilla + extremos de muros del piso activo).

**D4. Cotas, igual que en ArchiCAD.**
- Losa: con desfase 0,00, la **cara superior** queda a la cota del piso (losa de z −0,15 a 0,00). Bonsai la deja por defecto por encima; la ajustamos con `edit_layer_usage`.
- Muro y columna: arrancan en la cota del piso, y su altura por defecto es la altura del piso.
- Línea de referencia: se usa `tool.Model.offset_wall`.

**D5. Planta del piso activo.** La vista izquierda queda ortográfica desde arriba ("Top") y muestra solo la colección del piso activo, con colecciones locales de esa vista (`use_local_collections` + `object.hide_collection`). La vista 3D de la derecha sigue mostrando todo. **Cambio respecto al plan:** se quitaron los planos de corte a 1,20 m, porque Blender recortaba con ellos la vista previa y las cotas de dibujo de Bonsai, que desaparecían de la planta (verificado en la Fase 2). Visto desde arriba con un solo piso visible, el resultado es casi igual.

**D6. Navegador de pisos.** Panel en la barra lateral, pestaña "BIM Simple", con una lista (`UIList`) que muestra nombre, cota y altura, y botones Agregar / Renombrar / Borrar. **Diferencia con ArchiCAD:** las listas de Blender no detectan doble clic, así que **un clic** en la fila activa el piso.

**D7. Ocultar la interfaz sobrante solo en el espacio "BIM Simple".** El filtro de add-ons por espacio de trabajo (`WorkSpace.use_filter_by_owner` / `owner_ids`) oculta los paneles y menús de Bonsai (verificado en la Fase 1), pero no las herramientas de la barra izquierda. **Decisión aprobada:** en "BIM Simple" y en modo Objeto, la barra dibuja solo nuestras herramientas. Para eso se reemplaza `VIEW3D_PT_tools_active.draw` (`bim_simple/tools.py`), y al desactivar la extensión se restaura el original. Es un cambio sobre una parte interna de Blender: puede requerir ajustes con nuevas versiones de Blender.

**D8. Proyecto nuevo.** Primero se fijan las unidades de la escena (métrico, metros) y el esquema IFC4, y después se llama `bim.create_project`. `bim.new_project` no se usa, porque reinicia Blender.

## 4. Estructura de archivos

```
SOFTWARE BIM/
├─ bim_simple/                 la extensión
│  ├─ blender_manifest.toml
│  ├─ __init__.py              registrar / desregistrar
│  ├─ core.py                  lógica sin interfaz: proyecto, pisos, tipos, muros, losas, columnas
│  │                           (la usan las herramientas y la prueba)
│  ├─ props.py                 valores del Info Box y piso activo
│  ├─ tools.py                 herramientas de la barra + Info Box (draw_settings)
│  ├─ operators.py             operadores de dibujo y del navegador de pisos
│  ├─ ui.py                    panel del navegador de pisos y espacio de trabajo "BIM Simple"
│  └─ icons/                   *.dat generados
├─ tools/make_icons.py         genera los .dat
├─ tests/test_mvp.py           prueba automática (blender --background)
├─ PLAN.md
└─ PRUEBA_MANUAL.md            (Fase 4)
```

## 5. Riesgos

1. **Usamos clases internas de Bonsai.** `DumbWallGenerator`, `DumbSlabGenerator`, `DumbProfileGenerator`, `DumbWallJoiner` y `PolylineOperator` no son una API pública. Bonsai publica versiones alfa casi a diario y una actualización podría romper BIM Simple. Medidas: fijar Bonsai 0.9.0 en `blender_manifest.toml` / documentación, concentrar esas llamadas en `core.py`, y que `tests/test_mvp.py` detecte cualquier rotura.
2. **La barra de herramientas es global** (ver D7). Se resolvió reemplazando el dibujo de la barra solo en "BIM Simple"; depende de una parte interna de Blender.
3. **Bonsai cambia la interfaz global.** Al abrir un archivo agrega su espacio de trabajo "BIM", reinstala su barra de herramientas cada vez que se crea o abre un proyecto, y en modo Objeto redefine teclas como G, X, Supr, Tab y Ctrl+J. BIM Simple no tocará las preferencias de Bonsai, así que esas teclas siguen activas.
4. **Primer punto con altura falsa (Bonsai 0.9.0).** Si el clic que arranca el dibujo es el mismo que marca el primer punto, Bonsai guarda ese punto con la altura que trae el imán (se vio z = −10 m), y el primer tramo sale con largo y ángulo errados. La herramienta original de Bonsai falla igual con esos clics. `bimsimple.draw_wall` fija todos los puntos a la cota del piso activo (`flatten_points`).
5. **Deshacer (Ctrl+Z).** Las funciones de creación llamadas fuera de un `tool.Ifc.Operator` no quedan en el historial de deshacer IFC de Bonsai. Nuestros operadores interactivos deben heredar de `tool.Ifc.Operator`.
6. **Losa por polilínea** usa `container_obj.location.z` sin comprobar que haya piso activo (`slab.py:96`). `core.py` debe asegurarse siempre de que haya un piso activo.
7. **Menú File.** El filtro de add-ons de D7 también oculta las opciones IFC que Bonsai agrega al menú File. En "BIM Simple", `ui.py` agrega "Abrir IFC…", "Guardar IFC" y "Guardar IFC como…", que usan `bim.load_project` y `bim.save_project` de Bonsai.

## 6. Pendiente de tu aprobación

- D4: losa con la cara superior en la cota del piso, como ArchiCAD.
- D6: un clic (no doble clic) para activar un piso.
- D7: cómo resolver la barra de herramientas global si el filtro no basta.
- Seguir con la Fase 1.
