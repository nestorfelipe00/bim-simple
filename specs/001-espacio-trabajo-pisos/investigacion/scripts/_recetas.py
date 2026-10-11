"""Recetas candidatas para el plan (investigación, NO es el código del producto).

Cada llamada a Bonsai/IfcOpenShell está verificada en el código instalado (ver ifc.md).
Distancias en metros (SI); se convierten a unidades del proyecto con unit_scale.
"""

import math

import bpy

STOREY_QTO = "Qto_BuildingStoreyBaseQuantities"
DEFAULT_HEIGHT = 3.0


def tool():
    import bonsai.tool

    return bonsai.tool


def ifc():
    return tool().Ifc.get()


def unit_scale(f=None):
    import ifcopenshell.util.unit

    return ifcopenshell.util.unit.calculate_unit_scale(f or ifc())


# ---------------------------------------------------------------- proyecto


def new_project():
    """Proyecto nuevo IFC4 en metros SIN reiniciar Blender (no usa bim.new_project)."""
    t = tool()
    us = bpy.context.scene.unit_settings
    us.system, us.length_unit, us.scale_length = "METRIC", "METERS", 1.0
    pprops = t.Project.get_project_props()
    pprops.export_schema = "IFC4"
    pprops.template_file = "0"
    result = bpy.ops.bim.create_project()
    f = ifc()
    import ifcopenshell.api.attribute

    for cls, name in (("IfcProject", "Proyecto"), ("IfcSite", "Sitio"), ("IfcBuilding", "Edificio")):
        element = f.by_type(cls)[0]
        ifcopenshell.api.attribute.edit_attributes(f, product=element, attributes={"Name": name})
        sync_object_name(element)
    storey = f.by_type("IfcBuildingStorey")[0]
    rename_storey(storey, "Planta Baja")
    set_storey_elevation(storey, 0.0)
    set_storey_height(storey, DEFAULT_HEIGHT)
    activate_storey(storey)
    return result


def close_project():
    """Descarga el IFC actual sin read_homefile: borra los objetos/colecciones IFC y vacía IfcStore."""
    from bonsai.bim.ifc import IfcStore
    import bonsai.bim.handler

    t = tool()
    if not ifc():
        return
    project = ifc().by_type("IfcProject")[0]
    project_obj = t.Ifc.get_object(project)
    project_col = t.Blender.get_object_bim_props(project_obj).collection if project_obj else None
    for obj in list(bpy.data.objects):
        if t.Ifc.get_entity(obj) or (project_col and obj.name in project_col.all_objects):
            data = obj.data
            bpy.data.objects.remove(obj)
            if data is not None and getattr(data, "users", 1) == 0:
                try:
                    getattr(bpy.data, {"MESH": "meshes", "CURVE": "curves", "CAMERA": "cameras"}.get(type(data).__name__.upper(), "meshes")).remove(data)
                except Exception:
                    pass
    if project_col:
        for col in list(project_col.children_recursive) + [project_col]:
            bpy.data.collections.remove(col)
    t.Blender.get_bim_props().ifc_file = ""
    t.Blender.get_bim_props().is_dirty = False
    t.Spatial.get_spatial_props().default_container = 0
    IfcStore.purge()
    bonsai.bim.handler.refresh_ui_data()


# ---------------------------------------------------------------- pisos (lectura)


def get_building(f=None):
    f = f or ifc()
    buildings = f.by_type("IfcBuilding")
    return buildings[0] if buildings else None


def get_storeys(f=None, building=None):
    """Pisos del primer edificio (directos y de sus partes), ordenados por cota (abajo -> arriba)."""
    import ifcopenshell.util.element

    f = f or ifc()
    building = building or get_building(f)
    if not building:
        return []
    storeys = [e for e in ifcopenshell.util.element.get_decomposition(building) if e.is_a("IfcBuildingStorey")]
    return sorted(storeys, key=lambda s: (get_storey_elevation(s), s.id()))


def get_storey_elevation(storey):
    """Cota absoluta en metros: Z de la ubicación; si no hay ubicación, atributo Elevation."""
    import ifcopenshell.util.placement

    return ifcopenshell.util.placement.get_storey_elevation(storey) * unit_scale(storey.file)


def get_storey_height(storey, storeys=None):
    """Altura = distancia al piso de arriba; el más alto usa GrossHeight (o 3,00)."""
    import ifcopenshell.util.element

    storeys = storeys or get_storeys(storey.file)
    i = storeys.index(storey)
    if i + 1 < len(storeys):
        return get_storey_elevation(storeys[i + 1]) - get_storey_elevation(storey)
    qto = ifcopenshell.util.element.get_psets(storey, qtos_only=True).get(STOREY_QTO, {})
    if qto.get("GrossHeight"):
        return qto["GrossHeight"] * unit_scale(storey.file)
    return DEFAULT_HEIGHT


