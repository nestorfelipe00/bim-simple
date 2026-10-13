"""Prueba del motor de la función 002: muros con capas (constitución, Principio V; quickstart.md, parte A)."""

import base64
import time

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

from bimsimple_engine import EngineError, layers, materials, walls
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


def three_storeys(project):
    """Proyecto nuevo con pisos a 0,00, 3,00 y 6,00 y el Piso 1 activo; devuelve el estado."""
    execute(project, "new_project", {})
    execute(project, "add_storey_above", {})
    execute(project, "add_storey_above", {})
    piso1 = next(s for s in project.state()["storeys"] if s["name"] == "Piso 1")
    return execute(project, "activate_storey", {"id": piso1["id"]})["state"]


def basic_args(state, **extra):
    args = {"structure_id": None, "material_id": material_id(state, "Hormigón"), "thickness": 0.20, "height": 3.0,
            "reference": "exterior"}
    args.update(extra)
    return args


def draw(project, points, closed=True, **args):
    """Cadena de muros como la dibuja la interfaz: cada tramo es un create_wall."""
    state = project.state()
    base = basic_args(state)
    base.update(args)
    pairs = list(zip(points, points[1:] + ([points[0]] if closed else [])))
    return [execute(project, "create_wall", {"start": list(a), "end": list(b), **base})["wall_id"] for a, b in pairs]


def joins(project):
    """Uniones como conjunto de (muro, tipo, muro, tipo) con los ids ordenados por posición en la lista de muros."""
    result = set()
    for rel in project.file.by_type("IfcRelConnectsPathElements"):
        result.add((rel.RelatingElement.GlobalId, rel.RelatingConnectionType,
                    rel.RelatedElement.GlobalId, rel.RelatedConnectionType))
    return result


def infos(project):
    return {w.GlobalId: walls.wall_info(project, w) for w in project.file.by_type("IfcWall")}


def same_info(a, b):
    for key in ("reference", "structure_id", "kind"):
        if key != "structure_id" and a[key] != b[key]:
            return False
    numbers = ["height", "thickness"] + [f"{k}{i}" for k in ("start", "end") for i in (0, 1)]
    flat = lambda info: {"height": info["height"], "thickness": info["thickness"],
                         **{f"{k}{i}": info[k][i] for k in ("start", "end") for i in (0, 1)}}
    fa, fb = flat(a), flat(b)
    return all(abs(fa[n] - fb[n]) < 0.001 for n in numbers) and \
        [round(l["thickness"], 4) for l in a["layers"]] == [round(l["thickness"], 4) for l in b["layers"]]


# ---------- Historia 1: dibujar muros ----------
def test_recinto_basico_6x4(project):
    state = three_storeys(project)
    piso1 = project.entity(state["active_storey_id"])
    ids = draw(project, RING)
    ring = [project.entity(i) for i in ids]
    assert len(project.file.by_type("IfcWall")) == 4
    assert all(ifcopenshell.util.element.get_container(w) == piso1 for w in ring)  # FR-013, FR-023 de la 001
    for wall in ring:
        info = walls.wall_info(project, wall)
        assert info["thickness"] == pytest.approx(0.20) and info["height"] == pytest.approx(3.0)
        assert info["kind"] == "regenerable" and info["reference"] == "exterior" and info["structure_id"] is None
        assert walls.placement_matrix(project, wall)[2][3] == pytest.approx(3.0)  # base a la cota del Piso 1
    assert len(project.file.by_type("IfcRelConnectsPathElements")) == 4
    area = sum(layer_area(project, w) for w in ring)
    assert area == pytest.approx(3.84, rel=0.001)  # SC-002
    assert sum(occ_volume(w) for w in ring) == pytest.approx(3.84 * 3.0, rel=0.001)


def test_lineas_de_referencia(project):
    state = three_storeys(project)
    for reference, expected in (("exterior", (-0.20, 0.0)), ("center", (-0.10, 0.10)), ("interior", (0.0, 0.20))):
        wall_id = execute(project, "create_wall", {"start": [20.0, 0.0], "end": [24.0, 0.0],
                                                   **basic_args(state, reference=reference)})["wall_id"]
        wall = project.entity(wall_id)
        polygon = layers.layer_polygons(wall, 1.0)[0][1]
        assert (polygon[:, 1].min(), polygon[:, 1].max()) == pytest.approx(expected)
        assert walls.wall_info(project, wall)["reference"] == reference
        execute(project, "undo", {})


