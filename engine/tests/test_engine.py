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


# ---------- Historia 2: organizar los pisos ----------
def _abrir(project, ruta):
    """Carga un IFC de prueba sin pasar por open_project (Historia 4)."""
    project.replace_file(ifcopenshell.open(ruta), ruta)


def _pisos(project):
    return {s["name"]: s for s in project.state()["storeys"]}


def _z_mundo(elemento):
    import ifcopenshell.util.placement as up
    return round(float(up.get_local_placement(elemento.ObjectPlacement)[2][3]), 4)


def _sin_contadores(estado):
    return {k: v for k, v in estado.items() if k not in ("can_undo", "can_redo", "dirty")}


def test_agregar_arriba_y_abajo(project):
    execute(project, "new_project", {})
    execute(project, "add_storey_above", {})
    estado = execute(project, "add_storey_above", {})["state"]
    estado = execute(project, "add_storey_below", {})["state"]
    filas = [(s["name"], s["elevation"], s["height"]) for s in estado["storeys"]]
    assert filas == [("Piso 2", 6.0, 3.0), ("Piso 1", 3.0, 3.0), ("Planta Baja", 0.0, 3.0), ("Sótano 1", -3.0, 3.0)]
    assert estado["dirty"] is True and estado["can_undo"] is True


def test_altura_mueve_pisos_de_arriba_con_sus_elementos(project, fixtures):
    _abrir(project, fixtures["con_elementos"])
    pisos = _pisos(project)
    resultado = execute(project, "edit_storey", {"id": pisos["Planta Baja"]["id"], "height": 3.5})
    pisos = _pisos(project)
    assert (pisos["Planta Baja"]["height"], pisos["Piso 1"]["elevation"], pisos["Piso 2"]["elevation"]) == (3.5, 3.5, 6.5)
    muros = {m.Name: _z_mundo(m) for m in project.file.by_type("IfcWall")}
    assert muros == {"Muro Planta Baja": 0.0, "Muro Piso 1": 3.5, "Muro Piso 2": 6.5}
    assert set(resultado["changed_ids"]) >= {m.id() for m in project.file.by_type("IfcWall") if m.Name != "Muro Planta Baja"}


def test_cota_mueve_el_piso_y_los_de_arriba(project, fixtures):
    _abrir(project, fixtures["con_elementos"])
    pisos = _pisos(project)
    execute(project, "edit_storey", {"id": pisos["Piso 1"]["id"], "elevation": 3.2})
    pisos = _pisos(project)
    assert (pisos["Planta Baja"]["height"], pisos["Piso 1"]["elevation"], pisos["Piso 2"]["elevation"]) == (3.2, 3.2, 6.2)
    assert {m.Name: _z_mundo(m) for m in project.file.by_type("IfcWall")}["Muro Piso 2"] == 6.2


def test_rechazos_con_su_texto(project):
    execute(project, "new_project", {})
    piso1 = execute(project, "add_storey_above", {})["storey_id"]
    planta_baja = _pisos(project)["Planta Baja"]["id"]
    casos = [
        ({"id": piso1, "elevation": 0.0}, "La cota debe ser mayor que la del piso de abajo («Planta Baja», 0,00 m)."),
        ({"id": piso1, "height": 0}, "La altura debe ser mayor que 0."),
        ({"id": piso1, "name": "   "}, "El nombre del piso no puede quedar vacío."),
    ]
    antes = project.state()
    for args, texto in casos:
        with pytest.raises(EngineError) as error:
            execute(project, "edit_storey", args)
        assert str(error.value) == texto
    assert project.state() == antes
    execute(project, "delete_storey", {"id": piso1})
    with pytest.raises(EngineError, match="^No se puede borrar el único piso del edificio.$"):
        execute(project, "delete_storey", {"id": planta_baja})


def test_nombres_repetidos(project):
    execute(project, "new_project", {})
    piso1 = execute(project, "add_storey_above", {})["storey_id"]
    execute(project, "edit_storey", {"id": piso1, "name": "Planta Baja"})
    assert [s["name"] for s in project.state()["storeys"]] == ["Planta Baja", "Planta Baja"]


def test_borrar_piso_con_elementos(project, fixtures):
    _abrir(project, fixtures["con_elementos"])
    pisos = _pisos(project)
    project.active_storey_id = pisos["Piso 1"]["id"]
    assert execute(project, "count_storey_elements", {"id": pisos["Piso 1"]["id"]})["count"] == 1
    resultado = execute(project, "delete_storey", {"id": pisos["Piso 1"]["id"]})
    estado = resultado["state"]
    assert [s["name"] for s in estado["storeys"]] == ["Piso 2", "Planta Baja"]
    assert estado["active_storey_id"] == pisos["Planta Baja"]["id"]  # pasa al de abajo
    assert [e for e in project.file.by_type("IfcElement") if not ue.get_container(e)] == []
    assert pisos["Piso 1"]["id"] in resultado["deleted_ids"]
    assert _pisos(project)["Planta Baja"]["height"] == 6.0  # mide hasta el siguiente; los de arriba no se mueven
    assert ue.get_psets(project.file.by_id(pisos["Planta Baja"]["id"]), qtos_only=True)["Qto_BuildingStoreyBaseQuantities"]["GrossHeight"] == 6.0


