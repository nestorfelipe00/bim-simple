# Contrato: el programa BIM Simple (instalación, arranque y armado)

Fuente: research R1–R6, R17. Lo que este contrato fija lo comprueban `tools/armar_programa.ps1` (al armar)
y `tests/test_pisos.py` (sección "Entorno").

## Carpeta instalada

`%LOCALAPPDATA%\Programs\BIM Simple\` (ruta base de 90 caracteres o menos, escribible, sin administrador):

```text
BIM Simple\
├── bim_simple.ico
├── LEEME.txt                      qué es, cómo abrir, cómo desinstalar
├── licencias\                     GPL-3.0 + avisos de Blender, Bonsai e IfcOpenShell
└── blender\                       copia de Blender 5.2.0 sin blender.pdb (no se modifica)
    └── portable\
        ├── config\userpref.blend
        ├── temp\                  (quit.blend, BIM Simple.blend de sesión, recuperacion\)
        ├── extensions\user_default\bonsai\
        ├── extensions\user_default\bim_simple\
        ├── extensions\.local\lib\python3.13\site-packages\
        └── scripts\startup\bl_app_templates_user\bim_simple\{__init__.py, userpref.blend, startup.blend}
```

## Arranque

- Acceso directo `BIM Simple.lnk` (Escritorio y menú Inicio):
  - destino `…\blender\blender-launcher.exe`;
  - argumentos `--app-template bim_simple`;
  - carpeta de trabajo `…\blender`;
  - icono `…\bim_simple.ico,0`;
  - descripción "BIM Simple: modelado BIM sobre IFC".
- Condiciones que deben cumplirse al arrancar:
  - sin consola;
  - sin pantalla de bienvenida;
  - interfaz en español;
  - Bonsai y BIM Simple activos;
  - Bonsai sin espacio "BIM";
  - escena sin objetos;
  - pantalla de BIM Simple armada (ver [ui.md](ui.md)).

## Preferencias fijas

Tabla completa en research R5. La prueba automática comprueba:

| Preferencia | Valor |
|---|---|
| `bpy.utils.resource_path('USER')` | termina en `portable` |
| `preferences.app_template` | `bim_simple` |
| `view.language` | `es` |
| `view.show_splash` | `False` |
| `use_preferences_save` | `False` |
| `filepaths.temporary_directory` | `…\portable\temp\` |
| `apps.show_regions_visibility_toggle`, `apps.show_corner_split` | `False` |
| Add-ons activos | incluyen `bl_ext.user_default.bonsai` y `bl_ext.user_default.bim_simple` |
| Preferencias de Bonsai `should_setup_workspace`, `activate_workspace`, `should_setup_toolbar` | `False` |

## Script de armado `tools/armar_programa.ps1`

| Parámetro | Por defecto | Qué hace |
|---|---|---|
| `-Destino` | `%LOCALAPPDATA%\Programs\BIM Simple` | Carpeta del programa. |
| `-BonsaiZip` | (obligatorio en el primer armado) | Zip `bonsai_py313-0.9.0-windows-x64.zip`. Se compara su SHA-256 con el publicado. |
| `-SoloExtension` | apagado | Reinstala solo la extensión y la plantilla, corre la prueba y el control SC-005. |
| `-CrearAccesos` | apagado | Crea los dos `BIM Simple.lnk`. Nunca se crean sin este parámetro. |

**Salida**:
- una línea `OK …` o `ERROR …` por paso;
- la salida real de la prueba automática;
- el resultado del control SC-005 ("Blender del usuario sin cambios" o la lista de archivos que cambiaron).

**Código de salida**: 0 si todo pasa y 1 si falla cualquier paso o la prueba.

**Nunca**:
- escribe en `C:\Program Files\Blender Foundation\Blender 5.2`;
- escribe en `%APPDATA%\Blender Foundation\Blender\5.2`;
- descarga nada: el zip lo descarga el usuario o el asistente con permiso, antes de llamar al script.

## Desinstalar (FR-005)

Borrar `%LOCALAPPDATA%\Programs\BIM Simple\` y los dos `BIM Simple.lnk`. Así se explica en `LEEME.txt`.
Lo único que queda fuera es la caché compartida de Blender (`%LOCALAPPDATA%\Blender Foundation\Blender\Cache`),
diferencia D7.
