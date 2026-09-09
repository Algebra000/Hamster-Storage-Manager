@echo off
chcp 65001 >nul
setlocal DisableDelayedExpansion
pushd "%~dp0"
if errorlevel 1 exit /b 1

rem Execute Python to detect a usable Python 3, not just a Windows Store alias.
set "PYTHON_EXE="
for /f "delims=" %%P in ('python -c "import sys; print(sys.executable) if sys.version_info.major == 3 else sys.exit(1)" 2^>nul') do set "PYTHON_EXE=%%P"
if defined PYTHON_EXE goto python_ready
for /f "delims=" %%P in ('py -3 -c "import sys; print(sys.executable)" 2^>nul') do set "PYTHON_EXE=%%P"
if defined PYTHON_EXE goto python_ready

echo 未检测到可用的 Python 3 环境。
choice /c YN /n /m "是否同意下载并安装 Python？[Y/N] "
if errorlevel 2 goto cancelled
if errorlevel 1 goto install_python
goto cancelled

:install_python
set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python312\python.exe"
set "PYTHON_INSTALL_DIR=%LocalAppData%\Programs\Python\Python312"
echo 正在从 python.org 下载并安装 Python，请稍候...
rem Install per-user, include pip and PATH, and wait for installation to finish.
powershell -NoProfile -Command "$ErrorActionPreference = 'Stop'; $installer = Join-Path ([IO.Path]::GetTempPath()) (([guid]::NewGuid().ToString()) + '.exe'); try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $arch = $env:PROCESSOR_ARCHITECTURE; if ($env:PROCESSOR_ARCHITEW6432) { $arch = $env:PROCESSOR_ARCHITEW6432 }; $suffix = ''; if ($arch -eq 'AMD64') { $suffix = '-amd64' } elseif ($arch -eq 'ARM64') { $suffix = '-arm64' }; Invoke-WebRequest -UseBasicParsing -Uri ('https://www.python.org/ftp/python/3.12.10/python-3.12.10' + $suffix + '.exe') -OutFile $installer; $sig = Get-AuthenticodeSignature -LiteralPath $installer; if ($sig.Status -ne 'Valid' -or $sig.SignerCertificate.Subject -notmatch 'Python Software Foundation') { throw 'Python installer signature verification failed.' }; $arguments = '/quiet InstallAllUsers=0 PrependPath=1 Include_pip=1 Include_test=0 /norestart TargetDir=' + [char]34 + $env:PYTHON_INSTALL_DIR + [char]34; $process = Start-Process -FilePath $installer -ArgumentList $arguments -Wait -PassThru -WindowStyle Hidden; if ($process.ExitCode -notin @(0, 3010)) { throw ('Python installer exit code: ' + $process.ExitCode) } } catch { Write-Host $_; exit 1 } finally { if (Test-Path -LiteralPath $installer) { Remove-Item -LiteralPath $installer -Force } }"
if errorlevel 1 goto failed

:python_ready
"%PYTHON_EXE%" -c "import sys; sys.exit(0 if sys.version_info.major == 3 else 1)" >nul 2>&1
if errorlevel 1 goto failed
rem Make this interpreter available to install.py and its child processes.
for %%P in ("%PYTHON_EXE%") do set "PATH=%%~dpP;%%~dpPScripts;%PATH%"
echo 正在运行安装向导...
"%PYTHON_EXE%" "%~dp0install.py"
if errorlevel 1 goto failed

powershell -NoProfile -Command "$ErrorActionPreference = 'Stop'; $WshShell = New-Object -ComObject WScript.Shell; $desktop = [System.Environment]::GetFolderPath('Desktop'); $lnk = $WshShell.CreateShortcut([System.IO.Path]::Combine($desktop, '仓鼠存储管理器.lnk')); $lnk.TargetPath = Join-Path (Get-Location).Path 'start.bat'; $lnk.IconLocation = Join-Path (Get-Location).Path 'icon.ico'; $lnk.WorkingDirectory = (Get-Location).Path; $lnk.Save()"
if errorlevel 1 goto failed
echo 快捷方式已创建在桌面：仓鼠存储管理器.lnk
popd
pause
exit /b 0

:cancelled
echo 已取消安装。
popd
exit /b 1

:failed
echo 安装失败，未完成快捷方式创建。请检查上方错误信息后重试。
popd
pause
exit /b 1
