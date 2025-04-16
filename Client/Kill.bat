@echo off
setlocal enabledelayedexpansion

echo Sending 'stop' to all terminal windows...

for /f "tokens=*" %%W in ('powershell -command "Get-Process cmd | Where-Object { $_.MainWindowTitle -ne '' } | Select-Object -ExpandProperty MainWindowTitle"') do (
    echo Trying to activate: %%W
    powershell -Command "$wshell = New-Object -ComObject wscript.shell; if ($wshell.AppActivate('%%W')) { Start-Sleep -Milliseconds 300; $wshell.SendKeys('stop'); Start-Sleep -Milliseconds 300; $wshell.SendKeys('{ENTER}'); }"
    timeout /t 1 > nul
)

echo Waiting before killing all terminals...
timeout /t 2 > nul

echo Killing all terminal and python processes...

taskkill /IM python.exe /F > nul 2>&1

taskkill /IM cmd.exe /F > nul 2>&1

echo Done.
pause
