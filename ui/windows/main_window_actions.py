from __future__ import annotations

from tkinter import messagebox

from core.definitions.inventory_definitions import BUTTON_LAYOUT, SWORD_BUTTON_MODES


class MainWindowActionMixin:
    def apply_current_health(self) -> None:
        self.set_current_health(self.health_slider_var.get())

    def set_current_health(self, hearts: float) -> None:
        try:
            self.controller.set_health_hearts(hearts)
            self.refresh_state()
        except Exception as exc:
            messagebox.showerror("Bridge error", str(exc))
            self._render_logs()

    def adjust_current_health(self, delta: float) -> None:
        target = max(0.0, self.health_state.current_hearts + delta)
        self.set_current_health(target)

    def apply_max_health(self) -> None:
        self.set_max_health(self.max_health_slider_var.get())

    def set_max_health(self, hearts: float) -> None:
        try:
            self.controller.set_max_health_hearts(hearts)
            self.refresh_state()
        except Exception as exc:
            messagebox.showerror("Bridge error", str(exc))
            self._render_logs()

    def adjust_max_health(self, delta: float) -> None:
        target = max(1.0, self.health_state.max_hearts + delta)
        self.set_max_health(target)

    def full_heal(self) -> None:
        try:
            self.controller.full_heal()
            self.refresh_state()
        except Exception as exc:
            messagebox.showerror("Bridge error", str(exc))
            self._render_logs()

    def simulate_reward(self, viewer: str, reward_title: str, hearts_delta: float) -> None:
        try:
            self.controller.simulate_reward(viewer, reward_title, hearts_delta)
        except Exception as exc:
            messagebox.showerror("Reward error", str(exc))
        finally:
            self.refresh_state()

    def apply_item_value(self, slot: int) -> None:
        try:
            selected = self.item_select_vars[slot].get()
            value = self.item_choice_maps[slot][selected]
            self.controller.set_item_value(slot, value)
            self.refresh_state()
        except Exception as exc:
            messagebox.showerror("Item error", str(exc))

    def clear_item_slot(self, slot: int) -> None:
        try:
            self.controller.clear_item(slot)
            self.refresh_state()
        except Exception as exc:
            messagebox.showerror("Item error", str(exc))

    def apply_ammo_slot(self, slot: int) -> None:
        try:
            value = int(self.ammo_vars[slot].get())
            self.controller.set_ammo(slot, value)
            self.refresh_state()
        except Exception as exc:
            messagebox.showerror("Ammo error", str(exc))

    def zero_ammo_slot(self, slot: int) -> None:
        try:
            self.controller.set_ammo(slot, 0)
            self.refresh_state()
        except Exception as exc:
            messagebox.showerror("Ammo error", str(exc))

    def apply_magic_current(self) -> None:
        try:
            self.controller.set_magic_current(int(self.magic_current_var.get()))
            self.refresh_state()
        except Exception as exc:
            messagebox.showerror("Magic error", str(exc))

    def apply_magic_level(self) -> None:
        try:
            mapping = {
                "No magic": 0,
                "Normal magic": 1,
                "Double magic": 2,
            }
            self.controller.set_magic_level(mapping[self.magic_level_var.get()])
            self.refresh_state()
        except Exception as exc:
            messagebox.showerror("Magic error", str(exc))

    def fill_magic(self) -> None:
        try:
            self.controller.fill_magic()
            self.refresh_state()
        except Exception as exc:
            messagebox.showerror("Magic error", str(exc))

    def empty_magic(self) -> None:
        try:
            self.controller.empty_magic()
            self.refresh_state()
        except Exception as exc:
            messagebox.showerror("Magic error", str(exc))

    def apply_rupees(self) -> None:
        try:
            self.controller.set_rupees(int(self.rupees_var.get()))
            self.refresh_state()
        except Exception as exc:
            messagebox.showerror("Rupees error", str(exc))

    def adjust_rupees(self, delta: int) -> None:
        try:
            self.controller.adjust_rupees(delta)
            self.refresh_state()
        except Exception as exc:
            messagebox.showerror("Rupees error", str(exc))

    def fill_rupees(self) -> None:
        try:
            self.controller.fill_rupees()
            self.refresh_state()
        except Exception as exc:
            messagebox.showerror("Rupees error", str(exc))

    def zero_rupees(self) -> None:
        try:
            self.controller.set_rupees(0)
            self.refresh_state()
        except Exception as exc:
            messagebox.showerror("Rupees error", str(exc))

    def add_equipment_item(self, group_key: str, item_key: str) -> None:
        try:
            self.controller.add_equipment_item(group_key, item_key)
            self.refresh_state()
        except Exception as exc:
            messagebox.showerror("Equipment error", str(exc))

    def remove_equipment_item(self, group_key: str, item_key: str) -> None:
        try:
            self.controller.remove_equipment_item(group_key, item_key)
            self.refresh_state()
        except Exception as exc:
            messagebox.showerror("Equipment error", str(exc))

    def equip_equipment_item(self, group_key: str, item_key: str) -> None:
        try:
            self.controller.equip_equipment_item(group_key, item_key)
            self.refresh_state()
        except Exception as exc:
            messagebox.showerror("Equipment error", str(exc))

    def increase_upgrade_level(self, upgrade_key: str) -> None:
        try:
            self.controller.increase_upgrade_level(upgrade_key)
            self.refresh_state()
        except Exception as exc:
            messagebox.showerror("Upgrade error", str(exc))

    def decrease_upgrade_level(self, upgrade_key: str) -> None:
        try:
            self.controller.decrease_upgrade_level(upgrade_key)
            self.refresh_state()
        except Exception as exc:
            messagebox.showerror("Upgrade error", str(exc))

    def apply_button_assignment(self, button_key: str) -> None:
        try:
            selected = self.button_select_vars[button_key].get()
            item_key = self.button_choice_maps[button_key][selected]
            self.controller.set_button_assignment(button_key, item_key)
            self.refresh_state()
        except Exception as exc:
            messagebox.showerror("Button error", str(exc))

    def clear_button_assignment(self, button_key: str) -> None:
        try:
            self.controller.clear_button_assignment(button_key)
            self.refresh_state()
        except Exception as exc:
            messagebox.showerror("Button error", str(exc))

    def apply_sword_mode(self) -> None:
        try:
            reverse_map = {label: key for key, label in SWORD_BUTTON_MODES.items()}
            self.controller.set_sword_mode(reverse_map[self.sword_mode_var.get()])
            self.refresh_state()
        except Exception as exc:
            messagebox.showerror("Button error", str(exc))

    def teleport_to_warp_song(self, destination_key: str) -> None:
        """Handle one explicit warp-song teleport request from the UI."""
        try:
            self.controller.teleport_to_warp_song(destination_key)
            self.refresh_state()
        except Exception as exc:
            messagebox.showerror("Teleport error", str(exc))

    def teleport_random_safe(self) -> None:
        """Teleport to one destination from the conservative random pool."""
        try:
            destination = self.controller.teleport_random_safe()
            self.teleport_random_result_var.set(
                f"Last random result: {destination['label']}\n"
                f"{destination['entrance_name']} | 0x{destination['entrance_id']:04X}"
            )
            self.refresh_state()
        except Exception as exc:
            messagebox.showerror("Teleport error", str(exc))

    def toggle_quest_flag(self, flag_key: str) -> None:
        try:
            enabled = self.quest_flag_vars[flag_key].get()
            self.controller.set_quest_flag(flag_key, enabled)
            self.refresh_state()
        except Exception as exc:
            messagebox.showerror("Quest status error", str(exc))

    def apply_equips_equipment(self) -> None:
        try:
            self.controller.set_equips_equipment(int(self.equips_equipment_var.get()))
            self.refresh_state()
        except Exception as exc:
            messagebox.showerror("Equipment error", str(exc))

    def apply_inventory_equipment(self) -> None:
        try:
            self.controller.set_inventory_equipment(int(self.inventory_equipment_var.get()))
            self.refresh_state()
        except Exception as exc:
            messagebox.showerror("Equipment error", str(exc))

    def apply_equipment(self) -> None:
        try:
            self.controller.set_equipment(int(self.equipment_var.get()))
            self.refresh_state()
        except Exception as exc:
            messagebox.showerror("Equipment error", str(exc))

    def apply_upgrades(self) -> None:
        try:
            self.controller.set_upgrades(int(self.upgrades_var.get()))
            self.refresh_state()
        except Exception as exc:
            messagebox.showerror("Upgrades error", str(exc))

    def apply_quest_items(self) -> None:
        try:
            self.controller.set_quest_items(int(self.quest_items_var.get()))
            self.refresh_state()
        except Exception as exc:
            messagebox.showerror("Quest items error", str(exc))
