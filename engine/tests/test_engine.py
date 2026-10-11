"""Prueba del motor sin interfaz (constitución, Principio V)."""

import json


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
