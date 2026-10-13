"""IFC de prueba, generados con la API de IfcOpenShell (nunca dentro del proyecto).

Uso desde la prueba del programa:  python -m tests.make_fixtures <carpeta>
"""

import os
import sys

import numpy as np
import ifcopenshell.api.aggregate
import ifcopenshell.api.context
import ifcopenshell.api.geometry
import ifcopenshell.api.material
import ifcopenshell.api.project
import ifcopenshell.api.pset
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.api.type
import ifcopenshell.api.unit


def _base(units="METRE", project_name="Proyecto ajeno"):
    f = ifcopenshell.api.project.create_file(version="IFC4")
    project = ifcopenshell.api.root.create_entity(f, ifc_class="IfcProject", name=project_name)
    prefix = "MILLI" if units == "MILLIMETRE" else None
    length = ifcopenshell.api.unit.add_si_unit(f, unit_type="LENGTHUNIT", prefix=prefix)
    ifcopenshell.api.unit.assign_unit(f, units=[length])
    model = ifcopenshell.api.context.add_context(f, context_type="Model")
    body = ifcopenshell.api.context.add_context(f, context_type="Model", context_identifier="Body",
                                                target_view="MODEL_VIEW", parent=model)
    site = ifcopenshell.api.root.create_entity(f, ifc_class="IfcSite", name="Terreno")
    ifcopenshell.api.aggregate.assign_object(f, products=[site], relating_object=project)
    ifcopenshell.api.geometry.edit_object_placement(f, product=site)
    return f, site, body


def _building(f, site, name, z=0.0):
    building = ifcopenshell.api.root.create_entity(f, ifc_class="IfcBuilding", name=name)
    ifcopenshell.api.aggregate.assign_object(f, products=[building], relating_object=site)
    matrix = np.eye(4)
    matrix[2][3] = z
    ifcopenshell.api.geometry.edit_object_placement(f, product=building, matrix=matrix, is_si=True)
    return building


def _storey(f, building, name, z, with_placement=True, height=None):
    """z en unidades del archivo."""
    storey = ifcopenshell.api.root.create_entity(f, ifc_class="IfcBuildingStorey", name=name)
    ifcopenshell.api.aggregate.assign_object(f, products=[storey], relating_object=building)
    if with_placement:
        matrix = np.eye(4)
        matrix[2][3] = z
        ifcopenshell.api.geometry.edit_object_placement(f, product=storey, matrix=matrix, is_si=False)
    storey.Elevation = z
    if height is not None:
        qto = ifcopenshell.api.pset.add_qto(f, product=storey, name="Qto_BuildingStoreyBaseQuantities")
        ifcopenshell.api.pset.edit_qto(f, qto=qto, properties={"GrossHeight": height})
    return storey


def _proxy(f, container, name, ifc_class="IfcBuildingElementProxy"):
    element = ifcopenshell.api.root.create_entity(f, ifc_class=ifc_class, name=name)
    ifcopenshell.api.spatial.assign_container(f, products=[element], relating_structure=container)
    ifcopenshell.api.geometry.edit_object_placement(f, product=element)
    return element


def _wall(f, body, storey, z, p1=(0.0, 0.0), p2=(5.0, 0.0)):
    wall = ifcopenshell.api.root.create_entity(f, ifc_class="IfcWall", name=f"Muro {storey.Name}")
    ifcopenshell.api.spatial.assign_container(f, products=[wall], relating_structure=storey)
    rep = ifcopenshell.api.geometry.create_2pt_wall(f, element=wall, context=body, p1=p1, p2=p2,
                                                    elevation=z, height=3.0, thickness=0.2)
    ifcopenshell.api.geometry.assign_representation(f, product=wall, representation=rep)
    return wall


def _layer_set(f, name, layers):
    """layers: [(nombre del material, espesor)]."""
    layer_set = ifcopenshell.api.material.add_material_set(f, name=name, set_type="IfcMaterialLayerSet")
    for material_name, thickness in layers:
        material = next((m for m in f.by_type("IfcMaterial") if m.Name == material_name), None) \
            or ifcopenshell.api.material.add_material(f, name=material_name)
        layer = ifcopenshell.api.material.add_layer(f, layer_set=layer_set, material=material)
        ifcopenshell.api.material.edit_layer(f, layer=layer, attributes={"LayerThickness": thickness})
    return layer_set


