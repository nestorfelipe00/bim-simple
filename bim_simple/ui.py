import bpy

from . import core

WORKSPACE_NAME = "BIM Simple"


def _fmt(value, sign=False):
    return (f"{value:+.2f}" if sign else f"{value:.2f}").replace(".", ",")


# Navegador de pisos

_refresh_scheduled = False


def _storeys_out_of_date(props):
    active = core.active_storey()
    in_ifc = [(s.id(), s.Name or "", s == active) for s in reversed(core.get_storeys())]
    in_list = [(i.ifc_id, i.name, n == props.active_storey_index) for n, i in enumerate(props.storeys)]
    return in_ifc != in_list


def _schedule_refresh():
    # draw() no puede modificar propiedades, así que la lista se actualiza fuera de él.
    global _refresh_scheduled
    if _refresh_scheduled:
        return
    _refresh_scheduled = True

    def refresh():
        global _refresh_scheduled
        _refresh_scheduled = False
        from .props import refresh_storeys

        if core.get_file():
            refresh_storeys(bpy.context)

    bpy.app.timers.register(refresh, first_interval=0.0)


class BIMSIMPLE_UL_storeys(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        split = layout.split(factor=0.5, align=True)
        split.prop(item, "name", text="", emboss=False)
        numbers = split.row(align=True)
        numbers.label(text=_fmt(item.elevation, sign=True))
        numbers.label(text=_fmt(item.height))


class BIMSIMPLE_PT_storeys(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BIM Simple"
    bl_label = "Pisos"

    def draw(self, context):
        layout = self.layout
        if not core.get_file():
            layout.operator("bimsimple.new_project", icon="FILE_NEW")
            return
        props = context.scene.BIMSimpleProperties
        if _storeys_out_of_date(props):
            _schedule_refresh()

        header = layout.split(factor=0.5, align=True)
        header.label(text="Nombre")
        numbers = header.row(align=True)
        numbers.label(text="Cota")
        numbers.label(text="Altura")
        row = layout.row()
        row.template_list("BIMSIMPLE_UL_storeys", "", props, "storeys", props, "active_storey_index", rows=4)
        col = row.column(align=True)
        col.operator("bimsimple.add_storey", text="", icon="ADD")
        col.operator("bimsimple.delete_storey", text="", icon="REMOVE")
        layout.label(text="Clic: activar piso")
        layout.label(text="Doble clic en el nombre: renombrar")
        if context.workspace.name != WORKSPACE_NAME:
            layout.operator("bimsimple.open_workspace", icon="WORKSPACE")


# Espacio de trabajo


def open_workspace(context):
    """Activa el espacio BIM Simple; lo crea la primera vez a partir de Layout."""
    window = context.window
    workspace = bpy.data.workspaces.get(WORKSPACE_NAME)
    if workspace is None:
        base = bpy.data.workspaces.get("Layout") or window.workspace
        existing = set(bpy.data.workspaces)
        with context.temp_override(window=window, workspace=base):
            bpy.ops.workspace.duplicate()
        workspace = next(ws for ws in bpy.data.workspaces if ws not in existing)
        workspace.name = WORKSPACE_NAME
        workspace.object_mode = "OBJECT"
        # Solo se ve la interfaz de BIM Simple; los paneles y menús de Bonsai quedan ocultos aquí.
        workspace.use_filter_by_owner = True
        workspace.owner_ids.new(__package__)
        window.workspace = workspace
        # El cambio de espacio se aplica en el siguiente ciclo de eventos.
        bpy.app.timers.register(lambda: _build_layout(window), first_interval=0.1)
    else:
        window.workspace = workspace
        bpy.app.timers.register(lambda: _refresh_views(window), first_interval=0.1)


def _view3d_areas(window):
    """Vistas 3D del espacio, de izquierda a derecha: (planta, 3D)."""
    return sorted((a for a in window.screen.areas if a.type == "VIEW_3D"), key=lambda a: a.x)


def _build_layout(window):
    if window.workspace.name != WORKSPACE_NAME:
        return None
    screen = window.screen
    # Queda una sola vista 3D: se cierran esquema, propiedades y línea de tiempo.
    for area in [a for a in screen.areas if a.type != "VIEW_3D"]:
        with bpy.context.temp_override(window=window, screen=screen, area=area):
            bpy.ops.screen.area_close()
    main = _view3d_areas(window)[0]
    with bpy.context.temp_override(window=window, screen=screen, area=main):
        bpy.ops.screen.area_split(direction="VERTICAL", factor=0.5)

    plan, view3d = _view3d_areas(window)
    for area in (plan, view3d):
        # Cambiar regiones sin contexto de ventana cierra Blender (ED_region_visibility_change_update).
        with bpy.context.temp_override(window=window, screen=screen, area=area):
            area.show_menus = False
            space = area.spaces.active
            space.show_region_toolbar = True
            space.show_region_tool_header = True
            space.show_region_ui = area == view3d

    plan_region = next(r for r in plan.regions if r.type == "WINDOW")
    with bpy.context.temp_override(window=window, screen=screen, area=plan, region=plan_region):
        bpy.ops.wm.tool_set_by_id(name="bimsimple.select")
        bpy.ops.view3d.view_axis(type="TOP")
        plan_view = plan.spaces.active.region_3d
        plan_view.view_perspective = "ORTHO"
        plan_view.lock_rotation = True
        plan.spaces.active.use_local_collections = True

    _refresh_views(window)
    # La pestaña solo se puede elegir cuando la barra lateral ya se dibujó una vez.
    bpy.app.timers.register(lambda: _show_sidebar_tab(window), first_interval=0.3)
    return None


def _show_sidebar_tab(window):
    view3d = _view3d_areas(window)[-1]
    sidebar = next(r for r in view3d.regions if r.type == "UI")
    with bpy.context.temp_override(window=window, screen=window.screen, area=view3d, region=sidebar):
        sidebar.active_panel_category = "BIM Simple"
    return None


def _refresh_views(window):
    storey = core.active_storey() if core.get_file() else None
    if storey:
        _update_plan(window, storey)
    return None


def update_plan_view(context, storey):
    if not storey:
        return
    for window in context.window_manager.windows:
        if window.workspace.name == WORKSPACE_NAME:
            _update_plan(window, storey)


def _collection_index(view_layer, collection):
    """Índice que espera object.hide_collection: hermanos primero, luego sus hijos (BKE_layer_collection_from_index)."""
    counter = 0

    def walk(layer_collections):
        nonlocal counter
        for lc in layer_collections:
            if lc.collection == collection:
                return counter
            counter += 1
        for lc in layer_collections:
            if (found := walk(lc.children)) is not None:
                return found
        return None

    return walk([view_layer.layer_collection])


def _update_plan(window, storey):
    """La planta muestra solo el piso activo, visto desde arriba.

    Sin planos de corte: Blender recorta con ellos las ayudas de dibujo de Bonsai
    (vista previa y cotas) y desaparecen de la planta.
    """
    import bonsai.tool as tool

    views = _view3d_areas(window)
    if len(views) < 2:
        return
    plan = views[0]
    region = next(r for r in plan.regions if r.type == "WINDOW")
    collection = tool.Blender.get_object_bim_props(tool.Ifc.get_object(storey)).collection
    index = _collection_index(window.view_layer, collection)
    if index is not None:
        with bpy.context.temp_override(window=window, screen=window.screen, area=plan, region=region):
            bpy.ops.object.hide_collection(collection_index=index, toggle=False)
    plan.tag_redraw()


def _file_menu(self, context):
    # El filtro de add-ons del espacio oculta las opciones IFC que Bonsai agrega a File;
    # aquí se ofrecen las mismas, solo en BIM Simple para no duplicarlas en otros espacios.
    if context.workspace.name != WORKSPACE_NAME:
        return
    layout = self.layout
    layout.operator("bim.load_project", text="Abrir IFC…", icon="FILEBROWSER")
    layout.operator("bim.save_project", text="Guardar IFC", icon="FILE_TICK")
    layout.operator("bim.save_project", text="Guardar IFC como…").should_save_as = True
    layout.separator()


classes = (BIMSIMPLE_UL_storeys, BIMSIMPLE_PT_storeys)


def register():
    bpy.types.TOPBAR_MT_file.prepend(_file_menu)


def unregister():
    bpy.types.TOPBAR_MT_file.remove(_file_menu)
