# -*- coding: utf-8 -*-
"""
Forza Horizon 5 <-> Forza Horizon 6 涂装 JSON 转换器（图形界面）。

功能：
  * 文件拖入 / 选择文件
  * 自动识别 FH5 / FH6 格式并给出提醒（不阻止转换）
  * 一键转换，转换前询问输出文件名与存储路径
  * 转换失败弹出错误窗口
  * 浅色 / 深色主题，可跟随 Windows 系统主题自动切换
  * 简体中文 / English / 日本語 / 한국어 界面语言
"""

from __future__ import annotations

import ctypes
import json
import os
import queue
import re
import sys
import threading
import traceback
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

try:
    from PIL import Image, ImageTk
except ImportError:  # 无 PIL 时背景图片功能不可用
    Image = None
    ImageTk = None

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:  # 未安装 tkinterdnd2 时降级为无拖放
    TkinterDnD = None
    DND_FILES = None

import converter_core as core
import fh6_dump
import i18n


APP_VERSION = "1.8.5"


# ---------------------------------------------------------------------------
# Windows 系统主题检测
# ---------------------------------------------------------------------------

_THEME_KEY = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"


def windows_theme_is_dark() -> bool:
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _THEME_KEY) as key:
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return int(value) == 0
    except Exception:
        return False


def enable_dpi_awareness() -> None:
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# 主题
# ---------------------------------------------------------------------------

THEMES = {
    "light": {
        "bg": "#f2f3f5",
        "panel": "#ffffff",
        "fg": "#1c1c1e",
        "muted": "#6e6e73",
        "border": "#c7c7cc",
        "accent": "#007aff",
        "accent_fg": "#ffffff",
        "warning": "#b25000",
        "error": "#d70015",
        "ok": "#248a3d",
        "drop": "#e8f0fe",
        "entry": "#ffffff",
    },
    "dark": {
        "bg": "#1e1e1e",
        "panel": "#2a2a2c",
        "fg": "#e8e8e8",
        "muted": "#98989f",
        "border": "#48484a",
        "accent": "#0a84ff",
        "accent_fg": "#ffffff",
        "warning": "#ff9f0a",
        "error": "#ff453a",
        "ok": "#30d158",
        "drop": "#1d3557",
        "entry": "#323234",
    },
}


class ThemeManager:
    """管理浅色/深色主题与应用 ttk 样式。"""

    def __init__(self, root: tk.Tk, on_change=None) -> None:
        self.root = root
        self.on_change = on_change
        self.mode = "system"  # system / light / dark
        self.current = "light"
        self.style = ttk.Style(root)
        self.style.theme_use("clam")
        self._base_font = ("Segoe UI", 10)
        self._title_font = ("Segoe UI", 13, "bold")
        self._small_font = ("Segoe UI", 9)

    def effective(self) -> str:
        if self.mode == "system":
            return "dark" if windows_theme_is_dark() else "light"
        return self.mode

    def apply(self) -> None:
        self.current = self.effective()
        c = THEMES[self.current]
        self.root.configure(bg=c["bg"])

        self.style.configure(".", font=self._base_font, background=c["bg"], foreground=c["fg"])
        self.style.configure("TFrame", background=c["bg"])
        self.style.configure("Panel.TFrame", background=c["panel"])
        self.style.configure("TLabel", background=c["bg"], foreground=c["fg"], font=self._base_font)
        self.style.configure("Panel.TLabel", background=c["panel"], foreground=c["fg"], font=self._base_font)
        self.style.configure("Title.TLabel", background=c["bg"], foreground=c["fg"], font=self._title_font)
        self.style.configure("Muted.TLabel", background=c["bg"], foreground=c["muted"], font=self._small_font)
        self.style.configure("PanelMuted.TLabel", background=c["panel"], foreground=c["muted"], font=self._small_font)

        self.style.configure("TLabelframe", background=c["bg"], foreground=c["fg"], bordercolor=c["border"], relief="solid")
        self.style.configure("TLabelframe.Label", background=c["bg"], foreground=c["fg"], font=self._base_font)
        self.style.configure("Panel.TLabelframe", background=c["panel"], foreground=c["fg"], bordercolor=c["border"])
        self.style.configure("Panel.TLabelframe.Label", background=c["panel"], foreground=c["fg"], font=self._base_font)

        self.style.configure("TButton", background=c["panel"], foreground=c["fg"], bordercolor=c["border"],
                             padding=(12, 6), font=self._base_font)
        self.style.map("TButton",
                       background=[("pressed", c["accent"]), ("active", c["drop"])],
                       foreground=[("pressed", c["accent_fg"]), ("active", c["fg"])])
        self.style.configure("Accent.TButton", background=c["accent"], foreground=c["accent_fg"], bordercolor=c["accent"])
        self.style.map("Accent.TButton",
                       background=[("pressed", c["border"]), ("active", c["drop"]), ("disabled", c["border"])],
                       foreground=[("pressed", c["fg"]), ("active", c["accent_fg"]), ("disabled", c["muted"])])

        self.style.configure("TRadiobutton", background=c["bg"], foreground=c["fg"], font=self._base_font)
        self.style.map("TRadiobutton", background=[("active", c["bg"])])
        self.style.configure("Panel.TRadiobutton", background=c["panel"], foreground=c["fg"], font=self._base_font)
        self.style.map("Panel.TRadiobutton", background=[("active", c["panel"])])

        self.style.configure("TCombobox", fieldbackground=c["entry"], background=c["entry"],
                             foreground=c["fg"], arrowcolor=c["fg"], bordercolor=c["border"])
        self.style.map("TCombobox",
                       fieldbackground=[("readonly", c["entry"])],
                       foreground=[("readonly", c["fg"])],
                       selectbackground=[("readonly", c["accent"])],
                       selectforeground=[("readonly", c["accent_fg"])])
        self.style.configure(
            "TEntry",
            fieldbackground="#ffffff",
            foreground="#000000",
            insertcolor="#000000",
            bordercolor=c["border"],
        )

        self.style.configure("Status.TLabel", background=c["bg"], foreground=c["muted"], font=self._small_font)

        if self.on_change:
            self.on_change(c)

    def start_watching(self) -> None:
        """每 2.5 秒检查一次系统主题，跟随变化自动切换。"""

        def tick() -> None:
            if self.mode == "system":
                current = self.effective()
                if current != self.current:
                    self.apply()
            self.root.after(2500, tick)

        self.root.after(2500, tick)


