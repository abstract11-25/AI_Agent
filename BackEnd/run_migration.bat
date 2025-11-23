@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo 数据库迁移脚本
echo ========================================
echo.
echo 此脚本将为现有数据库添加新字段：
echo   - users 表：role 字段
echo   - api_keys 表：is_admin_key 字段
echo.
echo 注意：如果数据库是新建的，不需要运行此脚本
echo.
pause

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [错误] 虚拟环境不存在，请先运行 pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo 正在运行迁移脚本...
.venv\Scripts\python.exe migrate_add_role.py

echo.
pause

