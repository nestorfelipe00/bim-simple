"""Genera IFC de prueba "de otro programa" solo con ifcopenshell.api (sin Bonsai).

Se ejecuta dentro de Blender (--background) para usar el mismo ifcopenshell 0.9.0.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import ifcopenshell
import ifcopenshell.api.aggregate
import ifcopenshell.api.context
import ifcopenshell.api.geometry
import ifcopenshell.api.project
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.api.unit
import _util


def base(units="MILLIMETRE"):
    f = ifcopenshell.api.project.create_file(version="IFC4")
    project = ifcopenshell.api.root.create_entity(f, ifc_class="IfcProject", name="Proyecto ajeno")
    if units == "MILLIMETRE":
        length = ifcopenshell.api.unit.add_si_unit(f, unit_type="LENGTHUNIT", prefix="MILLI")
    else:
        length = ifcopenshell.api.unit.add_si_unit(f, unit_type="LENGTHUNIT")
    ifcopenshell.api.unit.assign_unit(f, units=[length])
    model = ifcopenshell.api.context.add_context(f, context_type="Model")
    ifcopenshell.api.context.add_context(f, context_type="Model", context_identifier="Body", target_view="MODEL_VIEW", parent=model)
    site = ifcopenshell.api.root.create_entity(f, ifc_class="IfcSite", name="Terreno")
    ifcopenshell.api.aggregate.assign_object(f, products=[site], relating_object=project)
    ifcopenshell.api.geometry.edit_object_placement(f, product=site)
    return f, project, site


def building(f, site, name, z=0.0):
    b = ifcopenshell.api.root.create_entity(f, ifc_class="IfcBuilding", name=name)
    ifcopenshell.api.aggregate.assign_object(f, products=[b], relating_object=site)
    m = np.eye(4)
    m[2][3] = z
    ifcopenshell.api.geometry.edit_object_placement(f, product=b, matrix=m, is_si=True)
    return b


def storey(f, b, name, z_mm, with_placement=True, elevation=True):
    s = ifcopenshell.api.root.create_entity(f, ifc_class="IfcBuildingStorey", name=name)
    ifcopenshell.api.aggregate.assign_object(f, products=[s], relating_object=b)
    if with_placement:
        m = np.eye(4)
        m[2][3] = z_mm
        ifcopenshell.api.geometry.edit_object_placement(f, product=s, matrix=m, is_si=False)
    if elevation:
        s.Elevation = z_mm
    return s


def proxy(f, container, name):
    e = ifcopenshell.api.root.create_entity(f, ifc_class="IfcBuildingElementProxy", name=name)
    ifcopenshell.api.spatial.assign_container(f, products=[e], relating_structure=container)
    ifcopenshell.api.geometry.edit_object_placement(f, product=e)
    return e


out = _util.OUT
# 1) Otro programa: milímetros, 3 pisos desordenados, sin Qto, uno sin placement (solo Elevation)
f, p, site = base("MILLIMETRE")
b = building(f, site, "Torre")
s2 = storey(f, b, "Nivel 2", 6000.0)
s0 = storey(f, b, "Nivel 0", 0.0)
s1 = storey(f, b, "Nivel 1", 3200.0)
sm = storey(f, b, "Subsuelo", -2800.0, with_placement=False)
proxy(f, s1, "Mueble en Nivel 1")
f.write(os.path.join(out, "otro_programa_mm.ifc"))

# 2) Dos edificios
f, p, site = base("METRE")
b1 = building(f, site, "Edificio A")
b2 = building(f, site, "Edificio B", z=10.0)
storey(f, b1, "A - PB", 0.0)
storey(f, b2, "B - PB", 0.0)
storey(f, b2, "B - P1", 3.0)
f.write(os.path.join(out, "dos_edificios.ifc"))

# 3) Edificio sin pisos, elemento en el edificio
f, p, site = base("METRE")
b = building(f, site, "Galpón")
proxy(f, b, "Elemento en el edificio")
f.write(os.path.join(out, "sin_pisos.ifc"))

# 4) Sin edificio
f, p, site = base("METRE")
proxy(f, site, "Elemento en el sitio")
f.write(os.path.join(out, "sin_edificio.ifc"))

# 5) Archivo dañado y archivo que no es IFC
with open(os.path.join(out, "danado.ifc"), "w", encoding="utf-8") as fh:
    fh.write("ISO-10303-21;\nHEADER;\nFILE_SCHEMA(('IFC4'));\nENDSEC;\nDATA;\n#1=IFCWALL('x',$,$\n")
with open(os.path.join(out, "no_es_ifc.ifc"), "w", encoding="utf-8") as fh:
    fh.write("Esto es un texto cualquiera.\n")
print("IFC de prueba generados en", out)
