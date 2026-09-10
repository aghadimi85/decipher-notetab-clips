@echo off
setlocal
cd /d "%~dp0"

echo Checking for Python 3.11...
py -3.11 --version >nul 2>&1
if %errorlevel%==0 (
    py -3.11 "%~dp0convert_decipher_clb_py3.py"
    goto done
)

echo Python 3.11 via "py" was not found. Trying "python"...
python --version >nul 2>&1
if %errorlevel%==0 (
    python "%~dp0convert_decipher_clb_py3.py"
    goto done
)

echo.
echo Python was not found on this computer.
echo Send a screenshot of this window to ChatGPT.
echo.

:done
echo.
pause
