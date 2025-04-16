@echo off
setlocal enabledelayedexpansion

set /P num="Number of clients to run: "

echo Starting !num! instances of main.py...

FOR /L %%x IN (1,1,%num%) DO (
    echo Launching instance %%x...
    start "client%%x" cmd /k "python main.py"
)

echo All clients launched.
pause