@pytest.mark.parametrize("cambio, error", [
    ({"end": [0.005, 0.0]}, "El muro es demasiado corto (mínimo 1 cm)."),
    ({"thickness": 0.0}, "El espesor debe ser mayor que 0."),
    ({"height": -1.0}, "La altura debe ser mayor que 0."),
    ({"reference": "x"}, "Línea de referencia no válida."),
    ({"material_id": 999999}, "El material elegido ya no existe."),
    ({"structure_id": 999999}, "La estructura elegida ya no existe."),
])
def test_rechazos_al_dibujar(project, cambio, error):
    state = three_storeys(project)
    before = len(list(project.file))
    args = {"start": [0.0, 0.0], "end": [4.0, 0.0], **basic_args(state)}
    args.update(cambio)
    with pytest.raises(EngineError) as raised:
        execute(project, "create_wall", args)
    assert str(raised.value) == error
    assert len(list(project.file)) == before


def test_deshacer_un_muro(project):
    three_storeys(project)
    draw(project, [(0.0, 0.0), (5.0, 0.0), (5.0, 4.0)], closed=False)
    assert len(project.file.by_type("IfcRelConnectsPathElements")) == 1
    execute(project, "undo", {})
    assert len(project.file.by_type("IfcWall")) == 1
    assert len(project.file.by_type("IfcRelConnectsPathElements")) == 0
    draw(project, [(5.0, 0.0), (5.0, 4.0)], closed=False)  # el índice se rearmó después de deshacer
    assert len(project.file.by_type("IfcRelConnectsPathElements")) == 1


def test_esquina_ocupada_no_se_rompe(project):
    three_storeys(project)
    ring = [project.entity(i) for i in draw(project, RING)]
    volumes = [occ_volume(w) for w in ring]
    draw(project, [(6.0, 4.0), (9.0, 4.0)], closed=False)  # desde una esquina donde ya se unen dos muros
    assert len(project.file.by_type("IfcRelConnectsPathElements")) == 4
    assert [occ_volume(w) for w in ring] == pytest.approx(volumes)


def test_muros_guardados_y_reabiertos(project, tmp_path):
    three_storeys(project)
    draw(project, RING)
    draw(project, [(10.0, 0.0), (14.0, 0.0)], closed=False, reference="center")
    before_infos, before_joins = infos(project), joins(project)
    path = str(tmp_path / "muros.ifc")
    execute(project, "save_project", {"path": path})
    execute(project, "open_project", {"path": path})
    after_infos = infos(project)
    assert set(after_infos) == set(before_infos)
    for key, info in before_infos.items():
        assert same_info(info, after_infos[key]), key
        assert project.file.by_guid(key) and walls.wall_info(project, project.file.by_guid(key))["storey_id"] is not None
    assert joins(project) == before_joins  # constitución, Principio V: uniones en el IFC reabierto


def test_mover_piso_y_seguir_dibujando(project):
    state = three_storeys(project)
    piso1 = state["active_storey_id"]
    draw(project, [(0.0, 0.0), (5.0, 0.0)], closed=False)
    execute(project, "edit_storey", {"id": piso1, "elevation": 3.5})
    draw(project, [(5.0, 0.0), (5.0, 4.0)], closed=False)  # desde el extremo libre del muro (ya movido)
    assert len(project.file.by_type("IfcRelConnectsPathElements")) == 1
    execute(project, "edit_storey", {"id": piso1, "height": 3.2})
    assert all(walls.wall_info(project, w)["height"] == pytest.approx(3.0) for w in project.file.by_type("IfcWall"))


def test_validacion_con_muros(project, tmp_path):
    three_storeys(project)
    draw(project, RING)
    path = str(tmp_path / "validar.ifc")
    execute(project, "save_project", {"path": path})
    assert execute(project, "validate_file", {"path": path})["errors"] == 0  # SC-005


