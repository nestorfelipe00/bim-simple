import math

import bpy
from bpy.props import FloatProperty, StringProperty

import bonsai.tool as tool
from bonsai.bim.ifc import IfcStore
from bonsai.bim.module.model.decorator import PolylineDecorator
from bonsai.bim.module.model.polyline import PolylineOperator

from . import core, ui
from .props import refresh_storeys


class BIMSIMPLE_OT_new_project(bpy.types.Operator):
    bl_idname = "bimsimple.new_project"
    bl_label = "Nuevo proyecto"
    bl_description = "Crea un proyecto IFC con una Planta Baja y abre el espacio BIM Simple"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return not core.get_file()

    def execute(self, context):
        core.ensure_project()
        refresh_storeys(context)
        ui.open_workspace(context)
        return {"FINISHED"}


class BIMSIMPLE_OT_open_workspace(bpy.types.Operator):
    bl_idname = "bimsimple.open_workspace"
    bl_label = "Espacio BIM Simple"
    bl_description = "Abre el espacio de trabajo BIM Simple: planta a la izquierda y 3D a la derecha"

    def execute(self, context):
        ui.open_workspace(context)
        return {"FINISHED"}


class BIMSIMPLE_OT_refresh_storeys(bpy.types.Operator):
    bl_idname = "bimsimple.refresh_storeys"
    bl_label = "Actualizar pisos"
    bl_options = {"INTERNAL"}

    def execute(self, context):
        refresh_storeys(context)
        return {"FINISHED"}


class BIMSIMPLE_OT_add_storey(bpy.types.Operator, tool.Ifc.Operator):
    bl_idname = "bimsimple.add_storey"
    bl_label = "Agregar piso"
    bl_description = "Agrega un piso nuevo"
    bl_options = {"REGISTER", "UNDO"}

    name: StringProperty(name="Nombre")
    elevation: FloatProperty(name="Cota", subtype="DISTANCE")
    height: FloatProperty(name="Altura", subtype="DISTANCE", default=core.DEFAULT_STOREY_HEIGHT, min=0.01)

    @classmethod
    def poll(cls, context):
        return bool(core.get_file())

    def invoke(self, context, event):
        # Por defecto, encima del piso más alto.
        top = core.get_storeys()[-1]
        self.elevation = core.get_storey_elevation(top) + core.get_storey_height(top)
        self.height = core.DEFAULT_STOREY_HEIGHT
        self.name = f"Piso {len(core.get_storeys())}"
        return context.window_manager.invoke_props_dialog(self)

    def _execute(self, context):
        storey = core.add_storey(self.name, self.elevation, self.height)
        core.activate_storey(storey)
        refresh_storeys(context)
        ui.update_plan_view(context, storey)


class BIMSIMPLE_OT_delete_storey(bpy.types.Operator, tool.Ifc.Operator):
    bl_idname = "bimsimple.delete_storey"
    bl_label = "Borrar piso"
    bl_description = "Borra el piso seleccionado y todo lo que contiene"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        props = context.scene.BIMSimpleProperties
        return bool(core.get_file()) and len(props.storeys) > 1

    def invoke(self, context, event):
        item = context.scene.BIMSimpleProperties.storeys[context.scene.BIMSimpleProperties.active_storey_index]
        return context.window_manager.invoke_confirm(
            self, event, title="Borrar piso", message=f"Se borrará «{item.name}» con todos sus elementos."
        )

    def _execute(self, context):
        props = context.scene.BIMSimpleProperties
        storey = core.get_file().by_id(props.storeys[props.active_storey_index].ifc_id)
        core.delete_storey(storey)
        refresh_storeys(context)
        ui.update_plan_view(context, core.active_storey())


