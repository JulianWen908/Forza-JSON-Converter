# Forza JSON Converter

Forza Horizon 6 / Forza Horizon 5 涂装 JSON 转换器（图形界面）。

本工具把 **Forza Horizon 6** 的彩绘 JSON 转换为 **Forza Horizon 5（forza-painter）** 可导入的 JSON，并支持从运行中的 FH6 进程直接读取内存导出当前彩绘组。

## 功能

- 文件拖入 / 选择文件
- 自动识别 FH5 / FH6 格式并给出提醒（不阻止转换）
- FH6 → FH5 一键转换（矩形 / 椭圆 / 三角形 / 软边椭圆类型映射）
- 从 FH6 内存导出当前彩绘组（完整类型码 + 内存坐标）
- 三角形大小调节（40% / 45% / 59% / 65%）
- 浅色 / 深色主题，可跟随 Windows 系统主题
- 简体中文 / English / 日本語 / 한국어
- 背景图片与不透明度设置

## 文件结构

- `gui_app.py`：图形界面
- `converter_core.py`：格式识别与转换核心
- `fh6_dump.py`：FH6 内存读取导出
- `i18n.py`：多语言文案
- `tests.py`：单元测试
- `build_exe.ps1`：PyInstaller 打包脚本
- `assets/app.ico`：应用图标

## 构建 exe

```powershell
powershell -ExecutionPolicy Bypass -File build_exe.ps1
```

打包产物位于 `dist/ForzaJSONConverter.exe`。

## 运行测试

```powershell
python tests.py
```

## 依赖

- Python 3.12+
- Pillow
- tkinterdnd2
- PyInstaller（打包时）
