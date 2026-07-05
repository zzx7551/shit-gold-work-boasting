@echo off
setlocal
cd /d "%~dp0"
echo Starting dev services...
echo Backend:  http://127.0.0.1:8000
echo Frontend: http://127.0.0.1:5173
start "job-packager-backend" cmd /k ""%~dp0start-backend.bat""
start "job-packager-frontend" cmd /k ""%~dp0start-frontend.bat""
echo Two service windows were opened. Close a window to stop that service.
