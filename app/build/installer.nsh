; Agregado al instalador NSIS de electron-builder (nsis.include en package.json).
; Al desinstalar (no al actualizar) borra la copia del instalador que queda en
; %LOCALAPPDATA%\bim-simple-updater (research R9, riesgo 3; SC-005).
!macro customUnInstall
  ${ifNot} ${isUpdated}
    RMDir /r "$LOCALAPPDATA\bim-simple-updater"
  ${endIf}
!macroend