def test_deshacer_y_rehacer(project, fixtures):
    _abrir(project, fixtures["con_elementos"])
    inicial = _sin_contadores(project.state())
    pisos = _pisos(project)
    acciones = [
        ("add_storey_above", {}),
        ("edit_storey", {"id": pisos["Planta Baja"]["id"], "height": 3.5, "name": "PB"}),
        ("delete_storey", {"id": pisos["Piso 2"]["id"]}),
    ]
    estados = [inicial]
    for cmd, args in acciones:
        execute(project, cmd, args)
        estados.append(_sin_contadores(project.state()))
    for esperado in reversed(estados[:-1]):
        execute(project, "undo", {})
        assert _sin_contadores(project.state()) == esperado
    for esperado in estados[1:]:
        execute(project, "redo", {})
        assert _sin_contadores(project.state()) == esperado
    assert project.state()["dirty"] is True
    with pytest.raises(EngineError, match="^No hay nada que rehacer.$"):
        execute(project, "redo", {})


def test_guardar_y_reabrir_pisos(project, tmp_path):
    import ifcopenshell.util.placement as up
    execute(project, "new_project", {})
    execute(project, "add_storey_above", {})
    piso2 = execute(project, "add_storey_above", {})["storey_id"]
    execute(project, "edit_storey", {"id": piso2, "name": "Azotea", "height": 2.5})
    ruta = str(tmp_path / "pisos.ifc")
    execute(project, "save_project", {"path": ruta})
    f = ifcopenshell.open(ruta)
    datos = {s.Name: (s.Elevation, round(float(up.get_local_placement(s.ObjectPlacement)[2][3]), 4),
                      ue.get_psets(s, qtos_only=True)["Qto_BuildingStoreyBaseQuantities"]["GrossHeight"])
             for s in f.by_type("IfcBuildingStorey")}
    assert datos == {"Planta Baja": (0.0, 0.0, 3.0), "Piso 1": (3.0, 3.0, 3.0), "Azotea": (6.0, 6.0, 2.5)}
    assert execute(project, "validate_file", {"path": ruta})["errors"] == 0


def test_tiempo_con_diez_pisos(project):
    import time
    execute(project, "new_project", {})
    for _ in range(9):
        execute(project, "add_storey_above", {})
    planta_baja = _pisos(project)["Planta Baja"]["id"]
    for cmd, args in (("add_storey_above", {}), ("edit_storey", {"id": planta_baja, "height": 3.2}), ("undo", {}), ("redo", {})):
        inicio = time.perf_counter()
        execute(project, cmd, args)
        assert (time.perf_counter() - inicio) * 1000 < 50, cmd


# ---------- Historia 3: trabajar en un piso ----------
def test_activar_no_cambia_el_ifc(project, fixtures):
    _abrir(project, fixtures["con_elementos"])
    pisos = _pisos(project)
    assert project.state()["active_storey_id"] == pisos["Planta Baja"]["id"]
    estado = execute(project, "activate_storey", {"id": pisos["Piso 1"]["id"]})["state"]
    assert estado["active_storey_id"] == pisos["Piso 1"]["id"]
    assert estado["dirty"] is False and estado["can_undo"] is False and estado["can_redo"] is False
    with pytest.raises(EngineError, match="^El piso indicado ya no existe.$"):
        execute(project, "activate_storey", {"id": 999999})
    assert project.state()["active_storey_id"] == pisos["Piso 1"]["id"]


def test_siempre_hay_un_piso_activo(project, fixtures):
    _abrir(project, fixtures["con_elementos"])
    pisos = _pisos(project)
    ids = {s["id"] for s in project.state()["storeys"]}
    # borrar el activo: pasa al de abajo; si era el más bajo, al de arriba
    execute(project, "activate_storey", {"id": pisos["Planta Baja"]["id"]})
    estado = execute(project, "delete_storey", {"id": pisos["Planta Baja"]["id"]})["state"]
    assert estado["active_storey_id"] == pisos["Piso 1"]["id"]
    # deshacer un piso nuevo que estaba activo: pasa al de cota más cercana a 0,00
    nuevo = execute(project, "add_storey_above", {})["storey_id"]
    execute(project, "activate_storey", {"id": nuevo})
    estado = execute(project, "undo", {})["state"]
    assert estado["active_storey_id"] in {s["id"] for s in estado["storeys"]}
    assert estado["active_storey_id"] == pisos["Piso 1"]["id"]
    # deshacer el borrado: el activo sigue existiendo
    estado = execute(project, "undo", {})["state"]
    assert {s["id"] for s in estado["storeys"]} == ids
    assert estado["active_storey_id"] in ids


def test_mallas_con_su_piso(project, fixtures):
    _abrir(project, fixtures["con_elementos"])
    pisos = _pisos(project)
    resultado = execute(project, "meshes", {})
    muros = {m["id"]: m for m in resultado["meshes"] if m["ifc_class"] == "IfcWall"}
    esperado = {m.id(): pisos[m.Name.replace("Muro ", "")]["id"] for m in project.file.by_type("IfcWall")}
    assert {i: m["storey_id"] for i, m in muros.items()} == esperado
    assert resultado["failures"] == []