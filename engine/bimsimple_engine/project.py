"""Estado del proyecto abierto (archivo IFC, ruta, cambios sin guardar, piso activo) y órdenes de proyecto."""

import ifcopenshell
import ifcopenshell.api.aggregate
import ifcopenshell.api.context
import ifcopenshell.api.geometry
import ifcopenshell.api.project as project_api
import ifcopenshell.api.root
import ifcopenshell.api.unit
import ifcopenshell.util.unit
import ifcopenshell.validate

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


# ---------- órdenes de proyecto ----------
def new_project(project):
    """IFC4 en metros: Proyecto > Sitio > Edificio > Planta Baja (0,00 / 3,00), activa, sin historial (FR-007)."""
    f = project_api.create_file(version="IFC4")
    ifc_project = ifcopenshell.api.root.create_entity(f, ifc_class="IfcProject", name="Proyecto")
    units = [ifcopenshell.api.unit.add_si_unit(f, unit_type=t)
             for t in ("LENGTHUNIT", "AREAUNIT", "VOLUMEUNIT", "PLANEANGLEUNIT")]
    ifcopenshell.api.unit.assign_unit(f, units=units)
    model = ifcopenshell.api.context.add_context(f, context_type="Model")
    ifcopenshell.api.context.add_context(f, context_type="Model", context_identifier="Body",
                                         target_view="MODEL_VIEW", parent=model)
    plan = ifcopenshell.api.context.add_context(f, context_type="Plan")
    ifcopenshell.api.context.add_context(f, context_type="Plan", context_identifier="Axis",
                                         target_view="GRAPH_VIEW", parent=plan)
    site = ifcopenshell.api.root.create_entity(f, ifc_class="IfcSite", name="Sitio")
    ifcopenshell.api.aggregate.assign_object(f, products=[site], relating_object=ifc_project)
    building = ifcopenshell.api.root.create_entity(f, ifc_class="IfcBuilding", name="Edificio")
    ifcopenshell.api.aggregate.assign_object(f, products=[building], relating_object=site)
    for element in (site, building):
        ifcopenshell.api.geometry.edit_object_placement(f, product=element)
    previous = project.file
    project.file = f
    try:
        storeys.create_storey(project, "Planta Baja", 0.0, storeys.DEFAULT_HEIGHT)
    except Exception:
        project.file = previous  # si algo falla, sigue abierto el proyecto anterior
        raise
    project.replace_file(f, "")
    return {"state": project.state()}


def save_project(project, path=None):
    """Escribe el IFC en path, o en la ruta actual (FR-009). La validación corre aparte (research R6)."""
    project.require_project()
    target = path or project.path
    if not target:
        raise EngineError("Elige dónde guardar el proyecto.")
    project.file.write(target)
    project.path = target
    project.dirty = False
    return {"state": project.state(), "path": target}


def validate_file(project, path):
    """Validación IFC4 con reglas EXPRESS; devuelve la cantidad de errores y los primeros mensajes (SC-003)."""
    logger = ifcopenshell.validate.json_logger()
    ifcopenshell.validate.validate(path, logger, express_rules=True)
    errors = [s for s in logger.statements if s.get("level") == "error"]
    return {"errors": len(errors), "messages": [str(s.get("message"))[:200] for s in errors[:5]]}
