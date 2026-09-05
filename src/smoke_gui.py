# -*- coding: utf-8 -*-
"""GUI 冒烟测试：启动界面、载入文件、截屏、切换主题与语言。"""

from pathlib import Path

from PIL import ImageGrab

import i18n
from gui_app import ConverterApp

try:
    from tkinterdnd2 import TkinterDnD
except ImportError:
    TkinterDnD = None

WORK = Path(__file__).resolve().parent / "work"
WORK.mkdir(exist_ok=True)

FH5_SAMPLE = r"C:/Users/wjunj/Desktop/Forza Painter Master/forza-painter-master/ASU fh5.json"
FH6_SAMPLE = r"E:/Vinylizer Files/asu v1 1850.json"


def capture(root, path: Path) -> None:
    root.update_idletasks()
    root.update()
    root.lift()
    root.attributes("-topmost", True)
    root.update()
    x = root.winfo_rootx()
    y = root.winfo_rooty()
    w = root.winfo_width()
    h = root.winfo_height()
    img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
    img.save(path)
    print(f"saved {path.name} ({w}x{h})")
    root.attributes("-topmost", False)


def main() -> None:
    root_cls = TkinterDnD.Tk if TkinterDnD is not None else None
    if root_cls is None:
        import tkinter as tk

        root_cls = tk.Tk
    root = root_cls()
    app = ConverterApp(root)

    root.update_idletasks()
    print(
        f"window geometry: {root.winfo_width()}x{root.winfo_height()} "
        f"(requested {root.winfo_reqwidth()}x{root.winfo_reqheight()})"
    )

    app._load_file(FH5_SAMPLE)
    app.theme.mode = "light"
    app.theme.apply()
    capture(root, WORK / "gui_light.png")

    app.theme.mode = "dark"
    app.theme.apply()
    capture(root, WORK / "gui_dark.png")

    # 语言切换：English / 日本語 / 한국어
    for code in ("en", "ja", "ko"):
        i18n.set_language(code)
        app._apply_all_strings()
        capture(root, WORK / f"gui_{code}.png")

    i18n.set_language("zh")
    app._apply_all_strings()
    app._load_file(FH6_SAMPLE)
    app.theme.mode = "dark"
    app.theme.apply()
    capture(root, WORK / "gui_dark_fh6.png")

    root.destroy()
    print("smoke test done")


if __name__ == "__main__":
    main()
