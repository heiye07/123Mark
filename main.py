"""123Mark 程序入口。"""
import os
import sys


def _get_base_dir():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def _create_root():
    """创建 Tk 根窗口，优先使用 TkinterDnD（支持拖放）"""
    try:
        from tkinterdnd2 import TkinterDnD
        root = TkinterDnD.Tk()
        return root
    except ImportError:
        import tkinter as tk
        return tk.Tk()


def main():
    if os.name == "nt":
        try:
            import ctypes

            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

    base_dir = _get_base_dir()
    from app import WatermarkApp

    root = _create_root()

    # 设置窗口图标
    for icon_name in ("icon.ico",):
        icon_path = os.path.join(base_dir, icon_name)
        if os.path.exists(icon_path):
            try:
                root.iconbitmap(icon_path)
            except Exception:
                pass
            break

    app = WatermarkApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
