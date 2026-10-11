"""Motor BIM de BIM Simple: IfcOpenShell detrás de un protocolo de órdenes JSON (contracts/core_api.md)."""

__version__ = "0.1.0"


class EngineError(Exception):
    """Error esperable (regla del modelo, archivo inválido…). El mensaje va en español, listo para el usuario."""
