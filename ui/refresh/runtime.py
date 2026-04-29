from __future__ import annotations

from core.definitions.inventory_definitions import BUTTON_ASSIGNABLE_ITEMS, BUTTON_LAYOUT, SWORD_BUTTON_MODES, WARP_SONG_DESTINATIONS

"""Refresh helpers for magic, buttons, and teleport runtime state."""

class MainWindowRuntimeRefreshMixin:
    def _refresh_magic_ui(self) -> None:
        try:
            state = self.controller.get_magic_state()
            self.magic_current_var.set(str(state.get("current", 0)))
            self.magic_level_var.set(state.get("level_label", "No magic"))
            self.magic_summary_var.set(
                f"Current: {state.get('current', 0)} / {state.get('max', 0)}\n"
                f"Flags: acquired={int(bool(state.get('acquired')))} | double={int(bool(state.get('double_acquired')))}\n"
                f"Runtime: level={state.get('level', 0)} | state={state.get('magic_state', 0)} | capacity={state.get('magic_capacity', 0)}"
            )
        except Exception:
            self.magic_current_var.set("0")
            self.magic_level_var.set("No magic")
            self.magic_summary_var.set("Magic unavailable")

    def _refresh_buttons_ui(self) -> None:
        try:
            state = self.controller.get_button_state()
            self.sword_mode_var.set(SWORD_BUTTON_MODES.get(state.get("sword_mode", "none"), "Swordless"))
            lines: list[str] = []
            for button_key, button_label in BUTTON_LAYOUT:
                button_state = state.get(button_key, {})
                label = button_state.get("item_label", "Unknown")
                value = button_state.get("value", 0)
                line = f"{button_label}: {label} (0x{value:02X})"
                lines.append(line)
                if button_key in self.button_value_vars:
                    self.button_value_vars[button_key].set(line)
                if button_key in self.button_select_vars:
                    current_label = BUTTON_ASSIGNABLE_ITEMS.get(button_state.get("item_key", "none"), "None")
                    if current_label in self.button_choice_maps[button_key]:
                        self.button_select_vars[button_key].set(current_label)
            self.button_summary_var.set("\n".join(lines))
        except Exception:
            self.button_summary_var.set("Buttons unavailable")
            for var in self.button_value_vars.values():
                var.set("Unknown")
            self.sword_mode_var.set("Swordless")

    def _refresh_teleport_ui(self) -> None:
        try:
            state = self.controller.get_teleport_state()
            destination_label = state.get("destination_label", "Unknown")
            self.teleport_summary_var.set(
                f"Current runtime entrance: 0x{state.get('next_entrance', 0):04X}\n"
                f"Last mapped destination: {destination_label}\n"
                f"Transition trigger: {state.get('transition_trigger', 0)} | transition type: 0x{state.get('transition_type', 0):02X}\n"
                f"gPlayState: 0x{state.get('gplaystate', 0):X}"
            )
            for destination_key, destination in WARP_SONG_DESTINATIONS.items():
                status = "Last used" if state.get("last_runtime_teleport_key") == destination_key else "Ready"
                self.teleport_status_vars[destination_key].set(
                    f"{status} | params 0x{destination.get('player_params', 0):04X}"
                )
            if not self.teleport_random_result_var.get():
                self.teleport_random_result_var.set("Random pool ready")
        except Exception:
            self.teleport_summary_var.set("Runtime teleport unavailable")
            self.teleport_random_result_var.set("Random pool unavailable")
            for var in self.teleport_status_vars.values():
                var.set("Unknown")
