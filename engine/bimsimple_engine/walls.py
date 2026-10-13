"""Muros (IfcWall) con capas: datos para la interfaz, clases de muro e índice de extremos
(data-model.md §3, §4 y §6; research R3, R5 y R10)."""

import numpy as np
import ifcopenshell.api.attribute
import ifcopenshell.api.geometry
import ifcopenshell.api.material
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.api.type
import ifcopenshell.util.element
import ifcopenshell.util.placement
import ifcopenshell.util.representation

from . import EngineError, layers, materials, storeys

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


class Analysis:
    """Lo que el motor lee de un muro una sola vez por orden: ubicación, eje, cuerpo, capas, uniones y clase."""

    def __init__(self, project, wall):
        scale = project.unit_scale()
        self.usage = layers.usage_of(wall)
        self.solid = layers.body_solid(wall)
        self.matrix = placement_matrix(project, wall)
        try:
            self.local = local_axis(project, wall)
        except Exception:  # sin eje ni perfil que lo reemplace
            self.local = None
        self.connections = path_connections(wall)
        self.polygons = None
        self.profile = None
        if self.usage is not None and self.solid is not None and self.usage.ForLayerSet.MaterialLayers:
            self.profile, z0, depth = layers.profile_polygon(self.solid, scale)
            thickness = [float(layer.LayerThickness) * scale for layer in self.usage.ForLayerSet.MaterialLayers]
            self.strips = layers.layer_strips(self.usage, thickness, scale)
            self.polygons = [(layer, layers.clip_strip(self.profile, y_min, y_max), z0, depth)
                             for layer, (y_min, y_max) in zip(self.usage.ForLayerSet.MaterialLayers, self.strips)]
        self.kind = self._kind(wall)

    def _kind(self, wall):
        """regenerable, custom_ends o locked (research R10)."""
        if self.usage is None or axis_representation(wall) is None or self.solid is None or self.local is None:
            return "locked"
        if not self.polygons or any(len(poly) < 3 for _, poly, _, _ in self.polygons):
            return "locked"
        if self.connections:
            return "regenerable"
        start, end = self.local
        if abs(start[1]) > layers.TOL or abs(end[1]) > layers.TOL or abs(start[0]) > layers.TOL:
            return "custom_ends"
        y_min, y_max = min(s[0] for s in self.strips), max(s[1] for s in self.strips)
        return "regenerable" if layers.is_plain_strip(self.profile, float(end[0]), y_min, y_max) else "custom_ends"

    def endpoints(self):
        if self.local is None:
            return None
        return [tuple(float(v) for v in (self.matrix @ np.array([p[0], p[1], 0.0, 1.0]))[:2]) for p in self.local]


def analyze(project, wall):
    return Analysis(project, wall)


def kind_of(project, wall):
    """regenerable, custom_ends o locked (research R10)."""
    return Analysis(project, wall).kind


def height_of(project, wall):
    solid = layers.body_solid(wall)
    return float(solid.Depth) * project.unit_scale() if solid is not None else 0.0


def structure_of(wall):
    """El tipo de muro si es una estructura del catálogo; None si el muro es Básico."""
    wall_type = ifcopenshell.util.element.get_type(wall)
    if wall_type is not None and wall_type.is_a("IfcWallType") and materials.layer_set_of(wall_type) is not None:
        return wall_type
    return None


