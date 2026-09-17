@echo off
setlocal
pushd "%~dp0"
if exist ".venv\Scripts\python.exe" goto deps
where py >nul 2>nul
if errorlevel 1 goto usepython
py -3 -m venv .venv
if errorlevel 1 goto fail
goto deps
:usepython
python -m venv .venv
if errorlevel 1 goto fail
:deps
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto fail
".venv\Scripts\python.exe" vnm_font.py --proof %*
set "rc=%errorlevel%"
popd
exit /b %rc%
:fail
echo Setup failed. Install Python 3.10 or newer and inspect the error above.
popd
exit /b 1
