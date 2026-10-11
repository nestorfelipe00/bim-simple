# Empaquetado de BIM Simple: instalador de Windows por usuario y sin administrador

**Fecha de la consulta**: 2026-10-11 · **Solo lectura**: no se instaló nada en el proyecto ni se ejecutó código de
terceros. Para revisar las licencias se resolvió el árbol de dependencias en una carpeta aparte
(`npm install --package-lock-only --ignore-scripts`): eso solo genera el `package-lock.json`, sin descargar los
paquetes ni ejecutar sus scripts. Los tamaños se estimaron con un script propio en Node (zlib integrado) sobre la
carpeta del prototipo (`%TEMP%\bsproto`).

**Marcas**: 📖 documentación oficial (con URL) · 📄 registro npm o código fuente (con URL o ruta) · ⚠️ no verificado o
estimado.

> **Ojo con la documentación**: la raíz de https://www.electron.build ya muestra la **v27 (todavía alfa)**. La
> documentación de la versión estable está en **https://www.electron.build/v26/docs/** 📖. Todo lo de abajo usa la v26.

---

## 1. electron-builder: versión, licencia y dependencias

| Dato | Valor | Fuente |
|---|---|---|
| Etiqueta `latest` en npm | **26.15.3** (2026-06-09). Es una etiqueta **atrasada**: no apunta a la última estable | 📄 https://registry.npmjs.org/electron-builder (`dist-tags`) |
| Etiqueta `v26` en npm | **26.17.0** (2026-09-26T09:53Z) | 📄 mismo registro |
| Última estable en GitHub ("Latest release") | **26.17.0** (2026-09-26) | 📄 https://github.com/electron-userland/electron-builder/releases/tag/electron-builder%4026.17.0 |
| Versión estable publicada hace más de dos semanas | **26.17.0** (15 días al 2026-10-11). Más margen: **26.16.1** (2026-09-07, 34 días) | 📄 registro, campo `time` |
| Versiones en prueba | `next` = 27.0.0-alpha.10 (2026-10-08), que pide Node ≥ 22.12. **No usar** | 📄 registro |
| Ninguna de las versiones 26.15.3 a 26.17.0 está marcada como `deprecated` | — | 📄 registro |
| Licencia | **MIT** | 📄 registro (`license`) |
| Node requerido | `>=14.0.0` (sirve Node 24.19) | 📄 registro (`engines`) |

**Riesgo importante con `npm install -D electron-builder` sin versión**: instala la 26.15.3 (etiqueta `latest`).
Esa versión está dentro del problema #9983: el instalador NSIS podía terminar "bien" pero sin el `.exe` principal ni las
DLL. La reproducción principal fue en arm64; en x64 hubo un informe de que funcionaba. Lo corrigió la **26.15.6**
("fix(nsis): reliably install the main executable and native binaries on x64 and arm64"). 📄
https://github.com/electron-userland/electron-builder/issues/9983 y las notas de la 26.15.6.
→ **Fijar la versión exacta: `"electron-builder": "26.17.0"`.**

**Licencias del árbol de dependencias** (electron-builder 26.17.0, 276 paquetes, incluidas las dependencias "peer" que
npm agrega solo) 📄 (lockfile resuelto desde el registro):

| Licencia | Paquetes |
|---|---|
| MIT | 207 |
| ISC | 35 |
| BSD-3-Clause | 9 |
| BlueOak-1.0.0 | 8 (tar, minimatch, minipass, chownr, isexe, sax, yallist) |
| Apache-2.0 | 6 |
| BSD-2-Clause | 5 |
| Python-2.0 (argparse), 0BSD (tslib), WTFPL / WTFPL o ISC / WTFPL o MIT (sanitize-filename y dos más), MIT o CC0 (type-fest) | 1 c/u |

**No hay GPL, LGPL ni AGPL.** Todas son permisivas. Además son herramientas de armado: **no viajan dentro del
programa**.

Lo que sí termina dentro del instalador: el "stub" de NSIS (licencia zlib/libpng) y sus complementos (UAC, StdUtils,
nsProcess, WinShell, SpiderBanner y **Nsis7z**). Nsis7z está basado en 7-Zip, que es LGPL en parte. Solo lo usa el
instalador mientras descomprime; no queda instalado con BIM Simple. ⚠️ No revisé el texto de licencia de cada
complemento. Conviene que lo confirme alguien de licencias si el criterio de "nada LGPL dentro del producto" incluye al
instalador.