# ---------------------------------------------------------------- pisos (escritura)


def sync_object_name(element):
    t = tool()
    if obj := t.Ifc.get_object(element):
        t.Root.set_object_name(obj, element)
        t.Collector.assign(obj)


def rename_storey(storey, name):
    """Igual que el navegador de Bonsai (spatial/prop.py:update_name)."""
    import bonsai.bim.handler

    tool().Spatial.edit_container_name(storey, name)
    sync_object_name(storey)
    bonsai.bim.handler.refresh_ui_data()


def add_storey(name, elevation, height=DEFAULT_HEIGHT):
    """Crea un IfcBuildingStorey bajo el edificio con el mismo camino que la interfaz de Bonsai."""
    f = ifc()
    building = get_building(f)
    before = {s.id() for s in f.by_type("IfcBuildingStorey")}
    bpy.ops.bim.add_part_to_object("EXEC_DEFAULT", element=building.id(), part_class="IfcBuildingStorey", part_name=name)
    storey = next(s for s in f.by_type("IfcBuildingStorey") if s.id() not in before)
    if storey.Name != name:  # Bonsai agrega " 2" si ya existe un objeto con ese nombre
        rename_storey(storey, name)
    set_storey_elevation(storey, elevation)
    set_storey_height(storey, height)
    return storey


def _moved_objects(storey):
    """Objetos de Blender que deben moverse con el piso: el piso y todo lo que contiene/agrega."""
    import ifcopenshell.util.element

    t = tool()
    objs = []
    for element in [storey, *ifcopenshell.util.element.get_decomposition(storey)]:
        if obj := t.Ifc.get_object(element):
            if isinstance(obj, bpy.types.Object):
                objs.append(obj)
    return objs


def set_storey_elevation(storey, elevation, move_contents=True):
    """Cambia la cota del piso. Con move_contents=True los elementos se mueven con él (IFC y Blender).

    IFC: ifcopenshell.api.geometry.edit_object_placement(..., should_transform_children=True) mantiene las
    ubicaciones relativas de los hijos -> se mueven. Blender: se desplaza cada objeto y se registra su
    posición (record_object_position) para que el guardado de Bonsai no lo vuelva a escribir.
    """
    import ifcopenshell.api.attribute
    import ifcopenshell.api.geometry

    t = tool()
    f = ifc()
    obj = t.Ifc.get_object(storey)
    delta = elevation - obj.matrix_world.translation.z
    others = [o for o in _moved_objects(storey) if o != obj] if move_contents else []
    obj.matrix_world.translation.z = elevation
    ifcopenshell.api.geometry.edit_object_placement(
        f, product=storey, matrix=t.Surveyor.get_absolute_matrix(obj), is_si=True,
        should_transform_children=move_contents,
    )
    t.Geometry.record_object_position(obj)
    for o in others:
        o.matrix_world.translation.z += delta
        t.Geometry.record_object_position(o)
    # Elevation (IFC4): cota respecto del 0,00 del edificio, en unidades del proyecto.
    building = get_building(f)
    building_z = 0.0
    if building and building.ObjectPlacement:
        import ifcopenshell.util.placement

        building_z = ifcopenshell.util.placement.get_local_placement(building.ObjectPlacement)[2][3] * unit_scale(f)
    ifcopenshell.api.attribute.edit_attributes(
        f, product=storey, attributes={"Elevation": (elevation - building_z) / unit_scale(f)}
    )
    bpy.context.view_layer.update()


def set_storey_height(storey, height):
    import ifcopenshell.api.pset
    import ifcopenshell.util.element

    f = ifc()
    qto = ifcopenshell.util.element.get_psets(storey, qtos_only=True).get(STOREY_QTO)
    qto = f.by_id(qto["id"]) if qto else ifcopenshell.api.pset.add_qto(f, product=storey, name=STOREY_QTO)
    ifcopenshell.api.pset.edit_qto(f, qto=qto, properties={"GrossHeight": height / unit_scale(f)})


def storey_contents(storey):
    """Todo lo que cuelga del piso (contenidos, partes, espacios, rellenos), sin las aberturas,
    que se borran con su muro."""
    import ifcopenshell.util.element

    return [
        e
        for e in ifcopenshell.util.element.get_decomposition(storey)
        if not e.is_a("IfcFeatureElementSubtraction")
    ]


