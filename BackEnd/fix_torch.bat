@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo 修复 PyTorch 安装问题
echo ========================================
echo.

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [错误] 虚拟环境不存在，请先创建虚拟环境
    echo 运行: python -m venv .venv
    pause
    exit /b 1
)

echo [1/3] 卸载现有的 PyTorch...
call .venv\Scripts\python.exe -m pip uninstall torch torchvision torchaudio -y

echo.
echo [2/3] 重新安装 PyTorch CPU 版本（适合 Windows）...
call .venv\Scripts\python.exe -m pip install torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cpu

if errorlevel 1 (
    echo.
    echo [错误] PyTorch 安装失败
    echo.
    echo 备选方案：尝试使用默认源安装
    call .venv\Scripts\python.exe -m pip install torch==2.1.0
)

echo.
echo [3/3] 验证 PyTorch 安装...
call .venv\Scripts\python.exe -c "import torch; print(f'PyTorch 版本: {torch.__version__}'); print('安装成功！')"

if errorlevel 1 (
    echo.
    echo [错误] PyTorch 验证失败
    echo.
    echo 可能的原因：
    echo 1. 缺少 Visual C++ Redistributable
    echo    下载地址: https://aka.ms/vs/17/release/vc_redist.x64.exe
    echo 2. 网络问题导致下载不完整
    echo    请检查网络连接后重试
    pause
    exit /b 1
)

echo.
echo ========================================
echo 修复完成！
echo ========================================
echo.
pause

