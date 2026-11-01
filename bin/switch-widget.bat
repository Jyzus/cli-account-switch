@echo off
REM CLI Account Switch · Windows Desktop Widget Launcher
setlocal
set "SCRIPT_DIR=%~dp0"
if exist "%SCRIPT_DIR%switch-widget" (
    python "%SCRIPT_DIR%switch-widget" %*
) else (
    echo Error: No se encontro switch-widget en %SCRIPT_DIR%
    exit /b 1
)
endlocal
