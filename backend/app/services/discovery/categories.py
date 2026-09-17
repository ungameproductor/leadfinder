from __future__ import annotations

import yaml

from app.config import get_settings


def load_categories() -> list[dict]:
    path = get_settings().categories_path
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return list(data.get("categories") or [])


def category_by_id(category_id: str) -> dict | None:
    for item in load_categories():
        if item.get("id") == category_id:
            return item
    return None


def search_query_for(category_id: str) -> str:
    item = category_by_id(category_id)
    if item:
        return str(item.get("search_query") or category_id)
    return category_id
