"""文本水印收藏管理器。"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from config import get_user_data_dir


class FavoritesManager:
    def __init__(self, data_file=None, max_items=10):
        self.data_file = Path(data_file) if data_file else get_user_data_dir() / "favorites.json"
        self.max_items = max(1, int(max_items))
        self.favorites = self._load()

    def _load(self):
        if not self.data_file.exists():
            return []
        try:
            data = json.loads(self.data_file.read_text(encoding="utf-8"))
            items = data.get("favorites", [])
            return [item for item in items if isinstance(item, dict)][: self.max_items]
        except (OSError, ValueError, TypeError):
            return []

    def _save(self):
        try:
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            temp_file = self.data_file.with_suffix(".tmp")
            temp_file.write_text(
                json.dumps({"favorites": self.favorites}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            temp_file.replace(self.data_file)
            return True
        except OSError:
            return False

    def get_all(self):
        return deepcopy(self.favorites)

    def get(self, index):
        if 0 <= index < len(self.favorites):
            return deepcopy(self.favorites[index])
        return None

    def add(self, item):
        text = str(item.get("text", "")).strip()
        if not text:
            return False
        normalized = {
            "name": str(item.get("name", text[:20])).strip() or text[:20],
            "text": text,
        }
        if isinstance(item.get("settings"), dict):
            normalized["settings"] = deepcopy(item["settings"])
        self.favorites = [
            favorite for favorite in self.favorites
            if (favorite.get("text"), favorite.get("settings"))
            != (text, normalized.get("settings"))
        ]
        self.favorites.insert(0, normalized)
        self.favorites = self.favorites[: self.max_items]
        return self._save()

    def remove(self, index):
        if 0 <= index < len(self.favorites):
            self.favorites.pop(index)
            return self._save()
        return False

    def move_up(self, index):
        if 0 < index < len(self.favorites):
            self.favorites[index - 1], self.favorites[index] = self.favorites[index], self.favorites[index - 1]
            return self._save()
        return False

    def move_down(self, index):
        if 0 <= index < len(self.favorites) - 1:
            self.favorites[index], self.favorites[index + 1] = self.favorites[index + 1], self.favorites[index]
            return self._save()
        return False

    def count(self):
        return len(self.favorites)

    def is_full(self):
        return len(self.favorites) >= self.max_items

    def clear(self):
        self.favorites.clear()
        return self._save()
