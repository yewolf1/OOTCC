from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from adapter.pdb_symbol_resolver import PdbSymbolResolver


LogCallback = Callable[[str], None]


class DllRuntimeSymbolResolver:
    """Resolve DLL runtime symbols from cache, configured RVA, then PDB.

    The resolver keeps the controller thin and preserves the existing runtime contract:
    it returns absolute process addresses ready to be sent to the native bridge.
    """

    DEFAULT_SYMBOLS: dict[str, list[str]] = {
        "invisible_flag": ["GameInteractor_InvisibleLinkActive", "InvisibleLinkActive"],
        "reverse_flag": ["GameInteractor_ReverseControlsActive", "ReverseControlsActive"],
        "burn_fn": ["GameInteractor::RawAction::BurnPlayer", "BurnPlayer"],
        "freeze_fn": ["GameInteractor::RawAction::FreezePlayer", "FreezePlayer"],
        "shock_fn": ["GameInteractor::RawAction::ElectrocutePlayer", "ElectrocutePlayer"],
        "spawn_actor_fn": ["GameInteractor::RawAction::SpawnActor", "SpawnActor"],
        "actor_spawn_fn": ["Actor_Spawn"],
    }

    RVA_CACHE_KEYS: dict[str, str] = {
        "invisible_flag": "invisible_flag_rva",
        "reverse_flag": "reverse_flag_rva",
        "burn_fn": "burn_fn_rva",
        "freeze_fn": "freeze_fn_rva",
        "shock_fn": "shock_fn_rva",
        "spawn_actor_fn": "spawn_actor_fn_rva",
        "actor_spawn_fn": "actor_spawn_fn_rva",
    }

    WRITABLE_SYMBOLS = {"invisible_flag", "reverse_flag"}
    RIP_RELATIVE_PATTERNS: dict[bytes, int] = {
        b"\x0F\xB6\x05": 7,
        b"\x8A\x05": 6,
        b"\x88\x05": 6,
        b"\x80\x3D": 7,
        b"\xC6\x05": 7,
    }

    def __init__(self, owner: Any, log: LogCallback) -> None:
        self._owner = owner
        self._log = log
        self._cache: dict[str, int] | None = None

    def resolve(self, force_refresh: bool = False) -> dict[str, int]:
        """Return absolute symbol addresses for the current attached process."""
        if not force_refresh and isinstance(self._cache, dict):
            return self._cache

        profile = self._profile
        adapter = self._adapter
        if not profile or not adapter:
            return {}

        module_base = adapter.memory.get_module_base("soh.exe")
        candidates = self.symbol_candidates()
        resolved = {key: 0 for key in candidates}

        if not force_refresh:
            resolved.update(self._load_from_runtime_cache(module_base))

        configured_symbols = self._load_from_configured_rvas(module_base)
        for key, value in configured_symbols.items():
            if value and not resolved.get(key):
                resolved[key] = value

        missing = [key for key, value in resolved.items() if not value]
        if missing:
            pdb_symbols = self._resolve_from_pdb()
            for key in missing:
                resolved[key] = int(pdb_symbols.get(key, 0))

        self._save_to_runtime_cache(module_base, resolved)
        self._cache = resolved

        missing = [key for key, value in resolved.items() if not value]
        if missing:
            self._log("DLL runtime symbols missing: " + ", ".join(missing))
        return resolved

    def clear_cache(self) -> None:
        self._cache = None

    @property
    def _profile(self) -> dict[str, Any] | None:
        return getattr(self._owner, "profile", None)

    @property
    def _adapter(self) -> Any:
        return getattr(self._owner, "adapter", None)

    def symbol_candidates(self) -> dict[str, list[str]]:
        profile = self._profile
        runtime = profile.get("runtime_resolution", {}) if profile else {}
        configured = runtime.get("link_state_symbols", {}) if isinstance(runtime, dict) else {}
        candidates = {key: list(value) for key, value in self.DEFAULT_SYMBOLS.items()}

        if isinstance(configured, dict):
            for key, value in configured.items():
                if isinstance(value, str):
                    candidates[key] = [value]
                elif isinstance(value, list):
                    candidates[key] = [str(item) for item in value if str(item).strip()]
        return candidates

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

    def _runtime_hash(self) -> str | None:
        profile = self._profile
        if not profile:
            return None
        value = profile.get("runtime_build_hash") or profile.get("build_hash")
        if not value:
            return None
        return str(value).strip().lower()

    def _runtime_cache_file(self) -> Path | None:
        profile = self._profile
        if not profile:
            return None
        value = profile.get("_profile_path")
        if not value:
            return None
        return Path(str(value))

    def _runtime_cache_section(self) -> str:
        profile = self._profile
        if not profile:
            return "runtime_cache"
        value = profile.get("_cache_section")
        if isinstance(value, str) and value.strip():
            return value.strip()
        runtime = profile.get("runtime_resolution", {})
        if isinstance(runtime, dict):
            configured = runtime.get("cache_section")
            if isinstance(configured, str) and configured.strip():
                return configured.strip()
        return "runtime_cache"

    def _is_address_valid(self, key: str, address: int) -> bool:
        adapter = self._adapter
        if not address or not adapter:
            return False
        memory = adapter.memory
        if key in self.WRITABLE_SYMBOLS:
            return memory.is_address_writable(address, 1)
        if hasattr(memory, "is_address_executable"):
            return memory.is_address_executable(address, 1)
        return True

    def _configured_rvas(self) -> dict[str, int]:
        profile = self._profile
        if not profile:
            return {}

        result: dict[str, int] = {}
        runtime = profile.get("runtime_resolution", {})
        if isinstance(runtime, dict):
            self._collect_configured_rvas(result, runtime.get("manual_link_state_rvas", {}), overwrite=True)

        structure = profile.get("structure_offsets", {})
        link = structure.get("link_state", {}) if isinstance(structure, dict) else {}
        self._collect_configured_rvas(result, link, overwrite=True)

        legacy = profile.get("legacy_profile", {})
        legacy_link = legacy.get("link_state", {}) if isinstance(legacy, dict) else {}
        self._collect_configured_rvas(result, legacy_link, overwrite=False)
        return result

    def _collect_configured_rvas(self, result: dict[str, int], source: Any, overwrite: bool) -> None:
        if not isinstance(source, dict):
            return
        for symbol_key, cache_key in self.RVA_CACHE_KEYS.items():
            parsed = self._parse_runtime_int(source.get(cache_key))
            if parsed is not None and (overwrite or symbol_key not in result):
                result[symbol_key] = parsed

    def _load_from_configured_rvas(self, module_base: int) -> dict[str, int]:
        result = {key: 0 for key in self.symbol_candidates()}
        for symbol_key, rva in self._configured_rvas().items():
            address = module_base + rva
            if self._is_address_valid(symbol_key, address):
                result[symbol_key] = address
            else:
                self._log(f"DLL configured RVA rejected: {symbol_key}=0x{address:016X} rva=0x{rva:X}")
        return result

    def _load_from_runtime_cache(self, module_base: int) -> dict[str, int]:
        result = {key: 0 for key in self.symbol_candidates()}
        profile_path = self._runtime_cache_file()
        runtime_hash = self._runtime_hash()
        if profile_path is None or runtime_hash is None or not profile_path.exists():
            return result

        try:
            data = json.loads(profile_path.read_text(encoding="utf-8"))
            cache = data.get(self._runtime_cache_section(), {})
            entry = cache.get(runtime_hash) if isinstance(cache, dict) else None
            if not isinstance(entry, dict):
                return result

            for symbol_key, cache_key in self.RVA_CACHE_KEYS.items():
                rva = self._parse_runtime_int(entry.get(cache_key))
                if rva is None:
                    continue
                address = module_base + rva
                if self._is_address_valid(symbol_key, address):
                    result[symbol_key] = address
                else:
                    self._log(f"DLL cached symbol rejected: {symbol_key}=0x{address:016X}")
        except Exception as exc:
            self._log(f"DLL runtime cache read failed: {exc}")
        return result

    def _save_to_runtime_cache(self, module_base: int, symbols: dict[str, int]) -> None:
        profile_path = self._runtime_cache_file()
        runtime_hash = self._runtime_hash()
        if profile_path is None or runtime_hash is None:
            return

        try:
            data = json.loads(profile_path.read_text(encoding="utf-8"))
            cache = data.setdefault(self._runtime_cache_section(), {})
            if not isinstance(cache, dict):
                return
            entry = cache.setdefault(runtime_hash, {})
            if not isinstance(entry, dict):
                return

            for symbol_key, cache_key in self.RVA_CACHE_KEYS.items():
                address = int(symbols.get(symbol_key, 0))
                if address and self._is_address_valid(symbol_key, address):
                    entry[cache_key] = address - module_base

            profile_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        except Exception as exc:
            self._log(f"DLL runtime cache write failed: {exc}")

    def _resolve_rip_relative_writable_target(self, symbol_address: int, scan_size: int = 96) -> int:
        adapter = self._adapter
        if not adapter or not symbol_address:
            return 0

        memory = adapter.memory
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

        for index in range(0, max(0, len(code) - 7)):
            for prefix, instruction_size in self.RIP_RELATIVE_PATTERNS.items():
                if not code.startswith(prefix, index):
                    continue
                disp_offset = index + len(prefix)
                disp = int.from_bytes(code[disp_offset:disp_offset + 4], "little", signed=True)
                target = symbol_address + index + instruction_size + disp
                if memory.is_address_writable(target, 1):
                    return target
        return 0

    def _resolve_from_pdb(self) -> dict[str, int]:
        profile = self._profile
        adapter = self._adapter
        if not profile or not adapter:
            return {}

        exe_path = profile.get("runtime_exe_path")
        candidates = self.symbol_candidates()
        if not exe_path:
            return {key: 0 for key in candidates}

        resolved: dict[str, int] = {}
        try:
            with PdbSymbolResolver(adapter.memory, str(exe_path)) as resolver:
                for key, names in candidates.items():
                    address = self._resolve_first_pdb_symbol(resolver, names)
                    if address and key in self.WRITABLE_SYMBOLS:
                        target = self._resolve_rip_relative_writable_target(address)
                        if target:
                            resolved[key] = target
                            self._log(
                                f"DLL PDB indirect symbol resolved: "
                                f"{key}=0x{address:016X} -> 0x{target:016X}"
                            )
                            continue
                    if address and self._is_address_valid(key, address):
                        resolved[key] = address
                    else:
                        resolved[key] = 0
                        if address:
                            self._log(f"DLL PDB symbol rejected: {key}=0x{address:016X}")
        except Exception as exc:
            self._log(f"DLL runtime symbol resolution failed: {exc}")
            resolved = {key: 0 for key in candidates}
        return resolved
