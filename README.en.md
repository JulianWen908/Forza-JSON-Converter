# Forza JSON Converter

A graphical Forza Horizon 6 / Forza Horizon 5 livery JSON converter.

This tool converts **Forza Horizon 6** livery JSON into JSON importable by **Forza Horizon 5 (forza-painter)**, and can also read the currently opened livery group directly from a running FH6 process via memory dump.

## Features

- Drag-and-drop or choose a file
- Automatically detects FH5 / FH6 format and shows a warning (conversion is not blocked)
- One-click FH6 → FH5 conversion (rectangle / ellipse / triangle / soft-ellipse type mapping)
- Dump the current livery group from FH6 memory (full type codes + memory coordinates)
- Triangle size adjustment (40% / 45% / 59% / 65%)
- Light / dark theme, with automatic Windows system-theme switching
- Simplified Chinese / English / Japanese / Korean
- Background image and opacity settings

## File Structure

- `gui_app.py`: graphical interface
- `converter_core.py`: format detection and conversion core
- `fh6_dump.py`: FH6 memory reading and export
- `i18n.py`: localized strings
- `tests.py`: unit tests
- `build_exe.ps1`: PyInstaller build script
- `assets/app.ico`: application icon

## Build the exe

```powershell
powershell -ExecutionPolicy Bypass -File build_exe.ps1
```

The build output is located at `dist/ForzaJSONConverter.exe`.

## Run Tests

```powershell
python tests.py
```

## Dependencies

- Python 3.12+
- Pillow
- tkinterdnd2
- PyInstaller (build only)
