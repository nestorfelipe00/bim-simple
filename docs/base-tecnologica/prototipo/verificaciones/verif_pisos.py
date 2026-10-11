"""Verificación para el plan 001: operaciones de pisos con la API LGPL de IfcOpenShell (sin Bonsai)."""
import inspect
import multiprocessing
import os
import sys
import time

sys.path.insert(0, r"C:\Users\Usuario\AppData\Local\Temp\bsproto\motor")
import numpy as np
import ifcopenshell
import ifcopenshell.api.attribute
import ifcopenshell.api.geometry
import ifcopenshell.api.pset
import ifcopenshell.api.root
import ifcopenshell.geom
import ifcopenshell.util.element as ue
import ifcopenshell.util.placement as up
import ifcopenshell.validate
import motor as M

SAL = r"C:\Users\Usuario\AppData\Local\Temp\bsproto\salida"
print("firmas:")
for fn in (ifcopenshell.api.root.remove_product, ifcopenshell.api.attribute.edit_attributes,
           ifcopenshell.api.geometry.edit_object_placement, ue.get_decomposition):
    print("  ", fn.__module__ + "." + fn.__name__, inspect.signature(fn))

m = M.Motor()
m.nuevo_proyecto()
m.agregar_piso_arriba()
m.agregar_piso_arriba()
f = m.f
pisos = {d["nombre"]: d["id"] for d in m._pisos()}
m.activar_piso(pisos["Planta Baja"]); m.crear_recinto(0, 0, 6, 4)
m.activar_piso(pisos["Piso 1"]); m.crear_recinto(0, 0, 4, 3)
m.activar_piso(pisos["Piso 2"]); m.crear_muro([0, 0], [5, 0])

def z_mundo(e):
    return round(float(up.get_local_placement(e.ObjectPlacement)[2][3]), 4)

def resumen(titulo):
    print(titulo)
    for d in reversed(m._pisos()):
        p = f.by_id(d["id"])
        muros = [e for e in ue.get_contained(p) if e.is_a("IfcWall")]
        print(f"   {d['nombre']:12} cota={d['cota']:<5} altura={d['altura']:<5} Elevation={p.Elevation} "
              f"muros={len(muros)} z_muros={sorted({z_mundo(w) for w in muros})}")

def transaccion(fn):
    f.begin_transaction(); fn(); f.end_transaction()

def mover_piso(piso, nueva_cota):
    """Mueve el piso y sus elementos (should_transform_children=True) y actualiza Elevation."""
    matriz = np.array(up.get_local_placement(piso.ObjectPlacement))
    matriz[2][3] = nueva_cota
    ifcopenshell.api.geometry.edit_object_placement(f, product=piso, matrix=matriz, is_si=True, should_transform_children=True)
    ifcopenshell.api.attribute.edit_attributes(f, product=piso, attributes={"Elevation": nueva_cota})

def altura(piso, h):
    qto = ue.get_psets(piso, qtos_only=True)["Qto_BuildingStoreyBaseQuantities"]["id"]
    ifcopenshell.api.pset.edit_qto(f, qto=f.by_id(qto), properties={"GrossHeight": h})

resumen("1. inicial")

# Renombrar
t = time.perf_counter()
transaccion(lambda: ifcopenshell.api.attribute.edit_attributes(f, product=f.by_id(pisos["Piso 1"]), attributes={"Name": "Primer piso"}))
print(f"2. renombrar: {f.by_id(pisos['Piso 1']).Name} ({(time.perf_counter()-t)*1000:.1f} ms)")
f.undo(); print("   deshacer ->", f.by_id(pisos["Piso 1"]).Name); f.redo(); print("   rehacer  ->", f.by_id(pisos["Piso 1"]).Name)

# Cambiar la altura de Planta Baja a 3,50: suben Piso 1 y Piso 2 con sus muros (FR-016)
t = time.perf_counter()
def subir():
    altura(f.by_id(pisos["Planta Baja"]), 3.5)
    for nombre in ("Piso 2", "Primer piso"):
        p = [x for x in f.by_type("IfcBuildingStorey") if x.Name == nombre][0]
        mover_piso(p, up.get_storey_elevation(p) + 0.5)
transaccion(subir)
resumen(f"3. altura de Planta Baja 3,50 ({(time.perf_counter()-t)*1000:.1f} ms)")
f.undo(); resumen("   deshacer"); f.redo(); resumen("   rehacer")

# Contar y borrar Piso 2 con su muro (FR-017)
p2 = f.by_id(pisos["Piso 2"])
cuenta = [e for e in ue.get_decomposition(p2) if e.is_a("IfcElement") and not e.is_a("IfcFeatureElementSubtraction")]
print("4. elementos en Piso 2:", len(cuenta))
t = time.perf_counter()
def borrar():
    for e in cuenta:
        ifcopenshell.api.root.remove_product(f, product=e)
    ifcopenshell.api.root.remove_product(f, product=p2)
transaccion(borrar)
huerfanos = [e for e in f.by_type("IfcElement") if not ue.get_container(e)]
resumen(f"   borrado ({(time.perf_counter()-t)*1000:.1f} ms); elementos sin piso: {len(huerfanos)}")
f.undo(); resumen("   deshacer el borrado")
f.redo()

ruta = os.path.join(SAL, "verif_pisos.ifc")
f.write(ruta)
reg = ifcopenshell.validate.json_logger()
ifcopenshell.validate.validate(ruta, reg, express_rules=True)
print("5. validación:", len([s for s in reg.statements if s.get("level") == "error"]), "errores")

# Abrir un IFC de terceros y teselar todo con el iterador en paralelo
f2 = ifcopenshell.open(ruta)
s = ifcopenshell.geom.settings(); s.set("use-world-coords", True)
t = time.perf_counter()
it = ifcopenshell.geom.iterator(s, f2, multiprocessing.cpu_count())
n = 0
if it.initialize():
    while True:
        forma = it.get(); n += 1
        if not it.next():
            break
print(f"6. iterador: {n} elementos teselados en {(time.perf_counter()-t)*1000:.1f} ms con {multiprocessing.cpu_count()} núcleos; id del primero: {forma.id}, guid: {forma.guid}")
