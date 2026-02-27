@echo off
REM AI 操作 KVM VNC 系统演示脚本

echo ========================================
echo   AI 操作 KVM VNC 系统
echo ========================================
echo.

echo 请选择运行模式:
echo   1. 演示模式 (demo) - 自动执行示例任务
echo   2. 交互模式 (interactive) - 手动输入任务
echo   3. 特定任务 (specific) - 执行预设任务
echo.

set /p mode="请输入选项 (1-3): "

if "%mode%"=="1" (
    echo.
    echo 启动演示模式...
    uv run python ai_vm_control.py --mode demo
) else if "%mode%"=="2" (
    echo.
    echo 启动交互模式...
    uv run python ai_vm_control.py --mode interactive
) else if "%mode%"=="3" (
    echo.
    echo 启动特定任务模式...
    uv run python ai_vm_control.py --mode specific
) else (
    echo.
    echo 无效选项，启动交互模式...
    uv run python ai_vm_control.py --mode interactive
)

pause