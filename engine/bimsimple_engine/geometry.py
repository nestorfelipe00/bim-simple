"""Formas 3D de los elementos para la interfaz (data-model.md §5).

- Muros editables: un prisma por capa, calculado desde el IFC (layers.py; research R6), con un grupo por capa.
- Todo lo demás: ifcopenshell.geom (núcleo OpenCASCADE), como en la función 001.

No se usa "enable-layerset-slicing": falla siempre en IfcOpenShell 0.9.0 con "Unexpected topology" y deja el
elemento sin forma (research R6).
"""

import base64
import multiprocessing

import numpy as np
import ifcopenshell.geom
import ifcopenshell.util.element

from . import layers, walls

_SETTINGS = ifcopenshell.geom.settings()
_SETTINGS.set("use-world-coords", True)


def _encode(array, dtype):
    return base64.b64encode(np.asarray(array, dtype=dtype).tobytes()).decode()


def _storey_id(element):
    container = ifcopenshell.util.element.get_container(element)
    return container.id() if container is not None and container.is_a("IfcBuildingStorey") else None


def _mesh(element, vertices, faces, groups=(), wall=None):
    return {
        "id": element.id(),
        "ifc_class": element.is_a(),
        "storey_id": _storey_id(element),
        "vertices": _encode(vertices, np.float32),
        "faces": _encode(faces, np.uint32),
        "groups": list(groups),
        "wall": wall,
    }


def layered_mesh(project, wall, info):
    """Malla de un muro editable con un grupo por capa; None si alguna capa no es un polígono convexo."""
    polygons = layers.layer_polygons(wall, project.unit_scale())
    if not polygons or not all(layers.is_convex(poly) for _, poly, _, _ in polygons):
        return None
    matrix = walls.placement_matrix(project, wall)
    all_vertices, all_faces, groups = [], [], []
    vertex_offset = index_offset = 0
    for layer, polygon, z0, depth in polygons:
        vertices, faces = layers.prism(polygon, z0, depth, matrix)
        groups.append({"start": index_offset, "count": len(faces),
                       "material_id": layer.Material.id() if layer.Material else None})
        all_vertices.append(vertices)
        all_faces.append(faces + vertex_offset)
        vertex_offset += len(vertices)
        index_offset += len(faces)
    return _mesh(wall, np.concatenate(all_vertices), np.concatenate(all_faces), groups, info)


def meshes(project, ids=None):
    """Con ids: esos elementos. Sin ids: todos (OpenCASCADE en paralelo para lo que no son muros editables)."""
    project.require_project()
    f = project.file
    if ids:
        elements = [project.entity(i) for i in ids]
        elements = [e for e in elements if e is not None and e.is_a("IfcElement") and e.Representation]
    else:
        elements = [e for e in f.by_type("IfcElement") if e.Representation]
    result, failures, pending, wall_data = [], [], [], {}
    for element in elements:
        if element.is_a("IfcWall"):
            info = walls.wall_info(project, element)
            wall_data[element.id()] = info
            mesh = layered_mesh(project, element, info) if info["kind"] != "locked" else None
            if mesh is not None:
                result.append(mesh)
                continue
        pending.append(element)
    if ids:
        for element in pending:
            try:
                shape = ifcopenshell.geom.create_shape(_SETTINGS, element)
            except RuntimeError as error:
                failures.append({"id": element.id(), "error": str(error)})
                continue
            result.append(_mesh(element, shape.geometry.verts, shape.geometry.faces, wall=wall_data.get(element.id())))
    elif pending:
        iterator = ifcopenshell.geom.iterator(_SETTINGS, f, multiprocessing.cpu_count(), include=pending)
        if iterator.initialize():
            while True:
                shape = iterator.get()
                element = f.by_id(shape.id)
                result.append(_mesh(element, shape.geometry.verts, shape.geometry.faces,
                                    wall=wall_data.get(element.id())))
                if not iterator.next():
                    break
    return {"meshes": result, "existing_ids": [e.id() for e in f.by_type("IfcElement")], "failures": failures}