Al armar por primera vez, electron-builder **descarga de GitHub** (con suma de control) las herramientas: NSIS 3.0.4.1
y nsis-resources 3.4.1 (las de siempre en la v26), 7-Zip y el zip de Electron (o lo toma de la caché). Las guarda en
`%LOCALAPPDATA%\electron-builder\Cache`. 📄
https://github.com/electron-userland/electron-builder/blob/electron-builder%4026.17.0/packages/app-builder-lib/src/toolsets/windows.ts
· 📖 https://www.electron.build/v26/docs/troubleshooting ("downloads build toolsets ... the first time they are needed,
then caches").

### Alternativa: Electron Forge (Squirrel, WiX o NSIS)

| | electron-builder + NSIS (recomendado) | Electron Forge + Squirrel.Windows |
|---|---|---|
| Versión / licencia | 26.17.0 / MIT 📄 | `@electron-forge/cli` 8.0.1 (2026-09-29, **menos de 2 semanas**) / MIT 📄 |
| Por usuario y sin administrador | Sí, con `oneClick` + `perMachine: false` 📖 | Sí, siempre ("no-prompt, no-hassle, no-admin") 📖 https://www.electronforge.io/config/makers/squirrel.windows |
| Elegir carpeta, licencia (EULA), asistente | Sí (asistente o licencia en un clic) 📖 | No ⚠️ |
| Nombre con espacio ("BIM Simple") | Sin problema | La documentación de Forge avisa: "can behave unexpectedly when application names contain spaces" 📖 |
| Eventos de instalación | No hace falta nada | Hay que atenderlos (`electron-squirrel-startup`) o el programa se abre varias veces 📖 |
| Estado | Objetivo por defecto de electron-builder | electron-builder dice de Squirrel: "maintained, but deprecated. Please use nsis instead" 📖 https://www.electron.build/v26/docs/squirrel-windows |
| NSIS en Forge | No hay maker NSIS oficial de Forge 📖 https://www.electronforge.io/llms.txt. electron-builder publica `electron-forge-maker-nsis`, pero avisa que publicación, actualización automática y firma "are only available when using electron-builder as your primary build tool" 📖 https://www.electron.build/v26/docs/features/electron-forge | — |
| MSI (WiX) | — | Hay que instalar **WiX Toolset v3** 📖 https://www.electronforge.io/config/makers/wix-msi |

**Conclusión**: electron-builder con NSIS. Hace lo pedido (por usuario, sin administrador, desinstalador y accesos
directos), no pide herramientas extra y no tiene el problema del espacio en el nombre.

---

## 2. NSIS por usuario sin administrador: opciones exactas

Opciones según la documentación de la v26 📖 https://www.electron.build/v26/docs/nsis (todas van en `build.nsis`).
Las citas son textuales:

| Opción | Qué hace (documentación) | Por defecto | Valor para BIM Simple |
|---|---|---|---|
| `oneClick` | "Whether to create one-click installer or assisted." | `true` | **`true`** |
| `perMachine` | "If oneClick is true (default): Whether to install per all users (per-machine)." · "If oneClick is false and perMachine is false (default): install mode installer page." | `false` | **`false`** |
| `allowElevation` | "assisted installer only. Allow requesting for elevation." | `true` | No aplica con `oneClick: true`. En modo asistente: `false` |
| `allowToChangeInstallationDirectory` | "assisted installer only. Whether to allow user to change installation directory." | `false` | **No ponerlo** con `oneClick: true`: el armado falla con "allowToChangeInstallationDirectory makes sense only for assisted installer" 📄 `NsisTarget.ts` |
| `createDesktopShortcut` | "Whether to create desktop shortcut. Set to always if to recreate also on reinstall" | `true` | `true` |
| `createStartMenuShortcut` | "Whether to create start menu shortcut." | `true` | `true` |
| `shortcutName` | "The name that will be used for all shortcuts. Defaults to the application name." | productName | `"BIM Simple"` |
| `installerIcon` | "The path to installer icon ... Defaults to build/installerIcon.ico or application icon." | icono del programa | `"build/icon.ico"` |
| `uninstallerIcon` | "Defaults to build/uninstallerIcon.ico or application icon." | icono del programa | `"build/icon.ico"` |
| `uninstallDisplayName` | "The uninstaller display name in the control panel." | `${productName} ${version}` | dejar el valor por defecto |
| `artifactName` | "Defaults to ${productName} Setup ${version}.${ext}." | `BIM Simple Setup 0.1.0.exe` | `"BIM-Simple-Setup-${version}.${ext}"` (sin espacios, mejor para descargar) |
| `license` | "The path to EULA license file. Defaults to license.txt or eula.txt ... txt, rtf and html supported" | — | `"build/licencia.txt"`. En un clic también se muestra: 📄 `oneClick.nsh` inserta `licensePage` |
| `runAfterFinish` | "Whether to run the installed application after finish." | `true` | `true` |
| `deleteAppDataOnUninstall` | "one-click installer only. Whether to delete app data on uninstall." | `false` | `false`, para no perder la configuración del usuario |
| `menuCategory` | "Whether to create submenu for start menu shortcut and program files directory." | `false` | `false` |
| `packElevateHelper` | "Whether to pack the elevate executable (required for electron-updater if per-machine installer used ...)" | `true` | `false`: no hace falta por usuario 📄 `nsisUtil.ts` |
| `differentialPackage` | `false` = sin actualizaciones diferenciales; si no, 7z "no sólido" con diccionario de 1 MB | `true` | `false` mientras no haya actualización automática (ver §6) |
| `include` | "The path to NSIS include script ... Defaults to build/installer.nsh." | — | `"build/installer.nsh"` (ver abajo) |
| `guid` | "If not specified, a deterministic GUID is generated from the app ID (appId) — but this means changing your appId will break silent upgrades" | derivado de `appId` | no ponerlo |

