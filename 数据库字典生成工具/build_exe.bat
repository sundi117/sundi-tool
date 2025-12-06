@echo off
chcp 65001 >nul
echo ========================================
echo 数据库字典生成工具 - 打包脚本
echo ========================================
echo.

echo 正在检查依赖...
pip install -r requirements.txt

echo.
echo 正在使用 PyInstaller 打包...
pyinstaller --onefile --windowed --name "数据库字典生成工具" --icon=NONE ^
    --hidden-import=ttkbootstrap ^
    --hidden-import=docx ^
    --collect-all=ttkbootstrap ^
    generator_md.py

echo.
echo ========================================
echo 打包完成！
echo 可执行文件位置: dist\数据库字典生成工具.exe
echo ========================================
pause

