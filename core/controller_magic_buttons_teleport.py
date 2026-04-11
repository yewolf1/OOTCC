from __future__ import annotations

from core.inventory_definitions import BUTTON_ASSIGNABLE_ITEMS, BUTTON_LAYOUT


class MagicButtonsTeleportControllerMixin:
    def get_magic_state(self) -> dict:
        """Return the current magic state and its derived label."""
        adapter = self._require_save_adapter()
        level = adapter.get_magic_level()
        current = adapter.get_magic_current()
        acquired = adapter.get_magic_acquired()
        double_acquired = adapter.get_double_magic_acquired()
        max_magic = adapter.get_effective_magic_capacity()

        if not acquired:
            level_label = "No magic"
        elif double_acquired:
            level_label = "Double magic"
        else:
            level_label = "Normal magic"

        return {
            "level": level,
            "level_label": level_label,
            "current": current,
            "max": max_magic,
            "acquired": acquired,
            "double_acquired": double_acquired,
            "magic_state": adapter.get_magic_state_value(),
            "magic_capacity": adapter.get_magic_capacity_value(),
            "fill_target": adapter.get_magic_fill_target_value(),
            "target": adapter.get_magic_target_value(),
        }

    def set_magic_level(self, level: int) -> None:
        """
        Reinitialize magic according to the requested level.

        The adapter owns the low-level reset sequence because several magic
        fields must be kept internally consistent to avoid broken runtime state.
        """
        adapter = self._require_save_adapter()

        if level < 0 or level > 2:
            raise ValueError(f"Invalid magic level: {level}")

        if level <= 0:
            adapter.disable_magic()
            self._log("Magic disabled")
            return

        adapter.apply_magic_reinit(double_magic=(level == 2))
        self._log("Triggered magic reinit: double" if level == 2 else "Triggered magic reinit: normal")

    def set_magic_current(self, value: int) -> None:
        """Write current magic after adapter-side clamping."""
        adapter = self._require_save_adapter()
        clamped = adapter.set_magic_current_direct(value)
        self._log(f"Magic current set to {clamped}/{adapter.get_effective_magic_capacity()}")

    def fill_magic(self) -> None:
        """Fill magic to current capacity."""
        adapter = self._require_save_adapter()
        clamped = adapter.set_magic_current_direct(adapter.get_effective_magic_capacity())
        self._log(f"Magic filled to {clamped}/{adapter.get_effective_magic_capacity()}")

    def empty_magic(self) -> None:
        """Empty magic completely."""
        adapter = self._require_save_adapter()
        adapter.set_magic_current_direct(0)
        self._log("Magic emptied")

    def get_button_state(self) -> dict:
        """
        Build a UI-friendly view of button assignments.

        Raw memory stores item values, but the UI needs symbolic keys and labels,
        so this method reverses the adapter mapping and enriches each entry.
        """
        adapter = self._require_save_adapter()
        raw = adapter.get_button_assignments()
        reverse_map = {value: key for key, value in adapter.get_button_items_map().items()}

        assignments = {}
        for button_key, _label in BUTTON_LAYOUT:
            value = raw.get(button_key, 0xFF)
            item_key = reverse_map.get(value, "unknown")
            assignments[button_key] = {
                "value": value,
                "item_key": item_key,
                "item_label": BUTTON_ASSIGNABLE_ITEMS.get(item_key, f"0x{value:02X}"),
            }

        assignments["sword_mode"] = {
            0: "none",
            1: "kokiri",
            2: "master",
            3: "biggoron",
        }.get(adapter.get_live_sword_nibble(), "none")

        return assignments

    def set_button_assignment(self, button_key: str, item_key: str) -> None:
        """Assign one non-B button."""
        adapter = self._require_save_adapter()
        if button_key == "b":
            raise ValueError("Use sword mode for the B button")
        adapter.set_button_item(button_key, item_key)
        self._log(f"Button assigned: {button_key}={item_key}")

    def clear_button_assignment(self, button_key: str) -> None:
        """Clear one button assignment."""
        adapter = self._require_save_adapter()
        if button_key == "b":
            adapter.apply_swordless()
            self._log("B button set to swordless")
            return
        adapter.clear_button_item(button_key)
        self._log(f"Button cleared: {button_key}")

    def set_sword_mode(self, sword_mode: str) -> None:
        """Apply one sword mode to both equips and the B button."""
        adapter = self._require_save_adapter()
        adapter.equip_live_sword(sword_mode)
        if sword_mode == "none":
            self._log("Sword mode set: swordless")
        else:
            self._log(f"Sword mode set: {sword_mode}")

    def get_warp_song_destinations(self) -> dict:
        """Expose the song destinations shown in the teleport UI."""
        return self.teleport_service.get_warp_song_destinations()

    def get_teleport_destinations(self) -> dict:
        """Expose every configured teleport destination."""
        return self.teleport_service.get_all_destinations()

    def get_safe_random_destinations(self) -> dict:
        """Expose the conservative pool used by random safe teleport."""
        return self.teleport_service.get_safe_random_destinations()

    def get_teleport_state(self) -> dict:
        """Read and enrich the current runtime warp state for the UI."""
        adapter = self._require_save_adapter()
        return self.teleport_service.get_runtime_state(adapter)

    def teleport_to_destination(self, destination_key: str) -> None:
        """Teleport Link to one configured destination and log the action."""
        adapter = self._require_save_adapter()
        destination = self.teleport_service.teleport_to_destination(adapter, destination_key)
        self._log(
            f"Runtime teleport: {destination['label']} "
            f"({destination['entrance_name']} / 0x{int(destination['entrance_id']):04X})"
        )

    def teleport_to_warp_song(self, destination_key: str) -> None:
        """Teleport Link to one of the validated song destinations."""
        adapter = self._require_save_adapter()
        destination = self.teleport_service.teleport_to_warp_song(adapter, destination_key)
        self._log(
            f"Warp song teleport: {destination['label']} "
            f"({destination['entrance_name']} / 0x{int(destination['entrance_id']):04X})"
        )

    def teleport_random_safe(self) -> dict:
        """Teleport to a random destination from the conservative safe pool."""
        adapter = self._require_save_adapter()
        destination = self.teleport_service.teleport_random_safe(adapter)
        self._log(
            f"Random safe teleport: {destination['label']} "
            f"({destination['entrance_name']} / 0x{int(destination['entrance_id']):04X})"
        )
        return dict(destination)



    def get_dll_bridge_status(self) -> dict:
        state = self.refresh()
        status = self.dll_bridge.get_status()
        status["attached"] = bool(state.attached)
        status["pid"] = getattr(getattr(self.adapter, "fingerprint", None), "pid", 0)
        return status

    def ensure_dll_bridge_injected(self) -> str:
        state = self.refresh()
        if not state.attached or not self.adapter:
            raise RuntimeError("SoH is not attached")
        output = self.dll_bridge.execute(self.adapter.fingerprint.pid, "inject_only")
        self._log("DLL bridge injected or already ready")
        return output

    def execute_dll_bridge_command(self, command: str) -> str:
        state = self.refresh()
        if not state.attached or not self.adapter:
            raise RuntimeError("SoH is not attached")
        output = self.dll_bridge.execute(self.adapter.fingerprint.pid, command)
        self._log(f"DLL bridge command: {command}")
        return output

    def set_link_state_player_address(self, raw_address: str) -> int:
        """Store the runtime Player address override used by link-state actions."""
        normalized = raw_address.strip()
        if normalized == "":
            raise ValueError("Player address is required")
        address = int(normalized, 16) if normalized.lower().startswith("0x") else int(normalized, 16)
        adapter = self._require_save_adapter()
        adapter.set_manual_player_address(address)
        self._log(f"Link state Player address set to 0x{address:016X}")
        return address

    def get_link_state(self) -> dict:
        adapter = self._require_save_adapter()
        return adapter.get_link_state()

    def apply_link_burn(self, flame_value: int) -> int:
        adapter = self._require_save_adapter()
        clamped = adapter.set_link_burn(flame_value)
        self._log(f"Applied burn state with flame value {clamped}")
        return clamped

    def clear_link_burn(self) -> None:
        adapter = self._require_save_adapter()
        adapter.clear_link_burn()
        self._log("Cleared burn state")

    def apply_link_freeze(self, duration: int) -> int:
        adapter = self._require_save_adapter()
        clamped = adapter.set_link_freeze(duration)
        self._log(f"Applied freeze timer {clamped}")
        return clamped

    def apply_link_shock(self, duration: int) -> int:
        adapter = self._require_save_adapter()
        clamped = adapter.set_link_shock(duration)
        self._log(f"Applied shock timer {clamped}")
        return clamped
