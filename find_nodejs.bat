@echo off
echo Searching for Node.js installation...

if exist "C:\Program Files\nodejs\node.exe" (
    echo Found Node.js at: C:\Program Files\nodejs\
    "C:\Program Files\nodejs\node.exe" --version
    goto :found
)

if exist "C:\Program Files (x86)\nodejs\node.exe" (
    echo Found Node.js at: C:\Program Files (x86)\nodejs\
    "C:\Program Files (x86)\nodejs\node.exe" --version
    goto :found
)

if exist "%USERPROFILE%\AppData\Roaming\npm\node.exe" (
    echo Found Node.js at: %USERPROFILE%\AppData\Roaming\npm\
    "%USERPROFILE%\AppData\Roaming\npm\node.exe" --version
    goto :found
)

echo Node.js not found. Please reinstall Node.js.
echo Download from: https://nodejs.org/
goto :end

:found
echo Node.js found! Adding to PATH...
set PATH=%PATH%;C:\Program Files\nodejs\;C:\Program Files (x86)\nodejs\
echo Testing node command...
node --version
npm --version

:end
pause