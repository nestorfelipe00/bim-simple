"""Motor BIM del prototipo de BIM Simple.

IfcOpenShell detrás de un protocolo muy simple: la interfaz escribe en stdin una línea
JSON por orden ({"id": n, "cmd": "...", "args": {...}}) y el motor responde en stdout
una línea JSON ({"id": n, "ok": true, "result": ..., "ms": ...}). El IFC es la única
fuente de verdad; cada orden que lo cambia es una transacción (un paso de deshacer).

Solo usa la API LGPL de IfcOpenShell (nada de Bonsai) y el núcleo OpenCASCADE.
"""

import base64
import json
import sys
import time
import traceback

T0 = time.perf_counter()

import numpy as np
import ifcopenshell
import ifcopenshell.api.aggregate
import ifcopenshell.api.attribute
import ifcopenshell.api.context
import ifcopenshell.api.geometry
import ifcopenshell.api.material
import ifcopenshell.api.project
import ifcopenshell.api.pset
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.api.type
import ifcopenshell.api.unit
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.placement
import ifcopenshell.util.representation
import ifcopenshell.util.unit
import ifcopenshell.validate

IMPORT_MS = round((time.perf_counter() - T0) * 1000)
TOLERANCIA = 0.01  # m: dos extremos de muro a menos de esto se consideran el mismo punto
ALTURA_POR_DEFECTO = 3.0


class ErrorMotor(Exception):
    """Error con mensaje en español para mostrar al usuario."""


