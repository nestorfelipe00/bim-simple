# SOLO para la copia portable de prueba del scratchpad: fija preferencias y las guarda.
# Se niega a correr si la configuracion no es la carpeta "portable" de la copia.
import bpy

user_dir = bpy.utils.resource_path('USER')
assert user_dir.rstrip("\\/").endswith("portable"), "NO es una configuracion portable: " + user_dir

p = bpy.context.preferences
p.view.show_splash = False
p.view.language = 'es'
p.view.use_translate_interface = True
p.view.use_translate_tooltips = True
p.view.use_translate_reports = True
p.view.use_translate_new_dataname = False
p.apps.show_corner_split = False
p.apps.show_edge_resize = False
p.apps.show_regions_visibility_toggle = False
sysp = p.system
print("system.use_online_access existe:", hasattr(sysp, "use_online_access"))
if hasattr(sysp, "use_online_access"):
    sysp.use_online_access = False
res = bpy.ops.wm.save_userpref()
print("save_userpref ->", res, "en", bpy.utils.user_resource('CONFIG'))
