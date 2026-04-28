from __future__ import annotations

from core.inventory_definitions import BUTTON_ASSIGNABLE_ITEMS, BUTTON_LAYOUT
from adapter.pdb_symbol_resolver import PdbSymbolResolver


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



    def _dll_symbol_candidates(self) -> dict[str, list[str]]:
        runtime = self.profile.get("runtime_resolution", {}) if self.profile else {}
        configured = runtime.get("link_state_symbols", {}) if isinstance(runtime, dict) else {}
        defaults: dict[str, list[str]] = {
            "invisible_flag": [
                "GameInteractor_InvisibleLinkActive",
                "InvisibleLinkActive",
            ],
            "reverse_flag": [
                "GameInteractor_ReverseControlsActive",
                "ReverseControlsActive",
            ],
            "burn_fn": [
                "GameInteractor::RawAction::BurnPlayer",
                "BurnPlayer",
            ],
            "freeze_fn": [
                "GameInteractor::RawAction::FreezePlayer",
                "FreezePlayer",
            ],
            "shock_fn": [
                "GameInteractor::RawAction::ElectrocutePlayer",
                "ElectrocutePlayer",
            ],
            "spawn_actor_fn": [
                "GameInteractor::RawAction::SpawnActor",
                "SpawnActor",
            ],
            "actor_spawn_fn": [
                "Actor_Spawn",
            ],
        }
        if isinstance(configured, dict):
            for key, value in configured.items():
                if isinstance(value, str):
                    defaults[key] = [value]
                elif isinstance(value, list):
                    defaults[key] = [str(item) for item in value if str(item).strip()]
        return defaults

    def _resolve_first_pdb_symbol(self, resolver: PdbSymbolResolver, names: list[str]) -> int:
        for name in names:
            try:
                address = resolver.find_exact(name)
            except Exception:
                address = None
            if address:
                return int(address)
        return 0

    def _resolve_dll_runtime_symbols(self, force_refresh: bool = False) -> dict[str, int]:
        if not force_refresh and hasattr(self, "_dll_runtime_symbols_cache"):
            cached = getattr(self, "_dll_runtime_symbols_cache")
            if isinstance(cached, dict):
                return cached

        if not self.profile:
            return {}

        exe_path = self.profile.get("runtime_exe_path")
        if not exe_path:
            return {}

        resolved: dict[str, int] = {}
        candidates = self._dll_symbol_candidates()
        try:
            with PdbSymbolResolver(self.adapter.memory, str(exe_path)) as resolver:
                for key, names in candidates.items():
                    resolved[key] = self._resolve_first_pdb_symbol(resolver, names)
        except Exception as exc:
            self._log(f"DLL runtime symbol resolution failed: {exc}")
            resolved = {key: 0 for key in candidates}

        setattr(self, "_dll_runtime_symbols_cache", resolved)
        missing = [key for key, value in resolved.items() if not value]
        if missing:
            self._log("DLL runtime symbols missing: " + ", ".join(missing))
        return resolved

    def _get_structure_offset(self, section: str, key: str, default_value: int) -> int:
        if not self.profile:
            return default_value
        root = self.profile.get("structure_offsets", {})
        values = root.get(section, {}) if isinstance(root, dict) else {}
        raw = values.get(key) if isinstance(values, dict) else None
        if raw is None:
            return default_value
        if isinstance(raw, int):
            return raw
        text = str(raw).strip()
        return int(text, 16) if text.lower().startswith("0x") else int(text, 10)

    def sync_dll_runtime_context(self, force_refresh: bool = False) -> str:
        state = self.refresh(force_runtime_scan=force_refresh)
        if not state.attached or not self.adapter or not self.save_adapter:
            raise RuntimeError("SoH is not attached")

        play_state = self.save_adapter.get_gplaystate_address()
        player = self.save_adapter.get_link_state_player_address()
        if play_state <= 0 or player <= 0:
            raise RuntimeError("Unable to resolve playState/player for DLL bridge")

        module_base = self.adapter.memory.get_module_base("soh.exe")
        actor_ctx_offset = self._get_structure_offset("play_state", "actor_ctx", 0x1C24)
        actor_ctx = play_state + actor_ctx_offset
        symbols = self._resolve_dll_runtime_symbols(force_refresh=force_refresh)

        output = self.dll_bridge.send_runtime_context(
            self.adapter.fingerprint.pid,
            module_base=module_base,
            play_state=play_state,
            player=player,
            invisible_flag=symbols.get("invisible_flag", 0),
            reverse_flag=symbols.get("reverse_flag", 0),
            burn_fn=symbols.get("burn_fn", 0),
            freeze_fn=symbols.get("freeze_fn", 0),
            shock_fn=symbols.get("shock_fn", 0),
            spawn_actor_fn=symbols.get("spawn_actor_fn", 0),
            actor_spawn_fn=symbols.get("actor_spawn_fn", 0),
            actor_ctx=actor_ctx,
        )
        self._log(
            f"DLL runtime context synced: playState=0x{play_state:016X}, "
            f"player=0x{player:016X}"
        )
        return output


    def get_dll_bridge_status(self) -> dict:
        state = self.refresh()
        status = self.dll_bridge.get_status()
        status["attached"] = bool(state.attached)
        status["pid"] = getattr(getattr(self.adapter, "fingerprint", None), "pid", 0)
        return status

    def ensure_dll_bridge_injected(self) -> str:
        output = self.sync_dll_runtime_context()
        self._log("DLL bridge injected and runtime context synced")
        return output

    def execute_dll_bridge_command(self, command: str) -> str:
        state = self.refresh()
        if not state.attached or not self.adapter:
            raise RuntimeError("SoH is not attached")
        self.sync_dll_runtime_context()
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
