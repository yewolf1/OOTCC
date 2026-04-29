from __future__ import annotations

from typing import Any, Callable

from core.controllers.app_controller import AppController
from core.definitions.inventory_definitions import (
    AMMO_SLOTS,
    BUTTON_ASSIGNABLE_ITEMS,
    BUTTON_LAYOUT,
    ITEM_SLOTS,
    SWORD_BUTTON_MODES,
    WARP_SONG_DESTINATIONS,
)
from services.view_model.view_models import (
    AppViewModel,
    ButtonsViewModel,
    EquipmentViewModel,
    HealthViewModel,
    InventoryViewModel,
    LinkStateViewModel,
    MagicViewModel,
    QuestStatusViewModel,
    RupeesViewModel,
    StatusViewModel,
    TeleportViewModel,
    TwitchViewModel,
)


class BridgePresenter:
    """Coordinates UI commands, controller calls, and view model generation."""

    def __init__(self, view: Any, controller: AppController) -> None:
        self.view = view
        self.controller = controller
        self._last_random_result_text = "Random pool not loaded"

    def initialize(self) -> None:
        self.refresh_state()

    def refresh_state(self, force_runtime_scan: bool = False) -> None:
        self.controller.process_twitch_timers()
        self.view.render(self._build_app_view_model(force_runtime_scan=force_runtime_scan))

    def apply_current_health(self, hearts: float) -> None:
        self._run(lambda: self.controller.set_health_hearts(hearts), "Bridge error")

    def adjust_current_health(self, delta: float) -> None:
        state = self.controller.refresh()
        target = max(0.0, state.current_hearts + delta)
        self.apply_current_health(target)

    def apply_max_health(self, hearts: float) -> None:
        self._run(lambda: self.controller.set_max_health_hearts(hearts), "Bridge error")

    def adjust_max_health(self, delta: float) -> None:
        state = self.controller.refresh()
        target = max(1.0, state.max_hearts + delta)
        self.apply_max_health(target)

    def full_heal(self) -> None:
        self._run(self.controller.full_heal, "Bridge error")

    def simulate_reward(self, viewer: str, reward_title: str, hearts_delta: float) -> None:
        self._run(
            lambda: self.controller.simulate_reward(viewer, reward_title, hearts_delta),
            "Reward error",
        )

    def connect_twitch(self) -> None:
        self._run(self.controller.connect_twitch, "Twitch error")

    def disconnect_twitch(self) -> None:
        self._run(self.controller.disconnect_twitch, "Twitch error")

    def reset_twitch_tokens(self) -> None:
        self._run(self.controller.reset_twitch_tokens, "Twitch error")

    def simulate_twitch_reward(self, reward_title: str, user_input: str, user_name: str) -> None:
        self._run(lambda: self.controller._handle_twitch_redeem(reward_title, user_input, user_name), "Twitch error")

    def apply_item_value(self, slot: int, selected_label: str, choice_map: dict[str, int]) -> None:
        def action() -> None:
            value = choice_map[selected_label]
            self.controller.set_item_value(slot, value)

        self._run(action, "Item error")

    def clear_item_slot(self, slot: int) -> None:
        self._run(lambda: self.controller.clear_item(slot), "Item error")

    def apply_ammo_slot(self, slot: int, raw_value: str) -> None:
        self._run(lambda: self.controller.set_ammo(slot, int(raw_value)), "Ammo error")

    def zero_ammo_slot(self, slot: int) -> None:
        self._run(lambda: self.controller.set_ammo(slot, 0), "Ammo error")

    def apply_magic_current(self, raw_value: str) -> None:
        self._run(lambda: self.controller.set_magic_current(int(raw_value)), "Magic error")

    def apply_magic_level(self, level_label: str) -> None:
        mapping = {
            "No magic": 0,
            "Normal magic": 1,
            "Double magic": 2,
        }
        self._run(lambda: self.controller.set_magic_level(mapping[level_label]), "Magic error")

    def fill_magic(self) -> None:
        self._run(self.controller.fill_magic, "Magic error")

    def empty_magic(self) -> None:
        self._run(self.controller.empty_magic, "Magic error")

    def apply_rupees(self, raw_value: str) -> None:
        self._run(lambda: self.controller.set_rupees(int(raw_value)), "Rupees error")

    def adjust_rupees(self, delta: int) -> None:
        self._run(lambda: self.controller.adjust_rupees(delta), "Rupees error")

    def fill_rupees(self) -> None:
        self._run(self.controller.fill_rupees, "Rupees error")

    def zero_rupees(self) -> None:
        self._run(lambda: self.controller.set_rupees(0), "Rupees error")

    def add_equipment_item(self, group_key: str, item_key: str) -> None:
        self._run(lambda: self.controller.add_equipment_item(group_key, item_key), "Equipment error")

    def remove_equipment_item(self, group_key: str, item_key: str) -> None:
        self._run(lambda: self.controller.remove_equipment_item(group_key, item_key), "Equipment error")

    def equip_equipment_item(self, group_key: str, item_key: str) -> None:
        self._run(lambda: self.controller.equip_equipment_item(group_key, item_key), "Equipment error")

    def increase_upgrade_level(self, upgrade_key: str) -> None:
        self._run(lambda: self.controller.increase_upgrade_level(upgrade_key), "Upgrade error")

    def decrease_upgrade_level(self, upgrade_key: str) -> None:
        self._run(lambda: self.controller.decrease_upgrade_level(upgrade_key), "Upgrade error")

    def apply_button_assignment(self, button_key: str, selected_label: str, choice_map: dict[str, str]) -> None:
        def action() -> None:
            item_key = choice_map[selected_label]
            self.controller.set_button_assignment(button_key, item_key)

        self._run(action, "Button error")

    def clear_button_assignment(self, button_key: str) -> None:
        self._run(lambda: self.controller.clear_button_assignment(button_key), "Button error")

    def apply_sword_mode(self, sword_mode_label: str) -> None:
        reverse_map = {label: key for key, label in SWORD_BUTTON_MODES.items()}
        self._run(lambda: self.controller.set_sword_mode(reverse_map[sword_mode_label]), "Button error")

    def teleport_to_warp_song(self, destination_key: str) -> None:
        self._run(lambda: self.controller.teleport_to_warp_song(destination_key), "Teleport error")

    def teleport_random_safe(self) -> None:
        def action() -> None:
            destination = self.controller.teleport_random_safe()
            self._last_random_result_text = (
                f"Last random result: {destination['label']}\n"
                f"{destination['entrance_name']} | 0x{destination['entrance_id']:04X}"
            )

        self._run(action, "Teleport error")

    def toggle_quest_flag(self, flag_key: str, enabled: bool) -> None:
        self._run(lambda: self.controller.set_quest_flag(flag_key, enabled), "Quest status error")

    def apply_equips_equipment(self, raw_value: str) -> None:
        self._run(lambda: self.controller.set_equips_equipment(int(raw_value)), "Equipment error")

    def apply_inventory_equipment(self, raw_value: str) -> None:
        self._run(lambda: self.controller.set_inventory_equipment(int(raw_value)), "Equipment error")

    def apply_equipment(self, raw_value: str) -> None:
        self._run(lambda: self.controller.set_equipment(int(raw_value)), "Equipment error")

    def apply_upgrades(self, raw_value: str) -> None:
        self._run(lambda: self.controller.set_upgrades(int(raw_value)), "Upgrades error")

    def apply_quest_items(self, raw_value: str) -> None:
        self._run(lambda: self.controller.set_quest_items(int(raw_value)), "Quest items error")

    def ensure_dll_bridge_injected(self) -> None:
        self._run(self.controller.ensure_dll_bridge_injected, "Link state error")

    def execute_dll_bridge_command(self, command: str) -> None:
        self._run(lambda: self.controller.execute_dll_bridge_command(command), "Link state error")

    def apply_link_state_player_address(self, raw_value: str) -> None:
        self._run(lambda: self.controller.set_link_state_player_address(raw_value), "Link state error")

    def apply_link_burn(self, raw_value: str) -> None:
        self._run(lambda: self.controller.apply_link_burn(int(raw_value)), "Link state error")

    def clear_link_burn(self) -> None:
        self._run(self.controller.clear_link_burn, "Link state error")

    def apply_link_freeze(self, raw_value: str) -> None:
        self._run(lambda: self.controller.apply_link_freeze(int(raw_value)), "Link state error")

    def apply_link_shock(self, raw_value: str) -> None:
        self._run(lambda: self.controller.apply_link_shock(int(raw_value)), "Link state error")

    def _run(self, action: Callable[[], None], error_title: str) -> None:
        try:
            action()
        except Exception as exc:
            self.view.show_error(error_title, str(exc))
        finally:
            self.refresh_state()

    def _build_app_view_model(self, force_runtime_scan: bool = False) -> AppViewModel:
        health_state = self.controller.refresh(force_runtime_scan=force_runtime_scan)

        return AppViewModel(
            status=self._build_status_view_model(health_state),
            health=self._build_health_view_model(health_state),
            rupees=self._build_rupees_view_model(),
            inventory=self._build_inventory_view_model(),
            magic=self._build_magic_view_model(),
            equipment=self._build_equipment_view_model(),
            buttons=self._build_buttons_view_model(),
            teleport=self._build_teleport_view_model(),
            link_state=self._build_link_state_view_model(),
            quest_status=self._build_quest_status_view_model(),
            twitch=self._build_twitch_view_model(),
            logs=self.controller.log_lines(),
        )

    def _build_status_view_model(self, health_state: Any) -> StatusViewModel:
        return StatusViewModel(
            status_text="Attached" if health_state.attached else "Offline",
            build_text=health_state.version_label,
            hearts_text=f"{health_state.current_hearts:.2f} / {health_state.max_hearts:.2f} hearts",
            message_text=health_state.message,
        )

    def _build_health_view_model(self, health_state: Any) -> HealthViewModel:
        ui_max = max(3.0, health_state.max_hearts, 20.0)
        return HealthViewModel(
            summary_text=(
                f"Current: {health_state.current_hearts:.2f} hearts ({health_state.current_quarters}/16)\n"
                f"Max: {health_state.max_hearts:.2f} hearts ({health_state.max_quarters}/16)"
            ),
            current_hearts=max(0.0, health_state.current_hearts),
            max_hearts=max(1.0, health_state.max_hearts),
            current_slider_max=ui_max,
            max_slider_max=max(20.0, health_state.max_hearts + 5.0),
            current_steps=max(48, int(ui_max * 16)),
            max_steps=320,
        )

    def _build_rupees_view_model(self) -> RupeesViewModel:
        try:
            state = self.controller.get_rupee_state()
            return RupeesViewModel(
                current_value=str(state.get("current", 0)),
                summary_text=(
                    f"Current: {state.get('current', 0)}\n"
                    f"Wallet: {state.get('wallet_label', 'Unknown')}\n"
                    f"Suggested cap: {state.get('capacity', 0)}"
                ),
            )
        except Exception:
            return RupeesViewModel(current_value="0", summary_text="Rupees unavailable")

    def _build_inventory_view_model(self) -> InventoryViewModel:
        try:
            inventory = self.controller.get_inventory()
            ammo = self.controller.get_ammo()
            item_texts: dict[int, str] = {}
            item_selected_labels: dict[int, str] = {}
            ammo_texts: dict[int, str] = {}

            for slot in ITEM_SLOTS:
                raw_value = inventory.get(slot, 0)
                item_texts[slot] = self._format_item_value(slot, raw_value)
                item_selected_labels[slot] = self._choice_label(slot, raw_value)

            for slot in AMMO_SLOTS:
                ammo_texts[slot] = str(ammo.get(slot, 0))

            return InventoryViewModel(
                item_texts=item_texts,
                item_selected_labels=item_selected_labels,
                ammo_texts=ammo_texts,
            )
        except Exception:
            return InventoryViewModel(
                item_texts={slot: "0" for slot in ITEM_SLOTS},
                item_selected_labels={},
                ammo_texts={slot: "0" for slot in AMMO_SLOTS},
            )

    def _build_magic_view_model(self) -> MagicViewModel:
        try:
            state = self.controller.get_magic_state()
            return MagicViewModel(
                current_value=str(state.get("current", 0)),
                level_label=state.get("level_label", "No magic"),
                summary_text=(
                    f"Current: {state.get('current', 0)} / {state.get('max', 0)}\n"
                    f"Flags: acquired={int(bool(state.get('acquired')))} | double={int(bool(state.get('double_acquired')))}\n"
                    f"Runtime: level={state.get('level', 0)} | state={state.get('magic_state', 0)} | capacity={state.get('magic_capacity', 0)}"
                ),
            )
        except Exception:
            return MagicViewModel(
                current_value="0",
                level_label="No magic",
                summary_text="Magic unavailable",
            )

    def _build_equipment_view_model(self) -> EquipmentViewModel:
        raw_field_values = {
            "equips_equipment": "0",
            "inventory_equipment": "0",
            "equipment": "0",
            "upgrades": "0",
            "quest_items": "0",
        }
        try:
            raw_field_values = {
                "equips_equipment": str(self.controller.get_equips_equipment()),
                "inventory_equipment": str(self.controller.get_inventory_equipment()),
                "equipment": str(self.controller.get_equipment()),
                "upgrades": str(self.controller.get_upgrades()),
                "quest_items": str(self.controller.get_quest_items()),
            }
        except Exception:
            pass

        try:
            snapshot = self.controller.get_equipment_snapshot()
            group_texts: dict[str, str] = {}
            entry_texts: dict[str, str] = {}
            upgrade_texts: dict[str, str] = {}

            for group_key, group_state in snapshot.get("groups", {}).items():
                entries_state = group_state.get("entries", [])
                equipped_labels = [entry["label"] for entry in entries_state if entry.get("equipped")]
                owned_count = sum(1 for entry in entries_state if entry.get("owned"))
                equipped_label = equipped_labels[0] if equipped_labels else "None"
                group_texts[group_key] = f"Owned: {owned_count} | Equipped: {equipped_label}"

                for entry in entries_state:
                    if entry.get("equipped"):
                        entry_texts[entry["key"]] = "Equipped"
                    elif entry.get("owned"):
                        entry_texts[entry["key"]] = "Owned"
                    else:
                        entry_texts[entry["key"]] = "Missing"

            for upgrade_key, upgrade_state in snapshot.get("upgrades", {}).items():
                level = upgrade_state.get("level", 0)
                max_level = upgrade_state.get("max_level", 0)
                level_label = upgrade_state.get("level_label", "Unknown")
                upgrade_texts[upgrade_key] = f"Level {level}/{max_level} - {level_label}"

            return EquipmentViewModel(
                summary_text=(
                    f"Owned=0x{snapshot.get('owned_mask', 0):04X} | "
                    f"Equipped=0x{snapshot.get('equipped_mask', 0):04X} | "
                    f"Upgrades=0x{snapshot.get('upgrades_mask', 0):08X}"
                ),
                raw_field_values=raw_field_values,
                group_texts=group_texts,
                entry_texts=entry_texts,
                upgrade_texts=upgrade_texts,
            )
        except Exception:
            return EquipmentViewModel(
                summary_text="Equipment snapshot unavailable",
                raw_field_values=raw_field_values,
            )

    def _build_buttons_view_model(self) -> ButtonsViewModel:
        try:
            state = self.controller.get_button_state()
            value_texts: dict[str, str] = {}
            selected_labels: dict[str, str] = {}
            summary_lines: list[str] = []

            for button_key, button_label in BUTTON_LAYOUT:
                button_state = state.get(button_key, {})
                label = button_state.get("item_label", "Unknown")
                value = button_state.get("value", 0)
                line = f"{button_label}: {label} (0x{value:02X})"
                value_texts[button_key] = line
                summary_lines.append(line)
                selected_labels[button_key] = BUTTON_ASSIGNABLE_ITEMS.get(button_state.get("item_key", "none"), "None")

            return ButtonsViewModel(
                summary_text="\n".join(summary_lines),
                sword_mode_label=SWORD_BUTTON_MODES.get(state.get("sword_mode", "none"), "Swordless"),
                value_texts=value_texts,
                selected_labels=selected_labels,
            )
        except Exception:
            return ButtonsViewModel(
                summary_text="Buttons unavailable",
                sword_mode_label="Swordless",
                value_texts={button_key: "Unknown" for button_key, _ in BUTTON_LAYOUT},
                selected_labels={},
            )

    def _build_teleport_view_model(self) -> TeleportViewModel:
        try:
            state = self.controller.get_teleport_state()
            status_texts: dict[str, str] = {}
            for destination_key, destination in WARP_SONG_DESTINATIONS.items():
                status = "Last used" if state.get("last_runtime_teleport_key") == destination_key else "Ready"
                status_texts[destination_key] = f"{status} | params 0x{destination.get('player_params', 0):04X}"

            random_result_text = self._last_random_result_text
            if random_result_text == "Random pool not loaded":
                random_result_text = "Random pool ready"

            return TeleportViewModel(
                summary_text=(
                    f"Current runtime entrance: 0x{state.get('next_entrance', 0):04X}\n"
                    f"Last mapped destination: {state.get('destination_label', 'Unknown')}\n"
                    f"Transition trigger: {state.get('transition_trigger', 0)} | transition type: 0x{state.get('transition_type', 0):02X}\n"
                    f"gPlayState: 0x{state.get('gplaystate', 0):X}"
                ),
                random_result_text=random_result_text,
                status_texts=status_texts,
            )
        except Exception:
            return TeleportViewModel(
                summary_text="Runtime teleport unavailable",
                random_result_text="Random pool unavailable",
                status_texts={key: "Unknown" for key in WARP_SONG_DESTINATIONS},
            )


    def _build_link_state_view_model(self) -> LinkStateViewModel:
        bridge_summary_text = "DLL bridge unavailable"

        try:
            bridge_status = self.controller.get_dll_bridge_status()
            host_found = bridge_status.get("host_exists", False)
            dll_found = bridge_status.get("dll_exists", False)
            attached = bridge_status.get("attached", False)
            pid = int(bridge_status.get("pid", 0))

            bridge_summary_text = (
                f"Host: {'OK' if host_found else 'Missing'} | "
                f"DLL: {'OK' if dll_found else 'Missing'} | "
                f"SoH attached: {'Yes' if attached else 'No'}"
            )

            if pid:
                bridge_summary_text += f"\nPID: {pid}"
        except Exception:
            bridge_summary_text = "DLL bridge unavailable"

        try:
            state = self.controller.get_link_state()
            burn_flames = state.get("burn_flames", [])
            active_flames = sum(1 for value in burn_flames if int(value) > 0)
            player_address = int(state.get("player_address", 0))

            return LinkStateViewModel(
                summary_text=(
                    f"Player: 0x{player_address:016X}\n"
                    f"Freeze timer: {state.get('freeze_timer', 0)} | Shock timer: {state.get('shock_timer', 0)}\n"
                    f"Burn flag: {state.get('burn_flag', 0)} | Active flame bytes: {active_flames}/{len(burn_flames)}"
                ),
                bridge_summary_text=bridge_summary_text,
                player_address_text=f"0x{player_address:016X}",
                burn_value_text=str(burn_flames[0] if burn_flames else 120),
                freeze_value_text=str(state.get("freeze_timer", 40)),
                shock_value_text=str(state.get("shock_timer", 40)),
            )
        except Exception:
            return LinkStateViewModel(
                summary_text="Link state unavailable. Set a valid runtime Player address first.",
                bridge_summary_text=bridge_summary_text,
                player_address_text="",
                burn_value_text="120",
                freeze_value_text="40",
                shock_value_text="40",
            )

    def _build_quest_status_view_model(self) -> QuestStatusViewModel:
        try:
            quest_status = self.controller.get_quest_status()
            if hasattr(quest_status, "flags"):
                flags = dict(quest_status.flags)
            elif isinstance(quest_status, dict):
                flags = dict(quest_status)
            else:
                flags = {}
            return QuestStatusViewModel(flags=flags)
        except Exception:
            return QuestStatusViewModel(flags={})

    def _build_twitch_view_model(self) -> TwitchViewModel:
        try:
            state = self.controller.get_twitch_state()
            return TwitchViewModel(
                status_text=state.get("status_text", "Disconnected"),
                config_path=state.get("config_path", ""),
                channel_login=state.get("channel_login", ""),
                last_event_text=state.get("last_event_text", "No Twitch redeem received yet"),
            )
        except Exception:
            return TwitchViewModel(
                status_text="Disconnected",
                config_path="",
                channel_login="",
                last_event_text="No Twitch redeem received yet",
            )

    def _format_item_value(self, slot: int, value: int) -> str:
        item_def = ITEM_SLOTS.get(slot)
        if not item_def:
            return str(value)
        if value == item_def.get("clear_value", 0xFF):
            return "Empty"
        label = item_def["choices"].get(value)
        if label:
            return label
        return f"Unknown ({value})"

    def _choice_label(self, slot: int, value: int) -> str:
        item_def = ITEM_SLOTS.get(slot)
        if not item_def:
            return str(value)
        label = item_def["choices"].get(value)
        if label:
            return f"{value} - {label}"
        choices = item_def["choices"]
        if choices:
            first_raw_value, first_label = next(iter(choices.items()))
            return f"{first_raw_value} - {first_label}"
        return str(value)
