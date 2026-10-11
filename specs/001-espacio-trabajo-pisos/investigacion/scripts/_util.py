"""Ayudas comunes para las pruebas de investigación (no es código del producto)."""

import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)


def tool():
    import bonsai.tool

    return bonsai.tool


def dump_tree(f, title=""):
    import ifcopenshell.util.element as ue
    import ifcopenshell.util.placement as up

    print(f"--- Jerarquía {title} ---")

    def rec(e, depth):
        extra = ""
        if e.is_a("IfcBuildingStorey"):
            z = up.get_local_placement(e.ObjectPlacement)[2][3] if e.ObjectPlacement else None
            qto = ue.get_psets(e, qtos_only=True).get("Qto_BuildingStoreyBaseQuantities", {})
            extra = f" Elevation={e.Elevation} placementZ={z} GrossHeight={qto.get('GrossHeight')}"
        print("  " * depth + f"#{e.id()} {e.is_a()} '{e.Name}'{extra}")
        for c in ue.get_contained(e):
            pl = c.ObjectPlacement
            rel = pl.PlacementRelTo if pl else None
            relowner = [p.is_a() + ":" + str(p.Name) for p in (rel.PlacesObject if rel else [])]
            m = up.get_local_placement(pl) if pl else None
            print(
                "  " * (depth + 1)
                + f"[contenido] #{c.id()} {c.is_a()} '{c.Name}' worldZ={None if m is None else round(m[2][3], 4)}"
                + f" PlacementRelTo={'#' + str(rel.id()) if rel else None} {relowner}"
            )
        for p in ue.get_parts(e):
            rec(p, depth + 1)

    for proj in f.by_type("IfcProject"):
        rec(proj, 0)
