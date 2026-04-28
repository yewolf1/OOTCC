from __future__ import annotations


class MainWindowCommandMixin:
    """Thin UI event handlers that delegate all application logic to the presenter."""

    def refresh_state(self) -> None:
        self.presenter.refresh_state()

    def force_refresh_state(self) -> None:
        self.presenter.refresh_state(force_runtime_scan=True)

    def apply_current_health(self) -> None:
        self.presenter.apply_current_health(self.health_slider_var.get())

    def adjust_current_health(self, delta: float) -> None:
        self.presenter.adjust_current_health(delta)

    def apply_max_health(self) -> None:
        self.presenter.apply_max_health(self.max_health_slider_var.get())

    def adjust_max_health(self, delta: float) -> None:
        self.presenter.adjust_max_health(delta)

    def full_heal(self) -> None:
        self.presenter.full_heal()

    def simulate_reward(self, viewer: str, reward_title: str, hearts_delta: float) -> None:
        self.presenter.simulate_reward(viewer, reward_title, hearts_delta)

    def apply_item_value(self, slot: int) -> None:
        self.presenter.apply_item_value(slot, self.item_select_vars[slot].get(), self.item_choice_maps[slot])

    def clear_item_slot(self, slot: int) -> None:
        self.presenter.clear_item_slot(slot)

    def apply_ammo_slot(self, slot: int) -> None:
        self.presenter.apply_ammo_slot(slot, self.ammo_vars[slot].get())

    def zero_ammo_slot(self, slot: int) -> None:
        self.presenter.zero_ammo_slot(slot)

    def apply_magic_current(self) -> None:
        self.presenter.apply_magic_current(self.magic_current_var.get())

    def apply_magic_level(self) -> None:
        self.presenter.apply_magic_level(self.magic_level_var.get())

    def fill_magic(self) -> None:
        self.presenter.fill_magic()

    def empty_magic(self) -> None:
        self.presenter.empty_magic()

    def apply_rupees(self) -> None:
        self.presenter.apply_rupees(self.rupees_var.get())

    def adjust_rupees(self, delta: int) -> None:
        self.presenter.adjust_rupees(delta)

    def fill_rupees(self) -> None:
        self.presenter.fill_rupees()

    def zero_rupees(self) -> None:
        self.presenter.zero_rupees()

    def add_equipment_item(self, group_key: str, item_key: str) -> None:
        self.presenter.add_equipment_item(group_key, item_key)

    def remove_equipment_item(self, group_key: str, item_key: str) -> None:
        self.presenter.remove_equipment_item(group_key, item_key)

    def equip_equipment_item(self, group_key: str, item_key: str) -> None:
        self.presenter.equip_equipment_item(group_key, item_key)

    def increase_upgrade_level(self, upgrade_key: str) -> None:
        self.presenter.increase_upgrade_level(upgrade_key)

    def decrease_upgrade_level(self, upgrade_key: str) -> None:
        self.presenter.decrease_upgrade_level(upgrade_key)

    def apply_button_assignment(self, button_key: str) -> None:
        self.presenter.apply_button_assignment(
            button_key,
            self.button_select_vars[button_key].get(),
            self.button_choice_maps[button_key],
        )

    def clear_button_assignment(self, button_key: str) -> None:
        self.presenter.clear_button_assignment(button_key)

    def apply_sword_mode(self) -> None:
        self.presenter.apply_sword_mode(self.sword_mode_var.get())

    def teleport_to_warp_song(self, destination_key: str) -> None:
        self.presenter.teleport_to_warp_song(destination_key)

    def teleport_random_safe(self) -> None:
        self.presenter.teleport_random_safe()

    def toggle_quest_flag(self, flag_key: str) -> None:
        self.presenter.toggle_quest_flag(flag_key, self.quest_flag_vars[flag_key].get())

    def apply_equips_equipment(self) -> None:
        self.presenter.apply_equips_equipment(self.equips_equipment_var.get())

    def apply_inventory_equipment(self) -> None:
        self.presenter.apply_inventory_equipment(self.inventory_equipment_var.get())

    def apply_equipment(self) -> None:
        self.presenter.apply_equipment(self.equipment_var.get())

    def apply_upgrades(self) -> None:
        self.presenter.apply_upgrades(self.upgrades_var.get())

    def apply_quest_items(self) -> None:
        self.presenter.apply_quest_items(self.quest_items_var.get())



    def ensure_dll_bridge_injected(self) -> None:
        self.presenter.ensure_dll_bridge_injected()

    def execute_dll_bridge_command(self, command: str) -> None:
        self.presenter.execute_dll_bridge_command(command)

    def apply_link_state_player_address(self) -> None:
        self.presenter.apply_link_state_player_address(self.link_player_address_var.get())

    def apply_link_burn(self) -> None:
        self.presenter.apply_link_burn(self.link_burn_value_var.get())

    def clear_link_burn(self) -> None:
        self.presenter.clear_link_burn()

    def apply_link_freeze(self) -> None:
        self.presenter.apply_link_freeze(self.link_freeze_value_var.get())

    def apply_link_shock(self) -> None:
        self.presenter.apply_link_shock(self.link_shock_value_var.get())

    def connect_twitch(self) -> None:
        self.presenter.connect_twitch()

    def disconnect_twitch(self) -> None:
        self.presenter.disconnect_twitch()

    def reset_twitch_tokens(self) -> None:
        self.presenter.reset_twitch_tokens()

    def simulate_twitch_reward(self) -> None:
        self.presenter.simulate_twitch_reward(
            self.twitch_test_reward_var.get(),
            self.twitch_test_input_var.get(),
            self.twitch_test_user_var.get(),
        )

    def open_bridge_log(self) -> None:
        self.open_log_window()
