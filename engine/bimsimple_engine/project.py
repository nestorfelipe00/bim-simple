"""Estado del proyecto abierto: el archivo IFC, su ruta, los cambios sin guardar y el piso activo."""

import ifcopenshell
import ifcopenshell.util.unit

from . import EngineError, storeys


class Project:
    def __init__(self):
        self.file = None  # ifcopenshell.file del proyecto abierto
        self.path = ""  # vacío si nunca se guardó
        self.dirty = False
        self.active_storey_id = None  # ajuste de la interfaz: vive aquí, no en el IFC

    # ---------- utilidades ----------
    def require_project(self):
        if self.file is None:
            raise EngineError("No hay ningún proyecto abierto.")

    def entity(self, ifc_id):
        try:
            return self.file.by_id(ifc_id)
        except RuntimeError:
            return None

    def unit_scale(self):
        return ifcopenshell.util.unit.calculate_unit_scale(self.file)

    def transaction(self, function):
        """Ejecuta una orden que cambia el IFC como un único paso de deshacer."""
        self.file.begin_transaction()
        try:
            result = function()
        except Exception:
            self.file.discard_transaction()
            raise
        self.file.end_transaction()
        self.dirty = True
        return result

    def replace_file(self, ifc_file, path):
        """Cambia de archivo (Nuevo o Abrir): historial vacío, sin cambios y piso activo recalculado."""
        ifc_file.history.clear()
        ifc_file.future.clear()
        self.file = ifc_file
        self.path = path
        self.dirty = False
        self.active_storey_id = storeys.nearest_to_zero(self)

    # ---------- estado para la interfaz (contracts/core_api.md, "Estado") ----------
    def state(self):
        if self.file is None:
            return {"has_project": False, "has_building": False, "path": "", "dirty": False, "storeys": [],
                    "active_storey_id": None, "notice": "", "can_undo": False, "can_redo": False}
        return {
            "has_project": True,
            "has_building": storeys.building(self) is not None,
            "path": self.path,
            "dirty": self.dirty,
            "storeys": storeys.list_storeys(self),
            "active_storey_id": self.active_storey_id,
            "notice": storeys.notice(self),
            "can_undo": len(self.file.history) > 0,
            "can_redo": len(self.file.future) > 0,
        }
