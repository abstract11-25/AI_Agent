@echo off
chcp 65001 >nul
echo ========================================
echo 安装后端依赖
echo ========================================
echo.

cd /d "%~dp0"

if not exist ".venv" (
    echo [错误] 虚拟环境不存在！
    echo 请先创建虚拟环境：
    echo   python -m venv .venv
    pause
    exit /b 1
)

echo 正在安装依赖，这可能需要几分钟...
echo.

.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [错误] 依赖安装失败！
    pause
    exit /b 1
)

echo.
echo ========================================
echo 依赖安装完成！
echo ========================================
echo.
echo 验证安装...
.venv\Scripts\python.exe -m pip list | findstr uvicorn
if errorlevel 1 (
    echo [警告] uvicorn 可能未正确安装
) else (
    echo [✓] uvicorn 已安装
)
echo.
pause

