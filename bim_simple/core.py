"""Lógica de BIM Simple sin interfaz.

La usan los operadores y tests/test_mvp.py, así la prueba ejercita exactamente
el mismo código que las herramientas. Distancias en metros.
"""

import math

import bpy

DEFAULT_STOREY_HEIGHT = 3.0
STOREY_QTO = "Qto_BuildingStoreyBaseQuantities"
DEFAULT_MATERIAL = "Genérico"


def _tool():
    import bonsai.tool

    return bonsai.tool


def get_file():
    return _tool().Ifc.get()


def unit_scale():
    import ifcopenshell.util.unit

    return ifcopenshell.util.unit.calculate_unit_scale(get_file())


# Proyecto


def ensure_project():
    """Crea un proyecto IFC4 en metros con una Planta Baja, si no hay uno abierto."""
    tool = _tool()
    if tool.Ifc.get():
        return tool.Ifc.get()
    units = bpy.context.scene.unit_settings
    units.system = "METRIC"
    units.length_unit = "METERS"
    units.scale_length = 1.0
    bpy.ops.bim.create_project()
    storey = get_file().by_type("IfcBuildingStorey")[0]
    rename_storey(storey, "Planta Baja")
    set_storey_elevation(storey, 0.0)
    set_storey_height(storey, DEFAULT_STOREY_HEIGHT)
    activate_storey(storey)
    return get_file()


# Pisos


def get_storeys():
    """Pisos ordenados de abajo hacia arriba."""
    ifc = get_file()
    if not ifc:
        return []
    return sorted(ifc.by_type("IfcBuildingStorey"), key=get_storey_elevation)


def get_storey_elevation(storey):
    import ifcopenshell.util.placement

    return ifcopenshell.util.placement.get_storey_elevation(storey) * unit_scale()


def get_storey_height(storey):
    """GrossHeight del piso; si falta, distancia al piso siguiente o la altura por defecto."""
    import ifcopenshell.util.element

    qto = ifcopenshell.util.element.get_psets(storey, qtos_only=True).get(STOREY_QTO, {})
    if qto.get("GrossHeight"):
        return qto["GrossHeight"] * unit_scale()
    storeys = get_storeys()
    i = storeys.index(storey)
    if i + 1 < len(storeys):
        return get_storey_elevation(storeys[i + 1]) - get_storey_elevation(storey)
    return DEFAULT_STOREY_HEIGHT


def set_storey_elevation(storey, elevation):
    import bonsai.core.geometry
    import ifcopenshell.api.attribute

    tool = _tool()
    obj = tool.Ifc.get_object(storey)
    obj.matrix_world[2][3] = elevation
    bonsai.core.geometry.edit_object_placement(tool.Ifc, tool.Geometry, tool.Surveyor, obj=obj)
    # Bonsai solo guarda la cota en la ubicación; el atributo Elevation lo llenamos nosotros.
    ifcopenshell.api.attribute.edit_attributes(
        get_file(), product=storey, attributes={"Elevation": elevation / unit_scale()}
    )


def set_storey_height(storey, height):
    import ifcopenshell.api.pset
    import ifcopenshell.util.element

    ifc = get_file()
    qto = ifcopenshell.util.element.get_psets(storey, qtos_only=True).get(STOREY_QTO)
    qto = ifc.by_id(qto["id"]) if qto else ifcopenshell.api.pset.add_qto(ifc, product=storey, name=STOREY_QTO)
    ifcopenshell.api.pset.edit_qto(ifc, qto=qto, properties={"GrossHeight": height / unit_scale()})


def add_storey(name, elevation, height=DEFAULT_STOREY_HEIGHT):
    ifc = get_file()
    building = ifc.by_type("IfcBuilding")[0]
    before = {s.id() for s in ifc.by_type("IfcBuildingStorey")}
    bpy.ops.bim.add_part_to_object(
        "EXEC_DEFAULT", element=building.id(), part_class="IfcBuildingStorey", part_name=name
    )
    storey = next(s for s in ifc.by_type("IfcBuildingStorey") if s.id() not in before)
    set_storey_elevation(storey, elevation)
    set_storey_height(storey, height)
    return storey


def rename_storey(storey, name):
    import bonsai.bim.handler

    tool = _tool()
    tool.Spatial.edit_container_name(storey, name)
    if obj := tool.Ifc.get_object(storey):
        tool.Root.set_object_name(obj, storey)
        tool.Collector.assign(obj)
    bonsai.bim.handler.refresh_ui_data()


