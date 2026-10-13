"""Prueba del motor de la función 002: muros con capas (constitución, Principio V; quickstart.md, parte A)."""

import base64

import numpy as np
import ifcopenshell
import ifcopenshell.api.geometry
import ifcopenshell.api.material
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.api.type
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.representation
import ifcopenshell.util.shape
import pytest

from bimsimple_engine import layers, materials, walls
from bimsimple_engine.commands import execute

SETTINGS = ifcopenshell.geom.settings()
SETTINGS.set("use-world-coords", True)
RING = [(0.0, 4.0), (6.0, 4.0), (6.0, 0.0), (0.0, 0.0)]  # sentido horario


def occ_volume(wall):
    return ifcopenshell.util.shape.get_volume(ifcopenshell.geom.create_shape(SETTINGS, wall).geometry)


def structure_id(state, name):
    return next(s["id"] for s in state["structures"] if s["name"] == name)


def material_id(state, name):
    return next(m["id"] for m in state["materials"] if m["name"] == name)


def layer_area(project, wall):
    return sum(abs(layers.signed_area(poly)) for _, poly, _, _ in layers.layer_polygons(wall, project.unit_scale()))


def _api_ring(project, wall_type):
    """Recinto armado directamente con la receta de research R4 (sin la orden create_wall)."""
    f = project.file
    storey = f.by_id(project.active_storey_id)
    body = ifcopenshell.util.representation.get_context(f, "Model", "Body", "MODEL_VIEW")
    axis = ifcopenshell.util.representation.get_context(f, "Plan", "Axis", "GRAPH_VIEW")
    created = []
    for i in range(4):
        p1, p2 = RING[i], RING[(i + 1) % 4]
        wall = ifcopenshell.api.root.create_entity(f, ifc_class="IfcWall", name="Muro")
        ifcopenshell.api.spatial.assign_container(f, products=[wall], relating_structure=storey)
        ifcopenshell.api.type.assign_type(f, related_objects=[wall], relating_type=wall_type)
        usage = ifcopenshell.util.element.get_material(wall)
        ifcopenshell.api.material.edit_layer_usage(f, usage=usage, attributes={"DirectionSense": "NEGATIVE"})
        thickness = sum(l.LayerThickness for l in usage.ForLayerSet.MaterialLayers)
        rep = ifcopenshell.api.geometry.create_2pt_wall(f, element=wall, context=body, p1=p1, p2=p2,
                                                        elevation=0.0, height=3.0, thickness=thickness)
        ifcopenshell.api.geometry.assign_representation(f, product=wall, representation=rep)
        length = float(np.hypot(p2[0] - p1[0], p2[1] - p1[1]))
        rep = ifcopenshell.api.geometry.add_axis_representation(f, context=axis, axis=[(0.0, 0.0), (length, 0.0)])
        ifcopenshell.api.geometry.assign_representation(f, product=wall, representation=rep)
        if created:
            ifcopenshell.api.geometry.connect_wall(f, wall, created[-1])
        if i == 3:
            ifcopenshell.api.geometry.connect_wall(f, created[0], wall)
        created.append(wall)
    for wall in created:
        ifcopenshell.api.geometry.regenerate_wall_representation(f, wall=wall, length=1.0, height=3.0)
    return created


# ---------- Base (fase 2) ----------
def test_proyecto_nuevo_trae_el_catalogo(project):
    state = execute(project, "new_project", {})["state"]
    assert [(m["name"], m["color"]) for m in state["materials"]] == sorted(
        materials.DEFAULT_MATERIALS, key=lambda row: row[0].casefold())
    assert [s["name"] for s in state["structures"]] == ["Muro de hormigón 25", "Muro exterior 30", "Tabique 15"]
    names = {m["id"]: m["name"] for m in state["materials"]}
    for name, expected in materials.DEFAULT_STRUCTURES:
        row = next(s for s in state["structures"] if s["name"] == name)
        assert [(names[l["material_id"]], l["thickness"]) for l in row["layers"]] == expected
        assert row["thickness"] == pytest.approx(sum(t for _, t in expected))
        assert row["walls"] == 0
    assert state["can_undo"] is False


def test_capas_de_un_muro_suman_su_volumen(project):
    state = execute(project, "new_project", {})["state"]
    ring = _api_ring(project, project.entity(structure_id(state, "Muro exterior 30")))
    for wall in ring:
        polygons = layers.layer_polygons(wall, project.unit_scale())
        assert len(polygons) == 4
        volume = sum(abs(layers.signed_area(poly)) * depth for _, poly, _, depth in polygons)
        assert volume == pytest.approx(occ_volume(wall), abs=1e-6)
        assert walls.kind_of(project, wall) == "regenerable"
        assert walls.reference_of(project, wall) == "exterior"


def test_clases_de_muros_de_otro_programa(project, fixtures):
    execute(project, "open_project", {"path": fixtures["muros_otro_programa"]})
    by_name = {w.Name: w for w in project.file.by_type("IfcWall")}
    assert walls.kind_of(project, by_name["Muro con capas"]) == "regenerable"
    assert walls.reference_of(project, by_name["Muro con capas"]) == "other"
    assert walls.kind_of(project, by_name["Muro sin capas"]) == "locked"
    assert walls.kind_of(project, by_name["Muro con recorte"]) == "locked"
    info = walls.wall_info(project, by_name["Muro sin capas"])
    assert info["locked_reason"] == walls.LOCKED_REASON and info["layers"] == []


def test_mallas_con_grupos(project):
    state = execute(project, "new_project", {})["state"]
    ring = _api_ring(project, project.entity(structure_id(state, "Muro exterior 30")))
    result = execute(project, "meshes", {})
    by_id = {m["id"]: m for m in result["meshes"]}
    expected = [material_id(state, n) for n in ("Revoque", "Ladrillo", "Aislación", "Revoque")]
    for wall in ring:
        mesh = by_id[wall.id()]
        faces = np.frombuffer(base64.b64decode(mesh["faces"]), dtype=np.uint32)
        assert [g["material_id"] for g in mesh["groups"]] == expected
        assert all(g["count"] % 3 == 0 for g in mesh["groups"])
        assert sum(g["count"] for g in mesh["groups"]) == len(faces)
        assert mesh["wall"]["kind"] == "regenerable" and mesh["wall"]["thickness"] == pytest.approx(0.30)
