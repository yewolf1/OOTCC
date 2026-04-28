from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from adapter.pdb_symbol_resolver import PdbSymbolResolver
from adapter.windows_memory import WindowsProcessMemory


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


class DynamicOffsetResolver:
    """Resolve SoH runtime globals from exact profile offsets or from the matching PDB."""

    _SAVE_CONTEXT_SYMBOLS = ["gSaveContext", "SaveContext", "gSaveContextRaw"]
    _GPLAYSTATE_SYMBOLS = ["gPlayState", "gGameState", "gPlayStatePtr"]

    def __init__(self, memory: WindowsProcessMemory, profile: Optional[dict]) -> None:
        self.memory = memory
        self.profile = profile or {}
        self._runtime_map: RuntimeAddressMap | None = None
        self._gplaystate_pointer_address: int | None = None
        self._symbol_errors: list[str] = []

    def is_enabled(self) -> bool:
        cfg = self.profile.get("dynamic_offsets", {})
        return bool(cfg.get("enabled")) or bool(self.profile.get("allow_dynamic_offsets"))

    def runtime_map(self) -> RuntimeAddressMap:
        if self._runtime_map is not None:
            return self._runtime_map

        exact = self._exact_runtime_map_if_valid()
        if exact is not None:
            self._runtime_map = exact
            return exact

        if self.is_enabled():
            symbols = self._symbol_runtime_map_if_valid()
            if symbols is not None:
                self._runtime_map = symbols
                return symbols

        detail = "; ".join(self._symbol_errors[-3:])
        if detail:
            raise RuntimeError(f"Runtime offset resolution failed: {detail}")
        raise RuntimeError("Runtime offset resolution failed: no exact profile and no valid PDB symbol map")

    def _profile_offset(self, section: str, key: str) -> int | None:
        cfg = self.profile.get(section, {})
        value = cfg.get(key)
        if value is None:
            return None
        return int(str(value), 16)

    def _module_base(self) -> int:
        return self.memory.get_module_base("soh.exe")

    def _exact_runtime_map_if_valid(self) -> RuntimeAddressMap | None:
        try:
            module_base = self._module_base()
            save_base_offset = self._profile_offset("save_context", "base_offset")
            items_base_offset = self._profile_offset("items_runtime", "base_offset")
            ammo_base_offset = self._profile_offset("ammo_runtime", "base_offset")
            current_offset = self._profile_offset("health", "current_offset")
            max_offset = self._profile_offset("health", "max_offset")
            rupees_offset = self._profile_offset("rupees", "offset")
            if None in (save_base_offset, items_base_offset, ammo_base_offset, current_offset, max_offset, rupees_offset):
                return None

            mapping = RuntimeAddressMap(
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
            )
            if self._map_is_valid(mapping):
                return mapping
            return None
        except Exception:
            return None

    def _symbol_runtime_map_if_valid(self) -> RuntimeAddressMap | None:
        try:
            module_base, module_size, module_path = self.memory.get_module_details("soh.exe")
            with PdbSymbolResolver(module_path, module_base, module_size) as symbols:
                candidates: list[tuple[str, int]] = []
                save_base = symbols.address_of_any(self._SAVE_CONTEXT_SYMBOLS)
                if save_base is not None:
                    candidates.append(("gSaveContext", save_base))
                candidates.extend(symbols.matching_addresses(["*gSaveContext*", "*SaveContext*"], ["save", "context"]))
                if not candidates:
                    self._symbol_errors.append("PDB loaded but gSaveContext was not found")
                    return None

                seen: set[int] = set()
                for name, address in candidates:
                    if address in seen:
                        continue
                    seen.add(address)
                    mapping = self._runtime_map_from_save_base(address)
                    if self._map_is_valid(mapping):
                        return mapping
                sample = ", ".join(f"{name}=0x{address:016X}" for name, address in candidates[:5])
                self._symbol_errors.append(f"PDB SaveContext candidates failed validation: {sample}")
                return None
        except Exception as exc:
            self._symbol_errors.append(str(exc))
            return None

    def _runtime_map_from_save_base(self, save_base: int) -> RuntimeAddressMap:
        return RuntimeAddressMap(
            save_base=save_base,
            items_base=save_base + 0x8C,
            ammo_base=save_base + 0xA4,
            current_health=save_base + 0x30,
            max_health=save_base + 0x2E,
            rupees=save_base + 0x34,
            equipped_equipment=save_base + 0x88,
            owned_equipment=save_base + 0xB4,
            upgrades=save_base + 0xB8,
            quest_items=save_base + 0xBC,
        )

    def _map_is_valid(self, mapping: RuntimeAddressMap) -> bool:
        if not self._map_is_write_capable(mapping):
            return False
        try:
            maximum = self.memory.read_i16(mapping.max_health)
            current = self.memory.read_i16(mapping.current_health)
            rupees = self.memory.read_u16(mapping.rupees)
            magic_level = self.memory.read_u8(mapping.save_base + 0x32)
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
        return True

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

    def resolve_global_address(self, name: str) -> int:
        runtime_map = self.runtime_map()
        return getattr(runtime_map, name)

    def resolve_gplaystate_pointer_address(self, fallback_address: int) -> int:
        if self._gplaystate_pointer_address is not None:
            return self._gplaystate_pointer_address
        if self._looks_like_gplaystate_pointer(fallback_address):
            self._gplaystate_pointer_address = fallback_address
            return fallback_address
        if self.is_enabled():
            found = self._symbol_gplaystate_pointer_address()
            if found is not None and self._looks_like_gplaystate_pointer(found):
                self._gplaystate_pointer_address = found
                return found
        return fallback_address

    def _symbol_gplaystate_pointer_address(self) -> int | None:
        try:
            module_base, module_size, module_path = self.memory.get_module_details("soh.exe")
            with PdbSymbolResolver(module_path, module_base, module_size) as symbols:
                address = symbols.address_of_any(self._GPLAYSTATE_SYMBOLS)
                if address is not None:
                    return address
                return symbols.find_first_matching(["*gPlayState*", "*PlayState*"], ["play", "state"])
        except Exception as exc:
            self._symbol_errors.append(str(exc))
            return None

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
        return trigger is not None and trigger <= 3 and next_entrance is not None and next_entrance <= 0x80FF and transition_type is not None and transition_type <= 0x30
