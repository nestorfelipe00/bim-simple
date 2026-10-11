"""Tabla de órdenes del protocolo (contracts/core_api.md). Cada orden recibe el proyecto y sus argumentos."""

from . import EngineError, geometry


def _state(project, **_):
    return project.state()


def _meshes(project, ids=None):
    return geometry.meshes(project, ids)


COMMANDS = {
    "state": _state,
    "meshes": _meshes,
}


def execute(project, cmd, args):
    if cmd not in COMMANDS:
        raise EngineError(f"Orden desconocida: {cmd}")
    return COMMANDS[cmd](project, **args)
