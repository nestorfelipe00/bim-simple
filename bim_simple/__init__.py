"""BIM Simple: interfaz de modelado tipo ArchiCAD sobre Bonsai."""

import bpy

try:
    import bonsai.tool  # noqa: F401
except ImportError as error:
    raise ImportError("BIM Simple necesita Bonsai 0.9.0 instalado y activado.") from error

from . import operators, props, tools, ui

classes = (*props.classes, *operators.classes, *ui.classes)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    props.register()
    tools.register()
    ui.register()


def unregister():
    ui.unregister()
    tools.unregister()
    props.unregister()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
