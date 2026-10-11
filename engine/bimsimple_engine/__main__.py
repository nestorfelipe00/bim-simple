"""Bucle del protocolo: una orden JSON por línea en stdin, una respuesta JSON por línea en stdout.

stdout queda reservado para el protocolo; cualquier print accidental va a stderr.
"""

import json
import sys
import time
import traceback

_T0 = time.perf_counter()

import ifcopenshell  # noqa: E402

from . import EngineError  # noqa: E402
from .commands import execute  # noqa: E402
from .project import Project  # noqa: E402

IMPORT_MS = round((time.perf_counter() - _T0) * 1000)


def main():
    protocol = sys.stdout
    sys.stdout = sys.stderr
    sys.stdin.reconfigure(encoding="utf-8")
    project = Project()
    protocol.write(json.dumps({"id": 0, "ok": True, "result": {
        "ready": True, "ifcopenshell": ifcopenshell.version, "import_ms": IMPORT_MS}}) + "\n")
    protocol.flush()
    for line in sys.stdin:
        line = line.lstrip("﻿").strip()
        if not line:
            continue
        started = time.perf_counter()
        message = {}
        try:
            message = json.loads(line)
            response = {"id": message.get("id"), "ok": True,
                        "result": execute(project, message["cmd"], message.get("args") or {})}
        except EngineError as error:
            response = {"id": message.get("id"), "ok": False, "error": str(error)}
        except Exception as error:  # falla del motor: se devuelve con su traza para el registro
            response = {"id": message.get("id") if isinstance(message, dict) else None, "ok": False,
                        "error": f"Error interno: {error}", "trace": traceback.format_exc(limit=6)}
            print(response["trace"], file=sys.stderr)
        response["ms"] = round((time.perf_counter() - started) * 1000, 1)
        protocol.write(json.dumps(response) + "\n")
        protocol.flush()


if __name__ == "__main__":
    main()