def wall_info(project, wall, analysis=None):
    """Datos del muro para la interfaz (data-model.md §6)."""
    a = analysis or Analysis(project, wall)
    container = ifcopenshell.util.element.get_container(wall)
    kind = a.kind
    usage = a.usage
    layer_rows = materials.layers_of(project, usage.ForLayerSet) if usage is not None else []
    start, end = a.endpoints() or (None, None)
    structure = structure_of(wall)
    return {
        "id": wall.id(),
        "storey_id": container.id() if container is not None and container.is_a("IfcBuildingStorey") else None,
        "start": list(start) if start else None,
        "end": list(end) if end else None,
        "reference": reference_of(project, wall),
        "height": round(float(a.solid.Depth) * project.unit_scale(), 6) if a.solid is not None else 0.0,
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
                if not is_wall(element):
                    continue
                analysis = Analysis(self.project, element)
                if analysis.kind != "locked":
                    for point in analysis.endpoints():
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


# ---------- validaciones (contracts/core_api.md, "Errores esperables") ----------
MIN_LENGTH = 0.01  # metros (spec, casos límite)


def check_positive(value, message):
    if not isinstance(value, (int, float)) or value <= 0:
        raise EngineError(message)


def check_reference(reference):
    if reference not in REFERENCES:
        raise EngineError("Línea de referencia no válida.")


def _point(value):
    if not isinstance(value, (list, tuple)) or len(value) != 2 or not all(isinstance(v, (int, float)) for v in value):
        raise EngineError("Punto no válido.")
    return (float(value[0]), float(value[1]))


def _contexts(project):
    f = project.file
    body = ifcopenshell.util.representation.get_context(f, "Model", "Body", "MODEL_VIEW")
    axis = ifcopenshell.util.representation.get_context(f, "Plan", "Axis", "GRAPH_VIEW")
    return body, axis


def regenerate(project, wall_list):
    """regenerate_wall_representation (research R4) de cada muro, con su altura actual."""
    for wall in wall_list:
        ifcopenshell.api.geometry.regenerate_wall_representation(project.file, wall=wall, length=1.0,
                                                                  height=height_of(project, wall))


def connected_walls(wall):
    return [other for other, _, _ in path_connections(wall)]


def end_is_joined(project, wall, point):
    """True si el extremo del muro que está en point ya tiene una unión ATSTART/ATEND."""
    first, last = endpoints(project, wall)
    end = "ATSTART" if np.hypot(first[0] - point[0], first[1] - point[1]) <= JOIN_TOLERANCE else "ATEND"
    return any(connection == end for _, connection, _ in path_connections(wall))


def basic_layer_set(project, mat, thickness):
    """Conjunto propio de una capa de un muro Básico (LayerSetName "Básica"; research R2)."""
    f = project.file
    layer_set = ifcopenshell.api.material.add_material_set(f, name="Básica", set_type="IfcMaterialLayerSet")
    layer = ifcopenshell.api.material.add_layer(f, layer_set=layer_set, material=mat)
    ifcopenshell.api.material.edit_layer(f, layer=layer, attributes={"LayerThickness": thickness / project.unit_scale()})
    return layer_set


def set_usage(project, wall, reference):
    """Sentido NEGATIVE y desplazamiento de la línea de referencia (research R3)."""
    usage = layers.usage_of(wall)
    total = sum(thicknesses(project, wall))
    ifcopenshell.api.material.edit_layer_usage(project.file, usage=usage, attributes={
        "DirectionSense": "NEGATIVE", "OffsetFromReferenceLine": offset_for(reference, total) / project.unit_scale()})


# ---------- crear (FR-005, FR-011 a FR-014; research R4) ----------
def create_wall(project, start, end, structure_id=None, material_id=None, thickness=None, height=None,
                reference="exterior"):
    project.require_project()
    storey = project.entity(project.active_storey_id) if project.active_storey_id else None
    if storey is None:
        raise EngineError("No hay un piso activo donde dibujar.")
    start, end = _point(start), _point(end)
    length = float(np.hypot(end[0] - start[0], end[1] - start[1]))
    if length < MIN_LENGTH:
        raise EngineError("El muro es demasiado corto (mínimo 1 cm).")
    check_positive(height, "La altura debe ser mayor que 0.")
    check_reference(reference)
    if structure_id is not None:
        wall_type = materials.structure(project, structure_id)
        mat = None
    else:
        wall_type = None
        mat = materials.material(project, material_id)
        check_positive(thickness, "El espesor debe ser mayor que 0.")

    def apply():
        f = project.file
        body, axis = _contexts(project)
        wall = ifcopenshell.api.root.create_entity(f, ifc_class="IfcWall", name="Muro")
        ifcopenshell.api.spatial.assign_container(f, products=[wall], relating_structure=storey)
        if wall_type is not None:
            ifcopenshell.api.type.assign_type(f, related_objects=[wall], relating_type=wall_type)  # una por muro
        else:
            ifcopenshell.api.material.assign_material(f, products=[wall], type="IfcMaterialLayerSetUsage",
                                                      material=basic_layer_set(project, mat, thickness))
        set_usage(project, wall, reference)
        total = sum(thicknesses(project, wall))
        # La cota es absoluta: edit_object_placement la pasa a relativa al piso (research R4).
        rep = ifcopenshell.api.geometry.create_2pt_wall(f, element=wall, context=body, p1=start, p2=end,
                                                        elevation=storeys.elevation(project, storey), height=height,
                                                        thickness=total)
        ifcopenshell.api.geometry.assign_representation(f, product=wall, representation=rep)
        scale = project.unit_scale()
        rep = ifcopenshell.api.geometry.add_axis_representation(f, context=axis, axis=[(0.0, 0.0), (length / scale, 0.0)])
        ifcopenshell.api.geometry.assign_representation(f, product=wall, representation=rep)
        touched = {wall}
        idx = index(project)
        for point in (start, end):
            for other_id in sorted(idx.near(storey.id(), point)):
                other = project.entity(other_id)
                if other is None or other == wall or kind_of(project, other) != "regenerable":
                    continue  # no se une con capas de esquina cortada ni con muros bloqueados (research R10)
                if end_is_joined(project, other, point):
                    continue  # un extremo admite una sola unión (connect_path.py:36-70): la esquina existente no cambia
                if ifcopenshell.api.geometry.connect_wall(f, wall, other) is not None:  # None: ejes paralelos
                    touched.add(other)
                    break
        # El muro nuevo se regenera siempre: create_2pt_wall deja el cuerpo hacia +Y sin mirar la usage, y recién la
        # regeneración lo pone del lado de su línea de referencia (research R3).
        regenerate(project, [wall] + [w for w in touched if w != wall and kind_of(project, w) != "locked"])
        return wall, touched

    try:
        wall, touched = project.transaction(apply)
    except Exception:
        project.discard_index()
        raise
    index(project).add(wall)
    return {"state": project.state(), "wall_id": wall.id(), "changed_ids": sorted(w.id() for w in touched)}


# ---------- separar en capas (FR-019 a FR-022; research R8) ----------
def require_walls(project, ids):
    project.require_project()
    found = [project.entity(i) if isinstance(i, int) else None for i in ids or []]
    if not found or any(not is_wall(w) for w in found):
        raise EngineError("Uno de los muros elegidos ya no existe.")
    return found


def own_layer_set(project, wall):
    """El conjunto de capas propio de un muro Básico (no el de un tipo ni uno compartido), o None."""
    if structure_of(wall) is not None:
        return None
    usage = layers.usage_of(wall)
    if usage is None:
        return None
    others = [u for u in project.file.get_inverse(usage.ForLayerSet) if u.is_a("IfcMaterialLayerSetUsage") and u != usage]
    return None if others else usage.ForLayerSet


def separate_layer(project, wall, layer, polygon, z0, depth, sense):
    """Un muro Básico con la forma exacta de una capa: ubicado sobre su cara exterior, sin uniones (research R8)."""
    import ifcopenshell.util.shape_builder

    f = project.file
    scale = project.unit_scale()
    body, axis = _contexts(project)
    y_face = float(polygon[:, 1].max() if sense == "NEGATIVE" else polygon[:, 1].min())
    on_face = polygon[np.abs(polygon[:, 1] - y_face) <= layers.TOL]
    xs = on_face[:, 0] if len(on_face) else polygon[:, 0]
    x0, x1 = float(xs.min()), float(xs.max())
    name = f"{wall.Name or 'Muro'} — {layer.Material.Name if layer.Material else 'Capa'}"
    part = ifcopenshell.api.root.create_entity(f, ifc_class="IfcWall", name=name)
    ifcopenshell.api.spatial.assign_container(f, products=[part], relating_structure=ifcopenshell.util.element.get_container(wall))
    ifcopenshell.api.material.assign_material(f, products=[part], type="IfcMaterialLayerSetUsage",
                                              material=basic_layer_set(project, layer.Material, float(layer.LayerThickness) * scale))
    ifcopenshell.api.material.edit_layer_usage(f, usage=layers.usage_of(part), attributes={
        "DirectionSense": sense, "OffsetFromReferenceLine": 0.0})
    shift = np.eye(4)
    shift[0][3], shift[1][3] = x0, y_face
    ifcopenshell.api.geometry.edit_object_placement(f, product=part, matrix=placement_matrix(project, wall) @ shift)
    builder = ifcopenshell.util.shape_builder.ShapeBuilder(f)
    local = [((float(x) - x0) / scale, (float(y) - y_face) / scale) for x, y in polygon]
    solid = builder.extrude(builder.profile(builder.polyline(local, closed=True)), magnitude=depth / scale,
                            position=(0.0, 0.0, z0 / scale))
    ifcopenshell.api.geometry.assign_representation(f, product=part, representation=builder.get_representation(body, [solid]))
    rep = ifcopenshell.api.geometry.add_axis_representation(f, context=axis, axis=[(0.0, 0.0), ((x1 - x0) / scale, 0.0)])
    ifcopenshell.api.geometry.assign_representation(f, product=part, representation=rep)
    return part


def split_walls(project, ids):
    found = require_walls(project, ids)
    targets = [w for w in found if kind_of(project, w) != "locked" and len(thicknesses(project, w)) >= 2]
    if not targets:
        raise EngineError("El muro ya tiene una sola capa.")

    def apply():
        new_ids, deleted = [], []
        for wall in targets:
            usage = layers.usage_of(wall)
            own = own_layer_set(project, wall)
            for layer, polygon, z0, depth in layers.layer_polygons(wall, project.unit_scale()):
                if len(polygon) >= 3:
                    new_ids.append(separate_layer(project, wall, layer, polygon, z0, depth, usage.DirectionSense).id())
            deleted.append(wall.id())
            ifcopenshell.api.root.remove_product(project.file, product=wall)  # también sus uniones
            if own is not None:
                ifcopenshell.api.material.remove_material_set(project.file, material=own)
        return new_ids, deleted

    new_ids, deleted = project.transaction(apply)
    project.discard_index()
    return {"state": project.state(), "deleted_ids": deleted, "new_ids": new_ids, "changed_ids": list(new_ids)}


# ---------- cambiar y borrar (FR-024 a FR-027; research R9) ----------
LOCKED_ERROR = "BIM Simple no puede cambiar la forma de este muro (viene de otro programa)."
OTHER_ERROR = "Este muro tiene una línea de referencia que BIM Simple no maneja; solo se puede cambiar su altura y su material."
SHAPE_ERROR = "El espesor de esta capa no se puede cambiar porque su forma no es un tramo recto."


def is_basic(wall):
    return structure_of(wall) is None


def _extended_polygon(project, wall, thickness):
    """Polígono de una capa con extremos propios con el espesor nuevo (research R10), o None."""
    usage = layers.usage_of(wall)
    scale = project.unit_scale()
    (_, polygon, _, _), = layers.layer_polygons(wall, scale)
    old = thicknesses(project, wall)[0]
    face = float(usage.OffsetFromReferenceLine) * scale
    sense = 1.0 if usage.DirectionSense == "POSITIVE" else -1.0
    return layers.extend_ends(polygon, face, face + sense * old, face + sense * thickness)


def _replace_profile(project, wall, polygon):
    """Cambia el cuerpo de una capa con extremos propios por la extrusión del polígono nuevo."""
    import ifcopenshell.util.shape_builder

    f = project.file
    scale = project.unit_scale()
    body, _ = _contexts(project)
    old_rep = ifcopenshell.util.representation.get_representation(wall, "Model", "Body", "MODEL_VIEW")
    solid = layers.body_solid(wall)
    _, z0, depth = layers.profile_polygon(solid, scale)
    builder = ifcopenshell.util.shape_builder.ShapeBuilder(f)
    local = [(float(x) / scale, float(y) / scale) for x, y in polygon]
    new_solid = builder.extrude(builder.profile(builder.polyline(local, closed=True)), magnitude=depth / scale,
                                position=(0.0, 0.0, z0 / scale))
    ifcopenshell.api.geometry.unassign_representation(f, product=wall, representation=old_rep)
    ifcopenshell.api.geometry.remove_representation(f, representation=old_rep)
    ifcopenshell.api.geometry.assign_representation(f, product=wall, representation=builder.get_representation(body, [new_solid]))


def _default_basic_material(project, wall):
    found = next((m for m in materials.materials(project) if m.Name == "Hormigón"), None)
    if found is None:
        usage = layers.usage_of(wall)
        found = usage.ForLayerSet.MaterialLayers[0].Material if usage is not None else None
    if found is None:
        raise EngineError("El material elegido ya no existe.")
    return found


def edit_walls(project, ids, **changes):
    """Aplica a todos los muros lo que viene: height, structure_id (None = Básica), material_id, thickness."""
    found = require_walls(project, ids)
    kinds = {w.id(): kind_of(project, w) for w in found}
    references = {w.id(): reference_of(project, w) for w in found}
    if any(kind == "locked" for kind in kinds.values()):
        raise EngineError(LOCKED_ERROR)
    if "height" in changes:
        check_positive(changes["height"], "La altura debe ser mayor que 0.")
    new_type = None
    if "structure_id" in changes:
        if changes["structure_id"] is not None:
            new_type = materials.structure(project, changes["structure_id"])
        if any(references[w.id()] == "other" for w in found):
            raise EngineError(OTHER_ERROR)
    new_material = materials.material(project, changes["material_id"]) if "material_id" in changes else None
    if "thickness" in changes:
        check_positive(changes["thickness"], "El espesor debe ser mayor que 0.")
        for wall in found:
            if is_basic(wall) and references[wall.id()] == "other":
                raise EngineError(OTHER_ERROR)
            if is_basic(wall) and kinds[wall.id()] == "custom_ends" and changes.get("structure_id", None) is None \
                    and _extended_polygon(project, wall, changes["thickness"]) is None:
                raise EngineError(SHAPE_ERROR)

    def apply():
        f = project.file
        scale = project.unit_scale()
        changed, regen = set(), {}

        def regenerate_with_neighbors(wall):
            regen[wall.id()] = wall
            for other in connected_walls(wall):
                if kind_of(project, other) != "locked":
                    regen[other.id()] = other

        for wall in found:
            changed.add(wall.id())
            reference = references[wall.id()]
            if "height" in changes:  # FR-025: solo la extrusión; conserva ingletes y cortes (research R9)
                ifcopenshell.api.attribute.edit_attributes(f, product=layers.body_solid(wall),
                                                           attributes={"Depth": changes["height"] / scale})
            if "structure_id" in changes:
                current = structure_of(wall)
                if new_type is not None and current != new_type:
                    own = own_layer_set(project, wall)
                    ifcopenshell.api.type.assign_type(f, related_objects=[wall], relating_type=new_type)
                    if own is not None:
                        ifcopenshell.api.material.remove_material_set(f, material=own)
                    set_usage(project, wall, reference)
                    regenerate_with_neighbors(wall)
                elif new_type is None and current is not None:
                    mat = new_material or _default_basic_material(project, wall)
                    ifcopenshell.api.type.unassign_type(f, related_objects=[wall])
                    ifcopenshell.api.material.assign_material(f, products=[wall], type="IfcMaterialLayerSetUsage",
                                                              material=basic_layer_set(project, mat, changes.get("thickness", 0.2)))
                    set_usage(project, wall, reference)  # assign_material deja POSITIVE y 0 (research R9)
                    regenerate_with_neighbors(wall)
                    continue
            if not is_basic(wall):
                continue
            if new_material is not None:
                own = own_layer_set(project, wall)
                if own is not None:
                    ifcopenshell.api.material.edit_layer(f, layer=own.MaterialLayers[0], material=new_material)
            if "thickness" in changes and abs(thicknesses(project, wall)[0] - changes["thickness"]) > 1e-9:
                thickness = changes["thickness"]
                custom = kinds[wall.id()] == "custom_ends"
                usage = layers.usage_of(wall)
                sense = usage.DirectionSense
                polygon = _extended_polygon(project, wall, thickness) if custom else None  # antes de cambiar la capa
                own = own_layer_set(project, wall)
                if own is not None:
                    ifcopenshell.api.material.edit_layer(f, layer=own.MaterialLayers[0],
                                                         attributes={"LayerThickness": thickness / scale})
                else:  # conjunto compartido (otro programa): el muro pasa a tener uno propio
                    mat = usage.ForLayerSet.MaterialLayers[0].Material
                    ifcopenshell.api.material.assign_material(f, products=[wall], type="IfcMaterialLayerSetUsage",
                                                              material=basic_layer_set(project, mat, thickness))
                    if custom:
                        ifcopenshell.api.material.edit_layer_usage(f, usage=layers.usage_of(wall), attributes={
                            "DirectionSense": sense, "OffsetFromReferenceLine": 0.0})
                if custom:  # la cara exterior queda y los cortes se prolongan (research R10)
                    _replace_profile(project, wall, polygon)
                else:
                    set_usage(project, wall, reference)
                    regenerate_with_neighbors(wall)
        regenerate(project, list(regen.values()))
        return sorted(changed | set(regen))

    changed = project.transaction(apply)
    project.discard_index()
    return {"state": project.state(), "changed_ids": changed}


def delete_walls(project, ids):
    """Borra los muros y regenera los que estaban unidos a ellos: su extremo queda recto (FR-026; research R9)."""
    found = require_walls(project, ids)

    def apply():
        deleted = {w.id() for w in found}
        neighbors = {}
        for wall in found:
            for other in connected_walls(wall):
                if other.id() not in deleted:
                    neighbors[other.id()] = other
        for wall in found:
            own = own_layer_set(project, wall)
            ifcopenshell.api.root.remove_product(project.file, product=wall)  # también sus uniones
            if own is not None:
                ifcopenshell.api.material.remove_material_set(project.file, material=own)
        regenerate(project, [w for w in neighbors.values() if kind_of(project, w) != "locked"])
        return sorted(deleted), sorted(neighbors)

    deleted, changed = project.transaction(apply)
    project.discard_index()
    return {"state": project.state(), "deleted_ids": deleted, "changed_ids": changed}
