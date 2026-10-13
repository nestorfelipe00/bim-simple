"""Geometría de las capas de un muro, calculada desde el IFC (research R6, R10). Código propio.

IfcOpenShell 0.9.0 no sirve para esto: "enable-layerset-slicing" falla siempre con "Unexpected topology" y deja
el muro sin forma (research R6). Por eso el motor recorta el perfil del cuerpo del muro por la franja de cada capa
y arma un prisma por capa. La suma de los prismas es igual al volumen que calcula OpenCASCADE.
"""

import numpy as np
import ifcopenshell.util.element
import ifcopenshell.util.placement
import ifcopenshell.util.representation

TOL = 1e-4  # metros


# ---------- cuerpo del muro ----------
def body_solid(wall):
    """El IfcExtrudedAreaSolid del cuerpo si es el único ítem, vertical, de perfil poligonal o rectangular."""
    rep = ifcopenshell.util.representation.get_representation(wall, "Model", "Body", "MODEL_VIEW")
    if rep is None or len(rep.Items) != 1 or not rep.Items[0].is_a("IfcExtrudedAreaSolid"):
        return None
    solid = rep.Items[0]
    if not np.allclose(_unit(solid.ExtrudedDirection.DirectionRatios), (0.0, 0.0, 1.0), atol=1e-6):
        return None
    if solid.Position is not None:
        matrix = ifcopenshell.util.placement.get_axis2placement(solid.Position)
        if not np.allclose(matrix[:3, 2], (0.0, 0.0, 1.0), atol=1e-6):
            return None
    area = solid.SweptArea
    if area.is_a("IfcRectangleProfileDef"):
        return solid
    if not area.is_a("IfcArbitraryClosedProfileDef") or area.is_a("IfcArbitraryProfileDefWithVoids"):
        return None
    curve = area.OuterCurve
    if curve.is_a("IfcPolyline"):
        return solid
    if curve.is_a("IfcIndexedPolyCurve") and all(s.is_a("IfcLineIndex") for s in (curve.Segments or ())):
        return solid
    return None


def _unit(vector):
    vector = np.asarray(vector, dtype=float)
    return vector / np.linalg.norm(vector)


def _curve_points(curve):
    if curve.is_a("IfcPolyline"):
        return [tuple(p.Coordinates[:2]) for p in curve.Points]
    coords = [tuple(p[:2]) for p in curve.Points.CoordList]
    if not curve.Segments:
        return coords
    points = []
    for segment in curve.Segments:
        for index in segment.wrappedValue:
            point = coords[index - 1]
            if not points or points[-1] != point:
                points.append(point)
    return points


def profile_polygon(solid, scale):
    """Polígono del perfil en coordenadas locales del muro (metros), sin repetir el primer punto; y z0 y depth."""
    area = solid.SweptArea
    if area.is_a("IfcRectangleProfileDef"):
        x, y = area.XDim / 2, area.YDim / 2
        points = np.array([(-x, -y), (x, -y), (x, y), (-x, y)], dtype=float)
        if area.Position is not None:
            m2 = ifcopenshell.util.placement.get_axis2placement(area.Position)
            points = np.array([(m2 @ np.array([px, py, 0.0, 1.0]))[:2] for px, py in points])
    else:
        points = np.array(_curve_points(area.OuterCurve), dtype=float)
    if len(points) > 1 and np.allclose(points[0], points[-1]):
        points = points[:-1]
    z0 = 0.0
    if solid.Position is not None:
        m3 = ifcopenshell.util.placement.get_axis2placement(solid.Position)
        points = np.array([(m3 @ np.array([px, py, 0.0, 1.0]))[:2] for px, py in points])
        z0 = float(m3[2][3])
    return points * scale, z0 * scale, float(solid.Depth) * scale


# ---------- franjas de las capas ----------
def layer_strips(usage, thicknesses, scale):
    """(y_min, y_max) de cada capa en metros, de la primera (exterior) a la última (research R3)."""
    y = float(usage.OffsetFromReferenceLine) * scale
    sense = 1.0 if usage.DirectionSense == "POSITIVE" else -1.0
    strips = []
    for thickness in thicknesses:
        y2 = y + sense * thickness
        strips.append((min(y, y2), max(y, y2)))
        y = y2
    return strips


def clip_strip(polygon, y_min, y_max):
    """Sutherland–Hodgman contra y <= y_max y y >= y_min."""
    def clip(points, inside, cut):
        out = []
        for i in range(len(points)):
            a, b = points[i], points[(i + 1) % len(points)]
            if inside(a):
                out.append(a)
            if inside(a) != inside(b):
                t = (cut - a[1]) / (b[1] - a[1])
                out.append(a + t * (b - a))
        return out

    points = [np.asarray(p, dtype=float) for p in polygon]
    points = clip(points, lambda p: p[1] <= y_max + 1e-12, y_max)
    if points:
        points = clip(points, lambda p: p[1] >= y_min - 1e-12, y_min)
    return _clean(np.array(points, dtype=float).reshape(-1, 2))


