"""Muros (IfcWall) con capas: datos para la interfaz, clases de muro e índice de extremos
(data-model.md §3, §4 y §6; research R3, R5 y R10)."""

import numpy as np
import ifcopenshell.util.element
import ifcopenshell.util.placement
import ifcopenshell.util.representation

from . import layers, materials

LOCKED_REASON = "Este muro viene de otro programa y BIM Simple no puede cambiar su forma; se puede borrar."
REFERENCES = ("exterior", "center", "interior")
JOIN_TOLERANCE = 0.001  # metros (research R4)


# ---------- lectura ----------
def is_wall(element):
    return element is not None and element.is_a("IfcWall")


def placement_matrix(project, wall):
    """Ubicación del muro en el mundo, con la traslación en metros."""
    matrix = np.array(ifcopenshell.util.placement.get_local_placement(wall.ObjectPlacement), dtype=float)
    matrix[:3, 3] *= project.unit_scale()
    return matrix


def axis_representation(wall):
    return ifcopenshell.util.representation.get_representation(wall, "Plan", "Axis", "GRAPH_VIEW")


def local_axis(project, wall):
    """Extremos del eje en coordenadas locales del muro (metros)."""
    scale = project.unit_scale()
    return [np.array(p[:2], dtype=float) * scale for p in ifcopenshell.util.representation.get_reference_line(wall)]


def endpoints(project, wall):
    """Extremos del eje en el mundo: [(x, y), (x, y)] en metros."""
    matrix = placement_matrix(project, wall)
    return [tuple(float(v) for v in (matrix @ np.array([p[0], p[1], 0.0, 1.0]))[:2]) for p in local_axis(project, wall)]


def thicknesses(project, wall):
    usage = layers.usage_of(wall)
    if usage is None:
        return []
    scale = project.unit_scale()
    return [float(layer.LayerThickness) * scale for layer in usage.ForLayerSet.MaterialLayers]


def reference_of(project, wall):
    """exterior, center o interior según el sentido NEGATIVE y el desplazamiento 0, T/2 o T; si no, other (R3)."""
    usage = layers.usage_of(wall)
    if usage is None or usage.DirectionSense != "NEGATIVE":
        return "other"
    total = sum(thicknesses(project, wall))
    offset = float(usage.OffsetFromReferenceLine) * project.unit_scale()
    for name, value in zip(REFERENCES, (0.0, total / 2, total)):
        if abs(offset - value) <= layers.TOL:
            return name
    return "other"


def offset_for(reference, total):
    """Desplazamiento de la usage (metros) para una línea de referencia, con sentido NEGATIVE (research R3)."""
    return {"exterior": 0.0, "center": total / 2, "interior": total}[reference]


def path_connections(wall):
    """[(otro muro, tipo de unión de este muro, rel)] de las IfcRelConnectsPathElements del muro (research R4)."""
    result = []
    for rel in list(wall.ConnectedTo or ()) + list(wall.ConnectedFrom or ()):
        if not rel.is_a("IfcRelConnectsPathElements"):
            continue
        if rel.RelatingElement == wall:
            result.append((rel.RelatedElement, rel.RelatingConnectionType, rel))
        else:
            result.append((rel.RelatingElement, rel.RelatedConnectionType, rel))
    return result


def kind_of(project, wall):
    """regenerable, custom_ends o locked (research R10)."""
    usage = layers.usage_of(wall)
    if usage is None or axis_representation(wall) is None or layers.body_solid(wall) is None:
        return "locked"
    polygons = layers.layer_polygons(wall, project.unit_scale())
    if not polygons or any(len(poly) < 3 for _, poly, _, _ in polygons):
        return "locked"
    if path_connections(wall):
        return "regenerable"
    start, end = local_axis(project, wall)
    if abs(start[1]) > layers.TOL or abs(end[1]) > layers.TOL or abs(start[0]) > layers.TOL:
        return "custom_ends"
    polygon, _, _ = layers.profile_polygon(layers.body_solid(wall), project.unit_scale())
    strips = layers.layer_strips(usage, thicknesses(project, wall), project.unit_scale())
    y_min, y_max = min(s[0] for s in strips), max(s[1] for s in strips)
    return "regenerable" if layers.is_plain_strip(polygon, float(end[0]), y_min, y_max) else "custom_ends"


