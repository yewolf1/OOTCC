from __future__ import annotations

from typing import Optional

from core.definitions.inventory_definitions import QUEST_FLAGS
from core.models import QuestStatusState


class DebugQuestControllerMixin:
    def get_save_context_addresses(self) -> dict[str, int]:
        """
        Return a merged debug address map.

        This is primarily useful for validation against Cheat Engine or for
        confirming that runtime and SaveContext pointers match expectations.
        """
        adapter = self._require_save_adapter()
        address_map = adapter.get_save_address_map()
        address_map["save_context_base"] = adapter.get_save_base()
        address_map["items_runtime_base"] = adapter.get_items_base()
        address_map["ammo_runtime_base"] = adapter.get_ammo_base()
        address_map["equips_equipment_address"] = adapter.get_equips_equipment_address()
        address_map["inventory_equipment_address"] = adapter.get_inventory_equipment_address()
        address_map["upgrades_address"] = adapter.get_upgrades_address()
        address_map["quest_items_address"] = adapter.get_quest_items_address()
        address_map["magic_level_address"] = adapter.get_magic_level_address()
        address_map["magic_current_address"] = adapter.get_magic_current_address()
        address_map["magic_acquired_address"] = adapter.get_magic_acquired_address()
        address_map["double_magic_acquired_address"] = adapter.get_double_magic_acquired_address()
        address_map["magic_state_address"] = adapter.get_magic_state_address()
        address_map["prev_magic_state_address"] = adapter.get_prev_magic_state_address()
        address_map["magic_capacity_address"] = adapter.get_magic_capacity_address()
        address_map["magic_fill_target_address"] = adapter.get_magic_fill_target_address()
        address_map["magic_target_address"] = adapter.get_magic_target_address()
        return address_map

    def get_quest_status(self) -> QuestStatusState:
        """Return quest flags as a structured QuestStatusState."""
        adapter = self._require_save_adapter()
        raw = adapter.read_quest_flags()
        state = QuestStatusState()

        for group in QUEST_FLAGS.values():
            for key, bit in group.items():
                state.set_flag(key, bool(raw & (1 << bit)))

        return state

    def set_quest_flag(self, key: str, enabled: bool) -> None:
        """
        Toggle one quest flag inside the quest bitfield.

        The key is resolved dynamically from QUEST_FLAGS so the controller does
        not duplicate bit positions locally.
        """
        adapter = self._require_save_adapter()
        raw = adapter.read_quest_flags()

        bit: Optional[int] = None
        for group in QUEST_FLAGS.values():
            if key in group:
                bit = group[key]
                break

        if bit is None:
            raise ValueError(f"Unknown quest flag: {key}")

        if enabled:
            raw |= (1 << bit)
        else:
            raw &= ~(1 << bit)

        adapter.write_quest_flags(raw)
        self._log(f"Quest flag set: {key}={'on' if enabled else 'off'}")
