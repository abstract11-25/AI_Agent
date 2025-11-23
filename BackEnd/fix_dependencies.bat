@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo 修复依赖冲突
echo ========================================
echo.

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [错误] 虚拟环境不存在，请先创建虚拟环境
    echo 运行: python -m venv .venv
    pause
    exit /b 1
)

echo [1/5] 升级 FastAPI 和 uvicorn 以支持 pydantic 2.7.x...
call .venv\Scripts\python.exe -m pip install "fastapi>=0.109.0" "uvicorn>=0.27.0" --upgrade

echo.
echo [2/5] 升级 pydantic 以解决 langchain 冲突...
call .venv\Scripts\python.exe -m pip install "pydantic>=2.7.4,<3.0.0" --upgrade

echo.
echo [3/5] 安装 datasets（如果使用 evals 或 evaluate）...
call .venv\Scripts\python.exe -m pip install "datasets>=2.0.0"

echo.
echo [4/5] 重新安装核心依赖以确保兼容性...
call .venv\Scripts\python.exe -m pip install -r requirements.txt --upgrade

echo.
echo [5/5] 检查依赖冲突...
call .venv\Scripts\python.exe -m pip check

echo.
echo ========================================
echo 修复完成！
echo ========================================
echo.
echo 注意：
echo - numpy 版本限制为 ^<2.0.0 以兼容 torch 2.1.0
echo - 如果 thinc 需要 numpy^>=2.0.0，这是已知冲突
echo - 如果不需要 thinc，可以卸载: pip uninstall thinc
echo - 核心功能不受这些可选依赖冲突影响
echo.
pause

