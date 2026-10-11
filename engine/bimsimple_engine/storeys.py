"""Pisos (IfcBuildingStorey) del edificio: lectura según data-model.md §3 y creación con la API LGPL de IfcOpenShell."""

import numpy as np
import ifcopenshell.api.aggregate
import ifcopenshell.api.attribute
import ifcopenshell.api.geometry
import ifcopenshell.api.pset
import ifcopenshell.api.root
import ifcopenshell.util.element
import ifcopenshell.util.placement

from . import EngineError

DEFAULT_HEIGHT = 3.0
QTO = "Qto_BuildingStoreyBaseQuantities"


# ---------- lectura ----------
def buildings(project):
    return project.file.by_type("IfcBuilding")


def building(project):
    found = buildings(project)
    return found[0] if found else None


def storey_entities(project):
    work_building = building(project)
    if work_building is None:
        return []
    return [e for e in ifcopenshell.util.element.get_decomposition(work_building) if e.is_a("IfcBuildingStorey")]


def elevation(project, storey):
    """Cota en metros: Z absoluta de la ubicación, o Elevation si el piso no tiene ubicación."""
    return float(ifcopenshell.util.placement.get_storey_elevation(storey)) * project.unit_scale()


def gross_height(project, storey):
    value = ifcopenshell.util.element.get_psets(storey, qtos_only=True).get(QTO, {}).get("GrossHeight")
    return float(value) * project.unit_scale() if value is not None else None


def elements(storey):
    """Elementos del piso (contenidos, partes, rellenos), sin aberturas."""
    return [e for e in ifcopenshell.util.element.get_decomposition(storey)
            if e.is_a("IfcElement") and not e.is_a("IfcFeatureElementSubtraction")]


def ordered(project):
    """Pisos de menor a mayor cota (empate por nombre), con su cota y altura en metros."""
    rows = sorted(((elevation(project, s), s.Name or "", s) for s in storey_entities(project)),
                  key=lambda row: (row[0], row[1]))
    result = []
    for i, (z, name, storey) in enumerate(rows):
        if i + 1 < len(rows):
            height = rows[i + 1][0] - z  # distancia al piso de arriba
        else:
            height = gross_height(project, storey) or DEFAULT_HEIGHT
        result.append({"entity": storey, "id": storey.id(), "name": name, "elevation": round(z, 4),
                       "height": round(height, 4)})
    return result


def list_storeys(project):
    """Pisos para la interfaz, del más alto al más bajo."""
    return [{"id": r["id"], "name": r["name"], "elevation": r["elevation"], "height": r["height"],
             "elements": len(elements(r["entity"]))} for r in reversed(ordered(project))]


def notice(project):
    found = buildings(project)
    if len(found) > 1:
        return f"El archivo tiene {len(found)} edificios; se muestran los pisos de «{found[0].Name or ''}»"
    if not storey_entities(project):
        return "Este archivo no tiene pisos"
    return ""


def nearest_to_zero(project):
    rows = ordered(project)
    return min(rows, key=lambda r: abs(r["elevation"]))["id"] if rows else None


# ---------- creación ----------
def create_storey(project, name, z, height):
    """Crea un IfcBuildingStorey en el edificio, a la cota z (m), con su GrossHeight (m)."""
    f = project.file
    scale = project.unit_scale()
    storey = ifcopenshell.api.root.create_entity(f, ifc_class="IfcBuildingStorey", name=name)
    ifcopenshell.api.aggregate.assign_object(f, products=[storey], relating_object=building(project))
    matrix = np.eye(4)
    matrix[2][3] = z
    ifcopenshell.api.geometry.edit_object_placement(f, product=storey, matrix=matrix, is_si=True)
    building_z = float(ifcopenshell.util.placement.get_local_placement(building(project).ObjectPlacement)[2][3]) * scale \
        if building(project).ObjectPlacement else 0.0
    ifcopenshell.api.attribute.edit_attributes(f, product=storey, attributes={"Elevation": (z - building_z) / scale})
    set_gross_height(project, storey, height)
    return storey


def set_gross_height(project, storey, height):
    f = project.file
    qto_id = ifcopenshell.util.element.get_psets(storey, qtos_only=True).get(QTO, {}).get("id")
    qto = f.by_id(qto_id) if qto_id else ifcopenshell.api.pset.add_qto(f, product=storey, name=QTO)
    ifcopenshell.api.pset.edit_qto(f, qto=qto, properties={"GrossHeight": height / project.unit_scale()})


# ---------- órdenes de pisos (FR-013 a FR-017; data-model.md §3) ----------
def _fmt(value):
    return f"{value:.2f}".replace(".", ",")


def _require_building(project):
    project.require_project()
    if building(project) is None:
        raise EngineError("Este archivo no tiene un edificio donde agregar pisos.")


def _row(project, storey_id):
    rows = ordered(project)
    for i, row in enumerate(rows):
        if row["id"] == storey_id:
            return rows, i
    raise EngineError("El piso indicado ya no existe.")


