# BIM Simple

Programa BIM de escritorio para arquitectos, con una forma de trabajo parecida a ArchiCAD. El modelo
es un archivo **IFC** (IFC4, en metros), que es la única fuente de verdad: lo que se ve en pantalla sale del
IFC, y el IFC guardado se abre en cualquier otro programa BIM.

> **Estado**: función 001 implementada. Incluye la pantalla (planta del piso activo + vista 3D), el proyecto
> nuevo, Abrir / Guardar / Guardar como, el navegador de pisos (agregar, editar cota y altura, borrar,
> activar con doble clic) y Deshacer / Rehacer. Las herramientas de dibujo (muro, losa, columna) llegan en las
> funciones siguientes.

## Cómo está hecho

Son tres piezas (constitución, Principio III):

| Pieza | Tecnología | Carpeta |
|---|---|---|
| **Ventana**: menús, diálogos de Windows, título, pregunta al cerrar | Electron 44.4.5 | `app/src/main/` |
| **Interfaz**: planta, vista 3D y panel "BIM Simple" | Three.js 0.186.1 + camera-controls 3.1.2 | `app/src/renderer/` |
| **Motor**: abre, cambia y guarda el IFC | Python 3.14.7 embebido + IfcOpenShell 0.9.0 | `engine/bimsimple_engine/` |

La interfaz nunca toca el IFC: le manda órdenes al motor, una línea JSON por mensaje
([contracts/core_api.md](specs/001-espacio-trabajo-pisos/contracts/core_api.md)).

## Requisitos

- Windows 11.
- Node.js 24 y npm 11, solo para desarrollar.

## Preparar el entorno de desarrollo

```bash
powershell -ExecutionPolicy Bypass -File tools/setup-dev.ps1
```

Arma dos carpetas que no van al repositorio:

- `runtime/python`: Python embebible con IfcOpenShell y sus dependencias, en las versiones fijas de
  `engine/requirements.txt`.
- `app/node_modules`: Electron, Three.js y camera-controls, en las versiones fijas de `app/package.json`.

Sin parámetros copia el Python ya verificado del prototipo. Con `-Descargar` lo baja de python.org y PyPI y
verifica el SHA-256.

## Abrir el programa en modo de desarrollo

```bash
npm --prefix app start
```

## Pruebas automáticas

Prueba del motor, sin interfaz:

```bash
runtime/python/python.exe -m pytest engine/tests -q -p no:cacheprovider
```

Prueba del programa, con la ventana oculta: recorre las cuatro historias como lo haría el usuario y deja
`resultado.json` y capturas en `app/test-output/`.

```bash
npm --prefix app test
```

Las dos tienen que terminar en verde: `N passed` y `RESULTADO: TODO OK`.

## Instalador

```bash
npm --prefix app run dist
```

Genera `app/dist/BIM Simple Setup <versión>.exe`. El instalador es por usuario y no pide administrador.
Crea los accesos directos en el Escritorio y en el menú Inicio, y se desinstala desde "Agregar o quitar
programas". Necesita electron-builder (tarea T050 de la función 001).

## Estructura

```
app/                  ventana e interfaz (Electron)
  src/main/           proceso principal: main.js, engine.js (motor), validator.js
  src/renderer/       página: vistas, panel de pisos, mallas
  test/               prueba del programa con la ventana oculta
  build/              icono, textos de licencias
engine/               motor (Python)
  bimsimple_engine/   protocolo, proyecto, pisos, geometría
  tests/              pruebas del motor e IFC de prueba
runtime/python/       Python embebido (lo arma tools/setup-dev.ps1; no está en git)
tools/                setup-dev.ps1, make_icon.py
specs/                especificaciones de cada función (Spec Kit)
.specify/             constitución y plantillas de Spec Kit
docs/                 evaluación de la base tecnológica y prototipo
```

## Método de trabajo

Cada función se construye con [Spec Kit](https://github.com/github/spec-kit): constitución
(`.specify/memory/constitution.md`) → especificación → plan → tareas → análisis → implementación, en
`specs/<número>-<nombre>/`.

## Licencia

Copyright (c) 2026 Nestor Torres. Todos los derechos reservados.

El archivo `LICENSE` del repositorio todavía tiene el texto GPL-3.0 del MVP anterior (una extensión de Blender
que ya no se usa). Su reemplazo está pendiente de la decisión del usuario (tarea T056). Los componentes de
terceros y sus licencias están en `app/build/LEEME-licencias.txt`. IfcOpenShell se usa bajo LGPL-3.0, en su
propia carpeta, sin modificar y reemplazable.
