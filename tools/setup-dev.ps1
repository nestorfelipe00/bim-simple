# Prepara el entorno de desarrollo de BIM Simple:
#   runtime\python   Python 3.14.7 embebible + IfcOpenShell 0.9.0 y dependencias (engine\requirements.txt)
#   app\node_modules Electron, Three.js y camera-controls (app\package.json)
#
# Uso:
#   powershell -ExecutionPolicy Bypass -File tools\setup-dev.ps1              (copia el Python del prototipo, %TEMP%\bsproto)
#   powershell -ExecutionPolicy Bypass -File tools\setup-dev.ps1 -Descargar   (descarga de python.org y PyPI; requiere permiso)
param([switch]$Descargar)

$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $PSScriptRoot
$Runtime = Join-Path $Repo "runtime\python"
$PythonExe = Join-Path $Runtime "python.exe"
$Prototipo = Join-Path $env:TEMP "bsproto\python"
$PythonZipUrl = "https://www.python.org/ftp/python/3.14.7/python-3.14.7-embed-amd64.zip"
$PythonSha256 = "d297e5ff019966817ad8502465176139f2d3d840fa4ed84b13bed399a6ab1f15"

function Ok($texto) { Write-Host "OK     $texto" }
function Falla($texto) { Write-Host "ERROR  $texto"; exit 1 }

# ---------- runtime\python ----------
if (Test-Path $PythonExe) {
    Ok "runtime\python ya existe (no se toca)"
} elseif ($Descargar) {
    $zip = Join-Path $env:TEMP "python-3.14.7-embed-amd64.zip"
    Invoke-WebRequest -UseBasicParsing $PythonZipUrl -OutFile $zip
    $hash = (Get-FileHash $zip -Algorithm SHA256).Hash.ToLower()
    if ($hash -ne $PythonSha256) { Falla "SHA-256 del Python descargado no coincide ($hash)" }
    Ok "Python 3.14.7 descargado, SHA-256 verificado"
    Expand-Archive $zip -DestinationPath $Runtime
    python -m pip install --disable-pip-version-check --only-binary=:all: --target (Join-Path $Runtime "Lib\site-packages") -r (Join-Path $Repo "engine\requirements.txt")
    if ($LASTEXITCODE -ne 0) { Falla "pip no pudo instalar engine\requirements.txt" }
    Ok "dependencias de engine\requirements.txt instaladas"
} else {
    if (-not (Test-Path (Join-Path $Prototipo "python.exe"))) { Falla "no está el Python del prototipo en $Prototipo (usar -Descargar, con permiso)" }
    $version = & (Join-Path $Prototipo "python.exe") -c "import sys, ifcopenshell; print(sys.version.split()[0], ifcopenshell.version)"
    if ($version -ne "3.14.7 0.9.0") { Falla "el Python del prototipo no es 3.14.7 con IfcOpenShell 0.9.0 ($version)" }
    New-Item -ItemType Directory -Force (Split-Path $Runtime) | Out-Null
    Copy-Item $Prototipo $Runtime -Recurse
    Ok "runtime\python copiado del prototipo (Python 3.14.7, IfcOpenShell 0.9.0)"
}

# El Python embebido ignora PYTHONPATH y la carpeta actual: el motor se encuentra por el ._pth.
#   ..\..\engine  en desarrollo (runtime\python -> engine\ del repositorio)
#   ..\engine     en el programa instalado (resources\python -> resources\engine)
$pth = "python314.zip`r`n.`r`nLib\site-packages`r`n..\..\engine`r`n..\engine`r`n"
[IO.File]::WriteAllText((Join-Path $Runtime "python314._pth"), $pth, (New-Object Text.UTF8Encoding($false)))
Ok "python314._pth escrito (Lib\site-packages, ..\..\engine, ..\engine)"

# MSVCP140.dll: la necesitan las DLL de IfcOpenShell y no viene con Python (research R9, riesgo 1).
$msvcp = Join-Path $Runtime "msvcp140.dll"
if (-not (Test-Path $msvcp)) { Copy-Item (Join-Path $env:WINDIR "System32\msvcp140.dll") $msvcp }
Ok "msvcp140.dll junto a Python"

$versiones = & $PythonExe -c "import sys, ifcopenshell, numpy, shapely; print(sys.version.split()[0], ifcopenshell.version, numpy.__version__, shapely.__version__)"
if ($LASTEXITCODE -ne 0) { Falla "runtime\python no puede importar IfcOpenShell" }
Ok "runtime\python: Python, IfcOpenShell, numpy, shapely = $versiones"

# ---------- app\node_modules ----------
& npm --prefix (Join-Path $Repo "app") install --no-audit --no-fund
if ($LASTEXITCODE -ne 0) { Falla "npm install en app\ falló" }
Ok "npm install en app\"
& node (Join-Path $Repo "app\node_modules\electron\install.js")
if ($LASTEXITCODE -ne 0) { Falla "no se pudo preparar el ejecutable de Electron" }
if (-not (Test-Path (Join-Path $Repo "app\node_modules\electron\dist\electron.exe"))) { Falla "falta electron.exe" }
$electron = (Get-Content (Join-Path $Repo "app\node_modules\electron\package.json") -Raw | ConvertFrom-Json).version
$three = (Get-Content (Join-Path $Repo "app\node_modules\three\package.json") -Raw | ConvertFrom-Json).version
$cc = (Get-Content (Join-Path $Repo "app\node_modules\camera-controls\package.json") -Raw | ConvertFrom-Json).version
Ok "Electron $electron, Three.js $three, camera-controls $cc"
Write-Host "LISTO  entorno de desarrollo preparado"
