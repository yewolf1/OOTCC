from __future__ import annotations

from core.definitions.inventory_definitions import AMMO_SLOTS, ITEM_SLOTS, UPGRADE_GROUPS


class RupeeInventoryControllerMixin:
    def get_rupees(self) -> int:
        """Read the current rupee count."""
        if not self.adapter:
            raise RuntimeError("SoH is not attached")
        return self.adapter.get_rupees()

    def _wallet_capacity_from_upgrade(self) -> int:
        """
        Derive the wallet capacity from the current wallet upgrade level.

        This keeps the UI aligned with gameplay limits even though rupees are
        written through HealthAdapter and wallet progression is stored elsewhere.
        """
        try:
            wallet_level = self.get_upgrade_level("wallet")
        except Exception:
            wallet_level = 0

        mapping = {
            0: 99,
            1: 200,
            2: 500,
            3: 999,
        }
        return mapping.get(wallet_level, 999)

    def get_rupee_state(self) -> dict:
        """Return current rupees together with wallet metadata."""
        current = self.get_rupees()
        capacity = self._wallet_capacity_from_upgrade()
        wallet_level = self.get_upgrade_level("wallet") if self.save_adapter else 0
        wallet_group = UPGRADE_GROUPS.get("wallet", {})
        wallet_levels = wallet_group.get("levels", ())
        wallet_label = wallet_levels[wallet_level] if 0 <= wallet_level < len(wallet_levels) else "Unknown"
        return {
            "current": current,
            "capacity": capacity,
            "wallet_level": wallet_level,
            "wallet_label": wallet_label,
        }

    def set_rupees(self, value: int) -> None:
        """Write the rupee count."""
        if not self.adapter:
            raise RuntimeError("SoH is not attached")
        clamped = self.adapter.set_rupees(value)
        self.logger.add(f"Rupees set to {clamped}")

    def fill_rupees(self) -> None:
        """Fill rupees to current wallet capacity."""
        capacity = self._wallet_capacity_from_upgrade()
        self.set_rupees(capacity)

    def adjust_rupees(self, delta: int) -> None:
        """Apply a signed rupee delta."""
        state = self.get_rupee_state()
        self.set_rupees(state["current"] + delta)

    def get_inventory(self) -> dict[int, int]:
        """Read all item slots."""
        adapter = self._require_save_adapter()
        return {slot: adapter.get_item_slot(slot) for slot in ITEM_SLOTS}

    def set_item_value(self, slot: int, value: int) -> None:
        """Write one raw item slot value."""
        adapter = self._require_save_adapter()
        adapter.set_item_slot(slot, value)
        self.logger.add(f"Set item slot {slot} to raw value {value}")

    def clear_item(self, slot: int) -> None:
        """Clear one item slot using its configured empty value."""
        adapter = self._require_save_adapter()
        clear_value = ITEM_SLOTS[slot]["clear_value"]
        adapter.set_item_slot(slot, clear_value)
        self.logger.add(f"Clear item slot {slot}")

    def get_ammo(self) -> dict[int, int]:
        """Read all configured ammo slots."""
        adapter = self._require_save_adapter()
        return {slot: adapter.get_ammo(slot) for slot in AMMO_SLOTS}

    def set_ammo(self, slot: int, value: int) -> None:
        """Write one ammo slot."""
        adapter = self._require_save_adapter()
        adapter.set_ammo(slot, value)
        self.logger.add(f"Set ammo slot {slot} to {value}")
