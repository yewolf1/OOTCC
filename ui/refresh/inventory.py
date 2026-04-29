from __future__ import annotations


"""Refresh helpers for health, rupees, items, and ammo."""

class MainWindowInventoryRefreshMixin:
    def _refresh_health_ui(self) -> None:
        self.health_summary_var.set(
            f"Current: {self.health_state.current_hearts:.2f} hearts ({self.health_state.current_quarters}/16)\n"
            f"Max: {self.health_state.max_hearts:.2f} hearts ({self.health_state.max_quarters}/16)"
        )

    def _refresh_rupees_ui(self) -> None:
        try:
            state = self.controller.get_rupee_state()
            self.rupees_var.set(str(state.get("current", 0)))
            self.rupees_summary_var.set(
                f"Current: {state.get('current', 0)}\n"
                f"Wallet: {state.get('wallet_label', 'Unknown')}\n"
                f"Suggested cap: {state.get('capacity', 0)}"
            )
        except Exception:
            self.rupees_var.set("0")
            self.rupees_summary_var.set("Rupees unavailable")

    def _refresh_inventory_ui(self) -> None:
        try:
            inventory = self.controller.get_inventory()
            ammo = self.controller.get_ammo()

            for slot, var in self.item_vars.items():
                raw_value = inventory.get(slot, 0)
                var.set(self._format_item_value(slot, raw_value))

                item_def = ITEM_SLOTS.get(slot)
                if item_def and raw_value in item_def["choices"]:
                    self.item_select_vars[slot].set(self._choice_label(slot, raw_value))

            for slot, var in self.ammo_vars.items():
                var.set(str(ammo.get(slot, 0)))
        except Exception:
            for var in self.item_vars.values():
                var.set("0")
            for var in self.ammo_vars.values():
                var.set("0")
