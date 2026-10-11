import bpy
from bpy.props import BoolProperty, CollectionProperty, EnumProperty, FloatProperty, IntProperty, StringProperty
from bpy.types import PropertyGroup

from . import core

# Evita que refresh_storeys dispare los callbacks de renombrar y activar.
_refreshing = False


def refresh_storeys(context):
    """Copia los pisos del IFC a la lista del navegador, el más alto arriba como en ArchiCAD."""
    global _refreshing
    props = context.scene.BIMSimpleProperties
    _refreshing = True
    try:
        props.storeys.clear()
        active = core.active_storey()
        index = 0
        for i, storey in enumerate(reversed(core.get_storeys())):
            item = props.storeys.add()
            item.ifc_id = storey.id()
            item.name = storey.Name or ""
            item.elevation = core.get_storey_elevation(storey)
            item.height = core.get_storey_height(storey)
            if storey == active:
                index = i
        props.active_storey_index = index
    finally:
        _refreshing = False


def _rename_storey(self, context):
    if _refreshing or not core.get_file():
        return
    core.rename_storey(core.get_file().by_id(self.ifc_id), self.name)


def _activate_storey(self, context):
    if _refreshing or not core.get_file() or not self.storeys:
        return
    from . import ui

    storey = core.get_file().by_id(self.storeys[self.active_storey_index].ifc_id)
    core.activate_storey(storey)
    ui.update_plan_view(context, storey)


class StoreyItem(PropertyGroup):
    ifc_id: IntProperty()
    name: StringProperty(name="Nombre", update=_rename_storey)
    elevation: FloatProperty(name="Cota", subtype="DISTANCE")
    height: FloatProperty(name="Altura", subtype="DISTANCE")


class BIMSimpleProperties(PropertyGroup):
    storeys: CollectionProperty(type=StoreyItem)
    active_storey_index: IntProperty(name="Piso activo", update=_activate_storey)

    # Info Box: valores que usará el próximo muro.
    wall_thickness: FloatProperty(name="Espesor", default=0.20, min=0.01, subtype="DISTANCE")
    wall_height_from_storey: BoolProperty(
        name="Altura del piso", description="El muro toma la altura del piso activo", default=True
    )
    wall_height: FloatProperty(name="Altura", default=core.DEFAULT_STOREY_HEIGHT, min=0.01, subtype="DISTANCE")
    wall_reference: EnumProperty(
        name="Línea de referencia",
        items=(
            ("EXTERIOR", "Exterior", "La línea dibujada es la cara exterior del muro"),
            ("CENTER", "Centro", "La línea dibujada es el eje del muro"),
            ("INTERIOR", "Interior", "La línea dibujada es la cara interior del muro"),
        ),
        default="EXTERIOR",
    )

    # Info Box de la losa.
    slab_thickness: FloatProperty(name="Espesor", default=0.15, min=0.01, subtype="DISTANCE")
    slab_offset: FloatProperty(
        name="Desfase", description="Cota de la cara superior respecto al piso", default=0.0, subtype="DISTANCE"
    )

    # Info Box de la columna.
    column_shape: EnumProperty(
        name="Sección",
        items=(("RECTANGLE", "Rectangular", ""), ("CIRCLE", "Circular", "")),
        default="RECTANGLE",
    )
    column_width: FloatProperty(name="Ancho", default=0.30, min=0.01, subtype="DISTANCE")
    column_depth: FloatProperty(name="Largo", default=0.30, min=0.01, subtype="DISTANCE")
    column_diameter: FloatProperty(name="Diámetro", default=0.30, min=0.01, subtype="DISTANCE")
    column_height_from_storey: BoolProperty(
        name="Altura del piso", description="La columna toma la altura del piso activo", default=True
    )
    column_height: FloatProperty(name="Altura", default=core.DEFAULT_STOREY_HEIGHT, min=0.01, subtype="DISTANCE")


classes = (StoreyItem, BIMSimpleProperties)


def register():
    bpy.types.Scene.BIMSimpleProperties = bpy.props.PointerProperty(type=BIMSimpleProperties)


def unregister():
    del bpy.types.Scene.BIMSimpleProperties
