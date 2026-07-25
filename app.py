"""123Mark 主窗口。"""
from __future__ import annotations

import os
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageDraw, ImageTk

from config import AppConfig
from engine import FONT_SIZE_OPTIONS, POSITION_PRESETS, PRESET_COLORS, get_rainbow_color, process_image
from favorites import FavoritesManager
from version import APP_DISPLAY_NAME, APP_VERSION


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff", ".ico"}
FORMAT_EXTENSION = {
    "JPEG": ".jpg",
    "PNG": ".png",
    "BMP": ".bmp",
    "WebP": ".webp",
}


class WatermarkApp:
    BG = "#F4F2ED"
    SURFACE = "#FFFFFF"
    INK = "#18202B"
    MUTED = "#69717D"
    LINE = "#D9D7D1"
    ACCENT = "#E33D24"
    ACCENT_HOVER = "#C9321D"
    SOFT = "#ECE9E2"
    PREVIEW_BG = "#202832"

    def __init__(self, root):
        self.root = root
        self.config = AppConfig()
        self.favorites = FavoritesManager()
        self.image_files: list[str] = []
        self.preview_photo = None
        self._preview_full = None
        self._preview_after_id = None
        self._tree_path_by_id = {}
        self._processing = False
        self._closing = False
        self._in_tray = False
        self.tray_icon = None
        self.tray_thread = None

        self._init_variables()
        self._configure_window()
        self._configure_theme()
        self._build_ui()
        self._load_config()
        self._bind_shortcuts()
        self._enable_drag_drop()
        self._on_mode_change()
        self._on_tile_toggle()

    def _init_variables(self):
        self.watermark_mode = tk.StringVar(value="text")
        self.watermark_text = tk.StringVar(value="仅限本项目投标使用")
        self.selected_color = tk.StringVar(value="白色")
        self.selected_font_size = tk.StringVar(value="48")
        self.selected_position = tk.StringVar(value="右下")
        self.opacity_var = tk.IntVar(value=50)
        self.rotation_var = tk.IntVar(value=0)
        self.margin_var = tk.IntVar(value=20)
        self.tile_var = tk.BooleanVar(value=False)
        self.tile_rows_var = tk.IntVar(value=3)
        self.tile_cols_var = tk.IntVar(value=3)
        self.rainbow_var = tk.BooleanVar(value=False)
        self.output_format_var = tk.StringVar(value="保持原格式")
        self.output_quality_var = tk.IntVar(value=95)
        self.output_dir_var = tk.StringVar(value="")
        self.watermark_image_path = tk.StringVar(value="")
        self.watermark_image_size_var = tk.StringVar(value="100%")
        self.topmost_var = tk.BooleanVar(value=False)
        self.count_text = tk.StringVar(value="尚未导入图片")
        self.status_text = tk.StringVar(value="就绪")

    def _configure_window(self):
        self.root.title(f"{APP_DISPLAY_NAME}  v{APP_VERSION}")
        geometry = self.config.get("window_geometry", "1180x760")
        if not isinstance(geometry, str) or "x" not in geometry:
            geometry = "1180x760"
        self.root.geometry(geometry)
        self.root.minsize(980, 640)
        self.root.configure(bg=self.BG)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _configure_theme(self):
        self.root.option_add("*Font", ("Microsoft YaHei UI", 9))
        self.root.option_add("*TCombobox*Listbox.font", ("Microsoft YaHei UI", 9))
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(".", background=self.BG, foreground=self.INK, font=("Microsoft YaHei UI", 9))
        style.configure("TFrame", background=self.BG)
        style.configure("Surface.TFrame", background=self.SURFACE)
        style.configure("TLabel", background=self.BG, foreground=self.INK)
        style.configure("Surface.TLabel", background=self.SURFACE, foreground=self.INK)
        style.configure("Muted.TLabel", background=self.BG, foreground=self.MUTED)
        style.configure("SurfaceMuted.TLabel", background=self.SURFACE, foreground=self.MUTED)
        style.configure("Section.TLabel", background=self.SURFACE, foreground=self.INK, font=("Microsoft YaHei UI", 10, "bold"))
        style.configure("Step.TLabel", background=self.SURFACE, foreground=self.ACCENT, font=("Microsoft YaHei UI", 8, "bold"))
        style.configure("TButton", padding=(11, 7), relief="flat", borderwidth=0, background=self.SOFT, foreground=self.INK)
        style.map("TButton", background=[("active", "#E2DED5"), ("pressed", "#D7D2C7")])
        style.configure("Primary.TButton", padding=(16, 9), background=self.ACCENT, foreground="#FFFFFF", font=("Microsoft YaHei UI", 9, "bold"))
        style.map("Primary.TButton", background=[("active", self.ACCENT_HOVER), ("pressed", "#A92919"), ("disabled", "#C9A49C")])
        style.configure("Quiet.TButton", padding=(9, 6), background=self.SURFACE, foreground=self.MUTED)
        style.map("Quiet.TButton", foreground=[("active", self.INK)], background=[("active", self.SOFT)])
        style.configure("Mode.TRadiobutton", background=self.SURFACE, padding=(10, 7), indicatorcolor=self.SURFACE)
        style.map("Mode.TRadiobutton", background=[("selected", self.INK), ("active", self.SOFT)], foreground=[("selected", "#FFFFFF")])
        style.configure("TCheckbutton", background=self.SURFACE, foreground=self.INK)
        style.map("TCheckbutton", background=[("active", self.SURFACE)])
        style.configure("TEntry", fieldbackground="#FBFAF7", bordercolor=self.LINE, lightcolor=self.LINE, darkcolor=self.LINE, padding=7)
        style.configure("TCombobox", fieldbackground="#FBFAF7", bordercolor=self.LINE, arrowsize=14, padding=5)
        style.map("TCombobox", fieldbackground=[("readonly", "#FBFAF7")], selectbackground=[("readonly", "#FBFAF7")], selectforeground=[("readonly", self.INK)])
        style.configure("TSpinbox", fieldbackground="#FBFAF7", bordercolor=self.LINE, padding=5)
        style.configure("Treeview", background=self.SURFACE, fieldbackground=self.SURFACE, foreground=self.INK, rowheight=30, borderwidth=0)
        style.map("Treeview", background=[("selected", "#F7D9D3")], foreground=[("selected", self.INK)])
        style.configure("Treeview.Heading", background="#EEEAE3", foreground=self.MUTED, relief="flat", padding=(7, 7), font=("Microsoft YaHei UI", 8, "bold"))
        style.map("Treeview.Heading", background=[("active", "#E5E0D7")])
        style.configure("Horizontal.TProgressbar", troughcolor="#DDD9D1", background=self.ACCENT, borderwidth=0, thickness=5)
        style.configure("TScale", background=self.SURFACE, troughcolor="#DDD9D1")

    def _build_ui(self):
        self._build_header()
        self._build_actionbar()

        shell = tk.PanedWindow(
            self.root,
            orient=tk.HORIZONTAL,
            bg=self.BG,
            bd=0,
            sashwidth=7,
            sashrelief=tk.FLAT,
            opaqueresize=True,
        )
        shell.pack(fill=tk.BOTH, expand=True, padx=18, pady=(16, 10))

        left = ttk.Frame(shell, style="Surface.TFrame")
        right = ttk.Frame(shell, style="Surface.TFrame", width=410)
        shell.add(left, minsize=520, stretch="always")
        shell.add(right, minsize=365, stretch="never")
        self.main_paned = shell

        self._build_workspace(left)
        self._build_settings(right)

    def _build_header(self):
        header = tk.Frame(self.root, bg=self.INK, height=76)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        brand = tk.Frame(header, bg=self.INK)
        brand.pack(side=tk.LEFT, fill=tk.Y, padx=(22, 0))
        tk.Label(brand, text="123Mark", bg=self.INK, fg="#FFFFFF", font=("Segoe UI", 20, "bold")).pack(anchor="w", pady=(12, 0))
        tk.Label(brand, text="投标图片水印 · 本地处理，不上传图片", bg=self.INK, fg="#AEB7C3", font=("Microsoft YaHei UI", 9)).pack(anchor="w")

        meta = tk.Frame(header, bg=self.INK)
        meta.pack(side=tk.RIGHT, fill=tk.Y, padx=18)
        tk.Label(meta, text=f"v{APP_VERSION}", bg=self.INK, fg="#98A3B0", font=("Consolas", 9)).pack(side=tk.RIGHT, padx=(14, 0))
        topmost = tk.Checkbutton(
            meta,
            text="窗口置顶",
            variable=self.topmost_var,
            command=self._toggle_topmost,
            bg=self.INK,
            fg="#E8EDF2",
            activebackground=self.INK,
            activeforeground="#FFFFFF",
            selectcolor=self.INK,
            bd=0,
            highlightthickness=0,
            font=("Microsoft YaHei UI", 9),
        )
        topmost.pack(side=tk.RIGHT)

    def _build_workspace(self, parent):
        toolbar = ttk.Frame(parent, style="Surface.TFrame", padding=(14, 12))
        toolbar.pack(fill=tk.X)
        title_area = ttk.Frame(toolbar, style="Surface.TFrame")
        title_area.pack(side=tk.LEFT)
        ttk.Label(title_area, text="步骤 1", style="Step.TLabel").pack(anchor="w")
        ttk.Label(title_area, text="导入待处理图片", style="Section.TLabel").pack(anchor="w")

        ttk.Button(toolbar, text="添加图片", style="Primary.TButton", command=self._add_images).pack(side=tk.RIGHT, padx=(6, 0))
        ttk.Button(toolbar, text="添加文件夹", command=self._add_folder).pack(side=tk.RIGHT, padx=(6, 0))

        list_wrap = ttk.Frame(parent, style="Surface.TFrame", padding=(14, 0, 14, 10))
        list_wrap.pack(fill=tk.BOTH, expand=True)

        columns = ("index", "filename", "dimensions", "filesize", "format")
        self.image_tree = ttk.Treeview(list_wrap, columns=columns, show="headings", selectmode="extended", height=6)
        headings = {
            "index": ("#", 42, tk.CENTER),
            "filename": ("文件名", 255, tk.W),
            "dimensions": ("尺寸", 90, tk.CENTER),
            "filesize": ("大小", 70, tk.E),
            "format": ("格式", 60, tk.CENTER),
        }
        for column, (text, width, anchor) in headings.items():
            self.image_tree.heading(column, text=text, anchor=anchor)
            self.image_tree.column(column, width=width, minwidth=width if column != "filename" else 120, anchor=anchor, stretch=column == "filename")
        scrollbar = ttk.Scrollbar(list_wrap, orient=tk.VERTICAL, command=self.image_tree.yview)
        self.image_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.image_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.image_tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        list_footer = ttk.Frame(parent, style="Surface.TFrame", padding=(14, 0, 14, 10))
        list_footer.pack(fill=tk.X)
        ttk.Label(list_footer, textvariable=self.count_text, style="SurfaceMuted.TLabel").pack(side=tk.LEFT)
        ttk.Button(list_footer, text="移除选中", style="Quiet.TButton", command=self._remove_selected).pack(side=tk.RIGHT)
        ttk.Button(list_footer, text="清空", style="Quiet.TButton", command=self._clear_images).pack(side=tk.RIGHT, padx=(0, 4))

        preview_head = ttk.Frame(parent, style="Surface.TFrame", padding=(14, 4, 14, 8))
        preview_head.pack(fill=tk.X)
        ttk.Label(preview_head, text="效果预览", style="Section.TLabel").pack(side=tk.LEFT)
        self.preview_name_label = ttk.Label(preview_head, text="导入图片后可预览", style="SurfaceMuted.TLabel")
        self.preview_name_label.pack(side=tk.RIGHT)

        preview_wrap = tk.Frame(parent, bg=self.PREVIEW_BG, height=190)
        preview_wrap.pack(fill=tk.BOTH, padx=14, pady=(0, 14))
        preview_wrap.pack_propagate(False)
        self.preview_label = tk.Label(
            preview_wrap,
            text="将图片拖到此窗口\n支持 JPG / PNG / BMP / WebP / TIFF / ICO",
            bg=self.PREVIEW_BG,
            fg="#AEB7C3",
            font=("Microsoft YaHei UI", 10),
            justify=tk.CENTER,
            cursor="hand2",
        )
        self.preview_label.pack(fill=tk.BOTH, expand=True)
        self.preview_label.bind("<Button-1>", self._zoom_preview)
        preview_wrap.bind("<Configure>", self._on_preview_resize)

    def _build_settings(self, parent):
        heading = ttk.Frame(parent, style="Surface.TFrame", padding=(16, 12, 16, 10))
        heading.pack(fill=tk.X)
        ttk.Label(heading, text="步骤 2", style="Step.TLabel").pack(anchor="w")
        ttk.Label(heading, text="设置水印与输出", style="Section.TLabel").pack(anchor="w")

        canvas = tk.Canvas(parent, bg=self.SURFACE, bd=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        self.settings_frame = ttk.Frame(canvas, style="Surface.TFrame", padding=(16, 0, 14, 18))
        window_item = canvas.create_window((0, 0), window=self.settings_frame, anchor="nw")
        self.settings_frame.bind("<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda event: canvas.itemconfigure(window_item, width=event.width))
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.bind("<Enter>", lambda _event: canvas.bind_all("<MouseWheel>", self._scroll_settings))
        canvas.bind("<Leave>", lambda _event: canvas.unbind_all("<MouseWheel>"))
        self.settings_canvas = canvas

        self._build_mode_section()
        self._build_text_section()
        self._build_image_section()
        self._build_color_section()
        self._build_style_section()
        self._build_position_section()
        self._build_output_section()

    def _section(self, title):
        frame = ttk.Frame(self.settings_frame, style="Surface.TFrame")
        frame.pack(fill=tk.X, pady=(0, 17))
        ttk.Label(frame, text=title, style="Section.TLabel").pack(anchor="w", pady=(0, 8))
        return frame

    def _build_mode_section(self):
        frame = self._section("水印类型")
        mode_row = ttk.Frame(frame, style="Surface.TFrame")
        mode_row.pack(fill=tk.X)
        ttk.Radiobutton(mode_row, text="文本水印", value="text", variable=self.watermark_mode, command=self._on_mode_change, style="Mode.TRadiobutton").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 3))
        ttk.Radiobutton(mode_row, text="图片水印", value="image", variable=self.watermark_mode, command=self._on_mode_change, style="Mode.TRadiobutton").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(3, 0))

    def _build_text_section(self):
        self.text_settings = self._section("水印内容")
        self.text_entry = ttk.Entry(self.text_settings, textvariable=self.watermark_text)
        self.text_entry.pack(fill=tk.X)
        self.text_entry.bind("<Return>", lambda _event: self._preview())

        fav_row = ttk.Frame(self.text_settings, style="Surface.TFrame")
        fav_row.pack(fill=tk.X, pady=(7, 0))
        self.fav_combo = ttk.Combobox(fav_row, state="readonly")
        self.fav_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.fav_combo.bind("<<ComboboxSelected>>", self._on_favorite_selected)
        ttk.Button(fav_row, text="收藏", style="Quiet.TButton", command=self._add_favorite).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(fav_row, text="管理", style="Quiet.TButton", command=self._manage_favorites).pack(side=tk.LEFT)
        self._refresh_favorite_combo()

    def _build_image_section(self):
        self.image_settings = self._section("水印图片")
        path_row = ttk.Frame(self.image_settings, style="Surface.TFrame")
        path_row.pack(fill=tk.X)
        ttk.Entry(path_row, textvariable=self.watermark_image_path).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(path_row, text="选择", command=self._select_watermark_image).pack(side=tk.LEFT, padx=(6, 0))
        scale_row = ttk.Frame(self.image_settings, style="Surface.TFrame")
        scale_row.pack(fill=tk.X, pady=(8, 0))
        ttk.Label(scale_row, text="相对原图尺寸", style="SurfaceMuted.TLabel").pack(side=tk.LEFT)
        ttk.Combobox(
            scale_row,
            textvariable=self.watermark_image_size_var,
            values=["25%", "33%", "50%", "75%", "100%", "150%", "200%"],
            state="readonly",
            width=8,
        ).pack(side=tk.RIGHT)

    def _build_color_section(self):
        self.color_section = self._section("文字颜色")
        grid = tk.Frame(self.color_section, bg=self.SURFACE)
        grid.pack(fill=tk.X)
        self.color_buttons = {}
        for index, color_name in enumerate(PRESET_COLORS):
            row, column = divmod(index, 5)
            rgb = PRESET_COLORS[color_name]
            button = tk.Canvas(grid, width=58, height=34, bg=self.SURFACE, highlightthickness=1, highlightbackground=self.LINE, cursor="hand2")
            button.grid(row=row, column=column, padx=(0, 6), pady=(0, 6), sticky="ew")
            grid.grid_columnconfigure(column, weight=1)
            if color_name == "彩虹":
                for x in range(42):
                    rc = get_rainbow_color(x / 41)
                    button.create_line(8 + x, 7, 8 + x, 21, fill=f"#{rc[0]:02x}{rc[1]:02x}{rc[2]:02x}")
            else:
                fill = f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
                outline = "#C7C4BD" if color_name in {"白色", "黄色"} else fill
                button.create_rectangle(8, 7, 50, 21, fill=fill, outline=outline)
            button.create_text(29, 28, text=color_name, fill=self.MUTED, font=("Microsoft YaHei UI", 7))
            button.bind("<Button-1>", lambda _event, name=color_name: self._on_color_click(name))
            self.color_buttons[color_name] = button
        self._highlight_color("白色")

    def _build_style_section(self):
        self.style_section = self._section("样式")
        self.font_row = ttk.Frame(self.style_section, style="Surface.TFrame")
        self.font_row.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(self.font_row, text="字号", style="SurfaceMuted.TLabel").pack(side=tk.LEFT)
        ttk.Combobox(
            self.font_row,
            textvariable=self.selected_font_size,
            values=[str(value) for value in FONT_SIZE_OPTIONS],
            width=8,
        ).pack(side=tk.RIGHT)

        self.opacity_row, self.opacity_value = self._build_slider_row(
            self.style_section, "不透明度", self.opacity_var, 1, 100, "50%", self._update_opacity_label
        )
        self.rotation_row, self.rotation_value = self._build_slider_row(
            self.style_section, "旋转角度", self.rotation_var, -180, 180, "0°", self._update_rotation_label
        )

    def _build_slider_row(self, parent, label, variable, start, end, value_text, command):
        row = ttk.Frame(parent, style="Surface.TFrame")
        row.pack(fill=tk.X, pady=4)
        ttk.Label(row, text=label, style="SurfaceMuted.TLabel", width=9).pack(side=tk.LEFT)
        value_label = ttk.Label(row, text=value_text, style="SurfaceMuted.TLabel")
        value_label.pack(side=tk.RIGHT)
        ttk.Scale(row, from_=start, to=end, variable=variable, orient=tk.HORIZONTAL, command=command).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 8))
        return row, value_label

    def _build_position_section(self):
        frame = self._section("位置与平铺")
        body = ttk.Frame(frame, style="Surface.TFrame")
        body.pack(fill=tk.X)

        position_grid = tk.Frame(body, bg=self.SURFACE)
        position_grid.pack(side=tk.LEFT, padx=(0, 16))
        self.position_buttons = {}
        positions = list(POSITION_PRESETS)
        for index, name in enumerate(positions):
            button = tk.Button(
                position_grid,
                text="●",
                width=3,
                height=1,
                relief=tk.FLAT,
                bd=0,
                bg=self.SOFT,
                fg="#9BA2AA",
                activebackground="#DED9D0",
                cursor="hand2",
                command=lambda value=name: self._select_position(value),
            )
            button.grid(row=index // 3, column=index % 3, padx=2, pady=2)
            self.position_buttons[name] = button
        self._highlight_position()

        controls = ttk.Frame(body, style="Surface.TFrame")
        controls.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ttk.Checkbutton(controls, text="按行列平铺", variable=self.tile_var, command=self._on_tile_toggle).pack(anchor="w")
        self.margin_row = ttk.Frame(controls, style="Surface.TFrame")
        self.margin_row.pack(fill=tk.X, pady=(8, 0))
        ttk.Label(self.margin_row, text="边距", style="SurfaceMuted.TLabel").pack(side=tk.LEFT)
        ttk.Spinbox(self.margin_row, from_=0, to=500, textvariable=self.margin_var, width=7).pack(side=tk.RIGHT)

        self.tile_grid_frame = ttk.Frame(controls, style="Surface.TFrame")
        ttk.Label(self.tile_grid_frame, text="行", style="SurfaceMuted.TLabel").pack(side=tk.LEFT)
        self.rows_spin = ttk.Spinbox(self.tile_grid_frame, from_=1, to=20, textvariable=self.tile_rows_var, width=5)
        self.rows_spin.pack(side=tk.LEFT, padx=(5, 12))
        ttk.Label(self.tile_grid_frame, text="列", style="SurfaceMuted.TLabel").pack(side=tk.LEFT)
        self.cols_spin = ttk.Spinbox(self.tile_grid_frame, from_=1, to=20, textvariable=self.tile_cols_var, width=5)
        self.cols_spin.pack(side=tk.LEFT, padx=(5, 0))

    def _build_output_section(self):
        frame = self._section("输出")
        path_row = ttk.Frame(frame, style="Surface.TFrame")
        path_row.pack(fill=tk.X)
        self.output_combo = ttk.Combobox(path_row, textvariable=self.output_dir_var)
        self.output_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(path_row, text="选择", command=self._select_output_dir).pack(side=tk.LEFT, padx=(6, 0))

        format_row = ttk.Frame(frame, style="Surface.TFrame")
        format_row.pack(fill=tk.X, pady=(9, 0))
        ttk.Label(format_row, text="格式", style="SurfaceMuted.TLabel").pack(side=tk.LEFT)
        ttk.Combobox(
            format_row,
            textvariable=self.output_format_var,
            values=["保持原格式", "JPEG", "PNG", "BMP", "WebP"],
            width=12,
            state="readonly",
        ).pack(side=tk.LEFT, padx=(8, 14))
        ttk.Label(format_row, text="JPEG 质量", style="SurfaceMuted.TLabel").pack(side=tk.LEFT)
        self.quality_value = ttk.Label(format_row, text="95", style="SurfaceMuted.TLabel", width=3)
        self.quality_value.pack(side=tk.RIGHT)

        quality_row = ttk.Frame(frame, style="Surface.TFrame")
        quality_row.pack(fill=tk.X, pady=(5, 0))
        ttk.Scale(
            quality_row,
            from_=10,
            to=100,
            variable=self.output_quality_var,
            orient=tk.HORIZONTAL,
            command=lambda _value: self.quality_value.configure(text=str(round(self.output_quality_var.get()))),
        ).pack(fill=tk.X)
        ttk.Label(frame, text="未指定目录时，将输出到首张图片旁的 output 文件夹。", style="SurfaceMuted.TLabel", wraplength=340).pack(anchor="w", pady=(6, 0))

    def _build_actionbar(self):
        bar = tk.Frame(self.root, bg="#ECE9E2", height=62, highlightthickness=1, highlightbackground="#D4D0C8")
        bar.pack(fill=tk.X, side=tk.BOTTOM)
        bar.pack_propagate(False)

        status = tk.Frame(bar, bg="#ECE9E2")
        status.pack(side=tk.LEFT, fill=tk.Y, padx=18)
        tk.Label(status, textvariable=self.status_text, bg="#ECE9E2", fg=self.INK, anchor="w", font=("Microsoft YaHei UI", 9)).pack(anchor="w", pady=(10, 2))
        self.progress = ttk.Progressbar(status, mode="determinate", length=280)
        self.progress.pack(anchor="w")

        actions = tk.Frame(bar, bg="#ECE9E2")
        actions.pack(side=tk.RIGHT, fill=tk.Y, padx=18, pady=10)
        self.preview_button = ttk.Button(actions, text="预览效果", command=self._preview)
        self.preview_button.pack(side=tk.LEFT, padx=(0, 8))
        self.process_button = ttk.Button(actions, text="开始批量处理", style="Primary.TButton", command=self._batch_process)
        self.process_button.pack(side=tk.LEFT)

    def _bind_shortcuts(self):
        self.root.bind("<Control-o>", lambda _event: self._add_images())
        self.root.bind("<Control-Return>", lambda _event: self._batch_process())
        self.root.bind("<F5>", lambda _event: self._preview())
        self.root.bind("<Delete>", lambda _event: self._remove_selected())

    def _scroll_settings(self, event):
        self.settings_canvas.yview_scroll(int(-event.delta / 120), "units")

    # -------------------- 图片导入 --------------------

    def _enable_drag_drop(self):
        try:
            from tkinterdnd2 import DND_FILES

            if hasattr(self.root, "drop_target_register"):
                self.root.drop_target_register(DND_FILES)
                self.root.dnd_bind("<<Drop>>", self._on_dnd_drop)
                return
        except (ImportError, tk.TclError):
            pass

    def _on_dnd_drop(self, event):
        self._process_dropped_files(self.root.tk.splitlist(event.data))

    def _process_dropped_files(self, files):
        candidates = []
        for raw_path in files:
            path = Path(str(raw_path).strip("{}"))
            if path.is_dir():
                candidates.extend(self._find_images(path))
            else:
                candidates.append(path)
        added, invalid = self._add_paths(candidates)
        self.status_text.set(f"已导入 {added} 张图片" + (f"，忽略 {invalid} 个无效文件" if invalid else ""))

    def _find_images(self, folder):
        try:
            return sorted(path for path in folder.iterdir() if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS)
        except OSError:
            return []

    def _add_images(self):
        files = filedialog.askopenfilenames(
            title="选择待加水印的图片",
            filetypes=[
                ("支持的图片", "*.jpg *.jpeg *.png *.bmp *.webp *.tif *.tiff *.ico"),
                ("所有文件", "*.*"),
            ],
        )
        if files:
            added, invalid = self._add_paths([Path(path) for path in files])
            self.status_text.set(f"已导入 {added} 张图片" + (f"，忽略 {invalid} 个无效文件" if invalid else ""))

    def _add_folder(self):
        folder = filedialog.askdirectory(title="选择图片文件夹")
        if folder:
            paths = self._find_images(Path(folder))
            added, invalid = self._add_paths(paths)
            self.status_text.set(f"从文件夹导入 {added} 张图片" + (f"，忽略 {invalid} 个无效文件" if invalid else ""))

    def _add_paths(self, paths):
        known = {os.path.normcase(os.path.abspath(path)) for path in self.image_files}
        added = invalid = 0
        for path in paths:
            normalized = os.path.normcase(os.path.abspath(str(path)))
            if normalized in known:
                continue
            if Path(path).suffix.lower() not in SUPPORTED_EXTENSIONS:
                invalid += 1
                continue
            try:
                with Image.open(path) as image:
                    image.verify()
                self.image_files.append(os.path.abspath(str(path)))
                known.add(normalized)
                added += 1
            except (OSError, ValueError):
                invalid += 1
        if added:
            self._refresh_image_list(select_last=True)
            if len(self.image_files) == added:
                self.root.after_idle(self._preview)
        return added, invalid

    def _refresh_image_list(self, select_last=False):
        for item in self.image_tree.get_children():
            self.image_tree.delete(item)
        self._tree_path_by_id.clear()
        for index, path in enumerate(self.image_files, start=1):
            try:
                with Image.open(path) as image:
                    dimensions = f"{image.width} × {image.height}"
                    image_format = image.format or Path(path).suffix[1:].upper()
                file_size = self._format_file_size(Path(path).stat().st_size)
            except OSError:
                dimensions, image_format, file_size = "无法读取", "—", "—"
            item_id = f"image_{index}"
            self._tree_path_by_id[item_id] = path
            self.image_tree.insert("", tk.END, iid=item_id, values=(index, Path(path).name, dimensions, file_size, image_format))
        if self.image_files:
            self.count_text.set(f"共 {len(self.image_files)} 张 · 可多选移除")
            if select_last:
                item = f"image_{len(self.image_files)}"
                self.image_tree.selection_set(item)
                self.image_tree.see(item)
        else:
            self.count_text.set("尚未导入图片")
            self._clear_preview()

    @staticmethod
    def _format_file_size(size):
        if size < 1024:
            return f"{size} B"
        if size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        return f"{size / (1024 * 1024):.1f} MB"

    def _current_image_path(self):
        selection = self.image_tree.selection()
        if selection:
            return self._tree_path_by_id.get(selection[0])
        return self.image_files[0] if self.image_files else None

    def _on_tree_select(self, _event=None):
        if self._current_image_path():
            self._schedule_preview()

    def _remove_selected(self):
        selection = self.image_tree.selection()
        if not selection:
            return
        selected_paths = {self._tree_path_by_id.get(item) for item in selection}
        self.image_files = [path for path in self.image_files if path not in selected_paths]
        self._refresh_image_list()
        self.status_text.set(f"已移除 {len(selected_paths)} 张图片")
        if self.image_files:
            self.image_tree.selection_set("image_1")
            self._schedule_preview()

    def _clear_images(self):
        if self.image_files and messagebox.askyesno("清空图片", "确定移除列表中的全部图片吗？\n原始文件不会被删除。", parent=self.root):
            count = len(self.image_files)
            self.image_files.clear()
            self._refresh_image_list()
            self.status_text.set(f"已从列表移除 {count} 张图片")

    # -------------------- 设置交互 --------------------

    def _on_mode_change(self):
        if self.watermark_mode.get() == "text":
            self.image_settings.pack_forget()
            self.text_settings.pack(fill=tk.X, pady=(0, 17), before=self.color_section)
            self.color_section.pack(fill=tk.X, pady=(0, 17), before=self.style_section)
            self.font_row.pack(fill=tk.X, pady=(0, 8), before=self.opacity_row)
        else:
            self.text_settings.pack_forget()
            self.color_section.pack_forget()
            self.image_settings.pack(fill=tk.X, pady=(0, 17), before=self.style_section)
            self.font_row.pack_forget()
        self._schedule_preview()

    def _on_color_click(self, color_name):
        self.selected_color.set(color_name)
        self.rainbow_var.set(color_name == "彩虹")
        self._highlight_color(color_name)
        self._schedule_preview()

    def _highlight_color(self, selected):
        for name, canvas in self.color_buttons.items():
            canvas.configure(
                highlightbackground=self.ACCENT if name == selected else self.LINE,
                highlightcolor=self.ACCENT if name == selected else self.LINE,
                highlightthickness=2 if name == selected else 1,
            )

    def _select_position(self, position):
        self.selected_position.set(position)
        self._highlight_position()
        self._schedule_preview()

    def _highlight_position(self):
        for name, button in getattr(self, "position_buttons", {}).items():
            selected = name == self.selected_position.get()
            button.configure(bg=self.ACCENT if selected else self.SOFT, fg="#FFFFFF" if selected else "#9BA2AA")

    def _on_tile_toggle(self):
        if self.tile_var.get():
            self.margin_row.pack_forget()
            self.tile_grid_frame.pack(fill=tk.X, pady=(8, 0))
        else:
            self.tile_grid_frame.pack_forget()
            self.margin_row.pack(fill=tk.X, pady=(8, 0))
        self._schedule_preview()

    def _update_opacity_label(self, *_args):
        self.opacity_value.configure(text=f"{round(self.opacity_var.get())}%")
        self._schedule_preview()

    def _update_rotation_label(self, *_args):
        self.rotation_value.configure(text=f"{round(self.rotation_var.get())}°")
        self._schedule_preview()

    def _select_watermark_image(self):
        path = filedialog.askopenfilename(
            title="选择水印图片",
            filetypes=[("支持的图片", "*.png *.jpg *.jpeg *.bmp *.webp *.ico"), ("所有文件", "*.*")],
        )
        if path:
            self.watermark_image_path.set(path)
            self._schedule_preview()

    def _select_output_dir(self):
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            self.output_dir_var.set(directory)
            self._save_output_history(directory)

    def _save_output_history(self, path):
        history = [item for item in self.config.get("output_dir_history", []) if item != path]
        history.insert(0, path)
        self.config.set("output_dir_history", history[:5])
        self._refresh_output_history()

    def _refresh_output_history(self):
        self.output_combo["values"] = self.config.get("output_dir_history", [])

    def _toggle_topmost(self):
        self.root.attributes("-topmost", self.topmost_var.get())

    def _get_watermark_params(self):
        try:
            font_size = max(1, min(1024, int(self.selected_font_size.get())))
            margin = max(0, min(500, int(self.margin_var.get())))
            rows = max(1, min(20, int(self.tile_rows_var.get())))
            cols = max(1, min(20, int(self.tile_cols_var.get())))
        except (ValueError, tk.TclError) as error:
            raise ValueError("字号、边距、行数和列数必须是有效数字") from error

        params = {
            "mode": self.watermark_mode.get(),
            "position": self.selected_position.get(),
            "opacity": round(self.opacity_var.get() / 100 * 255),
            "rotation": round(self.rotation_var.get()),
            "margin": margin,
            "tile": self.tile_var.get(),
            "tile_rows": rows,
            "tile_cols": cols,
        }
        if params["mode"] == "text":
            text = self.watermark_text.get().strip()
            if not text:
                raise ValueError("请输入水印文本")
            params.update(
                text=text,
                font_size=font_size,
                rainbow=self.rainbow_var.get(),
                color=PRESET_COLORS.get(self.selected_color.get()) or (255, 255, 255),
                font_path=None,
            )
        else:
            path = self.watermark_image_path.get().strip()
            if not path or not Path(path).is_file():
                raise ValueError("请选择有效的水印图片")
            try:
                scale = int(self.watermark_image_size_var.get().rstrip("%"))
            except ValueError as error:
                raise ValueError("图片水印尺寸设置无效") from error
            params.update(image_path=path, image_scale=scale)
        return params

    # -------------------- 收藏 --------------------

    def _refresh_favorite_combo(self):
        values = [item.get("name", item.get("text", "")) for item in self.favorites.get_all()]
        self.fav_combo["values"] = values
        self.fav_combo.set(values[0] if values else "")

    def _on_favorite_selected(self, _event=None):
        favorite = self.favorites.get(self.fav_combo.current())
        if favorite:
            self.watermark_text.set(favorite.get("text", ""))
            self._schedule_preview()

    def _add_favorite(self):
        text = self.watermark_text.get().strip()
        if not text:
            messagebox.showwarning("无法收藏", "请先输入水印文本。", parent=self.root)
            return
        if self.favorites.is_full() and not messagebox.askyesno(
            "收藏已满",
            "收藏最多保留 10 项。继续后会移除最旧的一项。",
            parent=self.root,
        ):
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("添加收藏")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        dialog.configure(bg=self.BG)
        body = ttk.Frame(dialog, padding=18)
        body.pack(fill=tk.BOTH, expand=True)
        ttk.Label(body, text="收藏名称", font=("Microsoft YaHei UI", 10, "bold")).pack(anchor="w")
        name_var = tk.StringVar(value=text[:20])
        entry = ttk.Entry(body, textvariable=name_var, width=36)
        entry.pack(fill=tk.X, pady=(8, 4))
        ttk.Label(body, text=f"内容：{text[:42]}{'…' if len(text) > 42 else ''}", style="Muted.TLabel").pack(anchor="w")

        def confirm():
            self.favorites.add({"name": name_var.get(), "text": text})
            self._refresh_favorite_combo()
            dialog.destroy()
            self.status_text.set("已保存到常用水印")

        buttons = ttk.Frame(body)
        buttons.pack(fill=tk.X, pady=(14, 0))
        ttk.Button(buttons, text="取消", command=dialog.destroy).pack(side=tk.RIGHT)
        ttk.Button(buttons, text="保存", style="Primary.TButton", command=confirm).pack(side=tk.RIGHT, padx=(0, 7))
        dialog.bind("<Return>", lambda _event: confirm())
        dialog.bind("<Escape>", lambda _event: dialog.destroy())
        dialog.update_idletasks()
        self._center_dialog(dialog, 380, 180)
        entry.focus_set()
        entry.selection_range(0, tk.END)

    def _manage_favorites(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("管理常用水印")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg=self.BG)
        body = ttk.Frame(dialog, padding=16)
        body.pack(fill=tk.BOTH, expand=True)
        ttk.Label(body, text="常用水印", font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w")
        ttk.Label(body, text="最多保存 10 项；顺序会同步到下拉列表。", style="Muted.TLabel").pack(anchor="w", pady=(2, 10))
        listbox = tk.Listbox(
            body,
            selectmode=tk.SINGLE,
            bg=self.SURFACE,
            fg=self.INK,
            selectbackground="#F7D9D3",
            selectforeground=self.INK,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=self.LINE,
            font=("Microsoft YaHei UI", 9),
        )
        listbox.pack(fill=tk.BOTH, expand=True)

        def refresh(selected=None):
            listbox.delete(0, tk.END)
            for item in self.favorites.get_all():
                listbox.insert(tk.END, f"{item.get('name', '')}   ·   {item.get('text', '')}")
            if selected is not None and listbox.size():
                listbox.selection_set(max(0, min(selected, listbox.size() - 1)))
            self._refresh_favorite_combo()

        def move(delta):
            selected = listbox.curselection()
            if not selected:
                return
            index = selected[0]
            changed = self.favorites.move_up(index) if delta < 0 else self.favorites.move_down(index)
            if changed:
                refresh(index + delta)

        def remove():
            selected = listbox.curselection()
            if selected:
                self.favorites.remove(selected[0])
                refresh(selected[0])

        buttons = ttk.Frame(body)
        buttons.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(buttons, text="上移", command=lambda: move(-1)).pack(side=tk.LEFT)
        ttk.Button(buttons, text="下移", command=lambda: move(1)).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons, text="删除", command=remove).pack(side=tk.LEFT)
        ttk.Button(buttons, text="完成", style="Primary.TButton", command=dialog.destroy).pack(side=tk.RIGHT)
        refresh()
        dialog.bind("<Escape>", lambda _event: dialog.destroy())
        dialog.update_idletasks()
        self._center_dialog(dialog, 540, 390)

    # -------------------- 预览与导出 --------------------

    def _schedule_preview(self):
        if not self.image_files:
            return
        if self._preview_after_id:
            self.root.after_cancel(self._preview_after_id)
        self._preview_after_id = self.root.after(280, self._preview)

    def _preview(self):
        self._preview_after_id = None
        path = self._current_image_path()
        if not path:
            messagebox.showwarning("无法预览", "请先添加图片。", parent=self.root)
            return
        try:
            params = self._get_watermark_params()
            result = process_image(path, params)
            self._preview_full = result.copy()
            self.preview_name_label.configure(text=Path(path).name)
            self._render_preview()
            self.status_text.set("预览已更新")
        except Exception as error:
            self.status_text.set(f"预览失败：{error}")
            if self.root.focus_displayof() is not None:
                messagebox.showerror("预览失败", str(error), parent=self.root)

    def _render_preview(self):
        if self._preview_full is None:
            return
        width = max(40, self.preview_label.winfo_width() - 28)
        height = max(40, self.preview_label.winfo_height() - 24)
        display = self._preview_full.copy()
        display.thumbnail((width, height), Image.Resampling.LANCZOS)
        self.preview_photo = ImageTk.PhotoImage(display)
        self.preview_label.configure(image=self.preview_photo, text="")

    def _on_preview_resize(self, _event=None):
        if self._preview_after_id:
            return
        if self._preview_full is not None:
            self._preview_after_id = self.root.after(120, self._finish_preview_resize)

    def _finish_preview_resize(self):
        self._preview_after_id = None
        self._render_preview()

    def _clear_preview(self):
        self._preview_full = None
        self.preview_photo = None
        self.preview_name_label.configure(text="导入图片后可预览")
        self.preview_label.configure(
            image="",
            text="将图片拖到此窗口\n支持 JPG / PNG / BMP / WebP / TIFF / ICO",
        )

    def _zoom_preview(self, _event=None):
        if self._preview_full is None:
            return
        full = self._preview_full
        screen_width = self.root.winfo_screenwidth() - 120
        screen_height = self.root.winfo_screenheight() - 160
        display = full.copy()
        display.thumbnail((screen_width, screen_height), Image.Resampling.LANCZOS)

        zoom = tk.Toplevel(self.root)
        zoom.title(f"水印预览 · {full.width} × {full.height}")
        zoom.configure(bg=self.PREVIEW_BG)
        zoom.transient(self.root)
        photo = ImageTk.PhotoImage(display)
        label = tk.Label(zoom, image=photo, bg=self.PREVIEW_BG)
        label.image = photo
        label.pack(padx=12, pady=12)
        zoom.bind("<Escape>", lambda _event: zoom.destroy())
        zoom.update_idletasks()
        self._center_dialog(zoom, zoom.winfo_reqwidth(), zoom.winfo_reqheight())

    def _batch_process(self):
        if self._processing:
            return
        if not self.image_files:
            messagebox.showwarning("无法处理", "请先添加图片。", parent=self.root)
            return
        try:
            params = self._get_watermark_params()
        except ValueError as error:
            messagebox.showwarning("设置不完整", str(error), parent=self.root)
            return

        output_dir = self.output_dir_var.get().strip()
        if not output_dir:
            output_dir = str(Path(self.image_files[0]).parent / "output")
            self.output_dir_var.set(output_dir)
        try:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        except OSError as error:
            messagebox.showerror("无法创建输出目录", str(error), parent=self.root)
            return

        jobs = self._build_output_jobs(Path(output_dir))
        existing_count = sum(1 for _, target, _ in jobs if target.exists())
        if existing_count and not messagebox.askyesno(
            "确认覆盖",
            f"输出目录中已有 {existing_count} 个同名文件。继续后将覆盖这些输出文件。",
            parent=self.root,
        ):
            return

        self._processing = True
        self.process_button.configure(state=tk.DISABLED, text="正在处理…")
        self.preview_button.configure(state=tk.DISABLED)
        self.progress.configure(maximum=len(jobs), value=0)
        self.status_text.set(f"准备处理 {len(jobs)} 张图片…")
        self._save_output_history(output_dir)
        quality = max(10, min(100, round(self.output_quality_var.get())))

        worker = threading.Thread(target=self._process_jobs, args=(jobs, params, output_dir, quality), daemon=True)
        worker.start()

    def _build_output_jobs(self, output_dir):
        selected_format = self.output_format_var.get()
        used_names = set()
        jobs = []
        for source_text in self.image_files:
            source = Path(source_text)
            extension = FORMAT_EXTENSION.get(selected_format, source.suffix.lower())
            if extension == ".jpeg":
                extension = ".jpg"
            base_name = source.stem
            candidate = f"{base_name}{extension}"
            counter = 2
            while candidate.casefold() in used_names:
                candidate = f"{base_name}_{counter}{extension}"
                counter += 1
            used_names.add(candidate.casefold())
            target = output_dir / candidate
            if self._same_path(source, target):
                target = output_dir / f"{base_name}_watermarked{extension}"
            jobs.append((source, target, selected_format))
        return jobs

    @staticmethod
    def _same_path(first, second):
        return os.path.normcase(os.path.abspath(first)) == os.path.normcase(os.path.abspath(second))

    def _process_jobs(self, jobs, params, output_dir, quality):
        successes = []
        failures = []
        for index, (source, target, selected_format) in enumerate(jobs, start=1):
            try:
                result = process_image(source, params)
                self._save_result(result, target, selected_format, quality)
                successes.append(target)
            except Exception as error:
                failures.append((source.name, str(error)))
            self.root.after(0, self._update_batch_progress, index, len(jobs), source.name)
        self.root.after(0, self._finish_batch, successes, failures, output_dir)

    @staticmethod
    def _save_result(result, target, selected_format, quality):
        explicit_format = None if selected_format == "保持原格式" else selected_format.upper()
        extension = target.suffix.lower()
        actual_format = explicit_format or {
            ".jpg": "JPEG",
            ".jpeg": "JPEG",
            ".png": "PNG",
            ".bmp": "BMP",
            ".webp": "WEBP",
            ".tif": "TIFF",
            ".tiff": "TIFF",
            ".ico": "ICO",
        }.get(extension)
        if not actual_format:
            raise ValueError(f"无法确定输出格式：{extension}")
        save_image = result
        options = {}
        if actual_format in {"JPEG", "BMP"}:
            save_image = result.convert("RGB")
        if actual_format == "JPEG":
            options.update(quality=quality, optimize=True, subsampling=0)
        elif actual_format == "WEBP":
            options.update(quality=quality, method=4)
        save_image.save(target, format=actual_format, **options)

    def _update_batch_progress(self, current, total, filename):
        if self._closing:
            return
        self.progress.configure(value=current)
        self.status_text.set(f"正在处理 {current}/{total} · {filename}")

    def _finish_batch(self, successes, failures, output_dir):
        if self._closing:
            return
        self._processing = False
        self.process_button.configure(state=tk.NORMAL, text="开始批量处理")
        self.preview_button.configure(state=tk.NORMAL)
        if failures:
            self.status_text.set(f"完成：成功 {len(successes)} 张，失败 {len(failures)} 张")
            details = "\n".join(f"• {name}：{reason}" for name, reason in failures[:6])
            if len(failures) > 6:
                details += f"\n…另有 {len(failures) - 6} 项"
            messagebox.showwarning(
                "处理完成（有失败项）",
                f"成功 {len(successes)} 张，失败 {len(failures)} 张。\n\n{details}\n\n输出目录：{output_dir}",
                parent=self.root,
            )
        else:
            self.status_text.set(f"完成：已输出 {len(successes)} 张图片")
            messagebox.showinfo(
                "处理完成",
                f"已成功处理 {len(successes)} 张图片。\n\n输出目录：{output_dir}",
                parent=self.root,
            )

    # -------------------- 配置、托盘与关闭 --------------------

    def _load_config(self):
        self.output_dir_var.set(self.config.get("output_dir", ""))
        output_format = self.config.get("output_format", "保持原格式")
        if output_format == "keep":
            output_format = "保持原格式"
        self.output_format_var.set(output_format)
        self.output_quality_var.set(self.config.get("output_quality", 95))
        self.watermark_mode.set(self.config.get("last_watermark_mode", "text"))
        self.quality_value.configure(text=str(round(self.output_quality_var.get())))
        self._refresh_output_history()

    def _save_config(self):
        geometry = self.root.geometry().split("+", 1)[0]
        self.config.update(
            {
                "output_dir": self.output_dir_var.get().strip(),
                "output_format": self.output_format_var.get(),
                "output_quality": round(self.output_quality_var.get()),
                "window_geometry": geometry,
                "last_watermark_mode": self.watermark_mode.get(),
            }
        )

    def _on_close(self):
        if self._processing:
            if not messagebox.askyesno(
                "处理尚未完成",
                "图片仍在处理中。现在退出可能导致当前输出不完整，确定退出吗？",
                parent=self.root,
            ):
                return
            self._full_exit()
            return

        if self.config.get("remember_choice", False):
            if self.config.get("close_action") == "tray":
                self._minimize_to_tray()
            else:
                self._full_exit()
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("关闭 123Mark")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        dialog.configure(bg=self.BG)
        body = ttk.Frame(dialog, padding=18)
        body.pack(fill=tk.BOTH, expand=True)
        ttk.Label(body, text="关闭窗口后", font=("Microsoft YaHei UI", 11, "bold")).pack(anchor="w")
        ttk.Label(body, text="你可以让 123Mark 留在系统托盘，也可以完全退出。", style="Muted.TLabel").pack(anchor="w", pady=(3, 12))
        remember_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(body, text="记住我的选择", variable=remember_var).pack(anchor="w")
        buttons = ttk.Frame(body)
        buttons.pack(fill=tk.X, pady=(14, 0))
        ttk.Button(buttons, text="完全退出", command=lambda: self._close_choice(dialog, "exit", remember_var.get())).pack(side=tk.RIGHT)
        ttk.Button(buttons, text="留在托盘", style="Primary.TButton", command=lambda: self._close_choice(dialog, "tray", remember_var.get())).pack(side=tk.RIGHT, padx=(0, 7))
        dialog.bind("<Escape>", lambda _event: dialog.destroy())
        dialog.update_idletasks()
        self._center_dialog(dialog, 430, 190)

    def _close_choice(self, dialog, action, remember):
        dialog.destroy()
        if remember:
            self.config.update({"close_action": action, "remember_choice": True})
        if action == "tray":
            self._minimize_to_tray()
        else:
            self._full_exit()

    def _minimize_to_tray(self):
        try:
            import pystray
        except ImportError:
            self.root.iconify()
            return
        if self.tray_icon is not None:
            self.root.withdraw()
            return
        menu = pystray.Menu(
            pystray.MenuItem("显示 123Mark", self._show_from_tray, default=True),
            pystray.MenuItem("退出", self._exit_from_tray),
        )
        self.tray_icon = pystray.Icon("123mark", self._create_tray_icon(), APP_DISPLAY_NAME, menu)
        self.root.withdraw()
        self._in_tray = True
        self.tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        self.tray_thread.start()

    def _show_from_tray(self, *_args):
        self.root.after(0, self._restore_window)

    def _restore_window(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self._in_tray = False
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None

    def _exit_from_tray(self, *_args):
        self.root.after(0, self._full_exit)

    def _full_exit(self):
        self._closing = True
        self._save_config()
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
            self.tray_icon = None
        self.root.destroy()

    def _create_tray_icon(self):
        base_dir = Path(getattr(__import__("sys"), "_MEIPASS", Path(__file__).parent))
        logo_path = base_dir / "水印logo.png"
        try:
            with Image.open(logo_path) as source:
                return source.convert("RGBA").resize((64, 64), Image.Resampling.LANCZOS)
        except OSError:
            image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            draw.rounded_rectangle((4, 4, 60, 60), radius=14, fill=self.ACCENT)
            draw.text((17, 16), "123", fill="#FFFFFF")
            return image

    def _center_dialog(self, dialog, width, height):
        x = self.root.winfo_x() + max(0, (self.root.winfo_width() - width) // 2)
        y = self.root.winfo_y() + max(0, (self.root.winfo_height() - height) // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
