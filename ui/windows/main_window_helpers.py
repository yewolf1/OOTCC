from __future__ import annotations

import json
from pathlib import Path

from core.definitions.inventory_definitions import EQUIPMENT_GROUPS, ITEM_SLOTS, QUEST_FLAGS, UPGRADE_GROUPS
from core.path_utils import get_user_base_dir


class MainWindowHelperMixin:
    def _base_dir(self) -> str:
        return str(get_user_base_dir())

    def _load_app_metadata(self) -> dict[str, str]:
        defaults = {"name": "SoH Bridge", "version": "V1.0"}
        profiles_path = Path(self._base_dir()) / "config" / "profiles.json"

        try:
            data = json.loads(profiles_path.read_text(encoding="utf-8"))
        except Exception:
            return defaults

        app = data.get("app", {})
        if not isinstance(app, dict):
            return defaults

        name = str(app.get("name", defaults["name"])).strip() or defaults["name"]
        version = str(app.get("version", defaults["version"])).strip() or defaults["version"]
        return {"name": name, "version": version}

    def _app_display_title(self) -> str:
        metadata = getattr(self, "app_metadata", None)
        if not isinstance(metadata, dict):
            metadata = self._load_app_metadata()

        name = str(metadata.get("name", "SoH Bridge")).strip() or "SoH Bridge"
        version = str(metadata.get("version", "")).strip()
        return f"{name} {version}".strip()

    def _equipment_groups_items(self) -> list[tuple[str, dict]]:
        if isinstance(EQUIPMENT_GROUPS, dict):
            return list(EQUIPMENT_GROUPS.items())
        items: list[tuple[str, dict]] = []
        for group in EQUIPMENT_GROUPS:
            items.append((group["key"], group))
        return items

    def _upgrade_groups_items(self) -> list[tuple[str, dict]]:
        if isinstance(UPGRADE_GROUPS, dict):
            return list(UPGRADE_GROUPS.items())
        items: list[tuple[str, dict]] = []
        for group in UPGRADE_GROUPS:
            items.append((group["key"], group))
        return items

    def _equipment_entries_items(self, group: dict) -> list[tuple[str, dict]]:
        entries = group["entries"]
        if isinstance(entries, dict):
            return list(entries.items())
        items: list[tuple[str, dict]] = []
        for entry in entries:
            items.append((entry["key"], entry))
        return items

    def _format_item_value(self, slot: int, value: int) -> str:
        item_def = ITEM_SLOTS.get(slot)
        if not item_def:
            return str(value)

        if value == item_def.get("clear_value", 0xFF):
            return "Empty"

        label = item_def["choices"].get(value)
        if label:
            return label

        return f"Unknown ({value})"

    def _choice_label(self, slot: int, value: int) -> str:
        item_def = ITEM_SLOTS.get(slot)
        if not item_def:
            return str(value)

        label = item_def["choices"].get(value)
        if label:
            return f"{value} - {label}"

        return str(value)

    def _quest_group_title(self, group_key: str) -> str:
        mapping = {
            "medallions": "Medallions",
            "warp_songs": "Warp Songs",
            "songs": "Songs",
            "stones": "Spiritual Stones",
            "misc": "Misc",
        }
        return mapping.get(group_key, group_key.replace("_", " ").title())

    def _quest_flag_title(self, flag_key: str) -> str:
        mapping = {
            "forest_medallion": "Forest Medallion",
            "fire_medallion": "Fire Medallion",
            "water_medallion": "Water Medallion",
            "spirit_medallion": "Spirit Medallion",
            "shadow_medallion": "Shadow Medallion",
            "light_medallion": "Light Medallion",
            "minuet_of_forest": "Minuet of Forest",
            "bolero_of_fire": "Bolero of Fire",
            "serenade_of_water": "Serenade of Water",
            "requiem_of_spirit": "Requiem of Spirit",
            "nocturne_of_shadow": "Nocturne of Shadow",
            "prelude_of_light": "Prelude of Light",
            "zeldas_lullaby": "Zelda's Lullaby",
            "eponas_song": "Epona's Song",
            "sarias_song": "Saria's Song",
            "suns_song": "Sun's Song",
            "song_of_time": "Song of Time",
            "song_of_storms": "Song of Storms",
            "kokiri_emerald": "Kokiri Emerald",
            "goron_ruby": "Goron Ruby",
            "zora_sapphire": "Zora Sapphire",
            "stone_of_agony": "Stone of Agony",
            "gerudo_card": "Gerudo Card",
            "gs_unlocked": "Gold Skulltula Icon",
            "heart_piece_icon": "Heart Piece Icon",
        }
        return mapping.get(flag_key, flag_key.replace("_", " ").title())


    def _auto_refresh_state(self) -> None:
        try:
            self.presenter.refresh_state()
        finally:
            self.after(3000, self._auto_refresh_state)