def count_storey_elements(storey):
    """Cantidad para el aviso de FR-017: elementos físicos (IfcElement) del piso, sin aberturas."""
    return len([e for e in storey_contents(storey) if e.is_a("IfcElement")])


def delete_storey(storey, with_contents=True):
    """Borra el piso; con with_contents=True borra antes todo su contenido (IFC y Blender)."""
    import bonsai.core.spatial
    import ifcopenshell.api.root

    t = tool()
    f = ifc()
    if with_contents:
        for element in storey_contents(storey):
            try:
                f.by_id(element.id())
            except RuntimeError:
                continue  # ya se borró junto con otro
            if obj := t.Ifc.get_object(element):
                t.Geometry.delete_ifc_object(obj)
            else:
                ifcopenshell.api.root.remove_product(f, product=element)
    bonsai.core.spatial.delete_container(t.Ifc, t.Spatial, t.Geometry, storey)


def activate_storey(storey):
    tool().Spatial.set_default_container(storey)


def active_storey():
    c = tool().Root.get_default_container()
    return c if c and c.is_a("IfcBuildingStorey") else None


# ---------------------------------------------------------------- elementos de prueba


def make_column_by_assign_class(name, x, y, z, size=0.3, height=3.0):
    """Elemento mínimo: malla de Blender + bim.assign_class (queda en el contenedor por defecto)."""
    import bmesh
    import ifcopenshell.util.representation

    f = ifc()
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size
        v.co.y *= size
        v.co.z = (v.co.z + 0.5) * height
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = (x, y, z)
    bpy.context.view_layer.update()
    body = ifcopenshell.util.representation.get_context(f, "Model", "Body", "MODEL_VIEW")
    bpy.ops.bim.assign_class(obj=obj.name, ifc_class="IfcColumn", context_id=body.id())
    element = tool().Ifc.get_entity(obj)
    print(f"   [assign_class] ObjectPlacement tras assign_class: {element.ObjectPlacement}")
    # Con una malla, assign_class usa la vía de teselado (root/operator.py) y NO escribe la ubicación;
    # Bonsai la escribe recién al guardar (export_ifc.py sync_object_placement). La escribimos ya.
    import bonsai.core.geometry

    t = tool()
    bonsai.core.geometry.edit_object_placement(t.Ifc, t.Geometry, t.Surveyor, obj=obj)
    return element


def get_wall_type(thickness=0.2):
    import ifcopenshell.api.material
    import ifcopenshell.api.root

    f = ifc()
    name = f"Muro {thickness:.2f}"
    for t_ in f.by_type("IfcWallType"):
        if t_.Name == name:
            return t_
    wt = ifcopenshell.api.root.create_entity(f, ifc_class="IfcWallType", name=name)
    mat = ifcopenshell.api.material.add_material(f, name="Genérico", category="concrete")
    ls = ifcopenshell.api.material.add_material_set(f, name=name, set_type="IfcMaterialLayerSet")
    layer = ifcopenshell.api.material.add_layer(f, layer_set=ls, material=mat)
    ifcopenshell.api.material.edit_layer(f, layer=layer, attributes={"LayerThickness": thickness / unit_scale(f)})
    ifcopenshell.api.material.assign_material(f, products=[wt], material=ls)
    return wt


def make_wall(start, end, height, storey=None):
    """Receta del MVP (DumbWallGenerator, clase interna). El muro va al contenedor por defecto."""
    import ifcopenshell.util.representation
    from bonsai.bim.module.model.wall import DumbWallGenerator
    from mathutils import Vector

    t = tool()
    f = ifc()
    if storey:
        activate_storey(storey)
    storey = active_storey()
    z = get_storey_elevation(storey)
    wt = get_wall_type()
    g = DumbWallGenerator(wt)
    g.file = f
    g.layers = t.Model.get_material_layer_parameters(wt)
    g.body_context = ifcopenshell.util.representation.get_context(f, "Model", "Body", "MODEL_VIEW")
    g.axis_context = ifcopenshell.util.representation.get_context(f, "Plan", "Axis", "GRAPH_VIEW")
    g.container = None
    g.container_obj = None
    g.width = g.layers["thickness"]
    g.height = height
    g.length = math.dist(start, end)
    g.rotation = math.atan2(end[1] - start[1], end[0] - start[0])
    g.location = Vector((start[0], start[1], z))
    g.x_angle = 0.0
    obj = g.create_wall()
    return t.Ifc.get_entity(obj)
