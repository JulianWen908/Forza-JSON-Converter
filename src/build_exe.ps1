# 使用 PyInstaller 打包 GUI 工具为单文件 exe
param(
    [string]$Python = "C:\Users\wjunj\AppData\Local\Programs\Python\Python312\python.exe"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

& $Python -m pip install --quiet pyinstaller tkinterdnd2

& $Python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name "ForzaJSONConverter" `
    --icon "assets/app.ico" `
    --add-data "assets/app.ico;assets" `
    --collect-all tkinterdnd2 `
    "gui_app.py"

# 保留源码，便于发布到 GitHub
$srcDir = Join-Path $root "dist\src"
New-Item -ItemType Directory -Path $srcDir -Force | Out-Null
Copy-Item "gui_app.py", "converter_core.py", "fh6_dump.py", "i18n.py", "tests.py", "build_exe.ps1", "make_icon.py", "smoke_gui.py", "README.md", "requirements.txt" $srcDir -Force
Copy-Item "assets" (Join-Path $srcDir "assets") -Recurse -Force

Write-Host "Build finished."