def _clean(polygon):
    """Quita puntos repetidos consecutivos."""
    out = []
    for p in polygon:
        if not out or np.linalg.norm(p - out[-1]) > 1e-9:
            out.append(p)
    if len(out) > 1 and np.linalg.norm(out[0] - out[-1]) <= 1e-9:
        out.pop()
    return np.array(out, dtype=float).reshape(-1, 2)


def usage_of(wall):
    found = ifcopenshell.util.element.get_material(wall)
    return found if found is not None and found.is_a("IfcMaterialLayerSetUsage") else None


def layer_polygons(wall, scale):
    """[(capa, polígono local en m, z0, depth)] o None si el muro no tiene usage o cuerpo simple."""
    usage = usage_of(wall)
    solid = body_solid(wall)
    if usage is None or solid is None or not usage.ForLayerSet.MaterialLayers:
        return None
    polygon, z0, depth = profile_polygon(solid, scale)
    layers = usage.ForLayerSet.MaterialLayers
    strips = layer_strips(usage, [float(layer.LayerThickness) * scale for layer in layers], scale)
    return [(layer, clip_strip(polygon, y_min, y_max), z0, depth) for layer, (y_min, y_max) in zip(layers, strips)]


# ---------- formas ----------
def signed_area(polygon):
    x, y = polygon[:, 0], polygon[:, 1]
    return 0.5 * (np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def is_convex(polygon):
    if len(polygon) < 3 or abs(signed_area(polygon)) < 1e-12:
        return False
    signs = set()
    n = len(polygon)
    for i in range(n):
        a, b, c = polygon[i], polygon[(i + 1) % n], polygon[(i + 2) % n]
        cross = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
        if abs(cross) > 1e-12:
            signs.add(cross > 0)
    return len(signs) == 1


def drop_collinear(polygon):
    """Quita los vértices que están sobre la recta de sus vecinos (la regeneración a veces los agrega)."""
    points = list(_clean(np.asarray(polygon, dtype=float)))
    changed = True
    while changed and len(points) > 3:
        changed = False
        for i in range(len(points)):
            a, b, c = points[i - 1], points[i], points[(i + 1) % len(points)]
            cross = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
            if abs(cross) <= 1e-10:
                del points[i]
                changed = True
                break
    return np.array(points, dtype=float).reshape(-1, 2)


def is_plain_strip(polygon, length, y_min, y_max):
    """True si el polígono es el rectángulo [0, length] x [y_min, y_max] (muro sin cortes en los extremos)."""
    polygon = drop_collinear(polygon)
    if len(polygon) != 4:
        return False
    corners = {(round(float(x) / TOL), round(float(y) / TOL)) for x, y in polygon}
    expected = {(round(x / TOL), round(y / TOL)) for x in (0.0, length) for y in (y_min, y_max)}
    return corners == expected


def prism(polygon, z0, depth, matrix):
    """Prisma de un polígono convexo: vértices (float32, mundo) y triángulos (uint32), con normales hacia afuera."""
    points = polygon if signed_area(polygon) > 0 else polygon[::-1]
    n = len(points)
    local = [(x, y, z0) for x, y in points] + [(x, y, z0 + depth) for x, y in points]
    vertices = np.array([(matrix @ np.array([x, y, z, 1.0]))[:3] for x, y, z in local], dtype=np.float32)
    faces = []
    for i in range(1, n - 1):
        faces += [0, i + 1, i]            # abajo, normal -Z
        faces += [n, n + i, n + i + 1]    # arriba, normal +Z
    for i in range(n):
        j = (i + 1) % n
        faces += [i, j, n + j, i, n + j, n + i]  # lado, normal hacia afuera (polígono antihorario)
    return vertices, np.array(faces, dtype=np.uint32)


def extend_ends(polygon, face_y, old_inner_y, new_inner_y):
    """Cambia el espesor de una capa con extremos cortados: las aristas de los extremos se prolongan como rectas
    desde la cara (face_y) hasta la cara nueva (new_inner_y). None si el polígono no es un cuadrilátero así."""
    polygon = drop_collinear(polygon)
    if len(polygon) != 4:
        return None
    on_face = [abs(p[1] - face_y) <= TOL for p in polygon]
    on_inner = [abs(p[1] - old_inner_y) <= TOL for p in polygon]
    if sum(on_face) != 2 or sum(on_inner) != 2 or any(a and b for a, b in zip(on_face, on_inner)):
        return None
    result = np.array(polygon, dtype=float)
    factor = (new_inner_y - face_y) / (old_inner_y - face_y)
    for i in range(4):
        if not on_inner[i]:
            continue
        neighbors = [(i - 1) % 4, (i + 1) % 4]
        face_neighbor = next((k for k in neighbors if on_face[k]), None)
        if face_neighbor is None:
            return None
        start = polygon[face_neighbor]
        result[i] = start + (polygon[i] - start) * factor
    return result
