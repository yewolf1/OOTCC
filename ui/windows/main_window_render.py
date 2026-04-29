from __future__ import annotations

from tkinter import messagebox

from services.view_model.view_models import AppViewModel


class MainWindowRenderMixin:
    """Applies presenter-provided view models to tkinter variables and widgets."""

    def render(self, view_model: AppViewModel) -> None:
        self._render_status(view_model)
        self._render_health(view_model)
        self._render_rupees(view_model)
        self._render_inventory(view_model)
        self._render_magic(view_model)
        self._render_equipment(view_model)
        self._render_buttons(view_model)
        self._render_teleport(view_model)
        self._render_link_state(view_model)
        self._render_quest_status(view_model)
        self._render_twitch(view_model)
        self._render_logs(view_model.logs)

    def show_error(self, title: str, message: str) -> None:
        messagebox.showerror(title, message)

    def _render_status(self, view_model: AppViewModel) -> None:
        self.status_var.set(view_model.status.status_text)
        self.build_var.set(view_model.status.build_text)
        self.hearts_var.set(view_model.status.hearts_text)
        self.message_var.set(view_model.status.message_text)

    def _render_health(self, view_model: AppViewModel) -> None:
        self.health_summary_var.set(view_model.health.summary_text)
        self.health_slider.configure(
            to=view_model.health.current_slider_max,
            number_of_steps=view_model.health.current_steps,
        )
        self.health_slider_var.set(view_model.health.current_hearts)
        self.max_health_slider.configure(
            to=view_model.health.max_slider_max,
            number_of_steps=view_model.health.max_steps,
        )
        self.max_health_slider_var.set(view_model.health.max_hearts)

    def _render_rupees(self, view_model: AppViewModel) -> None:
        self.rupees_var.set(view_model.rupees.current_value)
        self.rupees_summary_var.set(view_model.rupees.summary_text)

    def _render_inventory(self, view_model: AppViewModel) -> None:
        for slot, var in self.item_vars.items():
            var.set(view_model.inventory.item_texts.get(slot, "0"))
        for slot, var in self.item_select_vars.items():
            selected_label = view_model.inventory.item_selected_labels.get(slot)
            if selected_label and selected_label in self.item_choice_maps[slot]:
                var.set(selected_label)
        for slot, var in self.ammo_vars.items():
            var.set(view_model.inventory.ammo_texts.get(slot, "0"))

    def _render_magic(self, view_model: AppViewModel) -> None:
        self.magic_current_var.set(view_model.magic.current_value)
        self.magic_level_var.set(view_model.magic.level_label)
        self.magic_summary_var.set(view_model.magic.summary_text)

    def _render_equipment(self, view_model: AppViewModel) -> None:
        self.equipment_summary_var.set(view_model.equipment.summary_text)
        self.equips_equipment_var.set(view_model.equipment.raw_field_values.get("equips_equipment", "0"))
        self.inventory_equipment_var.set(view_model.equipment.raw_field_values.get("inventory_equipment", "0"))
        self.equipment_var.set(view_model.equipment.raw_field_values.get("equipment", "0"))
        self.upgrades_var.set(view_model.equipment.raw_field_values.get("upgrades", "0"))
        self.quest_items_var.set(view_model.equipment.raw_field_values.get("quest_items", "0"))

        for group_key, var in self.equipment_group_vars.items():
            var.set(view_model.equipment.group_texts.get(group_key, "No data"))
        for item_key, var in self.equipment_entry_vars.items():
            var.set(view_model.equipment.entry_texts.get(item_key, "Unknown"))
        for upgrade_key, var in self.upgrade_level_vars.items():
            var.set(view_model.equipment.upgrade_texts.get(upgrade_key, "Unknown"))

    def _render_buttons(self, view_model: AppViewModel) -> None:
        self.button_summary_var.set(view_model.buttons.summary_text)
        self.sword_mode_var.set(view_model.buttons.sword_mode_label)
        for button_key, var in self.button_value_vars.items():
            var.set(view_model.buttons.value_texts.get(button_key, "Unknown"))
        for button_key, var in self.button_select_vars.items():
            selected_label = view_model.buttons.selected_labels.get(button_key)
            if selected_label and selected_label in self.button_choice_maps[button_key]:
                var.set(selected_label)

    def _render_teleport(self, view_model: AppViewModel) -> None:
        self.teleport_summary_var.set(view_model.teleport.summary_text)
        self.teleport_random_result_var.set(view_model.teleport.random_result_text)
        for destination_key, var in self.teleport_status_vars.items():
            var.set(view_model.teleport.status_texts.get(destination_key, "Unknown"))

    def _render_link_state(self, view_model: AppViewModel) -> None:
        self.link_state_summary_var.set(view_model.link_state.summary_text)
        self.link_bridge_summary_var.set(view_model.link_state.bridge_summary_text)
        self.link_player_address_var.set(view_model.link_state.player_address_text)
        self.link_burn_value_var.set(view_model.link_state.burn_value_text)
        self.link_freeze_value_var.set(view_model.link_state.freeze_value_text)
        self.link_shock_value_var.set(view_model.link_state.shock_value_text)

    def _render_quest_status(self, view_model: AppViewModel) -> None:
        for key, var in self.quest_flag_vars.items():
            var.set(bool(view_model.quest_status.flags.get(key, False)))

    def _render_twitch(self, view_model: AppViewModel) -> None:
        self.twitch_status_var.set(view_model.twitch.status_text)
        self.twitch_config_path_var.set(view_model.twitch.config_path)
        self.twitch_channel_login_var.set(view_model.twitch.channel_login)
        self.twitch_last_event_var.set(view_model.twitch.last_event_text)

    def _render_logs(self, lines: list[str]) -> None:
        self.current_log_lines = list(lines)
        self._sync_log_window()