class PolylineTool(PolylineOperator, tool.Ifc.Operator):
    """Base de las herramientas que dibujan con clics en planta (muro, losa, columna).

    Reutiliza PolylineOperator de Bonsai (imán, largo tecleado, vista previa) como hace
    bim.draw_polyline_wall. Cada herramienta define INSTRUCTIONS, is_done() y finish().
    """

    INSTRUCTIONS = {}

    @classmethod
    def poll(cls, context):
        return context.space_data and context.space_data.type == "VIEW_3D" and core.active_storey()

    def __init__(self, *args, **kwargs):
        bpy.types.Operator.__init__(self, *args, **kwargs)
        PolylineOperator.__init__(self)
        self.shift_lock = False

    def invoke(self, context, event):
        return IfcStore.execute_ifc_operator(self, context, event, method="INVOKE")

    def _invoke(self, context, event):
        PolylineOperator.invoke(self, context, event)
        # Los puntos se toman a la cota del piso activo.
        self.tool_state.use_default_container = True
        self.tool_state.plane_method = "XY"
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        return IfcStore.execute_ifc_operator(self, context, event, method="MODAL")

    def _modal(self, context, event):
        PolylineDecorator.update(event, self.tool_state, self.input_ui, self.snapping_points[0])
        tool.Blender.update_viewport()

        self.handle_shift_lock(event)
        self.handle_lock_axis(context, event)
        if event.type in {"MIDDLEMOUSE", "WHEELUPMOUSE", "WHEELDOWNMOUSE"}:
            self.handle_mouse_move(context, event)
            return {"PASS_THROUGH"}

        self.handle_instructions(
            context, self.INSTRUCTIONS, [f"Imán: {self.snapping_points[0]['type']}"], overwrite=True
        )
        self.handle_mouse_move(context, event, should_round=True)
        self.choose_axis(event)
        self.handle_snap_selection(context, event)

        # Como en ArchiCAD, Esc también termina y conserva lo dibujado.
        if (
            not self.tool_state.is_input_on
            and event.value == "RELEASE"
            and event.type in {"RET", "NUMPAD_ENTER", "RIGHTMOUSE", "ESC"}
        ):
            return self.end(context)

        self.handle_keyboard_input(context, event)
        self.handle_inserting_polyline(context, event)
        self.flatten_points()
        if self.is_done():
            return self.end(context)
        cancel = self.handle_cancelation(context, event)
        if cancel is not None:
            return cancel
        return {"RUNNING_MODAL"}

    def end(self, context):
        self.finish(context, self.points())
        self.tool_state.plane_method = None
        self.cleanup(context)
        return {"FINISHED"}

    def points(self):
        polyline = tool.Model.get_polyline_props().insertion_polyline
        return [(p.x, p.y) for p in polyline[0].polyline_points] if polyline else []

    def is_closed(self):
        points = self.points()
        return len(points) > 3 and math.dist(points[0], points[-1]) < 1e-6

    def is_done(self):
        return False

    def finish(self, context, points):
        raise NotImplementedError

    def flatten_points(self):
        """Todos los puntos a la cota del piso activo.

        Nuestras herramientas arrancan con el mismo clic que marca el primer punto; en ese instante
        Bonsai aún no calculó la posición y toma el punto del imán tal cual, que en planta puede
        venir con otra altura (se vio z = -10). Ese desnivel falsea largo y ángulo del primer tramo.
        """
        polyline = tool.Model.get_polyline_props().insertion_polyline
        if not polyline:
            return
        elevation = tool.Root.get_default_container_elevation()
        for point in polyline[0].polyline_points:
            if point.z != elevation:
                point.z = elevation

    def handle_shift_lock(self, event):
        """Mientras se mantiene Shift, el tramo queda fijo en el múltiplo de 45° más cercano."""
        if event.type not in {"LEFT_SHIFT", "RIGHT_SHIFT"}:
            return
        if event.value == "PRESS" and not self.tool_state.lock_axis:
            angle = self.input_ui.get_number_value("WORLD_ANGLE") or 0.0
            self.tool_state.lock_axis = True
            self.tool_state.snap_angle = round(angle / 45) * 45
            self.shift_lock = True
        elif event.value == "RELEASE" and self.shift_lock:
            self.tool_state.lock_axis = False
            self.shift_lock = False


DRAWING_INSTRUCTIONS = {
    "Fijar 0/45/90°": {"icons": True, "keys": ["EVENT_SHIFT"]},
    "Escribir largo": {"icons": True, "keys": ["EVENT_D"]},
    "Cambiar dato": {"icons": True, "keys": ["EVENT_TAB"]},
    "Cerrar contorno": {"icons": True, "keys": ["EVENT_C"]},
    "Quitar último punto": {"icons": True, "keys": ["EVENT_BACKSPACE"]},
    "Terminar": {"icons": True, "keys": ["EVENT_ESC", "MOUSE_RMB"]},
}


class BIMSIMPLE_OT_draw_wall(PolylineTool, bpy.types.Operator):
    bl_idname = "bimsimple.draw_wall"
    bl_label = "Dibujar muro"
    bl_options = {"REGISTER", "UNDO"}

    INSTRUCTIONS = DRAWING_INSTRUCTIONS

    def finish(self, context, points):
        if len(points) < 2:
            return
        props = context.scene.BIMSimpleProperties
        storey = core.active_storey()
        height = core.get_storey_height(storey) if props.wall_height_from_storey else props.wall_height
        core.create_walls(
            points, props.wall_thickness, height, props.wall_reference, closed=self.is_closed(), storey=storey
        )


class BIMSIMPLE_OT_draw_slab(PolylineTool, bpy.types.Operator):
    bl_idname = "bimsimple.draw_slab"
    bl_label = "Dibujar losa"
    bl_options = {"REGISTER", "UNDO"}

    INSTRUCTIONS = DRAWING_INSTRUCTIONS

    def is_done(self):
        # Clic en el primer punto: el contorno se cierra y la losa se crea.
        return self.is_closed()

    def finish(self, context, points):
        props = context.scene.BIMSimpleProperties
        core.create_slab(points, props.slab_thickness, props.slab_offset, storey=core.active_storey())


class BIMSIMPLE_OT_place_column(PolylineTool, bpy.types.Operator):
    bl_idname = "bimsimple.place_column"
    bl_label = "Colocar columna"
    bl_options = {"REGISTER", "UNDO"}

    INSTRUCTIONS = {"Cancelar": {"icons": True, "keys": ["EVENT_ESC"]}}

    def is_done(self):
        return len(self.points()) >= 1

    def finish(self, context, points):
        if not points:
            return
        props = context.scene.BIMSimpleProperties
        storey = core.active_storey()
        height = core.get_storey_height(storey) if props.column_height_from_storey else props.column_height
        width = props.column_diameter if props.column_shape == "CIRCLE" else props.column_width
        core.create_column(points[0], props.column_shape, width, props.column_depth, height, storey=storey)


classes = (
    BIMSIMPLE_OT_new_project,
    BIMSIMPLE_OT_open_workspace,
    BIMSIMPLE_OT_refresh_storeys,
    BIMSIMPLE_OT_add_storey,
    BIMSIMPLE_OT_delete_storey,
    BIMSIMPLE_OT_draw_wall,
    BIMSIMPLE_OT_draw_slab,
    BIMSIMPLE_OT_place_column,
)
