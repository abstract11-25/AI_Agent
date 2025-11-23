@echo off
chcp 65001 >nul 2>&1

echo ========================================
echo MySQL 服务管理
echo ========================================
echo.

:: 检查 MySQL 服务状态
echo 正在检查 MySQL 服务状态...
sc query MySQL >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 MySQL 服务
    echo.
    echo 可能的原因：
    echo 1. MySQL 未安装
    echo 2. MySQL 服务名称不是 "MySQL"
    echo.
    echo 请检查 MySQL 服务名称：
    echo   sc query type= service | findstr /i mysql
    echo.
    pause
    exit /b 1
)

:: 查询服务状态
for /f "tokens=3" %%a in ('sc query MySQL ^| findstr /i "STATE"') do set STATE=%%a

if "%STATE%"=="RUNNING" (
    echo [OK] MySQL 服务正在运行
    echo.
    echo 服务状态: 运行中
) else (
    echo [警告] MySQL 服务未运行
    echo.
    echo 正在尝试启动 MySQL 服务...
    echo 注意: 需要管理员权限
    echo.
    
    :: 尝试启动服务
    net start MySQL >nul 2>&1
    if errorlevel 1 (
        echo [错误] 无法启动 MySQL 服务
        echo.
        echo 请以管理员身份运行此脚本，或手动启动：
        echo   1. 按 Win+R，输入 services.msc
        echo   2. 找到 MySQL 服务
        echo   3. 右键点击，选择"启动"
        echo.
        echo 或者以管理员身份运行命令：
        echo   net start MySQL
        echo.
    ) else (
        echo [OK] MySQL 服务已启动
    )
)

echo.
echo ========================================
echo 测试数据库连接
echo ========================================
echo.

cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    echo 正在测试数据库连接...
    call .venv\Scripts\python.exe test_mysql_connection.py
) else (
    echo [警告] 未找到虚拟环境，跳过连接测试
    echo 请先运行 start.bat 或手动测试连接
)

echo.
pause

