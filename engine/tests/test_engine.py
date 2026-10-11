"""Prueba del motor sin interfaz (constitución, Principio V)."""

import json
import os

import ifcopenshell
import ifcopenshell.util.element as ue
import ifcopenshell.util.unit
import pytest

from bimsimple_engine import EngineError
from bimsimple_engine.commands import execute


# ---------- protocolo (contracts/core_api.md, "Mensajes") ----------
def test_ready(run_engine):
    assert run_engine.ready["id"] == 0
    assert run_engine.ready["ok"] is True
    assert run_engine.ready["result"]["ready"] is True
    assert run_engine.ready["result"]["ifcopenshell"] == "0.9.0"


def test_orden_desconocida(run_engine):
    respuesta = run_engine.send("orden_que_no_existe")
    assert respuesta["ok"] is False
    assert respuesta["error"] == "Orden desconocida: orden_que_no_existe"


def test_sin_proyecto(run_engine):
    assert run_engine.send("meshes")["error"] == "No hay ningún proyecto abierto."
    estado = run_engine.send("state")["result"]
    assert estado["has_project"] is False and estado["storeys"] == [] and estado["can_undo"] is False


def test_acepta_bom(run_engine):
    respuesta = run_engine.send_line("﻿" + json.dumps({"id": 99, "cmd": "state", "args": {}}))
    assert respuesta["ok"] is True and respuesta["id"] == 99


def test_toda_respuesta_tiene_ms(run_engine):
    for respuesta in (run_engine.send("state"), run_engine.send("orden_que_no_existe")):
        assert isinstance(respuesta["ms"], (int, float))


# ---------- Historia 1: proyecto nuevo y guardar ----------
def test_nuevo_proyecto(project):
    estado = execute(project, "new_project", {})["state"]
    f = project.file
    assert f.schema == "IFC4"
    assert ifcopenshell.util.unit.get_project_unit(f, "LENGTHUNIT").Name == "METRE"
    assert [e.Name for e in f.by_type("IfcProject")] == ["Proyecto"]
    assert [e.Name for e in f.by_type("IfcSite")] == ["Sitio"]
    assert [e.Name for e in f.by_type("IfcBuilding")] == ["Edificio"]
    assert len(estado["storeys"]) == 1
    planta_baja = estado["storeys"][0]
    assert (planta_baja["name"], planta_baja["elevation"], planta_baja["height"]) == ("Planta Baja", 0.0, 3.0)
    assert ue.get_psets(f.by_id(planta_baja["id"]), qtos_only=True)["Qto_BuildingStoreyBaseQuantities"]["GrossHeight"] == 3.0
    assert estado["active_storey_id"] == planta_baja["id"]
    assert estado["dirty"] is False and estado["can_undo"] is False and estado["has_building"] is True


def test_segundo_nuevo_proyecto(project):
    execute(project, "new_project", {})
    estado = execute(project, "new_project", {})["state"]
    assert len(estado["storeys"]) == 1


def test_guardar_y_validar(project, tmp_path):
    execute(project, "new_project", {})
    ruta = str(tmp_path / "proyecto.ifc")
    resultado = execute(project, "save_project", {"path": ruta})
    assert os.path.exists(ruta)
    assert resultado["path"] == ruta and resultado["state"]["path"] == ruta and resultado["state"]["dirty"] is False
    assert execute(project, "validate_file", {"path": ruta})["errors"] == 0


def test_guardar_sin_ruta(project):
    execute(project, "new_project", {})
    with pytest.raises(EngineError, match="^Elige dónde guardar el proyecto.$"):
        execute(project, "save_project", {})
