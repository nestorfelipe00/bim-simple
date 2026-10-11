"""Prueba de punta a punta (investigación de la fase de plan, NO es la prueba del producto).

proyecto nuevo -> Planta Baja 0,00 / Piso 1 3,00 / Piso 2 6,00 con GrossHeight -> elemento en Piso 1
-> mover Piso 1 (cota 3,00 -> 3,50, desplaza los de arriba, FR-016) -> borrar Piso 2 con su contenido
-> guardar con write() -> reabrir con ifcopenshell.open -> comprobar pisos, Elevation, placements,
contención, GrossHeight y validación IFC4.

Ejecutar:
  "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" --background --python e2e_pisos.py
"""

import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import _recetas as R
import _util

IFC_PATH = os.path.join(_util.OUT, "e2e_pisos.ifc")
failures = []


def check(label, cond, detail=""):
    print(("  OK    " if cond else "  FALLA ") + label + (f" ({detail})" if detail != "" else ""))
    if not cond:
        failures.append(label)


def close(a, b, tol=1e-6):
    return abs(float(a) - float(b)) <= tol


try:
    import ifcopenshell
    import ifcopenshell.util.element as ue
    import ifcopenshell.util.placement as up
    import ifcopenshell.validate

    t = R.tool()
    print("Blender", bpy.app.version_string, "| Bonsai", t.Blender.get_bonsai_version(), "| ifcopenshell", ifcopenshell.version)

    print("1. Proyecto nuevo")
    R.new_project()
    f = R.ifc()
    check("esquema IFC4", f.schema == "IFC4", f.schema)
    check("unidades en metros", R.unit_scale() == 1.0, R.unit_scale())
    check("nombres Proyecto/Sitio/Edificio",
          [f.by_type(c)[0].Name for c in ("IfcProject", "IfcSite", "IfcBuilding")] == ["Proyecto", "Sitio", "Edificio"])
    pb = R.get_storeys()[0]
    check("Planta Baja activa", R.active_storey() == pb and pb.Name == "Planta Baja")

    print("2. Pisos con cota y altura")
    p1 = R.add_storey("Piso 1", 3.0, 3.0)
    p2 = R.add_storey("Piso 2", 6.0, 3.0)
    st = R.get_storeys()
    check("3 pisos ordenados", [s.Name for s in st] == ["Planta Baja", "Piso 1", "Piso 2"], [s.Name for s in st])
    check("cotas 0/3/6", [round(R.get_storey_elevation(s), 6) for s in st] == [0, 3, 6])

    print("3. Elemento en Piso 1 (muro con la receta del MVP)")
    R.activate_storey(p1)
    wall = R.make_wall((0, 0), (5, 0), 3.0)
    check("muro contenido en Piso 1", ue.get_container(wall) == p1)
    check("ubicación del muro relativa al Piso 1", wall.ObjectPlacement.PlacementRelTo == p1.ObjectPlacement)

    print("4. Cambiar la cota de Piso 1 a 3,50 (desplaza Piso 1 y los de arriba, FR-016)")
    delta = 3.5 - R.get_storey_elevation(p1)
    for s in [s for s in R.get_storeys() if R.get_storey_elevation(s) >= R.get_storey_elevation(p1)][::-1]:
        R.set_storey_elevation(s, R.get_storey_elevation(s) + delta)
    R.set_storey_height(pb, 3.5)  # la altura del de abajo es la nueva distancia
    check("Piso 1 a 3,50 y Piso 2 a 6,50",
          [round(R.get_storey_elevation(s), 6) for s in R.get_storeys()] == [0, 3.5, 6.5])
    wall_obj = t.Ifc.get_object(wall)
    check("muro se movió en el IFC", close(up.get_local_placement(wall.ObjectPlacement)[2][3], 3.5))
    check("muro se movió en Blender", close(wall_obj.matrix_world.translation.z, 3.5), wall_obj.matrix_world.translation.z)
    check("Bonsai no ve el muro como 'movido sin guardar'", not t.Ifc.is_moved(wall_obj))

    print("5. Borrar Piso 2 (con un elemento)")
    R.activate_storey(p2)
    col = R.make_column_by_assign_class("Columna P2", 1, 1, 6.5)
    n = R.count_storey_elements(p2)
    check("aviso: Piso 2 tiene 1 elemento", n == 1, n)
    col_id = col.id()
    R.activate_storey(p1)
    R.delete_storey(p2)
    check("quedan 2 pisos", [s.Name for s in R.get_storeys()] == ["Planta Baja", "Piso 1"])
    try:
        R.ifc().by_id(col_id)
        check("la columna se borró del IFC", False)
    except RuntimeError:
        check("la columna se borró del IFC", True)
    check("la columna se borró de Blender", "IfcColumn/Columna P2" not in bpy.data.objects)
    check("el piso de abajo pasa a medir hasta el siguiente (el más alto usa GrossHeight)",
          close(R.get_storey_height(p1), 3.0), R.get_storey_height(p1))

    print("6. Guardar con write() y reabrir")
    # write() NO sincroniza objetos movidos en Blender (bim.save_project sí: export_ifc.py sync_all_objects)
    unsynced = [o.name for o in bpy.data.objects if t.Ifc.get_entity(o) and t.Ifc.is_moved(o)]
    print("   objetos movidos sin sincronizar antes de write():", unsynced)
    R.ifc().write(IFC_PATH)
    g = ifcopenshell.open(IFC_PATH)
    sts = R.get_storeys(g)
    print("   pisos reabiertos:")
    for s in sts:
        qto = ue.get_psets(s, qtos_only=True).get("Qto_BuildingStoreyBaseQuantities", {})
        print(f"     {s.Name}: Elevation={s.Elevation} placementZ={up.get_local_placement(s.ObjectPlacement)[2][3]}"
              f" GrossHeight={qto.get('GrossHeight')} contenidos={[e.Name for e in ue.get_contained(s)]}")
    check("2 pisos en el archivo", [s.Name for s in sts] == ["Planta Baja", "Piso 1"], [s.Name for s in sts])
    check("Elevation = cota de la ubicación", all(close(s.Elevation, up.get_local_placement(s.ObjectPlacement)[2][3]) for s in sts))
    check("cotas 0,00 y 3,50", [round(float(up.get_storey_elevation(s)), 6) for s in sts] == [0.0, 3.5])
    check("GrossHeight 3,50 y 3,00",
          [ue.get_psets(s, qtos_only=True)["Qto_BuildingStoreyBaseQuantities"]["GrossHeight"] for s in sts] == [3.5, 3.0])
    gw = g.by_type("IfcWall")
    check("1 muro, contenido en Piso 1", len(gw) == 1 and ue.get_container(gw[0]).Name == "Piso 1")
    check("muro a cota 3,50, local 0,00 respecto del piso",
          close(up.get_local_placement(gw[0].ObjectPlacement)[2][3], 3.5)
          and gw[0].ObjectPlacement.PlacementRelTo == ue.get_container(gw[0]).ObjectPlacement)
    check("sin columnas ni elementos huérfanos",
          not g.by_type("IfcColumn") and all(ue.get_container(e) for e in g.by_type("IfcElement")))
    check("jerarquía Proyecto > Sitio > Edificio > pisos",
          ue.get_aggregate(g.by_type("IfcSite")[0]).is_a("IfcProject")
          and ue.get_aggregate(g.by_type("IfcBuilding")[0]).is_a("IfcSite")
          and all(ue.get_aggregate(s).is_a("IfcBuilding") for s in sts))
    _util.dump_tree(g, "archivo reabierto")

    print("7. Validación IFC4 (ifcopenshell.validate)")
    for express in (False, True):
        logger = ifcopenshell.validate.json_logger()
        try:
            ifcopenshell.validate.validate(IFC_PATH, logger, express_rules=express)
            errors = [s for s in logger.statements if s["level"] in ("error", "ERROR")]
            print(f"   express_rules={express}: {len(logger.statements)} mensajes, {len(errors)} errores")
            for s in logger.statements[:10]:
                print("     ", s["level"], s["message"][:200])
            check(f"validación sin errores (express_rules={express})", not errors)
        except Exception as ex:
            print(f"   express_rules={express}: no se pudo ejecutar -> {type(ex).__name__}: {ex}")
            if not express:
                failures.append("validate")
except Exception:
    traceback.print_exc()
    failures.append("excepción")

print("RESULTADO:", "TODO OK" if not failures else f"{len(failures)} FALLAS: {failures}")
sys.exit(1 if failures else 0)
