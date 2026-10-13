"""Materiales con su color y catálogo de estructuras compuestas (data-model.md §1-2; research R7, R11).

Una estructura compuesta es un IfcWallType con un IfcMaterialLayerSet del mismo nombre; el color de un material es
un IfcSurfaceStyle asignado en el contexto Body.
"""

import re

import ifcopenshell.api.material
import ifcopenshell.api.root
import ifcopenshell.api.style
import ifcopenshell.util.element
import ifcopenshell.util.representation

from . import EngineError

DEFAULT_COLOR = "#d9d9d6"
COLOR_PATTERN = re.compile(r"^#[0-9a-fA-F]{6}$")

DEFAULT_MATERIALS = [  # research R7
    ("Hormigón", "#b5b5b0"),
    ("Ladrillo", "#c1694f"),
    ("Bloque de hormigón", "#9a9a94"),
    ("Revoque", "#e8e2d4"),
    ("Aislación", "#f2d24b"),
    ("Placa de yeso", "#f4f4f0"),
    ("Madera", "#b9875a"),
]

DEFAULT_STRUCTURES = [  # spec, Supuestos
    ("Muro de hormigón 25", [("Hormigón", 0.20), ("Aislación", 0.05)]),
    ("Muro exterior 30", [("Revoque", 0.02), ("Ladrillo", 0.20), ("Aislación", 0.05), ("Revoque", 0.03)]),
    ("Tabique 15", [("Revoque", 0.015), ("Ladrillo", 0.12), ("Revoque", 0.015)]),
]


def body_context(project):
    return ifcopenshell.util.representation.get_context(project.file, "Model", "Body", "MODEL_VIEW")


def _hex_to_rgb(color):
    return tuple(int(color[i:i + 2], 16) / 255 for i in (1, 3, 5))


def _rgb_to_hex(red, green, blue):
    return "#" + "".join(f"{max(0, min(255, round(v * 255))):02x}" for v in (red, green, blue))


# ---------- materiales ----------
def materials(project):
    return project.file.by_type("IfcMaterial")


def material(project, material_id):
    entity = project.entity(material_id) if isinstance(material_id, int) else None
    if entity is None or not entity.is_a("IfcMaterial"):
        raise EngineError("El material elegido ya no existe.")
    return entity


def material_color(project, mat):
    context = body_context(project)
    style = ifcopenshell.util.representation.get_material_style(mat, context) if context else None
    for item in (style.Styles if style else None) or ():
        colour = getattr(item, "SurfaceColour", None)
        if colour is not None:
            return _rgb_to_hex(colour.Red, colour.Green, colour.Blue)
    return DEFAULT_COLOR


def list_materials(project):
    rows = [{"id": m.id(), "name": m.Name or "", "color": material_color(project, m)} for m in materials(project)]
    return sorted(rows, key=lambda r: (r["name"].casefold(), r["id"]))


def check_material_name(project, name, taken=None):
    """Nombre no vacío y único sin distinguir mayúsculas (FR-016). taken: nombres ya ocupados además del IFC."""
    if not name or not name.strip():
        raise EngineError("El nombre del material no puede quedar vacío.")
    names = {(m.Name or "").casefold() for m in materials(project)} | {n.casefold() for n in (taken or ())}
    if name.strip().casefold() in names:
        raise EngineError(f"Ya existe un material llamado «{name.strip()}».")


def check_color(color):
    if not isinstance(color, str) or not COLOR_PATTERN.match(color):
        raise EngineError("El color tiene que tener la forma #rrggbb.")


def add_material(project, name, color):
    """IfcMaterial con un IfcSurfaceStyleShading de ese color en el contexto Body (research R7)."""
    f = project.file
    mat = ifcopenshell.api.material.add_material(f, name=name.strip())
    style = ifcopenshell.api.style.add_style(f, name=name.strip())
    red, green, blue = _hex_to_rgb(color)
    ifcopenshell.api.style.add_surface_style(
        f, style=style, ifc_class="IfcSurfaceStyleShading",
        attributes={"SurfaceColour": {"Name": None, "Red": red, "Green": green, "Blue": blue}, "Transparency": 0.0})
    ifcopenshell.api.style.assign_material_style(f, material=mat, style=style, context=body_context(project))
    return mat


# ---------- estructuras compuestas ----------
def layer_set_of(element):
    """IfcMaterialLayerSet de un tipo o de una ocurrencia (a través de su usage), o None."""
    found = ifcopenshell.util.element.get_material(element)
    if found is None:
        return None
    if found.is_a("IfcMaterialLayerSetUsage"):
        return found.ForLayerSet
    return found if found.is_a("IfcMaterialLayerSet") else None


def structure_types(project):
    return [t for t in project.file.by_type("IfcWallType") if layer_set_of(t) is not None]


def structure(project, structure_id):
    entity = project.entity(structure_id) if isinstance(structure_id, int) else None
    if entity is None or not entity.is_a("IfcWallType") or layer_set_of(entity) is None:
        raise EngineError("La estructura elegida ya no existe.")
    return entity


def layers_of(project, layer_set):
    scale = project.unit_scale()
    return [{"material_id": layer.Material.id() if layer.Material else None,
             "thickness": round(float(layer.LayerThickness) * scale, 6)} for layer in layer_set.MaterialLayers]


def list_structures(project):
    rows = []
    for wall_type in structure_types(project):
        layers = layers_of(project, layer_set_of(wall_type))
        rows.append({"id": wall_type.id(), "name": wall_type.Name or "",
                     "thickness": round(sum(layer["thickness"] for layer in layers), 6),
                     "walls": len(ifcopenshell.util.element.get_types(wall_type)), "layers": layers})
    return sorted(rows, key=lambda r: (r["name"].casefold(), r["id"]))


def create_structure(project, name, layers):
    """layers: [(IfcMaterial, espesor en metros)], de exterior a interior (research R11)."""
    f = project.file
    scale = project.unit_scale()
    wall_type = ifcopenshell.api.root.create_entity(f, ifc_class="IfcWallType", name=name, predefined_type="STANDARD")
    layer_set = ifcopenshell.api.material.add_material_set(f, name=name, set_type="IfcMaterialLayerSet")
    for mat, thickness in layers:
        layer = ifcopenshell.api.material.add_layer(f, layer_set=layer_set, material=mat)
        ifcopenshell.api.material.edit_layer(f, layer=layer, attributes={"LayerThickness": thickness / scale})
    ifcopenshell.api.material.assign_material(f, products=[wall_type], type="IfcMaterialLayerSet", material=layer_set)
    return wall_type


def add_default_catalog(project):
    """Los 7 materiales y las 3 estructuras de ejemplo de un proyecto nuevo."""
    by_name = {name: add_material(project, name, color) for name, color in DEFAULT_MATERIALS}
    for name, layers in DEFAULT_STRUCTURES:
        create_structure(project, name, [(by_name[m], t) for m, t in layers])
