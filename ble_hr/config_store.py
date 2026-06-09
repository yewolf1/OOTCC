from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_LEVELS: list[dict[str, int]] = [
    {"bpm": 100, "speed_percent": 125},
    {"bpm": 115, "speed_percent": 150},
    {"bpm": 130, "speed_percent": 175},
    {"bpm": 145, "speed_percent": 200},
]

DEFAULT_CONFIG: dict[str, Any] = {
    "auto_connect_on_launch": False,
    "scan_timeout_ms": 8000,
    "reconnect_delay_ms": 3000,
    "preferred_address": "",
    "preferred_device_name": "",
    "preferred_name_substrings": [
        "H303",
        "MAGENE",
    ],
    "enemy_speed": {
        "enabled": True,
        "command_cooldown_ms": 2000,
        "levels": [dict(level) for level in DEFAULT_LEVELS],
    },
}


class BleHrConfigStore:
    def __init__(self, base_dir: str) -> None:
        self.config_dir = Path(base_dir) / "config"
        self.config_path = self.config_dir / "bluetooth_hr_config.json"

    def _merge_config(self, config: dict[str, Any] | None = None) -> dict[str, Any]:
        source = dict(config or {})
        merged = dict(source)

        merged["auto_connect_on_launch"] = source.get(
            "auto_connect_on_launch",
            DEFAULT_CONFIG["auto_connect_on_launch"],
        )
        merged["scan_timeout_ms"] = source.get(
            "scan_timeout_ms",
            DEFAULT_CONFIG["scan_timeout_ms"],
        )
        merged["reconnect_delay_ms"] = source.get(
            "reconnect_delay_ms",
            DEFAULT_CONFIG["reconnect_delay_ms"],
        )
        merged["preferred_address"] = str(source.get("preferred_address", "")).strip()
        merged["preferred_device_name"] = str(source.get("preferred_device_name", "")).strip()

        preferred_name_substrings = source.get("preferred_name_substrings")
        if isinstance(preferred_name_substrings, list):
            merged["preferred_name_substrings"] = [
                str(item).strip()
                for item in preferred_name_substrings
                if str(item).strip()
            ] or list(DEFAULT_CONFIG["preferred_name_substrings"])
        else:
            merged["preferred_name_substrings"] = list(DEFAULT_CONFIG["preferred_name_substrings"])

        enemy_speed_source = source.get("enemy_speed", {})
        if not isinstance(enemy_speed_source, dict):
            enemy_speed_source = {}

        legacy_hyper_source = source.get("hyper_enemies", {})
        if not isinstance(legacy_hyper_source, dict):
            legacy_hyper_source = {}

        if "levels" in enemy_speed_source and isinstance(enemy_speed_source.get("levels"), list):
            levels = self._normalize_levels(enemy_speed_source.get("levels"), allow_empty=True)
        elif legacy_hyper_source:
            legacy_on_bpm = self._coerce_int(
                legacy_hyper_source.get("on_bpm"),
                DEFAULT_LEVELS[0]["bpm"],
                minimum=1,
            )
            levels = [{"bpm": legacy_on_bpm, "speed_percent": 200}]
        else:
            levels = [dict(level) for level in DEFAULT_LEVELS]

        merged["enemy_speed"] = {
            "enabled": enemy_speed_source.get(
                "enabled",
                legacy_hyper_source.get(
                    "enabled",
                    DEFAULT_CONFIG["enemy_speed"]["enabled"],
                ),
            ),
            "command_cooldown_ms": enemy_speed_source.get(
                "command_cooldown_ms",
                legacy_hyper_source.get(
                    "command_cooldown_ms",
                    DEFAULT_CONFIG["enemy_speed"]["command_cooldown_ms"],
                ),
            ),
            "levels": levels,
        }

        merged.pop("hyper_enemies", None)
        return merged

    def _normalize_levels(self, levels: object, *, allow_empty: bool) -> list[dict[str, int]]:
        if not isinstance(levels, list):
            return [] if allow_empty else [dict(level) for level in DEFAULT_LEVELS]

        normalized: list[dict[str, int]] = []
        for item in levels:
            if not isinstance(item, dict):
                continue
            bpm = self._coerce_optional_int(item.get("bpm"), minimum=1)
            speed_percent = self._coerce_optional_int(item.get("speed_percent"), minimum=100)
            if bpm is None or speed_percent is None:
                continue
            normalized.append({
                "bpm": bpm,
                "speed_percent": speed_percent,
            })

        normalized.sort(key=lambda level: (level["bpm"], level["speed_percent"]))
        if normalized or allow_empty:
            return normalized
        return [dict(level) for level in DEFAULT_LEVELS]

    def _coerce_optional_int(self, value: object, *, minimum: int) -> int | None:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return None
        return max(minimum, parsed)

    def _coerce_int(self, value: object, default: int, *, minimum: int) -> int:
        parsed = self._coerce_optional_int(value, minimum=minimum)
        return default if parsed is None else parsed

    def ensure_config(self) -> dict[str, Any]:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        if not self.config_path.exists():
            merged = self._merge_config()
            self.config_path.write_text(
                json.dumps(merged, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            return merged
        return self.load_config()

    def load_config(self) -> dict[str, Any]:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        if not self.config_path.exists():
            return self.ensure_config()
        raw = json.loads(self.config_path.read_text(encoding="utf-8"))
        merged = self._merge_config(raw)
        if merged != raw:
            self.config_path.write_text(
                json.dumps(merged, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        return merged

    def save_config(self, config: dict[str, Any]) -> dict[str, Any]:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        merged = self._merge_config(config)
        self.config_path.write_text(
            json.dumps(merged, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return merged

    def save_preferred_device(self, *, address: str, name: str) -> dict[str, Any]:
        current = self.load_config()
        current["preferred_address"] = address
        current["preferred_device_name"] = name
        return self.save_config(current)

    def clear_preferred_device(self) -> dict[str, Any]:
        current = self.load_config()
        current["preferred_address"] = ""
        current["preferred_device_name"] = ""
        return self.save_config(current)
