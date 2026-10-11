"""Formas 3D de los elementos para la interfaz (data-model.md §5), calculadas con ifcopenshell.geom (núcleo OpenCASCADE)."""

import base64
import multiprocessing

import numpy as np
import ifcopenshell.geom
import ifcopenshell.util.element

_SETTINGS = ifcopenshell.geom.settings()
_SETTINGS.set("use-world-coords", True)
# No se usa "enable-layerset-slicing": falla con "Unexpected topology" (RESULTADOS del prototipo).


def _encode(array, dtype):
    return base64.b64encode(np.asarray(array, dtype=dtype).tobytes()).decode()


def _mesh(element, geometry):
    container = ifcopenshell.util.element.get_container(element)
    return {
        "id": element.id(),
        "ifc_class": element.is_a(),
        "storey_id": container.id() if container is not None and container.is_a("IfcBuildingStorey") else None,
        "vertices": _encode(geometry.verts, np.float32),
        "faces": _encode(geometry.faces, np.uint32),
    }


def meshes(project, ids=None):
    """Con ids: esos elementos (create_shape). Sin ids: todos, en paralelo (iterator)."""
    project.require_project()
    f = project.file
    result, failures = [], []
    if ids:
        for ifc_id in ids:
            element = project.entity(ifc_id)
            if element is None or not element.is_a("IfcElement") or not element.Representation:
                continue
            try:
                shape = ifcopenshell.geom.create_shape(_SETTINGS, element)
            except RuntimeError as error:
                failures.append({"id": ifc_id, "error": str(error)})
                continue
            result.append(_mesh(element, shape.geometry))
    elif f.by_type("IfcElement"):
        iterator = ifcopenshell.geom.iterator(_SETTINGS, f, multiprocessing.cpu_count(),
                                              include=f.by_type("IfcElement"))
        if iterator.initialize():
            while True:
                shape = iterator.get()
                result.append(_mesh(f.by_id(shape.id), shape.geometry))
                if not iterator.next():
                    break
    return {"meshes": result, "existing_ids": [e.id() for e in f.by_type("IfcElement")], "failures": failures}