def _move(project, storey, delta):
    """Mueve el piso delta metros en Z con todos sus elementos (should_transform_children) y actualiza Elevation."""
    f = project.file
    scale = project.unit_scale()
    z = elevation(project, storey) + delta
    if storey.ObjectPlacement:
        matrix = np.array(ifcopenshell.util.placement.get_local_placement(storey.ObjectPlacement), dtype=float)
        matrix[:3, 3] *= scale  # a metros
        matrix[2][3] = z
    else:
        matrix = np.eye(4)
        matrix[2][3] = z
    ifcopenshell.api.geometry.edit_object_placement(f, product=storey, matrix=matrix, is_si=True,
                                                    should_transform_children=True)
    work_building = building(project)
    building_z = (float(ifcopenshell.util.placement.get_local_placement(work_building.ObjectPlacement)[2][3]) * scale
                  if work_building.ObjectPlacement else 0.0)
    ifcopenshell.api.attribute.edit_attributes(f, product=storey, attributes={"Elevation": (z - building_z) / scale})
    return [storey.id()] + [e.id() for e in elements(storey)]


def _add(project, name, z, height):
    storey = project.transaction(lambda: create_storey(project, name, z, height))
    return {"state": project.state(), "storey_id": storey.id()}


def add_storey_above(project):
    _require_building(project)
    rows = ordered(project)
    if not rows:
        return _add(project, "Planta Baja", 0.0, DEFAULT_HEIGHT)
    top = rows[-1]
    n = sum(1 for r in rows if r["elevation"] > 0) + 1
    return _add(project, f"Piso {n}", top["elevation"] + top["height"], top["height"])


def add_storey_below(project):
    _require_building(project)
    rows = ordered(project)
    if not rows:
        return _add(project, "Planta Baja", 0.0, DEFAULT_HEIGHT)
    bottom = rows[0]
    n = sum(1 for r in rows if r["elevation"] < 0) + 1
    return _add(project, f"Sótano {n}", bottom["elevation"] - DEFAULT_HEIGHT, DEFAULT_HEIGHT)


def edit_storey(project, id, name=None, elevation=None, height=None):
    """Aplica solo lo que viene, en una transacción. Valida todo antes de cambiar nada."""
    project.require_project()
    rows, i = _row(project, id)
    if name is not None and not name.strip():
        raise EngineError("El nombre del piso no puede quedar vacío.")
    if height is not None and height <= 0:
        raise EngineError("La altura debe ser mayor que 0.")
    if elevation is not None and i > 0 and elevation <= rows[i - 1]["elevation"]:
        below = rows[i - 1]
        raise EngineError(f"La cota debe ser mayor que la del piso de abajo («{below['name']}», {_fmt(below['elevation'])} m).")

    def apply():
        changed = set()
        storey = rows[i]["entity"]
        if name is not None:
            ifcopenshell.api.attribute.edit_attributes(project.file, product=storey, attributes={"Name": name.strip()})
        if elevation is not None and abs(elevation - rows[i]["elevation"]) > 1e-9:
            delta = elevation - rows[i]["elevation"]
            for row in rows[i:]:  # el piso y todos los de arriba
                changed.update(_move(project, row["entity"], delta))
            if i > 0:
                set_gross_height(project, rows[i - 1]["entity"], elevation - rows[i - 1]["elevation"])
        if height is not None:
            current = ordered(project)
            j = next(k for k, r in enumerate(current) if r["id"] == id)
            if j + 1 < len(current):  # no es el más alto: los de arriba se mueven
                delta = height - current[j]["height"]
                if abs(delta) > 1e-9:
                    for row in current[j + 1:]:
                        changed.update(_move(project, row["entity"], delta))
            set_gross_height(project, storey, height)
        return sorted(changed)

    changed = project.transaction(apply)
    return {"state": project.state(), "changed_ids": changed}


def count_storey_elements(project, id):
    project.require_project()
    rows, i = _row(project, id)
    return {"count": len(elements(rows[i]["entity"]))}


def delete_storey(project, id):
    project.require_project()
    rows, i = _row(project, id)
    if len(rows) <= 1:
        raise EngineError("No se puede borrar el único piso del edificio.")
    storey = rows[i]["entity"]
    deleted = [e.id() for e in elements(storey)] + [storey.id()]

    def apply():
        for element in elements(storey):
            ifcopenshell.api.root.remove_product(project.file, product=element)
        ifcopenshell.api.root.remove_product(project.file, product=storey)
        if 0 < i < len(rows) - 1:  # el de abajo pasa a medir hasta el siguiente; los de arriba no se mueven
            set_gross_height(project, rows[i - 1]["entity"], rows[i + 1]["elevation"] - rows[i - 1]["elevation"])

    project.transaction(apply)
    if project.active_storey_id == id:
        project.active_storey_id = rows[i - 1]["id"] if i > 0 else rows[i + 1]["id"]
    return {"state": project.state(), "deleted_ids": deleted}
