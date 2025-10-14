@echo off
echo ============================================
echo R2SFCA v1.1.2 - Build and Upload to PyPI
echo ============================================
echo.

echo [Step 1] Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python not found! Please install Python or add it to PATH.
    pause
    exit /b 1
)
echo.

echo [Step 2] Upgrading build tools...
python -m pip install --upgrade pip
python -m pip install --upgrade build twine
echo.

echo [Step 3] Cleaning old builds...
if exist "build\" rd /s /q "build"
if exist "dist\" rd /s /q "dist"
if exist "r2sfca.egg-info\" rd /s /q "r2sfca.egg-info"
echo Cleaned old builds.
echo.

echo [Step 4] Building distribution packages...
python -m build
if %errorlevel% neq 0 (
    echo ERROR: Build failed!
    pause
    exit /b 1
)
echo.

echo [Step 5] Checking built packages...
python -m twine check dist/*
if %errorlevel% neq 0 (
    echo ERROR: Package check failed!
    pause
    exit /b 1
)
echo.

echo ============================================
echo Build completed successfully!
echo ============================================
echo.
echo Generated files in dist/:
dir /b dist
echo.
echo Next steps:
echo   1. To upload to TEST PyPI (recommended first):
echo      python -m twine upload --repository testpypi dist/*
echo.
echo   2. To upload to PRODUCTION PyPI:
echo      python -m twine upload dist/*
echo.
echo You will need your PyPI API token when prompted.
echo.
pause