class Motor:
    def __init__(self):
        self.f = None
        self.ids = {}  # building, body, wall_type
        self.activo = None
        self.sucio = False
        self.ruta = ""
        self.geom = ifcopenshell.geom.settings()
        self.geom.set("use-world-coords", True)
        # "enable-layerset-slicing" falla con estos muros ("Unexpected topology"): cada muro sale como un sólido.

    # ---------- utilidades ----------
    def _e(self, ifc_id):
        try:
            return self.f.by_id(ifc_id)
        except RuntimeError:
            return None

    def _exigir_proyecto(self):
        if self.f is None:
            raise ErrorMotor("No hay ningún proyecto abierto.")

    def _pisos(self):
        edificio = self._e(self.ids["building"])
        pisos = [e for e in ifcopenshell.util.element.get_decomposition(edificio) if e.is_a("IfcBuildingStorey")]
        escala = ifcopenshell.util.unit.calculate_unit_scale(self.f)
        datos = []
        for p in pisos:
            cota = ifcopenshell.util.placement.get_storey_elevation(p) * escala
            qto = ifcopenshell.util.element.get_psets(p, qtos_only=True).get("Qto_BuildingStoreyBaseQuantities", {})
            datos.append({"id": p.id(), "nombre": p.Name or "", "cota": round(cota, 4), "altura_qto": qto.get("GrossHeight")})
        datos.sort(key=lambda d: (d["cota"], d["nombre"]))
        for i, d in enumerate(datos):  # altura = distancia al piso de arriba; el más alto, su GrossHeight
            if i + 1 < len(datos):
                d["altura"] = round(datos[i + 1]["cota"] - d["cota"], 4)
            else:
                d["altura"] = round(d["altura_qto"] or ALTURA_POR_DEFECTO, 4)
            del d["altura_qto"]
        return list(reversed(datos))  # el más alto primero, como el navegador de ArchiCAD

    def _piso(self, ifc_id):
        for d in self._pisos():
            if d["id"] == ifc_id:
                return d
        raise ErrorMotor("El piso indicado ya no existe.")

    def _corregir_activo(self):
        ids = [d["id"] for d in self._pisos()]
        if self.activo not in ids:
            self.activo = min(self._pisos(), key=lambda d: abs(d["cota"]))["id"] if ids else None

    def _transaccion(self, funcion):
        self.f.begin_transaction()
        try:
            resultado = funcion()
        except Exception:
            self.f.discard_transaction()
            raise
        self.f.end_transaction()
        self.sucio = True
        return resultado

    # ---------- proyecto ----------
    def nuevo_proyecto(self):
        f = ifcopenshell.api.project.create_file(version="IFC4")
        proyecto = ifcopenshell.api.root.create_entity(f, ifc_class="IfcProject", name="Proyecto")
        unidades = [ifcopenshell.api.unit.add_si_unit(f, unit_type=t) for t in ("LENGTHUNIT", "AREAUNIT", "VOLUMEUNIT", "PLANEANGLEUNIT")]
        ifcopenshell.api.unit.assign_unit(f, units=unidades)
        modelo = ifcopenshell.api.context.add_context(f, context_type="Model")
        body = ifcopenshell.api.context.add_context(f, context_type="Model", context_identifier="Body", target_view="MODEL_VIEW", parent=modelo)
        planta = ifcopenshell.api.context.add_context(f, context_type="Plan")
        ifcopenshell.api.context.add_context(f, context_type="Plan", context_identifier="Axis", target_view="GRAPH_VIEW", parent=planta)
        sitio = ifcopenshell.api.root.create_entity(f, ifc_class="IfcSite", name="Sitio")
        ifcopenshell.api.aggregate.assign_object(f, products=[sitio], relating_object=proyecto)
        edificio = ifcopenshell.api.root.create_entity(f, ifc_class="IfcBuilding", name="Edificio")
        ifcopenshell.api.aggregate.assign_object(f, products=[edificio], relating_object=sitio)
        for e in (sitio, edificio):
            ifcopenshell.api.geometry.edit_object_placement(f, product=e)

        tipo = ifcopenshell.api.root.create_entity(f, ifc_class="IfcWallType", name="Muro 0,20", predefined_type="STANDARD")
        capas = ifcopenshell.api.material.add_material_set(f, name="Muro 0,20", set_type="IfcMaterialLayerSet")
        revoque = ifcopenshell.api.material.add_material(f, name="Revoque", category="plaster")
        ladrillo = ifcopenshell.api.material.add_material(f, name="Ladrillo", category="brick")
        for mat, espesor in ((revoque, 0.02), (ladrillo, 0.16), (revoque, 0.02)):
            capa = ifcopenshell.api.material.add_layer(f, layer_set=capas, material=mat)
            ifcopenshell.api.material.edit_layer(f, layer=capa, attributes={"LayerThickness": espesor})
        ifcopenshell.api.material.assign_material(f, products=[tipo], type="IfcMaterialLayerSet", material=capas)

        self.f = f
        self.ids = {"building": edificio.id(), "body": body.id(), "wall_type": tipo.id()}
        self.activo = self._crear_piso("Planta Baja", 0.0, ALTURA_POR_DEFECTO).id()
        self.f.history.clear()
        self.f.future.clear()
        self.sucio = False
        self.ruta = ""
        return self.estado()

    def _crear_piso(self, nombre, cota, altura):
        f = self.f
        piso = ifcopenshell.api.root.create_entity(f, ifc_class="IfcBuildingStorey", name=nombre)
        ifcopenshell.api.aggregate.assign_object(f, products=[piso], relating_object=self._e(self.ids["building"]))
        matriz = np.eye(4)
        matriz[2][3] = cota
        ifcopenshell.api.geometry.edit_object_placement(f, product=piso, matrix=matriz)
        ifcopenshell.api.attribute.edit_attributes(f, product=piso, attributes={"Elevation": cota})
        qto = ifcopenshell.api.pset.add_qto(f, product=piso, name="Qto_BuildingStoreyBaseQuantities")
        ifcopenshell.api.pset.edit_qto(f, qto=qto, properties={"GrossHeight": altura})
        return piso

    def agregar_piso_arriba(self):
        self._exigir_proyecto()

        def hacer():
            pisos = self._pisos()
            alto = pisos[0]
            n = sum(1 for d in pisos if d["cota"] > 0) + 1
            return self._crear_piso(f"Piso {n}", alto["cota"] + alto["altura"], alto["altura"]).id()

        self._transaccion(hacer)
        return self.estado()

    def activar_piso(self, id):
        self._exigir_proyecto()
        self._piso(id)
        self.activo = id
        return self.estado()

    # ---------- muros ----------
    def _extremos(self, muro):
        matriz = ifcopenshell.util.placement.get_local_placement(muro.ObjectPlacement)
        eje = ifcopenshell.util.representation.get_reference_line(muro)
        return [(matriz @ np.array([p[0], p[1], 0.0, 1.0]))[:2] for p in eje]

    def _muros_del_piso(self, piso_id):
        piso = self._e(piso_id)
        return [e for e in ifcopenshell.util.element.get_contained(piso) if e.is_a("IfcWall")]

    def _crear_muro(self, p1, p2):
        f = self.f
        piso = self._piso(self.activo)
        p1, p2 = np.array(p1, dtype=float), np.array(p2, dtype=float)
        largo = float(np.linalg.norm(p2 - p1))
        if largo < 0.05:
            raise ErrorMotor("El muro es demasiado corto.")
        vecinos = self._muros_del_piso(self.activo)
        muro = ifcopenshell.api.root.create_entity(f, ifc_class="IfcWall", name="Muro")
        ifcopenshell.api.spatial.assign_container(f, products=[muro], relating_structure=self._e(self.activo))
        ifcopenshell.api.type.assign_type(f, related_objects=[muro], relating_type=self._e(self.ids["wall_type"]))
        rep = ifcopenshell.api.geometry.create_2pt_wall(
            f, element=muro, context=self._e(self.ids["body"]), p1=tuple(p1), p2=tuple(p2),
            elevation=piso["cota"], height=piso["altura"], thickness=0.20,
        )
        ifcopenshell.api.geometry.assign_representation(f, product=muro, representation=rep)
        afectados = {muro.id()}
        for otro in vecinos:  # unir en esquina con los muros que comparten un extremo
            if any(np.linalg.norm(a - b) < TOLERANCIA for a in (p1, p2) for b in self._extremos(otro)):
                ifcopenshell.api.geometry.connect_wall(f, muro, otro)
                afectados.add(otro.id())
        for i in afectados:
            ifcopenshell.api.geometry.regenerate_wall_representation(f, wall=self._e(i), length=largo, height=piso["altura"])
        return afectados

    def crear_muro(self, p1, p2):
        self._exigir_proyecto()
        afectados = self._transaccion(lambda: self._crear_muro(p1, p2))
        return {"afectados": sorted(afectados), "estado": self.estado()}

    def crear_recinto(self, x, y, ancho, largo):
        """Cuatro muros unidos en las esquinas, en un solo paso de deshacer."""
        self._exigir_proyecto()
        esquinas = [(x, y), (x + ancho, y), (x + ancho, y + largo), (x, y + largo)]

        def hacer():
            afectados = set()
            for i in range(4):
                afectados |= self._crear_muro(esquinas[i], esquinas[(i + 1) % 4])
            return afectados

        afectados = self._transaccion(hacer)
        return {"afectados": sorted(afectados), "estado": self.estado()}

    # ---------- deshacer ----------
    def deshacer(self):
        self._exigir_proyecto()
        if not self.f.history:
            raise ErrorMotor("No hay nada que deshacer.")
        self.f.undo()
        self.sucio = True
        self._corregir_activo()
        return self.estado()

    def rehacer(self):
        self._exigir_proyecto()
        if not self.f.future:
            raise ErrorMotor("No hay nada que rehacer.")
        self.f.redo()
        self.sucio = True
        self._corregir_activo()
        return self.estado()

    # ---------- geometría para Three.js ----------
    def mallas(self, ids=None):
        self._exigir_proyecto()
        elementos = [self._e(i) for i in ids] if ids else self.f.by_type("IfcElement")
        salida, fallos, t0 = [], [], time.perf_counter()
        for e in elementos:
            if e is None or not e.Representation:
                continue
            try:
                forma = ifcopenshell.geom.create_shape(self.geom, e)
            except RuntimeError as error:
                fallos.append({"id": e.id(), "error": str(error)})
                continue
            g = forma.geometry
            contenedor = ifcopenshell.util.element.get_container(e)
            salida.append({
                "id": e.id(),
                "clase": e.is_a(),
                "piso": contenedor.id() if contenedor else None,
                "v": base64.b64encode(np.asarray(g.verts, dtype=np.float32).tobytes()).decode(),
                "c": base64.b64encode(np.asarray(g.faces, dtype=np.uint32).tobytes()).decode(),
                "m": base64.b64encode(np.asarray(g.material_ids, dtype=np.int16).tobytes()).decode(),
                "materiales": [m.name for m in g.materials],
            })
        return {"elementos": salida, "fallos": fallos, "existentes": [e.id() for e in self.f.by_type("IfcElement")],
                "teselado_ms": round((time.perf_counter() - t0) * 1000, 1)}

    # ---------- guardar ----------
    def guardar(self, ruta):
        self._exigir_proyecto()
        self.f.write(ruta)
        registro = ifcopenshell.validate.json_logger()
        ifcopenshell.validate.validate(ruta, registro, express_rules=True)
        errores = [s for s in registro.statements if s.get("level") == "error"]
        self.ruta, self.sucio = ruta, False
        return {"ruta": ruta, "errores": len(errores), "mensajes": [str(s.get("message"))[:200] for s in errores[:5]],
                "estado": self.estado()}

    def estado(self):
        if self.f is None:
            return {"proyecto": False}
        return {
            "proyecto": True, "pisos": self._pisos(), "activo": self.activo, "sucio": self.sucio, "ruta": self.ruta,
            "deshacer": len(self.f.history), "rehacer": len(self.f.future),
            "muros": len(self.f.by_type("IfcWall")),
        }

    def ejecutar(self, cmd, args):
        acciones = {
            "nuevo_proyecto": self.nuevo_proyecto, "agregar_piso_arriba": self.agregar_piso_arriba,
            "activar_piso": self.activar_piso, "crear_muro": self.crear_muro, "crear_recinto": self.crear_recinto,
            "deshacer": self.deshacer, "rehacer": self.rehacer, "mallas": self.mallas,
            "guardar": self.guardar, "estado": self.estado,
        }
        if cmd not in acciones:
            raise ErrorMotor(f"Orden desconocida: {cmd}")
        return acciones[cmd](**args)


