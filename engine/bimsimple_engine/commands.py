"""Tabla de órdenes del protocolo (contracts/core_api.md). Cada orden recibe el proyecto y sus argumentos."""

from . import EngineError, geometry, project as project_commands


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
}


def execute(project, cmd, args):
    if cmd not in COMMANDS:
        raise EngineError(f"Orden desconocida: {cmd}")
    return COMMANDS[cmd](project, **args)
