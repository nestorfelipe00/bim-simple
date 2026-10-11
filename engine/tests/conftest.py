"""Fixtures de las pruebas del motor: proyecto en memoria, motor real como proceso y IFC de prueba."""

import json
import subprocess
from pathlib import Path

import pytest

from bimsimple_engine.project import Project
from tests import make_fixtures

REPO = Path(__file__).resolve().parents[2]
PYTHON = REPO / "runtime" / "python" / "python.exe"


@pytest.fixture
def project():
    return Project()


class EngineProcess:
    """El motor real, lanzado como lo lanza Electron (python -u -m bimsimple_engine)."""

    def __init__(self):
        self.process = subprocess.Popen([str(PYTHON), "-u", "-m", "bimsimple_engine"], stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")
        self.ready = json.loads(self.process.stdout.readline())
        self.next_id = 1

    def send_line(self, line):
        self.process.stdin.write(line + "\n")
        self.process.stdin.flush()
        return json.loads(self.process.stdout.readline())

    def send(self, cmd, **args):
        self.next_id += 1
        return self.send_line(json.dumps({"id": self.next_id, "cmd": cmd, "args": args}))

    def close(self):
        self.process.stdin.close()
        self.process.wait(timeout=10)


@pytest.fixture
def run_engine():
    engine = EngineProcess()
    yield engine
    engine.close()


@pytest.fixture
def fixtures(tmp_path):
    return make_fixtures.write_all(str(tmp_path / "fixtures"))