def delete_storey(storey):
    """Borra el piso con todo lo que contiene, como ArchiCAD. Siempre queda al menos un piso."""
    import bonsai.core.spatial
    import ifcopenshell.util.element

    tool = _tool()
    storeys = get_storeys()
    if len(storeys) <= 1:
        raise ValueError("No se puede borrar el único piso.")
    was_active = active_storey() == storey
    for element in ifcopenshell.util.element.get_contained(storey):
        if obj := tool.Ifc.get_object(element):
            tool.Geometry.delete_ifc_object(obj)
    bonsai.core.spatial.delete_container(tool.Ifc, tool.Spatial, tool.Geometry, storey)
    if was_active:
        activate_storey(get_storeys()[0])


def activate_storey(storey):
    """Los elementos nuevos se crean en este piso."""
    _tool().Spatial.set_default_container(storey)


def active_storey():
    container = _tool().Root.get_default_container()
    if container and container.is_a("IfcBuildingStorey"):
        return container
    return None


# Tipos


def fmt_m(value):
    return f"{value:.2f}".replace(".", ",")


def _default_material():
    import ifcopenshell.api.material

    ifc = get_file()
    for material in ifc.by_type("IfcMaterial"):
        if material.Name == DEFAULT_MATERIAL:
            return material
    return ifcopenshell.api.material.add_material(ifc, name=DEFAULT_MATERIAL, category="concrete")


def _get_layered_type(ifc_class, name, thickness, predefined_type=None):
    """Tipo de una capa de material con el espesor dado; se crea la primera vez que se usa."""
    import ifcopenshell.api.material
    import ifcopenshell.api.root

    ifc = get_file()
    for element_type in ifc.by_type(ifc_class):
        if element_type.Name == name:
            return element_type
    element_type = ifcopenshell.api.root.create_entity(
        ifc, ifc_class=ifc_class, predefined_type=predefined_type, name=name
    )
    layer_set = ifcopenshell.api.material.add_material_set(ifc, name=name, set_type="IfcMaterialLayerSet")
    layer = ifcopenshell.api.material.add_layer(ifc, layer_set=layer_set, material=_default_material())
    ifcopenshell.api.material.edit_layer(ifc, layer=layer, attributes={"LayerThickness": thickness / unit_scale()})
    ifcopenshell.api.material.assign_material(ifc, products=[element_type], material=layer_set)
    return element_type


def get_wall_type(thickness):
    return _get_layered_type("IfcWallType", f"Muro {fmt_m(thickness)}", thickness)


def get_slab_type(thickness):
    return _get_layered_type("IfcSlabType", f"Losa {fmt_m(thickness)}", thickness, predefined_type="FLOOR")


COLUMN_SHAPES = ("RECTANGLE", "CIRCLE")


def get_column_type(shape, width, depth=None):
    """Tipo de columna con perfil rectangular (width × depth) o circular (diámetro = width)."""
    import ifcopenshell.api.material
    import ifcopenshell.api.profile
    import ifcopenshell.api.root

    ifc = get_file()
    if shape == "CIRCLE":
        name = f"Columna Ø {fmt_m(width)}"
        profile_class, dims = "IfcCircleProfileDef", {"Radius": width / 2 / unit_scale()}
    else:
        name = f"Columna {fmt_m(width)} × {fmt_m(depth)}"
        profile_class, dims = "IfcRectangleProfileDef", {"XDim": width / unit_scale(), "YDim": depth / unit_scale()}
    for column_type in ifc.by_type("IfcColumnType"):
        if column_type.Name == name:
            return column_type
    column_type = ifcopenshell.api.root.create_entity(ifc, ifc_class="IfcColumnType", predefined_type="COLUMN", name=name)
    profile = ifcopenshell.api.profile.add_parameterized_profile(ifc, ifc_class=profile_class)
    ifcopenshell.api.profile.edit_profile(ifc, profile=profile, attributes={"ProfileName": name, **dims})
    profile_set = ifcopenshell.api.material.add_material_set(ifc, name=name, set_type="IfcMaterialProfileSet")
    material_profile = ifcopenshell.api.material.add_profile(ifc, profile_set=profile_set, material=_default_material())
    ifcopenshell.api.material.assign_profile(ifc, material_profile=material_profile, profile=profile)
    ifcopenshell.api.material.assign_material(ifc, products=[column_type], material=profile_set)
    return column_type


# Muros

WALL_REFERENCES = ("EXTERIOR", "CENTER", "INTERIOR")