# ---------------------------------------------------------------------------
# 配置持久化
# ---------------------------------------------------------------------------

def config_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA") or str(Path.home())
    return Path(base) / "ForzaJSONConverter"


def load_config() -> dict:
    try:
        path = config_dir() / "config.json"
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
    except Exception:
        pass
    return {}


def save_config(config: dict) -> None:
    try:
        path = config_dir()
        path.mkdir(parents=True, exist_ok=True)
        (path / "config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# 主界面
# ---------------------------------------------------------------------------

class ConverterApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.tr = i18n.get
        self.root.minsize(620, 560)

        self.config = load_config()
        i18n.set_language(self.config.get("language", "zh"))
        self.tr = i18n.get
        self._set_title()

        self.current_path: Path | None = None
        self.detection: core.DetectionResult | None = None
        self.triangle_scale_var = tk.StringVar(value=str(self.config.get("triangle_scale", "0.59")))
        self.triangle_scale_var.trace_add("write", self._on_triangle_scale_changed)
        self.theme_var = tk.StringVar(value=self.config.get("theme", "system"))
        self.lang_var = tk.StringVar(value=i18n.get_language())

        self._info = {}          # 文件信息缓存，语言切换时重绘
        self._current_warnings: list[tuple[str, dict]] = []
        self._status_state: tuple | None = None
        self._drop_highlight = False
        self._panel_photos: list = []
        self._resize_after_id = None
        self.ui_queue: "queue.Queue" = queue.Queue()
        self._dump_cancel = threading.Event()
        self._convert_watchdog_id = None
        self._dump_watchdog_id = None

        # 背景图片设置
        self.bg_image_path = self.config.get("background_image", "") or ""
        self.bg_opacity = int(self.config.get("background_opacity", 100))
        self._bg_photo = None  # 保持 PhotoImage 引用，防止被回收
        self._bg_base_img = None

        self.theme = ThemeManager(root, on_change=self._apply_palette)

        self._build_ui()
        self.theme.mode = self.theme_var.get()
        self.theme.apply()
        self.theme.start_watching()
        self._register_drop()
        self._set_window_icon()
        self._apply_window_size()
        self._render_background()
        self._bind_resize()
        self._set_status("status.ready")
        self._poll_ui_queue()

    # ---------------- UI 构建 ----------------

    def _build_ui(self) -> None:
        root = self.root
        self.canvas = tk.Canvas(root, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)
        self._text_items: dict = {}
        self._bg_base_img = None  # 全窗口背景底图（含不透明度混合）
        self._bg_photo = None

        # 交互控件（通过 create_window 放置到画布上）
        self.refresh_button = ttk.Button(self.canvas, text=self.tr("btn.refresh"), command=self._refresh)
        self.settings_button = ttk.Button(self.canvas, text=self.tr("btn.settings"), command=self._open_settings)
        self.choose_button = ttk.Button(self.canvas, text=self.tr("btn.choose"), command=self._choose_file)
        self.clear_button = ttk.Button(self.canvas, text=self.tr("btn.clear"), command=self._clear_file)
        self.dump_button = ttk.Button(self.canvas, text=self.tr("btn.dump_fh6"), command=self._dump_fh6)
        self.layer_count_var = tk.StringVar(value=self.config.get("layer_count", ""))
        self.layer_count_entry = ttk.Entry(self.canvas, textvariable=self.layer_count_var, width=12)
        self.tri_smaller = ttk.Radiobutton(
            self.canvas, text=self.tr("triangle.smaller"), value="0.40", variable=self.triangle_scale_var,
        )
        self.tri_small = ttk.Radiobutton(
            self.canvas, text=self.tr("triangle.small"), value="0.45", variable=self.triangle_scale_var,
        )
        self.tri_normal = ttk.Radiobutton(
            self.canvas, text=self.tr("triangle.normal"), value="0.59", variable=self.triangle_scale_var,
        )
        self.tri_larger = ttk.Radiobutton(
            self.canvas, text=self.tr("triangle.larger"), value="0.65", variable=self.triangle_scale_var,
        )
        self.convert_button = ttk.Button(
            self.canvas, text=self.tr("btn.convert"), style="Accent.TButton", command=self._convert,
        )

        self._relayout()

    # ---------------- 画布布局与半透明面板 ----------------

    def _panel_opacity(self) -> int:
        """面板不透明度略低于背景不透明度。"""
        return max(0, min(100, self.bg_opacity - 15))

    def _draw_panel(self, x0: int, y0: int, x1: int, y1: int, c: dict, *, highlight: bool = False) -> None:
        w = max(1, x1 - x0)
        h = max(1, y1 - y0)
        if self._bg_base_img is not None and Image is not None and ImageTk is not None:
            region = self._bg_base_img.crop((x0, y0, x0 + w, y0 + h))
            solid = Image.new("RGB", (w, h), c["panel"])
            opacity = max(0.0, min(1.0, self._panel_opacity() / 100.0))
            frosted = Image.blend(region, solid, opacity)
            photo = ImageTk.PhotoImage(frosted)
            self._panel_photos.append(photo)
            self.canvas.create_image(x0, y0, image=photo, anchor="nw")
        else:
            fill = c["drop"] if highlight else c["panel"]
            self.canvas.create_rectangle(x0, y0, x1, y1, fill=fill, outline="")
        self.canvas.create_rectangle(x0, y0, x1, y1, outline=c["border"], width=1)

    def _relayout(self) -> None:
        self.canvas.delete("all")
        self._text_items = {}
        self._panel_photos = []
        W = self.canvas.winfo_width()
        H = self.canvas.winfo_height()
        if W <= 1 or H <= 1:
            return
        c = THEMES[self.theme.current]
        if self._bg_photo is not None:
            self.canvas.create_image(0, 0, image=self._bg_photo, anchor="nw")

        def _req_w(widget, default):
            try:
                w = widget.winfo_reqwidth()
                return w if w and w > 1 else default
            except Exception:
                return default

        M = 18
        G = 12
        x0 = M
        x1 = W - M
        y = M
        # 标题 + 刷新/设置按钮
        self.canvas.create_text(x0, y + 2, text=self.tr("app.title"), anchor="nw",
                                font=("Segoe UI", 13, "bold"), fill=c["fg"])
        self.canvas.create_window(x1, y + 2, window=self.settings_button, anchor="ne")
        refresh_x = x1 - _req_w(self.settings_button, 60) - 10
        self.canvas.create_window(refresh_x, y + 2, window=self.refresh_button, anchor="ne")
        y += 48 + G
        # 拖放区
        drop_h = 182
        self._draw_panel(x0, y, x1, y + drop_h, c, highlight=self._drop_highlight)
        self.canvas.create_text(x0 + 12, y + 8, text=self.tr("section.file"), anchor="nw",
                                font=("Segoe UI", 10, "bold"), fill=c["fg"])
        hint = self.canvas.create_text((x0 + x1) // 2, y + 28, text=self.tr("drop.hint"), anchor="n",
                                       font=("Segoe UI", 11), fill=c["muted"], justify="center")
        self.canvas.tag_bind(hint, "<Button-1>", lambda _e: self._choose_file())
        self.canvas.create_text(x0 + 12, y + 56, text=self.tr("dump.layer_count"), anchor="nw",
                                font=("Segoe UI", 9), fill=c["muted"])
        self.canvas.create_window(x0 + 12, y + 78, window=self.layer_count_entry, anchor="nw")
        self.canvas.create_window(x0 + 12, y + drop_h - 52, window=self.choose_button, anchor="nw")
        choose_w = _req_w(self.choose_button, 90)
        clear_x = x0 + 12 + choose_w + 10
        self.canvas.create_window(clear_x, y + drop_h - 52, window=self.clear_button, anchor="nw")
        self.canvas.create_window(clear_x + _req_w(self.clear_button, 70) + 10, y + drop_h - 52,
                                  window=self.dump_button, anchor="nw")
        y += drop_h + G
        # 文件信息
        info_h = 170
        self._draw_panel(x0, y, x1, y + info_h, c)
        self.canvas.create_text(x0 + 12, y + 3, text=self.tr("section.info"), anchor="nw",
                                font=("Segoe UI", 10, "bold"), fill=c["fg"])
        rows = [
            ("file", self.tr("info.file"), self._info_text("file")),
            ("format", self.tr("info.format"), self._info_text("format")),
            ("shapes", self.tr("info.shapes"), self._info_text("shape")),
            ("canvas", self.tr("info.canvas"), self._info_text("canvas")),
            ("types", self.tr("info.types"), self._info_text("types")),
        ]
        ry = y + 30
        for key, caption, value in rows:
            self.canvas.create_text(x0 + 12, ry, text=caption, anchor="nw",
                                    font=("Segoe UI", 9), fill=c["muted"])
            value_color = self._format_color() if key == "format" else c["fg"]
            self.canvas.create_text(x0 + 150, ry, text=value, anchor="nw",
                                    font=("Segoe UI", 10), fill=value_color)
            ry += 24
        y += info_h + G
        # 调节三角形的大小（一行四列）
        tri_h = 128
        self._draw_panel(x0, y, x1, y + tri_h, c)
        self.canvas.create_text(x0 + 12, y + 8, text=self.tr("section.triangle_size"), anchor="nw",
                                font=("Segoe UI", 10, "bold"), fill=c["fg"])
        self.canvas.create_text(x0 + 12, y + 28, text=self.tr("triangle.note"), anchor="nw",
                                font=("Segoe UI", 9), fill=c["muted"], width=max(120, x1 - x0 - 24))
        tri_radios = [self.tri_smaller, self.tri_small, self.tri_normal, self.tri_larger]
        rx = x0 + 16
        ry = y + tri_h - 40
        for radio in tri_radios:
            self.canvas.create_window(rx, ry, window=radio, anchor="nw")
            rx += _req_w(radio, 110) + 10
        y += tri_h + G
        # 提醒（占据剩余空间）
        warn_y2 = max(y + 100, H - M - 66)
        self._draw_panel(x0, y, x1, warn_y2, c)
        self.canvas.create_text(x0 + 12, y + 8, text=self.tr("section.warnings"), anchor="nw",
                                font=("Segoe UI", 10, "bold"), fill=c["fg"])
        self.canvas.create_text(x0 + 12, y + 38, text=self._warnings_text(), anchor="nw",
                                font=("Consolas", 9), fill=c["fg"], width=max(80, x1 - x0 - 40))
        # 转换按钮 + 状态（底部）
        self.canvas.create_window(x1, H - M - 8, window=self.convert_button, anchor="se")
        self.canvas.create_text(x0, H - M - 14, text=self._status_text(), anchor="sw",
                                font=("Segoe UI", 9), fill=c["muted"])

    def _info_text(self, key: str) -> str:
        info = self._info
        if key == "file":
            return info.get("file") or self.tr("info.no_file")
        if key == "format":
            if info.get("error"):
                return info["error"]
            fmt = info.get("format")
            if fmt in (None, "unknown"):
                return self.tr("fmt.unknown")
            return self.tr(f"fmt.{fmt}")
        if key == "shape":
            return info.get("shape") or self.tr("info.none")
        if key == "canvas":
            canvas = info.get("canvas")
            if canvas is None:
                return self.tr("info.canvas_none") if info.get("format") in ("fh6", "fh6_native") else self.tr("info.none")
            code, params = canvas
            return self.tr(code, **params)
        if key == "types":
            return info.get("types") or self.tr("info.none")
        return ""

    def _format_color(self) -> str:
        info = self._info
        c = THEMES[self.theme.current]
        if info.get("error"):
            return c["error"]
        fmt = info.get("format")
        if fmt == "fh5":
            return c["accent"]
        if fmt == "fh6":
            return "#30b0c0"
        if fmt == "fh6_native":
            return "#30b0c0"
        return c["warning"]

    def _warnings_text(self) -> str:
        if not self._current_warnings:
            return self.tr("no_warnings")
        return "\n".join("• " + self.tr(code, **params) for code, params in self._current_warnings)

    def _status_text(self) -> str:
        if self._status_state is None:
            return self.tr("status.ready")
        code, params, error = self._status_state
        return ("⚠ " if error else "") + self.tr(code, **params)

    def _apply_window_size(self) -> None:
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        w = min(max(700, int(screen_w * 0.42)), screen_w - 60)
        h = min(max(740, int(screen_h * 0.70)), screen_h - 80)
        x = max(0, (screen_w - w) // 2)
        y = max(0, (screen_h - h) // 2 - 20)
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.minsize(640, 600)

    def _set_title(self) -> None:
        self.root.title(f"{self.tr('app.title')}  ·  v{APP_VERSION}")

    # ---------------- 主题 / 语言 ----------------

    def _apply_palette(self, c: dict) -> None:
        self._render_background()

    def _theme_index(self) -> int:
        return ("system", "light", "dark").index(self.theme_var.get())

    def _apply_theme_mode(self, mode: str) -> None:
        self.theme.mode = mode
        self.theme_var.set(mode)
        self.theme.apply()
        self.config["theme"] = mode
        save_config(self.config)
        self._set_status("status.theme_changed", {"theme": self.tr(f"theme.{mode}")})

    def _apply_language_code(self, code: str) -> None:
        i18n.set_language(code)
        self.lang_var.set(code)
        self.config["language"] = code
        save_config(self.config)
        self._apply_all_strings()
        self._render_warnings()
        self._refresh_settings_dialog()
        self._set_status("status.language_changed", {"language": i18n.LANG_NAMES[code]})

    def _on_triangle_scale_changed(self, *_args) -> None:
        self.config["triangle_scale"] = self.triangle_scale_var.get()
        save_config(self.config)

    def _apply_all_strings(self) -> None:
        """语言切换后刷新所有静态文本。"""
        self._set_title()
        self.refresh_button.configure(text=self.tr("btn.refresh"))
        self.settings_button.configure(text=self.tr("btn.settings"))
        self.choose_button.configure(text=self.tr("btn.choose"))
        self.clear_button.configure(text=self.tr("btn.clear"))
        self.dump_button.configure(text=self.tr("btn.dump_fh6"))
        self.tri_smaller.configure(text=self.tr("triangle.smaller"))
        self.tri_small.configure(text=self.tr("triangle.small"))
        self.tri_normal.configure(text=self.tr("triangle.normal"))
        self.tri_larger.configure(text=self.tr("triangle.larger"))
        self.convert_button.configure(text=self.tr("btn.convert"))
        self._relayout()

    # ---------------- 设置 ----------------

    def _open_settings(self) -> None:
        if getattr(self, "settings_win", None) is not None and self.settings_win.winfo_exists():
            self.settings_win.lift()
            self.settings_win.focus_force()
            return
        self._build_settings_dialog()

    def _build_settings_dialog(self) -> None:
        win = tk.Toplevel(self.root)
        win.title(self.tr("settings.title"))
        win.transient(self.root)
        win.resizable(False, False)
        self.settings_win = win

        body = ttk.Frame(win, padding=16)
        body.pack(fill="both", expand=True)

        # 语言
        lang_row = ttk.Frame(body)
        lang_row.pack(fill="x", pady=(0, 8))
        self.settings_lang_label = ttk.Label(lang_row, text=self.tr("settings.language"), width=16, anchor="w")
        self.settings_lang_label.pack(side="left")
        self.settings_lang_combo = ttk.Combobox(
            lang_row, state="readonly", width=16,
            values=[i18n.LANG_NAMES[c] for c in i18n.LANG_CODES],
        )
        self.settings_lang_combo.pack(side="left")
        self.settings_lang_combo.current(i18n.LANG_CODES.index(i18n.get_language()))
        self.settings_lang_combo.bind("<<ComboboxSelected>>", self._settings_on_language)

        # 主题
        theme_row = ttk.Frame(body)
        theme_row.pack(fill="x", pady=(0, 8))
        self.settings_theme_label = ttk.Label(theme_row, text=self.tr("settings.theme"), width=16, anchor="w")
        self.settings_theme_label.pack(side="left")
        self.settings_theme_combo = ttk.Combobox(
            theme_row, state="readonly", width=16,
            values=[self.tr("theme.system"), self.tr("theme.light"), self.tr("theme.dark")],
        )
        self.settings_theme_combo.pack(side="left")
        self.settings_theme_combo.current(self._theme_index())
        self.settings_theme_combo.bind("<<ComboboxSelected>>", self._settings_on_theme)

        # 背景图片
        bg_frame = ttk.Labelframe(body, text=self.tr("settings.background"), padding=8)
        bg_frame.pack(fill="x", pady=(4, 8))
        self.settings_bg_hint = ttk.Label(
            bg_frame, text=self.tr("settings.background_hint"), style="PanelMuted.TLabel", wraplength=360,
        )
        self.settings_bg_hint.pack(fill="x", anchor="w", pady=(0, 6))
        bg_row = ttk.Frame(bg_frame)
        bg_row.pack(fill="x")
        self.settings_bg_path = ttk.Label(bg_row, text=self._bg_path_display(), style="Panel.TLabel")
        self.settings_bg_path.pack(side="left", fill="x", expand=True)
        self.settings_choose_btn = ttk.Button(bg_row, text=self.tr("settings.choose_image"), command=self._settings_choose_image)
        self.settings_choose_btn.pack(side="left", padx=(6, 0))
        self.settings_clear_btn = ttk.Button(bg_row, text=self.tr("settings.clear_image"), command=self._settings_clear_image)
        self.settings_clear_btn.pack(side="left", padx=(6, 0))

        # 不透明度
        opacity_row = ttk.Frame(body)
        opacity_row.pack(fill="x", pady=(0, 8))
        self.settings_opacity_label = ttk.Label(opacity_row, text=self.tr("settings.opacity"), width=16, anchor="w")
        self.settings_opacity_label.pack(side="left")
        self.bg_opacity_var = tk.DoubleVar(value=float(self.bg_opacity))
        self.settings_opacity_scale = ttk.Scale(
            opacity_row, from_=0, to=100, variable=self.bg_opacity_var,
            command=self._settings_on_opacity, length=220,
        )
        self.settings_opacity_scale.pack(side="left", padx=(0, 8))
        self.settings_opacity_value = ttk.Label(opacity_row, text=f"{self.bg_opacity}%", width=5)
        self.settings_opacity_value.pack(side="left")

        # 关闭
        close_row = ttk.Frame(body)
        close_row.pack(fill="x", pady=(8, 0))
        ttk.Button(close_row, text=self.tr("settings.close"), command=win.destroy).pack(side="right")

        win.update_idletasks()
        win.geometry(f"+{self.root.winfo_rootx() + 40}+{self.root.winfo_rooty() + 40}")

    def _refresh_settings_dialog(self) -> None:
        if getattr(self, "settings_win", None) is None or not self.settings_win.winfo_exists():
            return
        self.settings_win.title(self.tr("settings.title"))
        self.settings_lang_label.configure(text=self.tr("settings.language"))
        self.settings_theme_label.configure(text=self.tr("settings.theme"))
        self.settings_bg_hint.configure(text=self.tr("settings.background_hint"))
        self.settings_choose_btn.configure(text=self.tr("settings.choose_image"))
        self.settings_clear_btn.configure(text=self.tr("settings.clear_image"))
        self.settings_opacity_label.configure(text=self.tr("settings.opacity"))
        self.settings_theme_combo.configure(values=[self.tr("theme.system"), self.tr("theme.light"), self.tr("theme.dark")])
        self.settings_theme_combo.current(self._theme_index())
        self._refresh_bg_frame_texts()

    def _refresh_bg_frame_texts(self) -> None:
        if getattr(self, "settings_win", None) is None or not self.settings_win.winfo_exists():
            return
        self.settings_bg_path.configure(text=self._bg_path_display())
        self.settings_opacity_value.configure(text=f"{int(round(self.bg_opacity_var.get()))}%")

    def _bg_path_display(self) -> str:
        if not self.bg_image_path:
            return self.tr("settings.no_image")
        return self.bg_image_path

    def _settings_on_language(self, _event=None) -> None:
        code = i18n.LANG_CODES[self.settings_lang_combo.current()]
        self._apply_language_code(code)

    def _settings_on_theme(self, _event=None) -> None:
        mode = ("system", "light", "dark")[self.settings_theme_combo.current()]
        self._apply_theme_mode(mode)

    def _settings_choose_image(self) -> None:
        path = filedialog.askopenfilename(
            title=self.tr("settings.choose_image"),
            filetypes=[
                (self.tr("settings.background"), "*.png *.jpg *.jpeg *.bmp *.gif *.webp"),
                (self.tr("filetype.all"), "*.*"),
            ],
        )
        if not path:
            return
        self.bg_image_path = path
        self.config["background_image"] = path
        save_config(self.config)
        self._render_background()
        self._refresh_bg_frame_texts()
        self._set_status("status.bg_changed")

    def _settings_clear_image(self) -> None:
        self.bg_image_path = ""
        self.config["background_image"] = ""
        save_config(self.config)
        self._render_background()
        self._refresh_bg_frame_texts()
        self._set_status("status.bg_cleared")

    def _settings_on_opacity(self, _value=None) -> None:
        self.bg_opacity = int(round(float(self.bg_opacity_var.get())))
        self.config["background_opacity"] = self.bg_opacity
        save_config(self.config)
        self._render_background()
        self.settings_opacity_value.configure(text=f"{self.bg_opacity}%")

    # ---------------- 背景图片 ----------------

    def _render_background(self) -> None:
        c = THEMES[self.theme.current]
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        if w <= 1 or h <= 1:
            return
        if Image is None or ImageTk is None or not self.bg_image_path or not os.path.isfile(self.bg_image_path):
            self._bg_photo = None
            self._bg_base_img = None
            self._relayout()
            return
        try:
            img = Image.open(self.bg_image_path).convert("RGB")
            iw, ih = img.size
            scale = max(w / iw, h / ih)
            nw = max(1, int(round(iw * scale)))
            nh = max(1, int(round(ih * scale)))
            img = img.resize((nw, nh), Image.LANCZOS)
            left = (nw - w) // 2
            top = (nh - h) // 2
            img = img.crop((left, top, left + w, top + h))
            opacity = max(0.0, min(1.0, self.bg_opacity / 100.0))
            base = Image.new("RGB", (w, h), c["bg"])
            img = Image.blend(base, img, opacity)
            self._bg_base_img = img
            self._bg_photo = ImageTk.PhotoImage(img)
        except Exception as exc:  # noqa: BLE001
            self._bg_photo = None
            self._bg_base_img = None
            self._set_status("status.bg_error", {"error": str(exc)}, error=True)
        self._relayout()

    def _bind_resize(self) -> None:
        self._resize_after_id = None
        self.root.bind("<Configure>", self._on_resize)

    def _on_resize(self, event) -> None:
        if event.widget is not self.root:
            return
        if self._resize_after_id is not None:
            self.root.after_cancel(self._resize_after_id)
        self._resize_after_id = self.root.after(120, self._render_background)

    # ---------------- 拖放 ----------------

    def _register_drop(self) -> None:
        if TkinterDnD is None:
            self._set_status("status.no_dnd")
            return
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind("<<Drop>>", self._on_drop)
        self.root.dnd_bind("<<DropEnter>>", lambda _e: self._highlight(True))
        self.root.dnd_bind("<<DropLeave>>", lambda _e: self._highlight(False))

    def _highlight(self, on: bool) -> None:
        self._drop_highlight = on
        self._relayout()

    @staticmethod
    def _parse_dnd_paths(data: str) -> list[str]:
        return [p for p in re.findall(r"\{[^}]*\}|\S+", data or "") if p.strip("{}").strip()]

    def _on_drop(self, event) -> None:
        self._highlight(False)
        paths = [p.strip("{}").strip() for p in self._parse_dnd_paths(event.data)]
        if not paths:
            return
        if len(paths) > 1:
            self._set_status("status.multi_drop", {"count": len(paths)})
        self._load_file(paths[0])

    # ---------------- 文件操作 ----------------

    def _choose_file(self) -> None:
        path = filedialog.askopenfilename(
            title=self.tr("dialog.save_title"),
            filetypes=[
                (self.tr("filetype.json"), "*.json"),
                (self.tr("filetype.all"), "*.*"),
            ],
        )
        if path:
            self._load_file(path)

    def _clear_file(self) -> None:
        self.current_path = None
        self.detection = None
        self._info = {}
        self._render_info()
        self._current_warnings = []
        self._set_warnings([])
        self._set_status("status.cleared")

    def _load_file(self, path: str) -> None:
        path = os.path.normpath(path)
        try:
            payload = core.load_json(path)
            detection = core.detect_format(payload)
        except core.FormatError as exc:
            self.current_path = None
            self.detection = None
            self._info = {
                "file": path,
                "format": None,
                "shape": None,
                "canvas": None,
                "types": None,
                "error": self.tr(exc.code, **exc.params),
            }
            self._render_info()
            self._current_warnings = [("err.json_parse", {})]
            self._set_warnings([(exc.code, exc.params)])
            self._set_status("status.parse_failed", error=True)
            return

        self.current_path = Path(path)
        self.detection = detection

        canvas_text: tuple | None = None
        if detection.canvas is not None:
            data = detection.canvas.get("data", [])
            if len(data) == 4:
                canvas_text = ("info.canvas_fh5", {"w": data[2], "h": data[3]})
        self._info = {
            "file": str(self.current_path),
            "format": detection.format_name,
            "shape": str(detection.shape_count),
            "canvas": canvas_text,
            "types": detection.type_summary(),
            "error": None,
        }

        warnings = list(detection.warnings)
        if detection.format_name == "fh5":
            warnings.append(("note.only_fh6_to_fh5", {}))
        elif detection.format_name == "fh6":
            warnings.append(("note.fh6_target", {}))
        elif detection.format_name == "fh6_native":
            warnings.append(("note.fh6_native_target", {}))
        self._current_warnings = warnings
        self._render_info()
        self._set_warnings(warnings)
        self._set_status("status.loaded")

    def _render_info(self) -> None:
        self._relayout()

    # ---------------- 转换 ----------------

    def _convert(self) -> None:
        if self.current_path is None or self.detection is None:
            messagebox.showinfo(self.tr("app.title"), self.tr("msg.choose_first"))
            return

        if self.detection.format_name == "fh6_native":
            direction = "fh6_native_to_fh5"
        elif self.detection.format_name == "fh6":
            direction = "fh6_to_fh5"
        else:
            messagebox.showinfo(self.tr("app.title"), self.tr("err.only_fh6_to_fh5_supported"))
            return

        triangle_scale = float(self.triangle_scale_var.get())
        default_name = self.current_path.stem + "_fh5.json"

        target_path = filedialog.asksaveasfilename(
            title=self.tr("dialog.save_title"),
            defaultextension=".json",
            initialfile=default_name,
            initialdir=str(self.current_path.parent),
            filetypes=[
                (self.tr("filetype.json"), "*.json"),
                (self.tr("filetype.all"), "*.*"),
            ],
        )
        if not target_path:
            self._set_status("status.cancelled")
            return

        self.convert_button.configure(state="disabled")
        self._set_status("status.converting", {"target": "FH5"})

        def worker() -> None:
            try:
                result = core.convert_file(str(self.current_path), target_path, direction, triangle_scale)
                self.ui_queue.put(("convert_success", result, target_path))
            except Exception as exc:  # noqa: BLE001 - 需要捕获所有异常并弹窗
                self.ui_queue.put(("convert_failure", exc))

        threading.Thread(target=worker, daemon=True).start()
        self._convert_watchdog_id = self.root.after(30000, self._on_convert_timeout)

    def _on_convert_success(self, result: core.ConversionResult, target_path: str) -> None:
        try:
            self._current_warnings = list(result.warnings)
            self._set_warnings(result.warnings)
            messagebox.showinfo(
                self.tr("dialog.success_title"),
                self.tr("dialog.success_body", count=result.shape_count, path=target_path),
            )
            self._set_status(
                "status.done",
                {"source": result.source_format.upper(), "target": result.target_format.upper(), "count": result.shape_count},
            )
        finally:
            self._cancel_convert_watchdog()
            self.convert_button.configure(state="normal")

    def _on_convert_failure(self, exc: Exception) -> None:
        try:
            if isinstance(exc, core.FormatError):
                text = self.tr(exc.code, **exc.params)
            else:
                text = str(exc)
            messagebox.showerror(self.tr("dialog.error_title"), self.tr("dialog.error_body", error=text))
            self._set_status("status.convert_failed", error=True)
        finally:
            self._cancel_convert_watchdog()
            self.convert_button.configure(state="normal")

    def _on_convert_timeout(self) -> None:
        self._convert_watchdog_id = None
        try:
            self.convert_button.configure(state="normal")
        except Exception:
            pass
        self._set_status("status.convert_timeout", error=True)

    def _cancel_convert_watchdog(self) -> None:
        if self._convert_watchdog_id is not None:
            try:
                self.root.after_cancel(self._convert_watchdog_id)
            except Exception:
                pass
            self._convert_watchdog_id = None

    def _dump_fh6(self) -> None:
        target_path = filedialog.asksaveasfilename(
            title=self.tr("dialog.dump_save_title"),
            defaultextension=".json",
            initialfile="fh6_dump.json",
            filetypes=[
                (self.tr("filetype.json"), "*.json"),
                (self.tr("filetype.all"), "*.*"),
            ],
        )
        if not target_path:
            self._set_status("status.cancelled")
            return

        self._dump_cancel.clear()
        self.dump_button.configure(state="disabled")
        self._set_status("status.dump_started")

        layer_count: Optional[int] = None
        count_text = self.layer_count_var.get().strip()
        if count_text:
            try:
                layer_count = int(count_text)
            except ValueError:
                messagebox.showerror(self.tr("dialog.error_title"), self.tr("dialog.error_body", error=self.tr("dump.layer_count_invalid")))
                self.dump_button.configure(state="normal")
                return
            self.config["layer_count"] = count_text
            save_config(self.config)

        def worker() -> None:
            log_path = config_dir() / "fh6_dump_debug.log"

            def write_log(message: str) -> None:
                try:
                    with open(log_path, "a", encoding="utf-8") as handle:
                        handle.write(message + "\n")
                except Exception:  # noqa: BLE001
                    pass

            try:
                def on_progress(message: str) -> None:
                    write_log(message)
                    self.ui_queue.put(("dump_progress", message))

                payload = fh6_dump.dump_fh6(
                    timeout=180.0, count=layer_count, on_progress=on_progress, cancel_event=self._dump_cancel,
                )
                core.dump_fh6_json(target_path, payload)
                write_log(f"导出成功：{target_path}，图层数 {len(payload.get('shapes', []))}")
                self.ui_queue.put(("dump_success", payload, target_path))
            except Exception as exc:  # noqa: BLE001 - 需要捕获所有异常并弹窗
                write_log(f"导出失败：{exc}")
                try:
                    traceback.print_exc()
                except Exception:  # noqa: BLE001 - windowed 打包下 stderr 可能不可用
                    pass
                self.ui_queue.put(("dump_failure", exc))

        threading.Thread(target=worker, daemon=True).start()
        self._dump_watchdog_id = self.root.after(185000, self._on_dump_timeout)

    def _on_dump_success(self, payload: dict, target_path: str) -> None:
        try:
            count = len(payload.get("shapes", []))
            messagebox.showinfo(
                self.tr("dialog.dump_success_title"),
                self.tr("dialog.dump_success_body", count=count, path=target_path),
            )
            self._set_status("status.dump_done", {"count": count})
            self._load_file(target_path)
        finally:
            self._cancel_dump_watchdog()
            self.dump_button.configure(state="normal")

    def _on_dump_failure(self, exc: Exception) -> None:
        try:
            if self._dump_cancel.is_set():
                self._set_status("status.dump_cancelled", error=True)
            else:
                text = str(exc) or exc.__class__.__name__
                messagebox.showerror(self.tr("dialog.error_title"), self.tr("dialog.error_body", error=text))
                self._set_status("status.dump_failed", error=True)
        finally:
            self._cancel_dump_watchdog()
            self.dump_button.configure(state="normal")

    def _on_dump_timeout(self) -> None:
        self._dump_watchdog_id = None
        try:
            self.dump_button.configure(state="normal")
        except Exception:
            pass
        self._set_status("status.dump_timeout", error=True)

    def _cancel_dump_watchdog(self) -> None:
        if self._dump_watchdog_id is not None:
            try:
                self.root.after_cancel(self._dump_watchdog_id)
            except Exception:
                pass
            self._dump_watchdog_id = None

    # ---------------- 辅助 ----------------

    def _set_warnings(self, warnings: list[tuple[str, dict]]) -> None:
        self._current_warnings = list(warnings)
        self._relayout()

    def _render_warnings(self) -> None:
        self._relayout()

    def _set_status(self, code: str, params: dict | None = None, error: bool = False) -> None:
        self._status_state = (code, params or {}, error)
        if hasattr(self, "canvas"):
            self._relayout()

    def _poll_ui_queue(self) -> None:
        """主线程轮询 worker 线程放入的 UI 消息，避免跨线程调用 Tk。"""
        try:
            while True:
                message = self.ui_queue.get_nowait()
                kind = message[0]
                if kind == "convert_success":
                    self._on_convert_success(message[1], message[2])
                elif kind == "convert_failure":
                    self._on_convert_failure(message[1])
                elif kind == "dump_progress":
                    self._set_status("status.dump_progress", {"message": message[1]})
                elif kind == "dump_success":
                    self._on_dump_success(message[1], message[2])
                elif kind == "dump_failure":
                    self._on_dump_failure(message[1])
        except queue.Empty:
            pass
        if self.root.winfo_exists():
            self.root.after(100, self._poll_ui_queue)

    def _refresh(self) -> None:
        """中断正在进行的导出，并复位按钮与状态（保留已载入文件）。"""
        self._dump_cancel.set()
        if self._convert_watchdog_id is not None:
            try:
                self.root.after_cancel(self._convert_watchdog_id)
            except Exception:
                pass
        if self._dump_watchdog_id is not None:
            try:
                self.root.after_cancel(self._dump_watchdog_id)
            except Exception:
                pass
        self._convert_watchdog_id = None
        self._dump_watchdog_id = None
        try:
            self.convert_button.configure(state="normal")
        except Exception:
            pass
        try:
            self.dump_button.configure(state="normal")
        except Exception:
            pass
        self._set_status("status.refreshed")

    def _set_window_icon(self) -> None:
        try:
            icon_path = self._resource_path("assets/app.ico")
            if Path(icon_path).is_file():
                self.root.iconbitmap(icon_path)
        except Exception:
            pass

    @staticmethod
    def _resource_path(name: str) -> str:
        base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base, name)


def main() -> None:
    if "--cli" in sys.argv:
        # 命令行模式：ForzaJSONConverter.exe --cli <源文件> <目标文件> [--lang zh|en|ja|ko] [--triangle 0.59]
        try:
            args = sys.argv[sys.argv.index("--cli") + 1:]
            triangle_scale = 0.59
            positional = []
            i = 0
            while i < len(args):
                a = args[i]
                if a == "--lang" and i + 1 < len(args):
                    if args[i + 1] in i18n.LANG_CODES:
                        i18n.set_language(args[i + 1])
                    i += 2
                elif a == "--triangle" and i + 1 < len(args):
                    triangle_scale = float(args[i + 1])
                    i += 2
                else:
                    positional.append(a)
                    i += 1
            source, target = positional[0], positional[1]
            detection = core.detect_format(core.load_json(source))
            direction = "fh6_native_to_fh5" if detection.format_name == "fh6_native" else "fh6_to_fh5"
            result = core.convert_file(source, target, direction, triangle_scale)
            print(
                f"[OK] {result.source_format} -> {result.target_format}: "
                f"{result.shape_count} shapes -> {target}"
            )
            for warning in core.render_warnings(result.warnings):
                print(f"[WARN] {warning}")
        except Exception as exc:  # noqa: BLE001
            if isinstance(exc, core.FormatError):
                print(f"[ERROR] {i18n.get(exc.code, **exc.params)}", file=sys.stderr)
            else:
                print(f"[ERROR] {exc}", file=sys.stderr)
            print(f"[ARGS] {sys.argv!r}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    enable_dpi_awareness()
    if TkinterDnD is not None:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    root.withdraw()
    ConverterApp(root)
    root.deiconify()
    root.mainloop()


if __name__ == "__main__":
    main()
