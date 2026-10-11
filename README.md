# BIM Simple

Extensión de Blender que funciona encima de [Bonsai](https://bonsaibim.org) y ofrece una interfaz de modelado parecida a ArchiCAD: caja de herramientas con iconos propios, Info Box de parámetros y navegador de pisos. Sirve para dibujar muros, losas y columnas por piso sin entrar en los menús de Blender ni en los de Bonsai.

Cada elemento es una entidad IFC real (`IfcWall`, `IfcSlab`, `IfcColumn`) contenida en su `IfcBuildingStorey`. El `.ifc` resultante se abre y se edita con la interfaz estándar de Bonsai.

> Estado: en desarrollo (MVP). Fuera del MVP: puertas, ventanas, cubiertas, escaleras, cortes, láminas y cómputos.

## Requisitos

- Blender 5.2
- Bonsai 0.9.0 (versión `py313`), instalado y activado

## Instalación

1. Arma el paquete de la extensión desde la carpeta del repositorio:

   ```
   "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --command extension build --source-dir bim_simple
   ```

   Se crea `bim_simple-0.1.0.zip`.
2. En Blender: Editar > Preferencias > Obtener extensiones > menú ⌄ > Instalar desde disco, y elige el `.zip`.
3. En la barra lateral de la vista 3D (tecla N), pestaña **BIM Simple**, pulsa **Nuevo proyecto**.

## Prueba automática

```
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --python tests/test_mvp.py
```

Crea un proyecto con pisos a 0,00, 3,00 y 6,00 m, dibuja en el Piso 1 cuatro muros de 6 × 4 m, una losa y una columna, guarda el IFC, lo vuelve a abrir y comprueba el resultado.

## Estructura

- `bim_simple/`: la extensión (`core.py` tiene la lógica sin interfaz que usan las herramientas y la prueba).
- `tests/test_mvp.py`: prueba automática.
- `tools/make_icons.py`: genera los iconos `.dat` de la caja de herramientas.
- `PLAN.md`: API de Bonsai usada, decisiones de diseño y riesgos.

## Licencia

GPL-3.0-or-later, igual que Bonsai.