def create_walls(points, thickness, height, reference="EXTERIOR", closed=False, storey=None):
    """Muros encadenados por los puntos (x, y) de la planta, unidos en las esquinas.

    reference: línea de referencia EXTERIOR, CENTER o INTERIOR. Con EXTERIOR el muro
    crece a la izquierda del sentido de dibujo, así un contorno antihorario queda hacia adentro.
    """
    import ifcopenshell.util.representation
    from bonsai.bim.module.model.wall import DumbWallGenerator, DumbWallJoiner
    from mathutils import Vector

    tool = _tool()
    ifc = get_file()
    storey = storey or active_storey()
    # Bonsai asigna cada elemento nuevo al piso activo.
    activate_storey(storey)
    wall_type = get_wall_type(thickness)
    z = get_storey_elevation(storey)
    vertices = [Vector((x, y, z)) for x, y in points]
    if closed and len(vertices) > 1 and (vertices[0] - vertices[-1]).length < 1e-6:
        vertices.pop()
    segments = list(zip(vertices, vertices[1:] + vertices[:1])) if closed else list(zip(vertices, vertices[1:]))

    walls = []
    for start, end in segments:
        if (end - start).length < 1e-6:
            continue
        # Mismo patrón que usa Bonsai en bim.add_perpendicular_wall (wall.py).
        generator = DumbWallGenerator(wall_type)
        generator.file = ifc
        generator.layers = tool.Model.get_material_layer_parameters(wall_type)
        generator.body_context = ifcopenshell.util.representation.get_context(ifc, "Model", "Body", "MODEL_VIEW")
        generator.axis_context = ifcopenshell.util.representation.get_context(ifc, "Plan", "Axis", "GRAPH_VIEW")
        generator.container = None
        generator.container_obj = None
        generator.width = generator.layers["thickness"]
        generator.height = height
        generator.length = (end - start).length
        generator.rotation = math.atan2(end.y - start.y, end.x - start.x)
        generator.location = start
        generator.x_angle = 0.0
        obj = generator.create_wall()
        tool.Model.offset_wall(obj, reference)
        tool.Model.recreate_wall(tool.Ifc.get_entity(obj), obj)
        walls.append(obj)

    pairs = zip(walls, walls[1:] + walls[:1]) if closed and len(walls) > 2 else zip(walls, walls[1:])
    for previous, following in pairs:
        DumbWallJoiner().connect(following, previous)
    return walls


# Losas


def create_slab(points, thickness, offset=0.0, storey=None):
    """Losa con el contorno (x, y) dado. Como en ArchiCAD, su cara superior queda a la cota
    del piso + offset. Devuelve None si el contorno tiene menos de 3 puntos distintos."""
    import ifcopenshell.api.material
    import ifcopenshell.util.element
    from bonsai.bim.module.model.slab import DumbSlabGenerator, DumbSlabPlaner

    tool = _tool()
    ifc = get_file()
    storey = storey or active_storey()
    activate_storey(storey)
    outline = list(points)
    if len(outline) > 1 and math.dist(outline[0], outline[-1]) < 1e-6:
        outline.pop()
    if len(outline) < 3:
        return None

    # DumbSlabGenerator lee el contorno de la polilínea de Bonsai.
    polyline_props = tool.Model.get_polyline_props()
    polyline_props.insertion_polyline.clear()
    polyline = polyline_props.insertion_polyline.add()
    z = get_storey_elevation(storey)
    for x, y in outline:
        point = polyline.polyline_points.add()
        point.x, point.y, point.z = x, y, z
    obj = DumbSlabGenerator(get_slab_type(thickness)).generate("POLYLINE")
    tool.Polyline.clear_polyline()

    element = tool.Ifc.get_entity(obj)
    usage = ifcopenshell.util.element.get_material(element)
    ifcopenshell.api.material.edit_layer_usage(
        ifc,
        usage=usage,
        attributes={"OffsetFromReferenceLine": (offset - thickness) / unit_scale(), "DirectionSense": "POSITIVE"},
    )
    DumbSlabPlaner().regenerate_from_occurence(element, usage)
    return obj


# Columnas


def create_column(point, shape, width, depth, height, storey=None):
    """Columna centrada en el punto (x, y), desde la cota del piso y con la altura dada."""
    import ifcopenshell.util.element
    import ifcopenshell.util.representation
    from bonsai.bim.module.model.profile import DumbProfileGenerator
    from mathutils import Vector

    tool = _tool()
    ifc = get_file()
    storey = storey or active_storey()
    activate_storey(storey)
    column_type = get_column_type(shape, width, depth)
    # Lo mismo que hace DumbProfileGenerator.generate(), pero con el punto dado en vez del cursor 3D.
    generator = DumbProfileGenerator(column_type)
    generator.insertion_type = "CURSOR"
    generator.file = ifc
    generator.profile_set = ifcopenshell.util.element.get_material(column_type)
    generator.body_context = ifcopenshell.util.representation.get_context(ifc, "Model", "Body", "MODEL_VIEW")
    generator.axis_context = ifcopenshell.util.representation.get_context(ifc, "Model", "Axis", "GRAPH_VIEW")
    generator.container = storey
    generator.container_obj = tool.Ifc.get_object(storey)
    generator.depth = height
    generator.rotation = 0
    generator.location = Vector((point[0], point[1], get_storey_elevation(storey)))
    generator.cardinal_point = 5  # centro del perfil
    return generator.create_profile()
