"""Prueba automática de BIM Simple.

Ejecutar desde la carpeta del proyecto:
    "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" --background --python tests/test_mvp.py

Usa las mismas funciones de bim_simple.core que las herramientas, guarda el IFC,
lo vuelve a abrir con ifcopenshell y comprueba el resultado. Sale con código 1 si algo falla.
"""

import os
import sys
import tempfile
import traceback

import addon_utils
import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IFC_PATH = os.path.join(tempfile.gettempdir(), "bim_simple_test_mvp.ifc")
failures = []


def check(label, condition, detail=""):
    print(("  OK    " if condition else "  FALLA ") + label + (f" ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def close(a, b, tol=1e-6):
    return abs(a - b) <= tol


def load_bim_simple():
    """Usa la extensión instalada si está activa; si no, la carga desde la carpeta del proyecto."""
    if addon_utils.check("bl_ext.user_default.bim_simple")[1]:
        import bl_ext.user_default.bim_simple as bim_simple
    else:
        sys.path.insert(0, ROOT)
        import bim_simple

        bim_simple.register()
    return bim_simple


def test_storeys(core):
    print("Pisos")
    core.ensure_project()
    storeys = core.get_storeys()
    check("el proyecto nuevo tiene un piso", len(storeys) == 1)
    check("se llama Planta Baja", storeys[0].Name == "Planta Baja", storeys[0].Name)
    check("Planta Baja es el piso activo", core.active_storey() == storeys[0])

    core.add_storey("Piso 1", 3.0, 3.0)
    core.add_storey("Piso 2", 6.0, 3.0)
    temporary = core.add_storey("Temporal", 9.0, 2.5)
    check("agregar pisos", len(core.get_storeys()) == 4)
    check("altura propia del piso", close(core.get_storey_height(temporary), 2.5))
    core.delete_storey(temporary)
    check("borrar piso", [s.Name for s in core.get_storeys()] == ["Planta Baja", "Piso 1", "Piso 2"])

    core.rename_storey(core.get_storeys()[2], "Azotea")
    check("renombrar piso", core.get_storeys()[2].Name == "Azotea")
    core.rename_storey(core.get_storeys()[2], "Piso 2")

    piso1 = core.get_storeys()[1]
    core.activate_storey(piso1)
    check("activar Piso 1", core.active_storey() == piso1)

    try:
        for storey in core.get_storeys()[1:]:
            core.delete_storey(storey)
        core.delete_storey(core.get_storeys()[0])
        check("no deja borrar el único piso", False)
    except ValueError:
        check("no deja borrar el único piso", True)
    for name, elevation in (("Piso 1", 3.0), ("Piso 2", 6.0)):
        core.add_storey(name, elevation, 3.0)
    core.activate_storey(core.get_storeys()[1])


def bbox(element):
    """Caja envolvente (xmin, xmax, ymin, ymax, zmin, zmax) del cuerpo 3D en coordenadas de mundo."""
    import ifcopenshell.geom
    import ifcopenshell.util.representation

    settings = ifcopenshell.geom.settings()
    settings.set("use-world-coords", True)
    body = ifcopenshell.util.representation.get_representation(element, "Model", "Body", "MODEL_VIEW")
    verts = ifcopenshell.geom.create_shape(settings, element, body).geometry.verts
    xs, ys, zs = verts[0::3], verts[1::3], verts[2::3]
    return min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)


def boxes_close(a, b, tol=1e-4):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def test_walls(core):
    import bonsai.tool as tool

    print("Muros")
    piso1, piso2 = core.get_storeys()[1], core.get_storeys()[2]

    # Línea de referencia: se prueba con muros sueltos en el Piso 2 que después se borran.
    for reference, (ymin, ymax) in (("EXTERIOR", (10.0, 10.2)), ("CENTER", (9.9, 10.1)), ("INTERIOR", (9.8, 10.0))):
        wall = core.create_walls([(0, 10), (5, 10)], 0.20, 3.0, reference, storey=piso2)[0]
        box = bbox(tool.Ifc.get_entity(wall))
        check(f"línea de referencia {reference}", boxes_close(box, (0, 5, ymin, ymax, 6, 9)), box)
        tool.Geometry.delete_ifc_object(wall)

    core.activate_storey(piso1)
    walls = core.create_walls(
        [(0, 0), (6, 0), (6, 4), (0, 4)], 0.20, core.get_storey_height(piso1), "EXTERIOR", closed=True
    )
    check("4 muros creados", len(walls) == 4, len(walls))


def test_slab_and_column(core):
    import bonsai.tool as tool

    print("Losas y columnas")
    piso1, piso2 = core.get_storeys()[1], core.get_storeys()[2]

    # Desfase y columna circular: se prueban en el Piso 2 y se borran.
    slab = core.create_slab([(0, 10), (2, 10), (2, 12), (0, 12)], 0.15, offset=0.5, storey=piso2)
    box = bbox(tool.Ifc.get_entity(slab))
    check("losa con desfase +0,50: cara superior a cota 6,50", boxes_close(box, (0, 2, 10, 12, 6.35, 6.5)), box)
    tool.Geometry.delete_ifc_object(slab)
    column = core.create_column((1, 11), "CIRCLE", 0.40, None, 2.5, storey=piso2)
    box = bbox(tool.Ifc.get_entity(column))
    check("columna circular Ø 0,40 y altura 2,50", boxes_close(box, (0.8, 1.2, 10.8, 11.2, 6.0, 8.5), tol=2e-3), box)
    tool.Geometry.delete_ifc_object(column)
    check("contorno de 2 puntos no crea losa", core.create_slab([(0, 0), (1, 0)], 0.15, storey=piso2) is None)

    core.activate_storey(piso1)
    slab = core.create_slab([(0, 0), (6, 0), (6, 4), (0, 4), (0, 0)], 0.15)
    check("losa creada", slab is not None)
    column = core.create_column((3, 2), "RECTANGLE", 0.30, 0.30, core.get_storey_height(piso1))
    check("columna creada", column is not None)


def test_saved_file(core):
    import ifcopenshell
    import ifcopenshell.util.element
    import ifcopenshell.util.placement

    print("Archivo IFC guardado")
    core.get_file().write(IFC_PATH)
    ifc = ifcopenshell.open(IFC_PATH)
    check("esquema IFC4", ifc.schema == "IFC4", ifc.schema)
    storeys = sorted(ifc.by_type("IfcBuildingStorey"), key=ifcopenshell.util.placement.get_storey_elevation)
    check("3 IfcBuildingStorey", len(storeys) == 3, len(storeys))
    for storey, (name, elevation) in zip(storeys, (("Planta Baja", 0.0), ("Piso 1", 3.0), ("Piso 2", 6.0))):
        placement_z = ifcopenshell.util.placement.get_storey_elevation(storey)
        height = ifcopenshell.util.element.get_psets(storey, qtos_only=True)[core.STOREY_QTO]["GrossHeight"]
        parent = ifcopenshell.util.element.get_aggregate(storey)
        check(
            f"{name}: cota {elevation}, Elevation {elevation}, altura 3.0, dentro del edificio",
            storey.Name == name
            and close(placement_z, elevation)
            and close(storey.Elevation, elevation)
            and close(height, 3.0)
            and parent.is_a("IfcBuilding"),
            f"{storey.Name}, z={placement_z}, Elevation={storey.Elevation}, altura={height}, padre={parent.is_a()}",
        )

    walls = ifc.by_type("IfcWall")
    check("4 IfcWall", len(walls) == 4, len(walls))
    containers = {ifcopenshell.util.element.get_container(w).Name for w in walls}
    check("los muros están contenidos en el Piso 1", containers == {"Piso 1"}, containers)
    thicknesses = {
        round(ifcopenshell.util.element.get_material(w).ForLayerSet.TotalThickness, 6) for w in walls
    }
    check("espesor 0,20 (Info Box)", thicknesses == {0.2}, thicknesses)
    boxes = [bbox(w) for w in walls]
    heights = {round(b[5] - b[4], 6) for b in boxes}
    check("altura 3,00 = altura del piso, desde cota 3,00", heights == {3.0} and all(close(b[4], 3.0) for b in boxes), boxes)
    outline = (min(b[0] for b in boxes), max(b[1] for b in boxes), min(b[2] for b in boxes), max(b[3] for b in boxes))
    check("rectángulo exterior de 6 × 4 m", boxes_close(outline, (0, 6, 0, 4)), outline)
    joins = [
        r for r in ifc.by_type("IfcRelConnectsPathElements")
        if r.RelatingElement.is_a("IfcWall") and r.RelatedElement.is_a("IfcWall")
    ]
    check("4 esquinas unidas", len(joins) == 4, len(joins))

    slabs, columns = ifc.by_type("IfcSlab"), ifc.by_type("IfcColumn")
    check("1 IfcSlab", len(slabs) == 1, len(slabs))
    check("1 IfcColumn", len(columns) == 1, len(columns))
    for element in slabs + columns:
        container = ifcopenshell.util.element.get_container(element).Name
        check(f"{element.is_a()} contenido en el Piso 1", container == "Piso 1", container)
    slab_box = bbox(slabs[0])
    check("losa 6 × 4 × 0,15 con la cara superior a cota 3,00", boxes_close(slab_box, (0, 6, 0, 4, 2.85, 3.0)), slab_box)
    column_box = bbox(columns[0])
    check("columna 0,30 × 0,30 centrada en (3, 2), de cota 3,00 a 6,00", boxes_close(column_box, (2.85, 3.15, 1.85, 2.15, 3.0, 6.0)), column_box)
    profile = ifcopenshell.util.element.get_material(columns[0]).ForProfileSet.MaterialProfiles[0].Profile
    check("perfil IfcRectangleProfileDef 0,30 × 0,30", profile.is_a("IfcRectangleProfileDef") and close(profile.XDim, 0.3) and close(profile.YDim, 0.3), profile)


def test_open_in_bonsai():
    """Abre el IFC guardado en una escena vacía con la carga estándar de Bonsai (File > Open IFC Project)."""
    import bonsai.tool as tool

    print("Apertura en Bonsai")
    bpy.ops.wm.read_homefile(use_empty=True)
    result = bpy.ops.bim.load_project(filepath=IFC_PATH)
    check("bim.load_project termina bien", result == {"FINISHED"}, result)
    ifc = tool.Ifc.get()
    counts = {cls: len(ifc.by_type(cls)) for cls in ("IfcBuildingStorey", "IfcWall", "IfcSlab", "IfcColumn")}
    check("contenido leído por Bonsai", counts == {"IfcBuildingStorey": 3, "IfcWall": 4, "IfcSlab": 1, "IfcColumn": 1}, counts)
    missing = [e.is_a() for cls in counts for e in ifc.by_type(cls) if not tool.Ifc.get_object(e)]
    check("cada elemento tiene su objeto en Blender", not missing, missing)

    # "Guardar IFC" del menú File usa este mismo operador de Bonsai.
    import ifcopenshell

    saved_again = IFC_PATH.replace(".ifc", "_bonsai.ifc")
    result = bpy.ops.bim.save_project(filepath=saved_again, should_save_as=True)
    reread = ifcopenshell.open(saved_again) if os.path.exists(saved_again) else None
    check(
        "bim.save_project guarda y el archivo se vuelve a leer completo",
        result == {"FINISHED"} and reread is not None and len(reread.by_type("IfcWall")) == 4,
        result,
    )


def main():
    try:
        bim_simple = load_bim_simple()
        core = bim_simple.core
        test_storeys(core)
        test_walls(core)
        test_slab_and_column(core)
        test_saved_file(core)
        test_open_in_bonsai()
    except Exception:
        traceback.print_exc()
        failures.append("excepción")
    print(f"IFC guardado en {IFC_PATH}")
    if failures:
        print(f"RESULTADO: {len(failures)} FALLA(S): {', '.join(failures)}")
        sys.exit(1)
    print("RESULTADO: TODO OK")


main()
