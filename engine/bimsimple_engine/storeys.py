"""Pisos (IfcBuildingStorey) del edificio: lectura según data-model.md §3 y creación con la API LGPL de IfcOpenShell."""

import numpy as np
import ifcopenshell.api.aggregate
import ifcopenshell.api.attribute
import ifcopenshell.api.geometry
import ifcopenshell.api.pset
import ifcopenshell.api.root
import ifcopenshell.util.element
import ifcopenshell.util.placement

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
