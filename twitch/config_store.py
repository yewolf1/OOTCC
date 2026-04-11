from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_CONFIG: dict[str, Any] = {
    "channel_login": "your_twitch_channel",
    "client_id": "your_client_id",
    "client_secret": "your_client_secret",
    "scopes": ["CHANNEL_READ_REDEMPTIONS"],
    "rewards": {
        "Kill Link": {"action": "kill_link"},
        "1/4 heart": {"action": "quarter_heart"},
        "Unequip all slots": {"action": "unequip_all_slots"},
        "Rupees -50": {"action": "rupees_delta", "amount": -50},
        "Magic (choice)": {"action": "magic_choice"},
    },
}


class TwitchConfigStore:
    def __init__(self, base_dir: str) -> None:
        self.config_dir = Path(base_dir) / "config"
        self.config_path = self.config_dir / "twitch_config.json"
        self.tokens_path = self.config_dir / "twitch_tokens.json"

    def _merge_config(self, config: dict[str, Any] | None = None) -> dict[str, Any]:
        source = config or {}
        merged = dict(DEFAULT_CONFIG)
        merged.update(source)
        merged["rewards"] = dict(DEFAULT_CONFIG["rewards"])
        merged["rewards"].update(dict(source.get("rewards", {})))
        return merged

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

    def load_tokens(self) -> dict[str, Any] | None:
        if not self.tokens_path.exists():
            return None
        return json.loads(self.tokens_path.read_text(encoding="utf-8"))

    def save_tokens(self, tokens: dict[str, Any]) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.tokens_path.write_text(
            json.dumps(tokens, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def reset_tokens(self) -> None:
        if self.tokens_path.exists():
            self.tokens_path.unlink()
