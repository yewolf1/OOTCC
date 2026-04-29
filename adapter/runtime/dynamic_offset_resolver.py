from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from adapter.runtime.pdb_symbol_resolver import PdbSymbolResolver
from adapter.memory.windows_memory import WindowsProcessMemory


@dataclass(frozen=True)
class RuntimeAddressMap:
    save_base: int
    items_base: int
    ammo_base: int
    current_health: int
    max_health: int
    rupees: int
    equipped_equipment: int
    owned_equipment: int
    upgrades: int
    quest_items: int
    gplaystate_pointer: int | None = None
    resolved_by: str = "unknown"


class DynamicOffsetResolver:
    """Resolve SoH globals once, cache them in memory, and persist valid RVAs."""

    DEFAULT_SAVE_OFFSETS: dict[str, int] = {
        "health_max": 0x002E,
        "health_current": 0x0030,
        "magic_level": 0x0032,
        "magic_current": 0x0033,
        "rupees": 0x0034,
        "items": 0x008C,
        "ammo": 0x00A4,
        "equipped_equipment": 0x0088,
        "owned_equipment": 0x00B4,
        "upgrades": 0x00B8,
        "quest_items": 0x00BC,
        "entrance_index": 0x0000,
        "next_transition_type": 0x141D,
    }

    def __init__(self, memory: WindowsProcessMemory, profile: Optional[dict]) -> None:
        self.memory = memory
        self.profile = profile or {}
        self._runtime_map: RuntimeAddressMap | None = None
        self._gplaystate_pointer_address: int | None = None

    def is_enabled(self) -> bool:
        runtime = self.profile.get("runtime_resolution", {})
        if isinstance(runtime, dict) and "enabled" in runtime:
            return bool(runtime.get("enabled"))
        cfg = self.profile.get("dynamic_offsets", {})
        return bool(cfg.get("enabled")) or bool(self.profile.get("allow_dynamic_offsets"))

    def runtime_map(self, force_refresh: bool = False) -> RuntimeAddressMap:
        """Return the current map. PDB/cache/profile resolution happens only when needed."""
        if not force_refresh and self._runtime_map is not None:
            return self._runtime_map

        if force_refresh:
            self.invalidate_cache()

        if not force_refresh:
            cached = self._persistent_runtime_map_if_valid()
            if cached is not None:
                self._runtime_map = cached
                return cached

        if self.is_enabled():
            symbols = self._symbol_runtime_map_if_valid()
            if symbols is not None:
                self._runtime_map = symbols
                self._save_persistent_cache(symbols)
                return symbols

        if not force_refresh:
            legacy = self._legacy_runtime_map_if_valid()
            if legacy is not None:
                self._runtime_map = legacy
                self._save_persistent_cache(legacy)
                return legacy

        if force_refresh:
            cached = self._persistent_runtime_map_if_valid()
            if cached is not None:
                self._runtime_map = cached
                return cached

        raise RuntimeError("Runtime address resolution failed: no valid PDB symbols, cache, or legacy profile offsets")

    def invalidate_cache(self) -> None:
        self._runtime_map = None
        self._gplaystate_pointer_address = None

    def force_refresh(self) -> RuntimeAddressMap:
        return self.runtime_map(force_refresh=True)

    def _runtime_hash(self) -> str | None:
        value = self.profile.get("runtime_build_hash") or self.profile.get("build_hash")
        if not value:
            return None
        return str(value).strip().lower()

    def _profile_path(self) -> Path | None:
        value = self.profile.get("_profile_path")
        if not value:
            return None
        return Path(str(value))

    def _cache_section_name(self) -> str:
        value = self.profile.get("_cache_section")
        if isinstance(value, str) and value.strip():
            return value.strip()
        runtime = self.profile.get("runtime_resolution", {})
        if isinstance(runtime, dict):
            configured = runtime.get("cache_section")
            if isinstance(configured, str) and configured.strip():
                return configured.strip()
        return "runtime_cache"

    def _module_base(self) -> int:
        return self.memory.get_module_base("soh.exe")

    def _structure_offsets(self) -> dict[str, int]:
        raw_root = self.profile.get("structure_offsets", {})
        raw_save = raw_root.get("save_context", {}) if isinstance(raw_root, dict) else {}
        result = dict(self.DEFAULT_SAVE_OFFSETS)
        if isinstance(raw_save, dict):
            for key, value in raw_save.items():
                parsed = self._parse_int(value)
                if parsed is not None:
                    result[key] = parsed
        return result

    def _parse_int(self, value: Any) -> int | None:
        if value is None:
            return None
        if isinstance(value, int):
            return value
        raw = str(value).strip()
        if not raw:
            return None
        return int(raw, 16) if raw.lower().startswith("0x") else int(raw, 10)

    def _legacy_profile(self) -> dict[str, Any]:
        legacy = self.profile.get("legacy_profile")
        return legacy if isinstance(legacy, dict) else self.profile

    def _legacy_offset(self, section: str, key: str) -> int | None:
        cfg = self._legacy_profile().get(section, {})
        if not isinstance(cfg, dict):
            return None
        value = cfg.get(key)
        if value is None:
            return None
        try:
            return int(str(value), 16)
        except Exception:
            return None

    def _legacy_runtime_map_if_valid(self) -> RuntimeAddressMap | None:
        """Fallback for old exact profiles. Not used as the normal dynamic path."""
        try:
            module_base = self._module_base()
            save_base_offset = self._legacy_offset("save_context", "base_offset")
            items_base_offset = self._legacy_offset("items_runtime", "base_offset")
            ammo_base_offset = self._legacy_offset("ammo_runtime", "base_offset")
            current_offset = self._legacy_offset("health", "current_offset")
            max_offset = self._legacy_offset("health", "max_offset")
            rupees_offset = self._legacy_offset("rupees", "offset")
            if None in (save_base_offset, items_base_offset, ammo_base_offset, current_offset, max_offset, rupees_offset):
                return None

            gplaystate_offset = self._legacy_offset("gplaystate", "pointer_offset")
            if gplaystate_offset is None:
                gplaystate_offset = 0x2098530

            candidate = RuntimeAddressMap(
                save_base=module_base + int(save_base_offset),
                items_base=module_base + int(items_base_offset),
                ammo_base=module_base + int(ammo_base_offset),
                current_health=module_base + int(current_offset),
                max_health=module_base + int(max_offset),
                rupees=module_base + int(rupees_offset),
                equipped_equipment=module_base + 0x209CEC8,
                owned_equipment=module_base + 0x209CEF4,
                upgrades=module_base + 0x209CEF8,
                quest_items=module_base + 0x209CEFC,
                gplaystate_pointer=module_base + int(gplaystate_offset),
                resolved_by="legacy_profile",
            )
            if self._runtime_map_is_valid(candidate):
                return candidate
        except Exception:
            return None
        return None

    def _symbol_runtime_map_if_valid(self) -> RuntimeAddressMap | None:
        exe_path = self.profile.get("runtime_exe_path")
        if not exe_path:
            return None

        runtime = self.profile.get("runtime_resolution", {})
        symbols_cfg = runtime.get("symbols", {}) if isinstance(runtime, dict) else {}
        save_symbols = symbols_cfg.get("save_context", ["gSaveContext"])
        play_symbols = symbols_cfg.get("gplaystate_pointer", ["gPlayState"])
        if isinstance(save_symbols, str):
            save_symbols = [save_symbols]
        if isinstance(play_symbols, str):
            play_symbols = [play_symbols]

        try:
            with PdbSymbolResolver(self.memory, str(exe_path)) as symbols:
                save_base = symbols.find_first(list(save_symbols))
                gplaystate_pointer = symbols.find_first(list(play_symbols))
        except Exception:
            return None

        if save_base is None:
            return None

        candidate = self._runtime_map_from_save_base(
            save_base=save_base,
            gplaystate_pointer=gplaystate_pointer,
            resolved_by="pdb",
        )
        if not self._runtime_map_is_valid(candidate):
            return None
        return candidate

    def _persistent_runtime_map_if_valid(self) -> RuntimeAddressMap | None:
        profile_path = self._profile_path()
        exe_hash = self._runtime_hash()
        if profile_path is None or exe_hash is None or not profile_path.exists():
            return None

        try:
            data = json.loads(profile_path.read_text(encoding="utf-8"))
            cache = data.get(self._cache_section_name(), {})
            if not isinstance(cache, dict):
                return None
            entry = cache.get(exe_hash)
            if not isinstance(entry, dict):
                return None

            module_base = self._module_base()
            save_base = module_base + int(entry["save_base_rva"])
            gplaystate_rva = entry.get("gplaystate_pointer_rva")
            gplaystate_pointer = module_base + int(gplaystate_rva) if gplaystate_rva is not None else None
            candidate = self._runtime_map_from_save_base(
                save_base=save_base,
                gplaystate_pointer=gplaystate_pointer,
                resolved_by="runtime_cache",
            )
            if self._runtime_map_is_valid(candidate):
                return candidate
        except Exception:
            return None
        return None

    def _save_persistent_cache(self, runtime_map: RuntimeAddressMap) -> None:
        profile_path = self._profile_path()
        exe_hash = self._runtime_hash()
        if profile_path is None or exe_hash is None:
            return

        try:
            data = json.loads(profile_path.read_text(encoding="utf-8"))
            cache = data.setdefault(self._cache_section_name(), {})
            module_base = self._module_base()
            entry: dict[str, Any] = {
                "save_base_rva": runtime_map.save_base - module_base,
                "items_base_rva": runtime_map.items_base - module_base,
                "ammo_base_rva": runtime_map.ammo_base - module_base,
                "current_health_rva": runtime_map.current_health - module_base,
                "max_health_rva": runtime_map.max_health - module_base,
                "rupees_rva": runtime_map.rupees - module_base,
                "equipped_equipment_rva": runtime_map.equipped_equipment - module_base,
                "owned_equipment_rva": runtime_map.owned_equipment - module_base,
                "upgrades_rva": runtime_map.upgrades - module_base,
                "quest_items_rva": runtime_map.quest_items - module_base,
                "resolved_by": runtime_map.resolved_by,
            }
            if runtime_map.gplaystate_pointer is not None:
                entry["gplaystate_pointer_rva"] = runtime_map.gplaystate_pointer - module_base
            cache[exe_hash] = entry
            profile_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        except Exception:
            return

    def _runtime_map_from_save_base(
        self,
        save_base: int,
        gplaystate_pointer: int | None,
        resolved_by: str,
    ) -> RuntimeAddressMap:
        offsets = self._structure_offsets()
        return RuntimeAddressMap(
            save_base=save_base,
            items_base=save_base + offsets["items"],
            ammo_base=save_base + offsets["ammo"],
            current_health=save_base + offsets["health_current"],
            max_health=save_base + offsets["health_max"],
            rupees=save_base + offsets["rupees"],
            equipped_equipment=save_base + offsets["equipped_equipment"],
            owned_equipment=save_base + offsets["owned_equipment"],
            upgrades=save_base + offsets["upgrades"],
            quest_items=save_base + offsets["quest_items"],
            gplaystate_pointer=gplaystate_pointer,
            resolved_by=resolved_by,
        )

    def _runtime_map_is_valid(self, mapping: RuntimeAddressMap) -> bool:
        return self._map_is_write_capable(mapping) and self._save_base_is_valid(mapping.save_base)

    def _map_is_write_capable(self, mapping: RuntimeAddressMap) -> bool:
        addresses = [
            mapping.current_health,
            mapping.max_health,
            mapping.rupees,
            mapping.items_base,
            mapping.ammo_base,
            mapping.equipped_equipment,
            mapping.owned_equipment,
            mapping.upgrades,
            mapping.quest_items,
        ]
        return all(self.memory.is_address_writable(address, 2) for address in addresses)

    def _save_base_is_valid(self, save_base: int) -> bool:
        offsets = self._structure_offsets()
        try:
            maximum = self.memory.read_i16(save_base + offsets["health_max"])
            current = self.memory.read_i16(save_base + offsets["health_current"])
            rupees = self.memory.read_u16(save_base + offsets["rupees"])
            magic_level = self.memory.read_u8(save_base + offsets["magic_level"])
            magic_current = self.memory.read_u8(save_base + offsets["magic_current"])
            entrance = self.memory.read_u16(save_base + offsets["entrance_index"])
            next_transition_type = self.memory.read_u8(save_base + offsets["next_transition_type"])
        except Exception:
            return False

        if maximum < 0x30 or maximum > 0x140 or maximum % 0x10 != 0:
            return False
        if current < 0 or current > maximum:
            return False
        if rupees > 9999:
            return False
        if magic_level not in (0, 1, 2):
            return False
        if magic_current > 96:
            return False
        if entrance > 0x80FF:
            return False
        if next_transition_type > 0x30:
            return False
        return True

    def resolve_global_address(self, name: str) -> int:
        runtime_map = self.runtime_map()
        return getattr(runtime_map, name)

    def force_resolve_global_address(self, name: str) -> int:
        runtime_map = self.runtime_map(force_refresh=True)
        return getattr(runtime_map, name)

    def resolve_gplaystate_pointer_address(self, fallback_address: int) -> int:
        if self._gplaystate_pointer_address is not None:
            return self._gplaystate_pointer_address

        runtime_map = self.runtime_map()
        if runtime_map.gplaystate_pointer is not None:
            self._gplaystate_pointer_address = runtime_map.gplaystate_pointer
            return runtime_map.gplaystate_pointer

        if self._looks_like_gplaystate_pointer(fallback_address):
            self._gplaystate_pointer_address = fallback_address
            return fallback_address

        return fallback_address

    def _read_u8_safe(self, address: int) -> int | None:
        try:
            return self.memory.read_u8(address)
        except Exception:
            return None

    def _read_u16_safe(self, address: int) -> int | None:
        try:
            return self.memory.read_u16(address)
        except Exception:
            return None

    def _read_u64_safe(self, address: int) -> int | None:
        try:
            return int.from_bytes(self.memory.read_bytes(address, 8), "little")
        except Exception:
            return None

    def _looks_like_gplaystate_pointer(self, pointer_address: int) -> bool:
        pointed = self._read_u64_safe(pointer_address)
        if pointed is None or pointed < 0x10000:
            return False
        trigger = self._read_u8_safe(pointed + 0x21061)
        next_entrance = self._read_u16_safe(pointed + 0x21066)
        transition_type = self._read_u8_safe(pointed + 0x210AA)
        return (
            trigger is not None
            and trigger <= 3
            and next_entrance is not None
            and next_entrance <= 0x80FF
            and transition_type is not None
            and transition_type <= 0x30
        )