def test_muro_numero_201_rapido(project):
    three_storeys(project)
    for k in range(50):
        x0, y0 = (k % 10) * 7.0, (k // 10) * 5.0
        draw(project, [(x0, y0 + 4.0), (x0 + 6.0, y0 + 4.0), (x0 + 6.0, y0), (x0, y0)])
    assert len(project.file.by_type("IfcWall")) == 200
    started = time.perf_counter()
    draw(project, [(100.0, 0.0), (100.0, 4.0)], closed=False)
    assert (time.perf_counter() - started) < 0.2  # SC-006 (motor)


# ---------- Historia 2: muros compuestos y catálogo ----------
def structure_payload(state, structure_name, **changes):
    """Una estructura del estado como la manda el diálogo (contracts/core_api.md, apply_structures)."""
    row = next(s for s in state["structures"] if s["name"] == structure_name)
    payload = {"id": row["id"], "name": row["name"],
               "layers": [{"material": l["material_id"], "thickness": l["thickness"]} for l in row["layers"]]}
    payload.update(changes)
    return payload


def test_muro_compuesto(project):
    state = three_storeys(project)
    ext30 = structure_id(state, "Muro exterior 30")
    ring = [project.entity(i) for i in draw(project, RING, structure_id=ext30, material_id=None, thickness=None)]
    usages = {ifcopenshell.util.element.get_material(w) for w in ring}
    assert len(usages) == 4 and len({u.ForLayerSet for u in usages}) == 1  # usage propia, conjunto compartido
    meshes = {m["id"]: m for m in execute(project, "meshes", {"ids": [w.id() for w in ring]})["meshes"]}
    expected = [material_id(state, n) for n in ("Revoque", "Ladrillo", "Aislación", "Revoque")]
    assert all([g["material_id"] for g in meshes[w.id()]["groups"]] == expected for w in ring)
    assert sum(layer_area(project, w) for w in ring) == pytest.approx(6 * 4 - 5.4 * 3.4, rel=0.001)
    # La primera capa (Revoque 0,02) queda del lado de afuera del recinto: en el muro de arriba, entre y 3,98 y 4,00.
    top = ring[0]
    first = layers.layer_polygons(top, 1.0)[0][1]
    matrix = walls.placement_matrix(project, top)
    world_y = [(matrix @ np.array([x, y, 0.0, 1.0]))[1] for x, y in first]
    assert (min(world_y), max(world_y)) == pytest.approx((3.98, 4.0))


def _new_state(project, payload):
    return execute(project, "apply_structures", payload)["state"]


@pytest.mark.parametrize("caso, error", [
    ("vacio", "El nombre no puede quedar vacío."),
    ("repetido", "Ya existe una estructura llamada «tabique 15»."),
    ("sin_capas", "La estructura tiene que tener al menos una capa."),
    ("capa_cero", "La capa 2 de «Muro exterior 30» tiene que tener un espesor mayor que 0."),
    ("en_uso_1", "La estructura «Muro exterior 30» la usa 1 muro; no se puede borrar."),
    ("en_uso_3", "La estructura «Muro exterior 30» la usan 3 muros; no se puede borrar."),
    ("material_repetido", "Ya existe un material llamado «Ladrillo»."),
    ("color", "El color tiene que tener la forma #rrggbb."),
    ("material_inexistente", "El material elegido ya no existe."),
])
def test_apply_structures_reglas(project, caso, error):
    state = three_storeys(project)
    ext30 = structure_id(state, "Muro exterior 30")
    walls_to_draw = {"en_uso_1": 1, "en_uso_3": 3}.get(caso, 0)
    if walls_to_draw:
        draw(project, [(0.0, 0.0), (4.0, 0.0), (4.0, 4.0), (0.0, 4.0)][:walls_to_draw + 1], closed=False,
             structure_id=ext30, material_id=None, thickness=None)
        state = project.state()
    payload = {
        "vacio": {"structures": [structure_payload(state, "Tabique 15", name="  ")]},
        "repetido": {"structures": [structure_payload(state, "Muro exterior 30", name="tabique 15")]},
        "sin_capas": {"structures": [structure_payload(state, "Tabique 15", layers=[])]},
        "capa_cero": {"structures": [structure_payload(state, "Muro exterior 30", layers=[
            {"material": material_id(state, "Revoque"), "thickness": 0.02},
            {"material": material_id(state, "Ladrillo"), "thickness": 0.0}])]},
        "en_uso_1": {"deleted": [ext30]},
        "en_uso_3": {"deleted": [ext30]},
        "material_repetido": {"materials": [{"ref": "m1", "name": "ladrillo", "color": "#123456"}]},
        "color": {"materials": [{"ref": "m1", "name": "Piedra", "color": "rojo"}]},
        "material_inexistente": {"structures": [structure_payload(state, "Tabique 15", layers=[
            {"material": "m9", "thickness": 0.1}])]},
    }[caso]
    if caso == "material_repetido":
        error = "Ya existe un material llamado «ladrillo»."
    before = len(list(project.file))
    with pytest.raises(EngineError) as raised:
        execute(project, "apply_structures", payload)
    assert str(raised.value) == error
    assert len(list(project.file)) == before


def test_apply_structures_crea_duplica_renombra_y_borra(project):
    state = three_storeys(project)
    history = len(project.file.history)
    state = _new_state(project, {
        "materials": [{"ref": "m1", "name": "Piedra", "color": "#8a8174"}],
        "structures": [
            {"id": None, "ref": "s1", "name": "Muro 35", "layers": [
                {"material": "m1", "thickness": 0.30}, {"material": material_id(state, "Revoque"), "thickness": 0.05}]},
            {"id": None, "ref": "s2", "name": "Tabique 15 (copia)", "copy_of": structure_id(state, "Tabique 15"),
             "layers": structure_payload(state, "Tabique 15")["layers"]},
            structure_payload(state, "Muro de hormigón 25", name="Hormigón 25"),
        ],
    })
    assert len(project.file.history) == history + 1  # un solo paso de deshacer
    names = [s["name"] for s in state["structures"]]
    assert names == ["Hormigón 25", "Muro 35", "Muro exterior 30", "Tabique 15", "Tabique 15 (copia)"]
    piedra = next(m for m in state["materials"] if m["name"] == "Piedra")
    assert piedra["color"] == "#8a8174"
    muro35 = next(s for s in state["structures"] if s["name"] == "Muro 35")
    assert [(l["material_id"], l["thickness"]) for l in muro35["layers"]] == [(piedra["id"], 0.30), (material_id(state, "Revoque"), 0.05)]
    renamed = project.entity(structure_id(state, "Hormigón 25"))
    assert materials.layer_set_of(renamed).LayerSetName == "Hormigón 25"
    copy = next(s for s in state["structures"] if s["name"] == "Tabique 15 (copia)")
    assert copy["layers"] == next(s for s in state["structures"] if s["name"] == "Tabique 15")["layers"]
    state = _new_state(project, {"deleted": [copy["id"]]})
    assert "Tabique 15 (copia)" not in [s["name"] for s in state["structures"]]
    execute(project, "undo", {})
    assert "Tabique 15 (copia)" in [s["name"] for s in project.state()["structures"]]


def test_editar_estructura_cambia_sus_muros(project, tmp_path):
    state = three_storeys(project)
    ext30 = structure_id(state, "Muro exterior 30")
    common = {"structure_id": ext30, "material_id": None, "thickness": None, "height": 3.0}
    a = execute(project, "create_wall", {"start": [0.0, 0.0], "end": [5.0, 0.0], **common, "reference": "exterior"})["wall_id"]
    b = execute(project, "create_wall", {"start": [5.0, 0.0], "end": [5.0, 4.0], **common, "reference": "center"})["wall_id"]
    layers_payload = structure_payload(state, "Muro exterior 30")["layers"]
    layers_payload[2]["thickness"] = 0.08  # Aislación 0,05 → 0,08
    result = execute(project, "apply_structures", {"structures": [structure_payload(state, "Muro exterior 30", layers=layers_payload)]})
    assert {a, b} <= set(result["changed_ids"])
    wa, wb = project.entity(a), project.entity(b)
    assert walls.wall_info(project, wa)["thickness"] == pytest.approx(0.33)
    ya = np.concatenate([poly[:, 1] for _, poly, _, _ in layers.layer_polygons(wa, 1.0)])
    yb = np.concatenate([poly[:, 1] for _, poly, _, _ in layers.layer_polygons(wb, 1.0)])
    assert (ya.min(), ya.max()) == pytest.approx((-0.33, 0.0))  # Exterior: la cara exterior sigue en la línea
    assert (yb.min(), yb.max()) == pytest.approx((-0.165, 0.165))  # Centro: sigue centrado
    assert walls.reference_of(project, wa) == "exterior" and walls.reference_of(project, wb) == "center"
    assert len(project.file.by_type("IfcRelConnectsPathElements")) == 1
    path = str(tmp_path / "editada.ifc")
    execute(project, "save_project", {"path": path})
    assert execute(project, "validate_file", {"path": path})["errors"] == 0
    execute(project, "undo", {})
    assert walls.wall_info(project, project.entity(a))["thickness"] == pytest.approx(0.30)


def test_catalogo_guardado_y_reabierto(project, tmp_path):
    state = three_storeys(project)
    state = _new_state(project, {
        "materials": [{"ref": "m1", "name": "Piedra", "color": "#8a8174"}],
        "structures": [{"id": None, "ref": "s1", "name": "Muro 35", "layers": [
            {"material": "m1", "thickness": 0.30}, {"material": material_id(state, "Revoque"), "thickness": 0.05}]}]})
    before = (state["materials"], [(s["name"], s["thickness"], len(s["layers"])) for s in state["structures"]])
    path = str(tmp_path / "catalogo.ifc")
    execute(project, "save_project", {"path": path})
    state = execute(project, "open_project", {"path": path})["state"]
    after = (state["materials"], [(s["name"], s["thickness"], len(s["layers"])) for s in state["structures"]])
    assert [(m["name"], m["color"]) for m in after[0]] == [(m["name"], m["color"]) for m in before[0]]
    assert after[1] == before[1]


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
