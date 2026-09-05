@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul

rem Resolve every path from this script, so build.bat can be launched anywhere.
set "BUILD_DIR=%~dp0"
for %%I in ("%BUILD_DIR%..") do set "PROJECT_ROOT=%%~fI"
set "FILE_LIST=%BUILD_DIR%filelist.txt"
set "RELEASE_DIR=%BUILD_DIR%release"

if not exist "%FILE_LIST%" (
    echo [ERROR] File list not found: "%FILE_LIST%"
    exit /b 1
)

if not exist "%RELEASE_DIR%" (
    mkdir "%RELEASE_DIR%"
    if errorlevel 1 (
        echo [ERROR] Cannot create release directory: "%RELEASE_DIR%"
        exit /b 1
    )
)

set /a COPIED_COUNT=0
set /a FAILED_COUNT=0

echo Project root : "%PROJECT_ROOT%"
echo File list    : "%FILE_LIST%"
echo Release dir  : "%RELEASE_DIR%"
echo.

for /f "usebackq delims=" %%F in ("%FILE_LIST%") do call :COPY_FILE "%%F"

echo.
echo Copied: %COPIED_COUNT%
echo Failed: %FAILED_COUNT%

if not "%FAILED_COUNT%"=="0" (
    echo [ERROR] Release build finished with errors.
    exit /b 1
)

echo [OK] Release files are up to date.
exit /b 0

:COPY_FILE
set "RELATIVE_PATH=%~1"
if not defined RELATIVE_PATH exit /b 0
if "%RELATIVE_PATH:~0,1%"=="#" exit /b 0

set "SOURCE_PATH=%PROJECT_ROOT%\%RELATIVE_PATH%"
set "DESTINATION_PATH=%RELEASE_DIR%\%RELATIVE_PATH%"

if not exist "%SOURCE_PATH%" (
    echo [MISSING] %RELATIVE_PATH%
    set /a FAILED_COUNT+=1
    exit /b 0
)

for %%D in ("%DESTINATION_PATH%") do set "DESTINATION_PARENT=%%~dpD"
if not exist "%DESTINATION_PARENT%" (
    mkdir "%DESTINATION_PARENT%"
    if errorlevel 1 (
        echo [MKDIR FAILED] %RELATIVE_PATH%
        set /a FAILED_COUNT+=1
        exit /b 0
    )
)

copy /y /b "%SOURCE_PATH%" "%DESTINATION_PATH%" >nul
if errorlevel 1 (
    echo [COPY FAILED] %RELATIVE_PATH%
    set /a FAILED_COUNT+=1
) else (
    echo [COPIED] %RELATIVE_PATH%
    set /a COPIED_COUNT+=1
)
exit /b 0
