@echo off
chcp 65001 >nul
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $desktop = [System.Environment]::GetFolderPath('Desktop'); $lnk = $WshShell.CreateShortcut([System.IO.Path]::Combine($desktop, '仓鼠存储管理器.lnk')); $lnk.TargetPath = '%~dp0start.bat'; $lnk.IconLocation = '%~dp0icon.ico'; $lnk.WorkingDirectory = '%~dp0'; $lnk.Save()"
echo 快捷方式已创建在桌面：仓鼠存储管理器.lnk
pause