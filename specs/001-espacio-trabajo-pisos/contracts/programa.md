# Contrato: el programa BIM Simple (instalación, carpetas, arranque y licencias)

Fuente: research R1, R3, R9 y R10; spec FR-001, FR-005, SC-005 y SC-007. La prueba del programa y
la lista manual comprueban lo que este contrato fija.

## Instalador

| Elemento | Contrato |
|---|---|
| Archivo | `BIM Simple Setup <versión>.exe`, armado con `npm --prefix app run dist` (electron-builder 26.17.0, destino NSIS) |
| Instalación | **Por usuario, sin administrador** (`perMachine: false`), en un paso (`oneClick: true`) |
| Destino | `%LOCALAPPDATA%\Programs\<nombre del paquete>\` |
| Accesos directos | "BIM Simple" en el Escritorio y en el menú Inicio (los crea el instalador) |
| Desinstalar | Desde "Agregar o quitar programas". No deja nada fuera de los archivos del usuario (SC-005): ni la carpeta del programa, ni `%APPDATA%\BIM Simple` (con `deleteAppDataOnUninstall: true`), ni la copia `%LOCALAPPDATA%\bim-simple-updater` (research R9, riesgo 3) |
| Identidad | `appId` y AppUserModelID = `BIMSimple.BIMSimple`. No se cambia nunca |
| Icono | `app/build/icon.ico` con 16, 24, 32, 48 y 256 px |

## Carpetas instaladas

```text
%LOCALAPPDATA%\Programs\<nombre del paquete>\
├── BIM Simple.exe                 Electron (ventana + interfaz en resources\app.asar)
├── resources\
│   ├── app.asar                   código de la ventana y la interfaz
│   ├── python\                    Python 3.14.7 embebible + Lib\site-packages (IfcOpenShell en su carpeta, sin modificar)
│   └── engine\bimsimple_engine\   motor BIM
├── LICENSES.chromium.html         (de Electron)
└── licencias\                     textos de licencia: GPL-3.0 de BIM Simple, LGPL-3.0 y GPL-3.0 (para IfcOpenShell), MIT de Electron, Three.js y camera-controls, PSF de Python y las de las dependencias
```

## Datos del usuario

- **Proyectos**: donde el usuario los guarde (`.ifc`).
- **Registro del motor** (stderr): `%APPDATA%\BIM Simple\logs\engine.log`, que es la carpeta de
  datos de Electron. Se borra al desinstalar.
- No se escribe en el registro de Windows salvo lo que hace el instalador (entrada de desinstalación).
- No se modifica ninguna otra instalación: Blender, Python del sistema y similares.

## Arranque

1. El acceso directo abre `BIM Simple.exe`.
2. El proceso principal fija el AppUserModelID, crea la ventana y lanza el motor
   (`resources\python\python.exe -u -m bimsimple_engine`, con `windowsHide`).
3. El motor anuncia `ready`; la pantalla queda lista sin proyecto (FR-006).
4. Desde el doble clic hasta poder pulsar "Nuevo proyecto": menos de 10 s (SC-007).

## Licencias en el programa (Principio VI)

- **"Ayuda > Acerca de BIM Simple"** (texto exacto en [ui.md](ui.md)) indica que BIM Simple es
  software libre bajo GPL-3.0-or-later con el enlace a su código, que usa IfcOpenShell bajo
  LGPL-3.0, dónde está el código de IfcOpenShell y que los textos de las licencias están en
  `licencias\` (el de BIM Simple, en `licencias\bim-simple\GPL-3.0.txt`).
- IfcOpenShell se distribuye sin modificar, en su propia carpeta y reemplazable.
- Antes de **entregar el programa a otros**, el programa NO se distribuye sin:
  1. los textos de licencia de CGAL, OpenCASCADE, Boost y manifold, que vienen dentro de IfcOpenShell;
  2. la firma de código (research R9, riesgo 2);
  3. la prueba en una PC limpia (research R9, riesgo 1).
