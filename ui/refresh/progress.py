from __future__ import annotations

from core.definitions.inventory_definitions import QUEST_FLAGS

"""Refresh helpers for flags, equipment, and quest progression."""

class MainWindowProgressRefreshMixin:
    def _refresh_flags_ui(self) -> None:
        try:
            equipped_value = self.controller.get_equips_equipment()
            inventory_equipment = self.controller.get_inventory_equipment()

            self.equips_equipment_var.set(str(equipped_value))
            self.inventory_equipment_var.set(str(inventory_equipment))
            self.equipment_var.set(str(self.controller.get_equipment()))
            self.upgrades_var.set(str(self.controller.get_upgrades()))
            self.quest_items_var.set(str(self.controller.get_quest_items()))
        except Exception:
            self.equips_equipment_var.set("0")
            self.inventory_equipment_var.set("0")
            self.equipment_var.set("0")
            self.upgrades_var.set("0")
            self.quest_items_var.set("0")

    def _refresh_equipment_ui(self) -> None:
        try:
            snapshot = self.controller.get_equipment_snapshot()

            owned_mask = snapshot.get("owned_mask", 0)
            equipped_mask = snapshot.get("equipped_mask", 0)
            upgrades_mask = snapshot.get("upgrades_mask", 0)
            self.equipment_summary_var.set(
                f"Owned=0x{owned_mask:04X} | Equipped=0x{equipped_mask:04X} | Upgrades=0x{upgrades_mask:08X}"
            )

            for group_key, group in self._equipment_groups_items():
                group_state = snapshot["groups"].get(group_key, {"entries": []})
                entries_state = group_state.get("entries", [])

                equipped_labels = [entry["label"] for entry in entries_state if entry.get("equipped")]
                owned_count = sum(1 for entry in entries_state if entry.get("owned"))
                equipped_label = equipped_labels[0] if equipped_labels else "None"

                if group_key in self.equipment_group_vars:
                    self.equipment_group_vars[group_key].set(f"Owned: {owned_count} | Equipped: {equipped_label}")

                by_key = {entry["key"]: entry for entry in entries_state}
                for item_key, _entry_def in self._equipment_entries_items(group):
                    state = by_key.get(item_key)
                    if not state:
                        text = "Unknown"
                    elif state.get("equipped"):
                        text = "Equipped"
                    elif state.get("owned"):
                        text = "Owned"
                    else:
                        text = "Missing"
                    if item_key in self.equipment_entry_vars:
                        self.equipment_entry_vars[item_key].set(text)

            for upgrade_key, _group in self._upgrade_groups_items():
                upgrade_state = snapshot["upgrades"].get(upgrade_key)
                if upgrade_state and upgrade_key in self.upgrade_level_vars:
                    level = upgrade_state.get("level", 0)
                    max_level = upgrade_state.get("max_level", 0)
                    level_label = upgrade_state.get("level_label", "Unknown")
                    self.upgrade_level_vars[upgrade_key].set(f"Level {level}/{max_level} - {level_label}")
        except Exception:
            self.equipment_summary_var.set("Equipment snapshot unavailable")
            for var in self.equipment_group_vars.values():
                var.set("No data")
            for var in self.equipment_entry_vars.values():
                var.set("Unknown")
            for var in self.upgrade_level_vars.values():
                var.set("Unknown")

    def _refresh_quest_status_ui(self) -> None:
        try:
            quest_status = self.controller.get_quest_status()

            flags: dict[str, bool] = {}
            if hasattr(quest_status, "flags"):
                flags = quest_status.flags
            elif isinstance(quest_status, dict):
                flags = quest_status

            for key, var in self.quest_flag_vars.items():
                var.set(bool(flags.get(key, False)))
        except Exception:
            for var in self.quest_flag_vars.values():
                var.set(False)
