from __future__ import annotations

import json
from pathlib import Path
from typing import Any

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

    def _parse_runtime_int(self, value: Any) -> int | None:
        if value is None:
            return None
        if isinstance(value, int):
            return value
        text = str(value).strip()
        if not text:
            return None
        try:
            return int(text, 16) if text.lower().startswith("0x") else int(text, 10)
        except ValueError:
            return None

    def _dll_runtime_hash(self) -> str | None:
        if not self.profile:
            return None
        value = self.profile.get("runtime_build_hash") or self.profile.get("build_hash")
        if not value:
            return None
        return str(value).strip().lower()

    def _dll_runtime_cache_file(self) -> Path | None:
        if not self.profile:
            return None
        value = self.profile.get("_profile_path")
        if not value:
            return None
        return Path(str(value))

    def _dll_runtime_cache_section(self) -> str:
        if not self.profile:
            return "runtime_cache"
        value = self.profile.get("_cache_section")
        if isinstance(value, str) and value.strip():
            return value.strip()
        runtime = self.profile.get("runtime_resolution", {})
        if isinstance(runtime, dict):
            configured = runtime.get("cache_section")
            if isinstance(configured, str) and configured.strip():
                return configured.strip()
        return "runtime_cache"

    def _dll_rva_cache_keys(self) -> dict[str, str]:
        return {
            "invisible_flag": "invisible_flag_rva",
            "reverse_flag": "reverse_flag_rva",
            "burn_fn": "burn_fn_rva",
            "freeze_fn": "freeze_fn_rva",
            "shock_fn": "shock_fn_rva",
            "spawn_actor_fn": "spawn_actor_fn_rva",
            "actor_spawn_fn": "actor_spawn_fn_rva",
        }

    def _is_dll_symbol_address_valid(self, key: str, address: int) -> bool:
        if not address or not self.adapter:
            return False
        memory = self.adapter.memory
        if key in {"invisible_flag", "reverse_flag"}:
            return memory.is_address_writable(address, 1)
        if hasattr(memory, "is_address_executable"):
            return memory.is_address_executable(address, 1)
        return True


    def _configured_dll_rvas(self) -> dict[str, int]:
        if not self.profile:
            return {}
        result: dict[str, int] = {}
        runtime = self.profile.get("runtime_resolution", {})
        if isinstance(runtime, dict):
            manual = runtime.get("manual_link_state_rvas", {})
            if isinstance(manual, dict):
                for symbol_key, cache_key in self._dll_rva_cache_keys().items():
                    parsed = self._parse_runtime_int(manual.get(cache_key))
                    if parsed is not None:
                        result[symbol_key] = parsed
        structure = self.profile.get("structure_offsets", {})
        link = structure.get("link_state", {}) if isinstance(structure, dict) else {}
        if isinstance(link, dict):
            for symbol_key, cache_key in self._dll_rva_cache_keys().items():
                parsed = self._parse_runtime_int(link.get(cache_key))
                if parsed is not None:
                    result[symbol_key] = parsed
        legacy = self.profile.get("legacy_profile", {})
        legacy_link = legacy.get("link_state", {}) if isinstance(legacy, dict) else {}
        if isinstance(legacy_link, dict):
            for symbol_key, cache_key in self._dll_rva_cache_keys().items():
                parsed = self._parse_runtime_int(legacy_link.get(cache_key))
                if parsed is not None and symbol_key not in result:
                    result[symbol_key] = parsed
        return result

    def _load_dll_symbols_from_configured_rvas(self, module_base: int) -> dict[str, int]:
        result = {key: 0 for key in self._dll_symbol_candidates()}
        for symbol_key, rva in self._configured_dll_rvas().items():
            address = module_base + rva
            if self._is_dll_symbol_address_valid(symbol_key, address):
                result[symbol_key] = address
            else:
                self._log(f"DLL configured RVA rejected: {symbol_key}=0x{address:016X} rva=0x{rva:X}")
        return result

    def _load_dll_symbols_from_runtime_cache(self, module_base: int) -> dict[str, int]:
        result = {key: 0 for key in self._dll_symbol_candidates()}
        profile_path = self._dll_runtime_cache_file()
        runtime_hash = self._dll_runtime_hash()
        if profile_path is None or runtime_hash is None or not profile_path.exists():
            return result

        try:
            data = json.loads(profile_path.read_text(encoding="utf-8"))
            cache = data.get(self._dll_runtime_cache_section(), {})
            entry = cache.get(runtime_hash) if isinstance(cache, dict) else None
            if not isinstance(entry, dict):
                return result

            for symbol_key, cache_key in self._dll_rva_cache_keys().items():
                rva = self._parse_runtime_int(entry.get(cache_key))
                if rva is None:
                    continue
                address = module_base + rva
                if self._is_dll_symbol_address_valid(symbol_key, address):
                    result[symbol_key] = address
                else:
                    self._log(f"DLL cached symbol rejected: {symbol_key}=0x{address:016X}")
        except Exception as exc:
            self._log(f"DLL runtime cache read failed: {exc}")
        return result

    def _save_dll_symbols_to_runtime_cache(self, module_base: int, symbols: dict[str, int]) -> None:
        profile_path = self._dll_runtime_cache_file()
        runtime_hash = self._dll_runtime_hash()
        if profile_path is None or runtime_hash is None:
            return

        try:
            data = json.loads(profile_path.read_text(encoding="utf-8"))
            cache = data.setdefault(self._dll_runtime_cache_section(), {})
            if not isinstance(cache, dict):
                return
            entry = cache.setdefault(runtime_hash, {})
            if not isinstance(entry, dict):
                return

            for symbol_key, cache_key in self._dll_rva_cache_keys().items():
                address = int(symbols.get(symbol_key, 0))
                if address and self._is_dll_symbol_address_valid(symbol_key, address):
                    entry[cache_key] = address - module_base

            profile_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        except Exception as exc:
            self._log(f"DLL runtime cache write failed: {exc}")
            
    def _resolve_rip_relative_writable_target(self, symbol_address: int, scan_size: int = 96) -> int:
        if not self.adapter or not symbol_address:
            return 0

        memory = self.adapter.memory

        try:
            pointer = int.from_bytes(memory.read_bytes(symbol_address, 8), "little", signed=False)
            if memory.is_address_writable(pointer, 1):
                return pointer
        except Exception:
            pass

        if not memory.is_address_executable(symbol_address, 1):
            return 0

        try:
            code = memory.read_bytes(symbol_address, scan_size)
        except Exception:
            return 0

        rip_relative_patterns = {
            b"\x0F\xB6\x05": 7,
            b"\x8A\x05": 6,
            b"\x88\x05": 6,
            b"\x80\x3D": 7,
            b"\xC6\x05": 7,
        }

        for index in range(0, max(0, len(code) - 7)):
            for prefix, instruction_size in rip_relative_patterns.items():
                if not code.startswith(prefix, index):
                    continue

                disp_offset = index + len(prefix)
                disp = int.from_bytes(code[disp_offset:disp_offset + 4], "little", signed=True)
                target = symbol_address + index + instruction_size + disp

                if memory.is_address_writable(target, 1):
                    return target

        return 0

    def _resolve_dll_symbols_from_pdb(self) -> dict[str, int]:
        if not self.profile:
            return {}
        exe_path = self.profile.get("runtime_exe_path")
        candidates = self._dll_symbol_candidates()
        if not exe_path:
            return {key: 0 for key in candidates}

        resolved: dict[str, int] = {}
        try:
            with PdbSymbolResolver(self.adapter.memory, str(exe_path)) as resolver:
                for key, names in candidates.items():
                    address = self._resolve_first_pdb_symbol(resolver, names)
                    if address and key in {"invisible_flag", "reverse_flag"}:
                        self._debug_pdb_symbol_memory(key, address)
                        target = self._resolve_rip_relative_writable_target(address)
                        if target:
                            resolved[key] = target
                            self._log(
                                f"DLL PDB indirect symbol resolved: "
                                f"{key}=0x{address:016X} -> 0x{target:016X}"
                            )
                            continue
                    if address and self._is_dll_symbol_address_valid(key, address):
                        resolved[key] = address
                    else:
                        resolved[key] = 0
                        if address:
                            self._log(f"DLL PDB symbol rejected: {key}=0x{address:016X}")
        except Exception as exc:
            self._log(f"DLL runtime symbol resolution failed: {exc}")
            resolved = {key: 0 for key in candidates}
        return resolved

    def _resolve_dll_runtime_symbols(self, force_refresh: bool = False) -> dict[str, int]:
        if not force_refresh and hasattr(self, "_dll_runtime_symbols_cache"):
            cached = getattr(self, "_dll_runtime_symbols_cache")
            if isinstance(cached, dict):
                return cached

        if not self.profile or not self.adapter:
            return {}

        module_base = self.adapter.memory.get_module_base("soh.exe")
        candidates = self._dll_symbol_candidates()
        resolved = {key: 0 for key in candidates}

        if not force_refresh:
            resolved.update(self._load_dll_symbols_from_runtime_cache(module_base))

        configured_symbols = self._load_dll_symbols_from_configured_rvas(module_base)
        for key, value in configured_symbols.items():
            if value and not resolved.get(key):
                resolved[key] = value

        missing = [key for key, value in resolved.items() if not value]
        if missing:
            pdb_symbols = self._resolve_dll_symbols_from_pdb()
            for key in missing:
                resolved[key] = int(pdb_symbols.get(key, 0))

        self._save_dll_symbols_to_runtime_cache(module_base, resolved)

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
            "DLL symbols resolved: "
            f"all={symbols}, "
            f"invisible=0x{symbols.get('invisible_flag', 0):016X}, "
            f"reverse=0x{symbols.get('reverse_flag', 0):016X}, "
            f"burn=0x{symbols.get('burn_fn', 0):016X}"
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
    
    def _debug_pdb_symbol_memory(self, key: str, address: int) -> None:
        if not self.adapter or not address:
            return

        memory = self.adapter.memory

        try:
            raw = memory.read_bytes(address, 16)
            hex_bytes = " ".join(f"{byte:02X}" for byte in raw)
        except Exception as exc:
            hex_bytes = f"<read failed: {exc}>"

        writable = False
        executable = False

        try:
            writable = memory.is_address_writable(address, 1)
        except Exception:
            pass

        try:
            executable = memory.is_address_executable(address, 1)
        except Exception:
            pass

        self._log(
            f"DLL PDB debug: {key}=0x{address:016X}, "
            f"writable={writable}, executable={executable}, bytes={hex_bytes}"
        )
