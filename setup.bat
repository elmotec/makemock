@rem activate venv
call %~dp0\venv\scripts\activate.bat
if not %errorlevel%==0 exit /b %errorlevel%

python setup.py develop
if not %errorlevel%==0 exit /b %errorlevel%

exit /b 0
