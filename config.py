"""123Mark 本地配置管理。"""
from __future__ import annotations

import json
import os
from pathlib import Path


def get_user_data_dir() -> Path:
    """返回可长期写入的用户数据目录，兼容 PyInstaller 单文件模式。"""
    base = Path(os.environ.get("APPDATA") or Path.home())
    target = base / "123Mark"
    target.mkdir(parents=True, exist_ok=True)
    return target


class AppConfig:
    DEFAULTS = {
        "close_action": "ask",
        "remember_choice": False,
        "output_dir": "",
        "output_dir_history": [],
        "output_format": "保持原格式",
        "output_quality": 95,
        "window_geometry": "1180x760",
        "last_watermark_mode": "text",
    }

    def __init__(self, config_file=None):
        self.config_file = Path(config_file) if config_file else get_user_data_dir() / "config.json"
        self.data = self._load()

    def _load(self):
        data = dict(self.DEFAULTS)
        if self.config_file.exists():
            try:
                loaded = json.loads(self.config_file.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    data.update(loaded)
            except (OSError, ValueError, TypeError):
                pass
        return data

    def _save(self):
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            temp_file = self.config_file.with_suffix(".tmp")
            temp_file.write_text(
                json.dumps(self.data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            temp_file.replace(self.config_file)
            return True
        except OSError:
            return False

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        return self._save()

    def update(self, values):
        self.data.update(values)
        return self._save()
