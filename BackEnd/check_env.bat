@echo off
chcp 65001 >nul
echo ========================================
echo 环境检查脚本 - 将结果保存到 error_log.txt
echo ========================================
echo.

cd /d "%~dp0"

echo 检查虚拟环境...
if exist ".venv" (
    echo [✓] 虚拟环境存在
) else (
    echo [✗] 虚拟环境不存在
)

echo.
echo 检查 Python...
if exist ".venv\Scripts\python.exe" (
    echo [✓] Python 存在
    echo Python 路径: %CD%\.venv\Scripts\python.exe
    echo.
    echo 检查 uvicorn...
    .venv\Scripts\python.exe -m pip show uvicorn
    if errorlevel 1 (
        echo [✗] uvicorn 未安装
    ) else (
        echo [✓] uvicorn 已安装
    )
) else (
    echo [✗] Python 不存在
)

echo.
echo 尝试启动 uvicorn（测试）...
.venv\Scripts\python.exe -m uvicorn --version
if errorlevel 1 (
    echo [错误] uvicorn 无法运行
    echo.
    echo 错误详情:
    .venv\Scripts\python.exe -m uvicorn --version 2>&1
) else (
    echo [✓] uvicorn 可以正常运行
)

echo.
echo ========================================
echo 检查完成！结果已显示在上方
echo ========================================
pause

