"""Caja de herramientas (barra izquierda) e Info Box (barra sobre la vista)."""

import os

import bpy
from bpy.types import WorkSpaceTool

import bonsai.tool as tool

from . import core

ICONS = os.path.join(os.path.dirname(__file__), "icons")


def _no_project(layout):
    if core.get_file() and core.active_storey():
        return False
    layout.label(text="Crea un proyecto en la pestaña BIM Simple", icon="INFO")
    return True


class SelectTool(WorkSpaceTool):
    bl_space_type = "VIEW_3D"
    bl_context_mode = "OBJECT"
    bl_idname = "bimsimple.select"
    bl_label = "Flecha"
    bl_description = "Seleccionar elementos"
    # Blender agrega ".dat" a la ruta.
    bl_icon = os.path.join(ICONS, "select")
    bl_widget = None
    bl_keymap = tool.Blender.get_default_selection_keypmap()


class WallTool(WorkSpaceTool):
    bl_space_type = "VIEW_3D"
    bl_context_mode = "OBJECT"
    bl_idname = "bimsimple.wall"
    bl_label = "Muro"
    bl_description = "Dibujar muros en planta: clic en el inicio y clic en cada esquina"
    bl_icon = os.path.join(ICONS, "wall")
    bl_widget = None
    bl_keymap = (("bimsimple.draw_wall", {"type": "LEFTMOUSE", "value": "PRESS"}, None),)

    def draw_settings(context, layout, ws_tool):
        if _no_project(layout):
            return
        props = context.scene.BIMSimpleProperties
        layout.prop(props, "wall_thickness")
        _draw_height(layout, props, "wall_height_from_storey", "wall_height")
        layout.prop(props, "wall_reference", text="Referencia")


class SlabTool(WorkSpaceTool):
    bl_space_type = "VIEW_3D"
    bl_context_mode = "OBJECT"
    bl_idname = "bimsimple.slab"
    bl_label = "Losa"
    bl_description = "Dibujar losas: clic en cada vértice; se cierra con clic en el primer punto o Enter"
    bl_icon = os.path.join(ICONS, "slab")
    bl_widget = None
    bl_keymap = (("bimsimple.draw_slab", {"type": "LEFTMOUSE", "value": "PRESS"}, None),)

    def draw_settings(context, layout, ws_tool):
        if _no_project(layout):
            return
        props = context.scene.BIMSimpleProperties
        layout.prop(props, "slab_thickness")
        layout.prop(props, "slab_offset")


class ColumnTool(WorkSpaceTool):
    bl_space_type = "VIEW_3D"
    bl_context_mode = "OBJECT"
    bl_idname = "bimsimple.column"
    bl_label = "Columna"
    bl_description = "Colocar columnas con un clic"
    bl_icon = os.path.join(ICONS, "column")
    bl_widget = None
    bl_keymap = (("bimsimple.place_column", {"type": "LEFTMOUSE", "value": "PRESS"}, None),)

    def draw_settings(context, layout, ws_tool):
        if _no_project(layout):
            return
        props = context.scene.BIMSimpleProperties
        layout.prop(props, "column_shape", text="")
        if props.column_shape == "CIRCLE":
            layout.prop(props, "column_diameter")
        else:
            layout.prop(props, "column_width")
            layout.prop(props, "column_depth")
        _draw_height(layout, props, "column_height_from_storey", "column_height")


def _draw_height(layout, props, from_storey_prop, height_prop):
    """Altura del Info Box: con el candado activado usa la altura del piso activo."""
    from_storey = getattr(props, from_storey_prop)
    row = layout.row(align=True)
    row.prop(props, from_storey_prop, text="", icon="LINKED" if from_storey else "UNLINKED")
    if from_storey:
        row.label(text=f"Altura {core.fmt_m(core.get_storey_height(core.active_storey()))} (piso)")
    else:
        row.prop(props, height_prop)


TOOLS = (SelectTool, WallTool, SlabTool, ColumnTool)

_original_toolbar_draw = None
_bim_simple_toolbar = None


def _toolbar_draw(self, context):
    """En el espacio BIM Simple (modo Objeto) la barra muestra solo nuestras herramientas."""
    from .ui import WORKSPACE_NAME

    if context.mode == "OBJECT" and context.workspace.name == WORKSPACE_NAME:
        _bim_simple_toolbar.draw_cls(self.layout, context)
    else:
        _original_toolbar_draw(self, context)


def _install_toolbar_filter():
    """Cambio interno de Blender aprobado por el usuario: depende de VIEW3D_PT_tools_active,
    así que una actualización de Blender puede requerir ajustarlo."""
    global _original_toolbar_draw, _bim_simple_toolbar
    from bl_ui.space_toolsystem_toolbar import VIEW3D_PT_tools_active

    class BIMSimpleToolbar(VIEW3D_PT_tools_active):
        # Sin registrar: solo cambia la lista que se dibuja, no la de atajos ni la del resto de Blender.
        @classmethod
        def tools_from_context(cls, context, mode=None):
            yield from (tool_cls._bl_tool for tool_cls in TOOLS)

    _bim_simple_toolbar = BIMSimpleToolbar
    _original_toolbar_draw = VIEW3D_PT_tools_active.draw
    VIEW3D_PT_tools_active.draw = _toolbar_draw


def _remove_toolbar_filter():
    from bl_ui.space_toolsystem_toolbar import VIEW3D_PT_tools_active

    VIEW3D_PT_tools_active.draw = _original_toolbar_draw


def _move_to_top():
    """Pone nuestras herramientas al principio de la barra, separadas de las de Blender y Bonsai.

    register_tool(after=...) no sirve: con una herramienta de grupo (la selección de Blender)
    mete la nuestra dentro del desplegable del grupo.
    """
    from bl_ui.space_toolsystem_common import ToolSelectPanelHelper

    tools = ToolSelectPanelHelper._tool_class_from_space_type("VIEW_3D")._tools["OBJECT"]
    ours = [cls._bl_tool for cls in TOOLS]
    for tool_def in ours:
        tools.remove(tool_def)
    tools[0:0] = ours + [None]


def register():
    # Sin ventana no hay mapa de teclas para herramientas (Bonsai hace lo mismo).
    if bpy.app.background:
        return
    for cls in TOOLS:
        bpy.utils.register_tool(cls)
    _move_to_top()
    _install_toolbar_filter()


def unregister():
    if bpy.app.background:
        return
    _remove_toolbar_filter()
    for cls in reversed(TOOLS):
        bpy.utils.unregister_tool(cls)