def main():
    salida = sys.stdout
    sys.stdout = sys.stderr  # cualquier print accidental no rompe el protocolo
    sys.stdin.reconfigure(encoding="utf-8")
    motor = Motor()
    salida.write(json.dumps({"id": 0, "ok": True, "result": {"listo": True, "ifcopenshell": ifcopenshell.version,
                                                             "importar_ms": IMPORT_MS}}) + "\n")
    salida.flush()
    for linea in sys.stdin:
        linea = linea.lstrip("﻿").strip()
        if not linea:
            continue
        t0 = time.perf_counter()
        msg = {}
        try:
            msg = json.loads(linea)
            respuesta = {"id": msg.get("id"), "ok": True, "result": motor.ejecutar(msg["cmd"], msg.get("args") or {})}
        except ErrorMotor as e:
            respuesta = {"id": msg.get("id"), "ok": False, "error": str(e)}
        except Exception as e:  # error inesperado: se devuelve con su traza para depurar
            respuesta = {"id": msg.get("id") if isinstance(msg, dict) else None, "ok": False,
                         "error": f"Error interno: {e}", "traza": traceback.format_exc(limit=4)}
        respuesta["ms"] = round((time.perf_counter() - t0) * 1000, 1)
        salida.write(json.dumps(respuesta) + "\n")
        salida.flush()


if __name__ == "__main__":
    main()