def height_of(project, wall):
    solid = layers.body_solid(wall)
    return float(solid.Depth) * project.unit_scale() if solid is not None else 0.0


def structure_of(wall):
    """El tipo de muro si es una estructura del catálogo; None si el muro es Básico."""
    wall_type = ifcopenshell.util.element.get_type(wall)
    if wall_type is not None and wall_type.is_a("IfcWallType") and materials.layer_set_of(wall_type) is not None:
        return wall_type
    return None


def wall_info(project, wall):
    """Datos del muro para la interfaz (data-model.md §6)."""
    container = ifcopenshell.util.element.get_container(wall)
    kind = kind_of(project, wall)
    usage = layers.usage_of(wall)
    layer_rows = materials.layers_of(project, usage.ForLayerSet) if usage is not None else []
    try:
        start, end = endpoints(project, wall)
    except Exception:  # sin eje ni perfil que lo reemplace
        start = end = None
    structure = structure_of(wall)
    return {
        "id": wall.id(),
        "storey_id": container.id() if container is not None and container.is_a("IfcBuildingStorey") else None,
        "start": list(start) if start else None,
        "end": list(end) if end else None,
        "reference": reference_of(project, wall),
        "height": round(height_of(project, wall), 6),
        "structure_id": structure.id() if structure is not None else None,
        "layers": layer_rows,
        "thickness": round(sum(row["thickness"] for row in layer_rows), 6),
        "kind": kind,
        "locked_reason": LOCKED_REASON if kind == "locked" else "",
    }


# ---------- índice de extremos (research R5) ----------
class EndpointIndex:
    """Piso → celda de 1 mm → ids de muros con un extremo ahí. Vive en el motor, fuera del IFC."""

    def __init__(self, project):
        self.project = project
        self.storeys = {}

    @staticmethod
    def _key(point):
        return (round(point[0], 3), round(point[1], 3))

    def _storey(self, storey_id):
        if storey_id not in self.storeys:
            cells = {}
            storey = self.project.entity(storey_id)
            for element in ifcopenshell.util.element.get_contained(storey) if storey is not None else []:
                if is_wall(element) and kind_of(self.project, element) != "locked":
                    for point in endpoints(self.project, element):
                        cells.setdefault(self._key(point), set()).add(element.id())
            self.storeys[storey_id] = cells
        return self.storeys[storey_id]

    def add(self, wall):
        container = ifcopenshell.util.element.get_container(wall)
        if container is None or kind_of(self.project, wall) == "locked":
            return
        cells = self._storey(container.id())
        for point in endpoints(self.project, wall):
            cells.setdefault(self._key(point), set()).add(wall.id())

    def remove(self, wall_id):
        for cells in self.storeys.values():
            for ids in cells.values():
                ids.discard(wall_id)

    def near(self, storey_id, point):
        """Ids de muros del piso con un extremo a menos de 1 mm del punto."""
        cells = self._storey(storey_id)
        x, y = self._key(point)
        found = set()
        for dx in (-0.001, 0.0, 0.001):
            for dy in (-0.001, 0.0, 0.001):
                for wall_id in cells.get((round(x + dx, 3), round(y + dy, 3)), ()):
                    wall = self.project.entity(wall_id)
                    if wall is not None and any(np.hypot(p[0] - point[0], p[1] - point[1]) <= JOIN_TOLERANCE
                                                for p in endpoints(self.project, wall)):
                        found.add(wall_id)
        return found


def index(project):
    if project.endpoint_index is None:
        project.endpoint_index = EndpointIndex(project)
    return project.endpoint_index
