from __future__ import annotations

from core.definitions.inventory_definitions import EQUIPMENT_GROUPS, UPGRADE_GROUPS
from core.models import EquipmentEntryState, EquipmentGroupState, EquipmentState


class EquipmentControllerMixin:
    def get_equipment(self) -> int:
        """Read the legacy equipment field."""
        return self._require_save_adapter().get_equipment()

    def set_equipment(self, value: int) -> None:
        """Write the legacy equipment field."""
        self._require_save_adapter().set_equipment(value)
        self.logger.add(f"Set legacy equipment field to {value}")

    def get_equips_equipment(self) -> int:
        """Read the live equipped equipment mask."""
        return self._require_save_adapter().get_equips_equipment()

    def set_equips_equipment(self, value: int) -> None:
        """Write the live equipped equipment mask."""
        self._require_save_adapter().set_equips_equipment(value)
        self.logger.add(f"Set equipped equipment mask to {value}")

    def get_inventory_equipment(self) -> int:
        """Read the owned equipment mask."""
        return self._require_save_adapter().get_inventory_equipment()

    def set_inventory_equipment(self, value: int) -> None:
        """Write the owned equipment mask."""
        self._require_save_adapter().set_inventory_equipment(value)
        self.logger.add(f"Set inventory equipment mask to {value}")

    def get_upgrades(self) -> int:
        """Read the upgrades mask."""
        return self._require_save_adapter().get_upgrades()

    def set_upgrades(self, value: int) -> None:
        """Write the upgrades mask."""
        self._require_save_adapter().set_upgrades(value)
        self.logger.add(f"Set upgrades to {value}")

    def get_quest_items(self) -> int:
        """Read the quest items mask."""
        return self._require_save_adapter().get_quest_items()

    def set_quest_items(self, value: int) -> None:
        """Write the quest items mask."""
        self._require_save_adapter().set_quest_items(value)
        self.logger.add(f"Set quest items to {value}")

    def _get_equipment_group(self, group_key: str) -> dict:
        """Resolve one equipment group definition."""
        group = EQUIPMENT_GROUPS.get(group_key)
        if not group:
            raise ValueError(f"Unknown equipment group: {group_key}")
        return group

    def _get_equipment_entry(self, group_key: str, item_key: str) -> dict:
        """Resolve one equipment entry definition."""
        group = self._get_equipment_group(group_key)
        entry = group["entries"].get(item_key)
        if not entry:
            raise ValueError(f"Unknown equipment item: {group_key}.{item_key}")
        return entry

    def _get_upgrade_group(self, upgrade_key: str) -> dict:
        """Resolve one upgrade group definition."""
        group = UPGRADE_GROUPS.get(upgrade_key)
        if not group:
            raise ValueError(f"Unknown upgrade group: {upgrade_key}")
        return group

    def _owned_equipment_bit(self, group_key: str, item_key: str) -> int:
        """Return the ownership bit for one equipment entry."""
        entry = self._get_equipment_entry(group_key, item_key)
        return entry["owned_bit"]

    def _equipped_group_value(self, group_key: str) -> int:
        """Read the currently equipped nibble for one equipment group."""
        adapter = self._require_save_adapter()
        shift = self._get_equipment_group(group_key)["shift"]
        current_mask = adapter.read_equipped_equipment_mask()
        return (current_mask >> shift) & 0xF

    def _set_equipped_group_value(self, group_key: str, value: int) -> None:
        """
        Update only one equipment group inside the global equipped mask.

        Each group occupies one nibble, so the previous nibble must be cleared
        before inserting the new value.
        """
        adapter = self._require_save_adapter()
        group = self._get_equipment_group(group_key)

        shift = group["shift"]
        clear_mask = group["clear_mask"]

        current_mask = adapter.read_equipped_equipment_mask()
        new_mask = (current_mask & clear_mask) | ((value & 0xF) << shift)

        adapter.write_equipped_equipment_mask(new_mask)

    def _first_owned_fallback(self, group_key: str) -> int:
        """
        Return the first owned entry equip value for a group.

        This is used when removing an equipped item and the game needs a valid
        fallback instead of keeping a now-invalid equipped state.
        """
        group = self._get_equipment_group(group_key)
        owned_mask = self.get_inventory_equipment()

        entries = sorted(group["entries"].values(), key=lambda item: item["index"])
        for entry in entries:
            if owned_mask & entry["owned_bit"]:
                return entry["equip_value"]

        return 0

    def add_equipment_item(self, group_key: str, item_key: str, auto_equip: bool = False) -> None:
        """Mark an equipment item as owned, with optional auto-equip."""
        bit = self._owned_equipment_bit(group_key, item_key)
        owned_mask = self.get_inventory_equipment() | bit
        self.set_inventory_equipment(owned_mask)

        if auto_equip:
            self.equip_equipment_item(group_key, item_key)

        self._log(f"Equipment added: {group_key}.{item_key}")

    def remove_equipment_item(self, group_key: str, item_key: str) -> None:
        """
        Remove an owned equipment item and repair equipped state if needed.

        Swords are special because the live B button and sword nibble must stay
        consistent with the equipped equipment mask.
        """
        entry = self._get_equipment_entry(group_key, item_key)
        bit = self._owned_equipment_bit(group_key, item_key)

        owned_mask = self.get_inventory_equipment() & ~bit
        self.set_inventory_equipment(owned_mask)

        if self._equipped_group_value(group_key) == entry["equip_value"]:
            fallback = self._first_owned_fallback(group_key)
            self._set_equipped_group_value(group_key, fallback)

            if group_key == "swords":
                if fallback == 0:
                    self._require_save_adapter().apply_swordless()
                else:
                    fallback_key = next(
                        (
                            key
                            for key, sword_entry in self._get_equipment_group("swords")["entries"].items()
                            if sword_entry["equip_value"] == fallback
                        ),
                        None,
                    )
                    if fallback_key:
                        self._require_save_adapter().equip_live_sword(fallback_key.replace("_sword", ""))

        self._log(f"Equipment removed: {group_key}.{item_key}")

    def equip_equipment_item(self, group_key: str, item_key: str) -> None:
        """
        Equip one owned equipment item.

        Sword equipment is mirrored to live runtime fields because the B button
        representation must remain synchronized with the equipment mask.
        """
        entry = self._get_equipment_entry(group_key, item_key)
        bit = self._owned_equipment_bit(group_key, item_key)

        if not (self.get_inventory_equipment() & bit):
            raise ValueError(f"Cannot equip non-owned item: {group_key}.{item_key}")

        self._set_equipped_group_value(group_key, entry["equip_value"])

        if group_key == "swords":
            self._require_save_adapter().equip_live_sword(item_key.replace("_sword", ""))

        self._log(f"Equipment equipped: {group_key}.{item_key}")

    def unequip_equipment_group(self, group_key: str) -> None:
        """Unequip one whole equipment group."""
        self._set_equipped_group_value(group_key, 0)
        if group_key == "swords":
            self._require_save_adapter().apply_swordless()
        self._log(f"Equipment unequipped: {group_key}")

    def get_upgrade_level(self, upgrade_key: str) -> int:
        """Read one upgrade level from the global upgrades mask."""
        group = self._get_upgrade_group(upgrade_key)
        upgrades_mask = self.get_upgrades()
        return (upgrades_mask >> group["shift"]) & group["mask_bits"]

    def set_upgrade_level(self, upgrade_key: str, level: int) -> None:
        """
        Update one upgrade field inside the upgrades mask.

        Like equipment groups, each upgrade occupies only part of the full mask,
        so the target bits must be cleared before writing the new level.
        """
        group = self._get_upgrade_group(upgrade_key)
        max_level = len(group["levels"]) - 1
        if level < 0 or level > max_level:
            raise ValueError(f"Invalid level for {upgrade_key}: {level}")

        upgrades_mask = self.get_upgrades()
        clear_mask = group["mask_bits"] << group["shift"]
        upgrades_mask &= ~clear_mask
        upgrades_mask |= (level & group["mask_bits"]) << group["shift"]

        self.set_upgrades(upgrades_mask)
        self._log(f"Upgrade level set: {upgrade_key}={level}")

    def increase_upgrade_level(self, upgrade_key: str) -> None:
        """Increase one upgrade level by one step."""
        group = self._get_upgrade_group(upgrade_key)
        current = self.get_upgrade_level(upgrade_key)
        self.set_upgrade_level(upgrade_key, min(current + 1, len(group["levels"]) - 1))

    def decrease_upgrade_level(self, upgrade_key: str) -> None:
        """Decrease one upgrade level by one step."""
        self.set_upgrade_level(upgrade_key, max(self.get_upgrade_level(upgrade_key) - 1, 0))

    def get_equipment_snapshot(self) -> dict:
        """
        Build a raw structured snapshot of owned equipment, equipped equipment,
        and upgrade levels.

        This snapshot is the intermediate representation later transformed into
        UI-oriented EquipmentState objects.
        """
        owned_mask = self.get_inventory_equipment()
        equipped_mask = self._require_save_adapter().read_equipped_equipment_mask()
        upgrades_mask = self.get_upgrades()

        result = {
            "owned_mask": owned_mask,
            "equipped_mask": equipped_mask,
            "upgrades_mask": upgrades_mask,
            "groups": {},
            "upgrades": {},
        }

        for group_key, group in EQUIPMENT_GROUPS.items():
            shift = group["shift"]
            equipped_value = (equipped_mask >> shift) & 0xF
            entries = []

            for item_key, entry in group["entries"].items():
                bit = entry["owned_bit"]
                entries.append(
                    {
                        "key": item_key,
                        "label": entry["label"],
                        "owned": bool(owned_mask & bit),
                        "equipped": equipped_value == entry["equip_value"],
                        "equip_value": entry["equip_value"],
                    }
                )

            result["groups"][group_key] = {
                "label": group["label"],
                "entries": entries,
            }

        for upgrade_key, group in UPGRADE_GROUPS.items():
            level = self.get_upgrade_level(upgrade_key)
            max_level = len(group["levels"]) - 1
            display_level = min(level, max_level)
            level_label = group["levels"][display_level]
            if level > max_level:
                level_label = f"{level_label} (raw {level})"

            result["upgrades"][upgrade_key] = {
                "label": group["label"],
                "level": level,
                "display_level": display_level,
                "level_label": level_label,
                "max_level": max_level,
                "levels": list(group["levels"]),
            }

        return result

    def get_equipment_state(self) -> EquipmentState:
        """
        Transform the raw equipment snapshot into a UI-ready EquipmentState.

        This layer is intentionally presentation-oriented: it computes human
        labels, per-entry status text, and action availability flags.
        """
        try:
            snapshot = self.get_equipment_snapshot()
        except Exception as exc:
            return EquipmentState(available=False, message=str(exc))

        groups: list[EquipmentGroupState] = []

        for group_key, group_data in snapshot["groups"].items():
            raw_text = f"inventory=0x{snapshot['owned_mask']:04X} | equipped=0x{snapshot['equipped_mask']:04X}"
            entries = []

            for entry in group_data["entries"]:
                if entry["equipped"]:
                    status_text = "Owned | Equipped"
                elif entry["owned"]:
                    status_text = "Owned"
                else:
                    status_text = "Missing"

                entries.append(
                    EquipmentEntryState(
                        key=entry["key"],
                        label=entry["label"],
                        status_text=status_text,
                        owned=entry["owned"],
                        equipped=entry["equipped"],
                        can_add=not entry["owned"],
                        can_remove=entry["owned"],
                        can_equip=entry["owned"] and not entry["equipped"],
                    )
                )

            groups.append(
                EquipmentGroupState(
                    key=group_key,
                    label=group_data["label"],
                    entries=entries,
                    raw_value_text=raw_text,
                    group_type="equipment",
                )
            )

        for upgrade_key, upgrade_data in snapshot["upgrades"].items():
            entries = []

            current_display_level = upgrade_data.get("display_level", upgrade_data["level"])
            for level_index, level_label in enumerate(upgrade_data["levels"]):
                entries.append(
                    EquipmentEntryState(
                        key=f"{upgrade_key}_level_{level_index}",
                        label=level_label,
                        status_text="Current" if level_index == current_display_level else "Available",
                        level=level_index,
                        max_level=upgrade_data["max_level"],
                    )
                )

            groups.append(
                EquipmentGroupState(
                    key=upgrade_key,
                    label=upgrade_data["label"],
                    entries=entries,
                    raw_value_text=(
                        f"upgrades=0x{snapshot['upgrades_mask']:08X} | current={upgrade_data['level_label']}"
                    ),
                    group_type="upgrade",
                )
            )

        return EquipmentState(
            equipped_mask=snapshot["equipped_mask"],
            inventory_mask=snapshot["owned_mask"],
            upgrades_mask=snapshot["upgrades_mask"],
            groups=groups,
            available=True,
            message="Equipment state ready",
        )