**Por qué no pide administrador** 📄 https://github.com/electron-userland/electron-builder/blob/electron-builder%4026.17.0/packages/app-builder-lib/templates/nsis/installer.nsi:
si `perMachine` no es `true`, el instalador se compila con `RequestExecutionLevel user`. Por eso **no aparece la
ventana de UAC**.

**Dónde instala por defecto** 📄 `templates/nsis/multiUser.nsh` (macro `setInstallModePerUser`):

- Usa la carpeta conocida **`FOLDERID_UserProgramFiles`**. Su ruta por defecto es **`%LOCALAPPDATA%\Programs`** 📖
  https://learn.microsoft.com/en-us/windows/win32/shell/knownfolderid. A eso le agrega `\${APP_FILENAME}`.
- **Con `oneClick: true`**, `APP_FILENAME` es el **`name` del package.json** "sanitizado". Con `"name": "bim-simple"`
  instala en **`%LOCALAPPDATA%\Programs\bim-simple\`** 📄 `targetUtil.ts` (`getWindowsInstallationDirName`).
- Con el asistente (`oneClick: false`) usa el productName: `%LOCALAPPDATA%\Programs\BIM Simple\`.
- Si ya había una instalación, usa la ruta guardada en `HKCU\Software\<GUID>\InstallLocation`. Acepta `/D=ruta`.

**¿Aparece en "Agregar o quitar programas"? Sí.** 📄 `templates/nsis/include/installer.nsh` (macro `registryAddInstallInfo`):

- Escribe en `SHELL_CONTEXT\Software\Microsoft\Windows\CurrentVersion\Uninstall\<GUID>`: `DisplayName`,
  `UninstallString` (`"…\Uninstall BIM Simple.exe" /currentuser`), `QuietUninstallString`, `DisplayVersion`,
  `DisplayIcon`, `Publisher` (sale de `author.name`), `EstimatedSize` y otras.
- En modo por usuario `SHELL_CONTEXT` es **HKCU** 📖 https://nsis.sourceforge.io/Docs/Chapter4.html ("If root_key is
  SHCTX or SHELL_CONTEXT, it will be replaced with HKLM if SetShellVarContext all, HKCU otherwise").
- Aparece en Configuración > Aplicaciones **solo para ese usuario de Windows** ⚠️.
- El desinstalador `Uninstall BIM Simple.exe` queda en la carpeta de instalación. Borra la carpeta, los accesos directos
  y las claves de registro. Los datos de `%APPDATA%` quedan, salvo con `deleteAppDataOnUninstall` 📄 `uninstaller.nsh`.

**Hallazgo: copia del instalador que queda huérfana** 📄 `include/installer.nsh` línea 93 y `NsisTarget.ts` línea 615:

- En cada instalación, el instalador **se copia a sí mismo** en
  `%LOCALAPPDATA%\bim-simple-updater\installer.exe`. Es para las actualizaciones diferenciales de electron-updater.
- Con un instalador de ~180 MB, son **~180 MB extra** en el disco del usuario.
- **El desinstalador no la borra**: `uninstaller.nsh` no la menciona.
- Mientras no haya actualización automática, se puede borrar con `build/installer.nsh` ⚠️ (no probado):

```nsis
; build/installer.nsh — BIM Simple no usa actualización automática (todavía).
!macro customInstall
  RMDir /r "$LOCALAPPDATA\bim-simple-updater"
