import bpy, os, sys
def p(*a): print("[EXP15-GEN]", *a, flush=True)
OUT = os.environ["EXP_OUT"]
win = bpy.context.window_manager.windows[0]
ws = win.workspace
ws.name = "BIM Simple"
ws.use_filter_by_owner = True
ws.owner_ids.new("bl_ext.user_default.bim_simple")
bpy.data.batch_remove([w for w in bpy.data.workspaces if w != ws])
bpy.data.batch_remove(list(bpy.data.objects))
win.screen.show_statusbar = False
# convertir propiedades/esquema/línea de tiempo en vistas 3D no reduce áreas; solo comprobamos tipos
for a in win.screen.areas:
    if a.type == "DOPESHEET_EDITOR":
        a.type = "VIEW_3D"
v = next(a for a in win.screen.areas if a.type == "VIEW_3D").spaces.active
v.use_local_collections = True
rv = v.region_3d
rv.view_perspective = "ORTHO"; rv.is_orthographic_side_view = True; rv.lock_rotation = True
path = os.path.join(OUT, "startup.blend")
p("save", bpy.ops.wm.save_as_mainfile(filepath=path, copy=True), os.path.getsize(path))