def _other_program_walls():
    """Muros como los haría otro programa (función 002, T008): uno con capas en sentido POSITIVE, uno sin capas y
    uno con un recorte inclinado."""
    f, site, body = _base(project_name="Muros de otro programa")
    plan = ifcopenshell.api.context.add_context(f, context_type="Plan")
    axis = ifcopenshell.api.context.add_context(f, context_type="Plan", context_identifier="Axis",
                                                target_view="GRAPH_VIEW", parent=plan)
    edificio = _building(f, site, "Edificio")
    storey = _storey(f, edificio, "Planta Baja", 0.0, height=3.0)

    # Con capas: tipo de 2 capas, usage POSITIVE con desplazamiento 0 (la que crea assign_type), regenerado.
    wall_type = ifcopenshell.api.root.create_entity(f, ifc_class="IfcWallType", name="Ladrillo revocado",
                                                    predefined_type="STANDARD")
    ifcopenshell.api.material.assign_material(f, products=[wall_type], type="IfcMaterialLayerSet",
                                              material=_layer_set(f, "Ladrillo revocado",
                                                                  [("Ladrillo", 0.15), ("Revoque", 0.02)]))
    layered = ifcopenshell.api.root.create_entity(f, ifc_class="IfcWall", name="Muro con capas")
    ifcopenshell.api.spatial.assign_container(f, products=[layered], relating_structure=storey)
    ifcopenshell.api.type.assign_type(f, related_objects=[layered], relating_type=wall_type)
    rep = ifcopenshell.api.geometry.create_2pt_wall(f, element=layered, context=body, p1=(0.0, 0.0), p2=(5.0, 0.0),
                                                    elevation=0.0, height=3.0, thickness=0.17)
    ifcopenshell.api.geometry.assign_representation(f, product=layered, representation=rep)
    rep = ifcopenshell.api.geometry.add_axis_representation(f, context=axis, axis=[(0.0, 0.0), (5.0, 0.0)])
    ifcopenshell.api.geometry.assign_representation(f, product=layered, representation=rep)
    ifcopenshell.api.geometry.regenerate_wall_representation(f, wall=layered, length=5.0, height=3.0)

    # Sin capas: solo el cuerpo.
    unlayered = _wall(f, body, storey, 0.0, p1=(0.0, 3.0), p2=(5.0, 3.0))
    unlayered.Name = "Muro sin capas"

    # Con recorte: usage y eje, pero el cuerpo es un IfcBooleanClippingResult.
    clipped = ifcopenshell.api.root.create_entity(f, ifc_class="IfcWall", name="Muro con recorte")
    ifcopenshell.api.spatial.assign_container(f, products=[clipped], relating_structure=storey)
    ifcopenshell.api.material.assign_material(f, products=[clipped], type="IfcMaterialLayerSetUsage",
                                              material=_layer_set(f, "Básica", [("Hormigón", 0.2)]))
    ifcopenshell.api.geometry.edit_object_placement(f, product=clipped, matrix=np.array(
        [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 6.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]))
    rep = ifcopenshell.api.geometry.add_wall_representation(
        f, context=body, length=5.0, height=3.0, thickness=0.2,
        clippings=[{"location": (2.5, 0.0, 2.0), "normal": (0.0, 0.0, 1.0)}])
    ifcopenshell.api.geometry.assign_representation(f, product=clipped, representation=rep)
    rep = ifcopenshell.api.geometry.add_axis_representation(f, context=axis, axis=[(0.0, 0.0), (5.0, 0.0)])
    ifcopenshell.api.geometry.assign_representation(f, product=clipped, representation=rep)
    return f


def write_all(folder):
    """Escribe todos los IFC de prueba en la carpeta y devuelve {nombre: ruta}."""
    os.makedirs(folder, exist_ok=True)
    paths = {}

    def save(name, f):
        paths[name] = os.path.join(folder, f"{name}.ifc")
        f.write(paths[name])

    # Otro programa: milímetros, pisos desordenados, sin Qto, el subsuelo sin ubicación (solo Elevation).
    f, site, _ = _base("MILLIMETRE")
    torre = _building(f, site, "Torre")
    _storey(f, torre, "Nivel 2", 6000.0)
    _storey(f, torre, "Nivel 0", 0.0)
    nivel1 = _storey(f, torre, "Nivel 1", 3200.0)
    _storey(f, torre, "Subsuelo", -2800.0, with_placement=False)
    _proxy(f, nivel1, "Mueble en Nivel 1")
    save("otro_programa_mm", f)

    f, site, _ = _base()
    edificio_a = _building(f, site, "Edificio A")
    edificio_b = _building(f, site, "Edificio B", z=10.0)
    _storey(f, edificio_a, "A - PB", 0.0)
    _storey(f, edificio_b, "B - PB", 0.0)
    _storey(f, edificio_b, "B - P1", 3.0)
    save("dos_edificios", f)

    f, site, _ = _base()
    galpon = _building(f, site, "Galpón")
    _proxy(f, galpon, "Elemento en el edificio")
    save("sin_pisos", f)

    f, site, _ = _base()
    _proxy(f, site, "Elemento en el sitio")
    save("sin_edificio", f)

    # Con elementos: 3 pisos en metros, un muro por piso y una puerta sin editar en Planta Baja.
    f, site, body = _base(project_name="Proyecto con elementos")
    edificio = _building(f, site, "Edificio")
    for name, z in (("Planta Baja", 0.0), ("Piso 1", 3.0), ("Piso 2", 6.0)):
        storey = _storey(f, edificio, name, z, height=3.0)
        _wall(f, body, storey, z)
        if name == "Planta Baja":
            _proxy(f, storey, "Puerta", ifc_class="IfcDoor")
    save("con_elementos", f)

    save("muros_otro_programa", _other_program_walls())

    paths["danado"] = os.path.join(folder, "danado.ifc")
    with open(paths["danado"], "w", encoding="utf-8") as archivo:
        archivo.write("ISO-10303-21;\nHEADER;\nFILE_SCHEMA(('IFC4'));\nENDSEC;\nDATA;\n#1=IFCWALL('x',$,$\n")
    paths["no_es_ifc"] = os.path.join(folder, "no_es_ifc.ifc")
    with open(paths["no_es_ifc"], "w", encoding="utf-8") as archivo:
        archivo.write("Esto es un texto cualquiera.\n")
    return paths


if __name__ == "__main__":
    for name, path in write_all(sys.argv[1]).items():
        print(name, path)