!macroend
!macro customUnInstall
  RMDir /r "$LOCALAPPDATA\bim-simple-updater"
!macroend
```

Las macros `customInstall` y `customUnInstall` están documentadas 📖 https://www.electron.build/v26/docs/nsis#custom-nsis-script.
`customInstall` corre **después** de copiar los archivos 📄 `installSection.nsh`.

**Variante con asistente (para elegir carpeta) sin administrador** ⚠️ no probada:

```jsonc
"nsis": { "oneClick": false, "perMachine": false, "allowElevation": false, "allowToChangeInstallationDirectory": true }
```

Hay que agregar la macro `customInstallMode` en `build/installer.nsh`, porque si no aparece la página "¿para todos los
usuarios o solo para mí?":

```nsis
!macro customInstallMode
  StrCpy $isForceCurrentInstall "1"
!macroend
```

- `$isForceCurrentInstall` está documentado 📖 https://www.electron.build/v26/docs/nsis#custom-nsis-script.
- Con ese valor en "1", la plantilla salta la página y usa el modo por usuario 📄 `multiUserUi.nsh` líneas 39–64.
- Riesgo ⚠️: si el usuario elige una carpeta sin permiso de escritura (por ejemplo `C:\Program Files`), la instalación
  falla.
- Para un arquitecto, el instalador de un clic es lo más simple.

---

## 3. Python y el motor fuera del archivo asar

**Por qué no pueden ir dentro del asar**: Electron dice que de las funciones que ejecutan programas, "only execFile is
supported to execute binaries inside ASAR archive" 📖 https://www.electronjs.org/docs/latest/tutorial/asar-archives.
Además, Python no puede leer `motor.py` desde dentro de un `.asar`: el formato es de Electron y Python no lo conoce.

**`extraResources` (lo recomendado)** 📖 https://www.electron.build/v26/docs/contents:

- "extraResources — Copies into the resources/ directory" (en Windows: `resources/`).
- "Use extraResources for native binaries, CLI tools, or data files that need to be accessible at runtime. Access them
  in your app via process.resourcesPath."
- `from` es relativo a la carpeta del proyecto y `to`, a la carpeta `resources` 📖 (tabla FileSet).

**`asarUnpack` no conviene acá**: saca archivos del asar a `app.asar.unpacked/`, pero esos archivos siguen pasando por
la lógica de `files`. Las exclusiones por defecto de `files` incluyen `*.pyc`, `__pycache__`, `*.a`, `*.o`, `*.obj`,
`*.pdb` y otras 📄 `fileMatcher.ts` (`excludedExts`, `excludedNames`). Eso podría romper partes de Python.

**`extraResources` no aplica esas exclusiones**: copia todo lo que diga el filtro 📄 `fileMatcher.ts`
(`getFileMatchers`; las exclusiones solo se agregan en `getMainFileMatchers`). Por eso la carpeta de IfcOpenShell queda
**idéntica**, que es lo que pide la LGPL ("carpeta separada sin modificar").

**Importante**: si `recursos/` está dentro de la carpeta del programa, hay que **excluirla de `files`**. Si no, los
~640 MB entrarían **también** al asar. `files` toma por defecto `**/*` 📖 /v26/docs/contents. Las carpetas `build/` y
`dist/` se excluyen solas 📄 `getMainFileMatchers`.

Disposición propuesta del proyecto:

```
proyecto/
├── package.json, main.js, preload.js, index.html, …   → van al app.asar
├── build/icon.ico, build/licencia.txt, build/installer.nsh
└── recursos/
    ├── python/      (Python 3.14.7 embebible + Lib/site-packages con IfcOpenShell sin modificar)
    ├── motor/       (motor.py, …)
    └── licencias/   (LGPL-3.0 de IfcOpenShell, PSF de Python, avisos de terceros)
```

Instalado queda así: `%LOCALAPPDATA%\Programs\bim-simple\resources\python\python.exe`, `…\resources\motor\motor.py` y
`…\resources\app.asar`.

**Cómo encontrar Python en tiempo de ejecución**:

- `process.resourcesPath`: "A string representing the path to the resources directory." 📖
  https://www.electronjs.org/docs/latest/api/process#processresourcespath
- `app.isPackaged`: "returns true if the app is packaged" 📖 https://www.electronjs.org/docs/latest/api/app#appispackaged-readonly
- Mientras se desarrolla (`electron .`), `process.resourcesPath` apunta a los recursos del Electron de `node_modules`.
  Por eso hace falta la bifurcación ⚠️:

```js
const RECURSOS = app.isPackaged ? process.resourcesPath : path.join(__dirname, "recursos");
const PYTHON = path.join(RECURSOS, "python", "python.exe");
const MOTOR = path.join(RECURSOS, "motor", "motor.py");
motor = spawn(PYTHON, ["-u", MOTOR], { windowsHide: true, stdio: ["pipe", "pipe", "pipe"] });
// Registros: no escribirlos en la carpeta de instalación (hoy el prototipo usa BASE\salida).
const SALIDA = app.getPath("logs");
```

Notas:

- Python escribe `__pycache__` junto a los `.py` la primera vez. La carpeta por usuario se puede escribir, así que no
  falla, y el desinstalador la borra entera (`RMDir /r $INSTDIR`) 📄.
- Conviene **no empaquetar** los `__pycache__` del armado (filtro `!**/__pycache__/**`). En el prototipo hay 129.
- Ruta más larga dentro de `python\`: 120 caracteres. Sumando `C:\Users\Usuario\AppData\Local\Programs\bim-simple\resources\`
  (61) da ~181, por debajo de 260. Hay margen para nombres de usuario más largos ⚠️.

---

## 4. appId, AppUserModelID e icono

**Tienen que ser la misma cadena**:

1. `build.appId` 📖 https://www.electron.build/v26/docs/configuration: "Used as ... Application User Model ID for
   Windows (NSIS target only ...). It is strongly recommended that an explicit ID is set." Por defecto vale
   `com.electron.${name}`.
2. El instalador graba ese `appId` en los accesos directos: `WinShell::SetLnkAUMI "$newStartMenuLink" "${APP_ID}"` 📄
   `include/installer.nsh` líneas 200–240. Al desinstalar lo borra (`WinShell::UninstAppUserModelId`) 📄.
3. El programa tiene que declarar el mismo valor con `app.setAppUserModelId(id)`. Electron: "Changes the Application
   User Model ID to id." 📖 https://www.electronjs.org/docs/latest/api/app#appsetappusermodelidid-windows. Según la
   página de NSIS: "The AUMID should be set within the Main process and before any BrowserWindows have been opened" 📖
   /v26/docs/nsis#guid-vs-application-name.
4. Microsoft: "If an application uses an explicit AppUserModelID, it must also assign the same AppUserModelID to all
   running windows or processes, shortcuts, and file associations." 📖
   https://learn.microsoft.com/en-us/windows/win32/shell/appids
   - Formato: `CompanyName.ProductName`, como máximo 128 caracteres y **sin espacios**.
   - Sin número de versión, para que la versión nueva comparta el ID.
5. Si no coinciden, pueden aparecer dos botones en la barra de tareas o un anclado que no corresponde al acceso del
   menú Inicio ⚠️ (comportamiento general; no lo reproduje).

**Hoy el prototipo usa `"BIMSimple.Prototipo"`**. Hay que elegir el ID definitivo **antes de la primera versión que
llegue a usuarios** y **no cambiarlo más**:

- El GUID del desinstalador se calcula a partir del `appId` (UUID v5) 📄 `NsisTarget.ts` línea 221.
- Cambiarlo rompe las actualizaciones encima de la instalación anterior 📖 (`guid`).

Propuesta: `"BIMSimple.BIMSimple"` o `"com.<empresa>.bimsimple"`; los dos cumplen el formato. Una constante única en
`main.js` (`const APP_ID = "…"`) y el mismo texto en `build.appId`.

**Icono `.ico`**:

| Tamaño | Fuente |
|---|---|
| Mínimo para electron-builder: 256×256. Recomendado: 512×512 o SVG (convierte solo) | 📖 https://www.electron.build/v26/docs/features/icons-and-images |
| Microsoft: "Apps should have, at the bare minimum: 16x16, 24x24, 32x32, 48x48, and 256x256" | 📖 https://learn.microsoft.com/en-us/windows/apps/design/iconography/app-icon-construction |
| Barra de tareas según la escala: 24 / 30 / 36 / 48 px (100 %–200 %). Título y bandeja: 16 / 20 / 24 / 32 px | 📖 misma página |

**Recomendación**: un `build/icon.ico` hecho a mano con **16, 20, 24, 32, 40, 48, 64, 96 y 256** px.

- Si existe un `.ico`, electron-builder lo usa sin convertir: "pre-built Windows icon (skips conversion)" 📖.
- Por defecto `win.icon` es `build/icon.ico` 📖 /v26/docs/win. El instalador y el desinstalador toman ese mismo icono.
- electron-builder lo pone dentro de `BIM Simple.exe` (con resedit, en JavaScript) 📄 `winPackager.ts` / `util/resEdit.ts`.
- La ventana puede seguir usando `icon:` en `BrowserWindow`.

---

## 5. Firma de código (solo como información)

**Sin firmar** 📖 https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation:

- Aparece "Windows protected your PC" (en español, "Windows protegió su PC"). El usuario tiene que entrar en "Más
  información" y elegir **"Ejecutar de todas formas"**: "User must choose 'Run anyway' before the app can run.
  Enterprise policy can prevent continuation entirely."
- "When a file is not signed, SmartScreen reputation must build for each new version of your files, starting with zero
  reputation." Cada versión nueva vuelve a mostrar el aviso.
- **Smart App Control** (Windows 11): "will block execution of unsigned files unless the file has a positive
  reputation ... signature checks apply to all executable files, not just those downloaded from the Internet."
  **Riesgo real**, comprobado leyendo las firmas del prototipo (`Get-AuthenticodeSignature`, solo lectura):
  `electron.exe` (será `BIM Simple.exe`), `ffmpeg.dll`, las `.pyd` de IfcOpenShell y las de numpy **no están
  firmadas**. `python.exe` y `python314.dll` sí: "Python Software Foundation". En una PC con Smart App Control
  activado, el programa podría no abrir ⚠️ (no probado).

**Opciones y costo aproximado** 📖 https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options
(actualizada 2026-08-29):

| Opción | Costo | Disponibilidad | SmartScreen |
|---|---|---|---|
| Azure **Artifact Signing** (antes Trusted Signing) | ~US$ 9,99/mes | Organizaciones: EE. UU., Canadá, UE y Reino Unido. **Personas: solo EE. UU. y Canadá** | La reputación se construye con el tiempo |
| Certificado **OV** (DigiCert, Sectigo, etc.) | US$ 150–300/año | Todo el mundo. Desde junio de 2023 la clave tiene que estar en un HSM o token físico | Igual: la reputación se construye y se hereda entre versiones firmadas con el mismo certificado |
| Certificado **EV** | US$ 400+/año | Todo el mundo | **Desde 2024 ya no evita el aviso**: "Same as OV since 2024" |
| Microsoft Store (MSIX) | Gratis | Todo el mundo | Sin avisos (otro tipo de paquete, no NSIS) |

- La documentación de electron-builder todavía dice que EV da "Instant trust". **Está desactualizada**; vale lo de
  Microsoft.
- Para firmar, electron-builder usa `WIN_CSC_LINK` / `WIN_CSC_KEY_PASSWORD` o `win.azureSignOptions` 📖
  https://www.electron.build/v26/docs/features/code-signing/code-signing-win.
- **Sin certificado no descarga nada para firmar**: registra "no code signing certificate configured, signing is
  skipped" 📄 `codeSign/windowsSignToolManager.ts`.
- Cuando se firme, puede aparecer en Windows el error conocido de enlaces simbólicos al descomprimir `winCodeSign`
  ("Cannot create symbolic link"). Se resuelve activando el Modo de desarrollador ⚠️
  https://github.com/electron-userland/electron-builder/issues/8149.

---

## 6. Tamaño del instalador y tiempo de instalación

**Cómo comprime electron-builder** 📄 `targets/archive.ts` y `differentialUpdateInfoBuilder.ts`:

- El programa va en un **7z (LZMA) con `-mx=9`** y el filtro BCJ (el único que entiende el extractor Nsis7z).
- Con `differentialPackage: true` (por defecto): 7z **no sólido** y **diccionario de 1 MB**, pensado para
  actualizaciones diferenciales. Comprime algo peor.
- Con `differentialPackage: false`: 7z sólido con el diccionario normal de `-mx=9`. Instalador más chico; cada
  actualización futura se descargaría entera.
- `compression: "maximum"` no cambia nada para 7z (ya usa `-mx=9`).
- La documentación de `win` lo confirma: "maximum doesn't lead to noticeable size difference, but increase build
  time" 📖 /v26/docs/win.
- Los archivos de `preCompressedFileExtensions` (videos) se guardan sin comprimir 📖.

**Medición sobre el prototipo** (script propio con zlib de Node, archivo por archivo; Node no trae LZMA) ⚠️ estimación:

| Parte | En disco | Brotli-9 | Deflate-9 |
|---|---|---|---|
| Electron 44.4.5 (`dist`) | 367 MB | 124 MB (34 %) | 154 MB (42 %) |
| Python + IfcOpenShell + numpy + shapely | 261 MB | 75 MB (29 %) | 88 MB (34 %) |
| **Total** | **628 MB** | **199 MB** | **242 MB** |

- LZMA con BCJ suele comprimir un 5–15 % mejor que Brotli-9 en ejecutables. **Instalador esperado: ~170–190 MB** ⚠️.
- Se puede bajar más:
  - `electronLanguages: ["es", "es-419", "en-US"]` deja 3 de las 55 traducciones de Chromium (49 MB en disco) 📖
    /v26/docs/win.
  - Sacar `pytest`, `pygments` y otros paquetes que pide la validación completa, si no hacen falta en el producto.
  - Empaquetar Three.js en el renderer y pasar `three` y `camera-controls` a `devDependencies`, para que no viajen
    23 MB de `node_modules` dentro del asar.
- NSIS tiene un límite de ~2 GB por instalador, muy lejos de esto ⚠️.

**Espacio en el disco del usuario**: ~640 MB del programa **más ~180 MB** de la copia `installer.exe` en
`%LOCALAPPDATA%\bim-simple-updater` (§2) si no se borra con `installer.nsh`.

**Tiempo de instalación**: **no hay datos oficiales**. Estimación ⚠️: 20–60 s en SSD para ~4.200 archivos y ~640 MB.
El tiempo lo dominan la descompresión LZMA y el análisis de Windows Defender archivo por archivo. **Hay que medirlo**
con el primer instalador.

---

## 7. ¿Hace falta instalar algo más en la PC de armado?

| Herramienta | ¿Hace falta en Windows? | Fuente |
|---|---|---|
| Wine | **No.** Solo para armar instaladores de Windows desde Linux o macOS. En Windows el código lo rechaza: "Wine toolset is not supported on Windows" | 📖 https://www.electron.build/v26/docs/features/multi-platform-build · 📄 `toolsets/wine.ts` |
| Mono | **No** (solo Squirrel desde Linux o macOS: "NSIS doesn't require Mono") | 📖 misma página |
| Visual Studio, Python, node-gyp | **No**, porque no hay módulos nativos de Node (three y camera-controls son JS puro). Con `"npmRebuild": false` ni lo intenta | 📖 /v26/docs/configuration (`npmRebuild`, por defecto `true`) |
| Rust | **No.** Todo el árbol es JavaScript y las herramientas (NSIS, 7-Zip) vienen compiladas | 📄 lockfile y `toolsets/*.ts` |
| Internet en el primer armado | **Sí**: NSIS, 7-Zip y Electron se descargan de GitHub con suma de control y quedan en caché | 📄 `toolsets/windows.ts`, `toolsets/7zip.ts` |
| Administrador o Modo de desarrollador | **No, mientras no se firme.** Si se firma, puede hacer falta por los enlaces simbólicos de `winCodeSign` | ⚠️ issue #8149 |

**Confirmado**: en Windows 11 con Node 24.19 y npm 11.17, `npx electron-builder --win nsis --x64` debería funcionar
directo, sin instalar nada más que el paquete `electron-builder` 📄 (código revisado, no ejecutado).

Nota sobre npm 11: en el árbol, solo `electron-winstaller@5.4.0` (que llega como "peer" para Squirrel) tiene script de
instalación 📄 lockfile. Si npm lo bloquea, a NSIS no le afecta.

---

## 8. Riesgo encontrado de paso: el runtime de Visual C++ en una PC limpia

Leí la tabla de importaciones de las DLL (script propio, solo lectura):

- **`_ifcopenshell_wrapper.cp314-win_amd64.pyd`**, `ifcopenshell.parse.dll`, `ifcopenshell.geometry.dll`,
  `ifcopenshell.plugin.dll` y `boost_program_options-…dll` importan **`MSVCP140.dll`**.
- **Ni el Python embebible ni la rueda de IfcOpenShell la traen.**
  - El embebible trae `vcruntime140.dll` y `vcruntime140_1.dll`.
  - numpy y shapely traen sus propias copias renombradas (`msvcp140-<hash>.dll`), que IfcOpenShell no usa.
- En esta PC funciona porque existe `C:\Windows\System32\msvcp140.dll` (Visual C++ Redistributable ya instalado).
- **En un Windows recién instalado sin ese paquete, `import ifcopenshell` fallaría** ("DLL load failed") ⚠️, no
  probado en una PC limpia.

Opciones:

- **Instalar el Redistributable** ("central deployment") pone los archivos en `Windows\System32` y por lo tanto **pide
  administrador**. Choca con el objetivo.
- **Copiar `msvcp140.dll` junto a `python.exe`** ("local deployment") está admitido por Microsoft, pero no lo
  recomienda: "Because Microsoft can't automatically update locally deployed Microsoft C++ libraries, we don't recommend
  local deployment" 📖 https://learn.microsoft.com/en-us/cpp/windows/deployment-in-visual-cpp.
  - Si se copia en `python\` (no dentro de `ifcopenshell\`), IfcOpenShell sigue sin modificar.
  - ⚠️ Revisar las condiciones de redistribución de Microsoft para esa DLL.
- **Probar el instalador en Windows Sandbox** (viene con Windows 11 Pro) o en una máquina virtual limpia antes de
  vender.

---

## Configuración recomendada (`package.json`)

```jsonc
{
  "name": "bim-simple",
  "productName": "BIM Simple",
  "version": "0.1.0",
  "description": "Modelador BIM simple",
  "author": { "name": "<Empresa o autor>" },          // aparece como "Editor" en Agregar o quitar programas
  "main": "main.js",
  "devDependencies": {
    "electron": "44.4.5",
    "electron-builder": "26.17.0"                     // versión exacta: la etiqueta "latest" de npm es la 26.15.3
  },
  "scripts": { "instalador": "electron-builder --win nsis --x64" },
  "build": {
    "appId": "BIMSimple.BIMSimple",                   // = app.setAppUserModelId(...); no cambiarlo nunca
    "productName": "BIM Simple",
    "copyright": "Copyright © 2026 <Empresa>",
    "directories": { "output": "dist", "buildResources": "build" },
    "files": ["**/*", "!recursos/**"],
    "extraResources": [
      { "from": "recursos/python",    "to": "python",    "filter": ["**/*", "!**/__pycache__/**"] },
      { "from": "recursos/motor",     "to": "motor",     "filter": ["**/*", "!**/__pycache__/**"] },
      { "from": "recursos/licencias", "to": "licencias" }
    ],
    "asar": true,
    "npmRebuild": false,
    "electronLanguages": ["es", "es-419", "en-US"],
    "win": {
      "target": [{ "target": "nsis", "arch": ["x64"] }],
      "icon": "build/icon.ico"
    },
    "nsis": {
      "oneClick": true,
      "perMachine": false,
      "createDesktopShortcut": true,
      "createStartMenuShortcut": true,
      "shortcutName": "BIM Simple",
      "installerIcon": "build/icon.ico",
      "uninstallerIcon": "build/icon.ico",
      "license": "build/licencia.txt",
      "artifactName": "BIM-Simple-Setup-${version}.${ext}",
      "runAfterFinish": true,
      "deleteAppDataOnUninstall": false,
      "packElevateHelper": false,
      "differentialPackage": false,
      "include": "build/installer.nsh"
    }
  }
}
```

Resultado esperado: `dist\BIM-Simple-Setup-0.1.0.exe` (~170–190 MB ⚠️).

- Instala sin UAC en `%LOCALAPPDATA%\Programs\bim-simple\`.
- Crea accesos directos con AUMID = `appId`.
- Aparece en Agregar o quitar programas (HKCU) con su desinstalador.

## Riesgos, en orden

1. **`MSVCP140.dll` falta en una PC limpia** (§8): puede impedir que arranque el motor. Probar en Windows Sandbox.
2. **Sin firma**: aviso de SmartScreen en cada versión, y posible bloqueo con Smart App Control (§5).
3. **No usar `npm i electron-builder` sin versión**: instala la 26.15.3, afectada por el error de instaladores sin
   `.exe` (corregido en la 26.15.6).
4. **Copia de ~180 MB del instalador** en `%LOCALAPPDATA%\bim-simple-updater` que el desinstalador no borra (§2).
5. **`appId` definitivo** antes de la primera versión que llegue a usuarios (el GUID se calcula a partir de él).
6. **No olvidar excluir `recursos/` de `files`**: si no, los ~640 MB entran también al asar.
7. Tiempo de instalación y tamaño final: estimados, falta medirlos (§6).
