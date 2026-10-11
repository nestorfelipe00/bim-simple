"""Tabla de órdenes del protocolo (contracts/core_api.md). Cada orden recibe el proyecto y sus argumentos."""

from . import EngineError, geometry, project as project_commands, storeys


def _state(project, **_):
    return project.state()


def _meshes(project, ids=None):
    return geometry.meshes(project, ids)


COMMANDS = {
    "state": _state,
    "meshes": _meshes,
    "new_project": lambda project: project_commands.new_project(project),
    "save_project": lambda project, path=None: project_commands.save_project(project, path),
    "validate_file": lambda project, path: project_commands.validate_file(project, path),
    "undo": lambda project: project_commands.undo(project),
    "redo": lambda project: project_commands.redo(project),
    "add_storey_above": lambda project: storeys.add_storey_above(project),
    "add_storey_below": lambda project: storeys.add_storey_below(project),
    "edit_storey": lambda project, id, name=None, elevation=None, height=None: storeys.edit_storey(
        project, id, name, elevation, height),
    "count_storey_elements": lambda project, id: storeys.count_storey_elements(project, id),
    "delete_storey": lambda project, id: storeys.delete_storey(project, id),
}


def execute(project, cmd, args):
    if cmd not in COMMANDS:
        raise EngineError(f"Orden desconocida: {cmd}")
    return COMMANDS[cmd](project, **args)
