from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Optional

from core.models import BuildFingerprint


class ProfileManager:
    """Loads SoH runtime configuration and returns a normalized runtime profile."""

    DEFAULT_PROCESS_NAMES = ["soh.exe"]

    def __init__(self, profile_path: str) -> None:
        self.profile_path = Path(profile_path)
        self._raw = self.load_raw()
        self._legacy_profiles = self._load_legacy_profiles()

    def load_raw(self) -> dict[str, Any]:
        """Read the complete profiles JSON document from disk."""
        return json.loads(self.profile_path.read_text(encoding="utf-8"))

    def save_raw(self, data: dict[str, Any]) -> None:
        """Write the complete profiles JSON document to disk and refresh the in-memory config."""
        self.profile_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        self._raw = data
        self._legacy_profiles = self._load_legacy_profiles()

    def _load_legacy_profiles(self) -> list[dict[str, Any]]:
        """Return old exact-build profiles, regardless of their section name."""
        profiles = self._raw.get("legacy_profiles")
        if profiles is None:
            profiles = self._raw.get("profiles", [])
        result = list(profiles if isinstance(profiles, list) else [])
        for profile in result:
            profile["_profile_path"] = str(self.profile_path)
        return result

    def _runtime_resolution(self) -> dict[str, Any]:
        section = self._raw.get("runtime_resolution", {})
        return section if isinstance(section, dict) else {}

    def _structure_offsets(self) -> dict[str, Any]:
        section = self._raw.get("structure_offsets", {})
        return section if isinstance(section, dict) else {}

    def _cache_section_name(self) -> str:
        cache_name = self._runtime_resolution().get("cache_section")
        if isinstance(cache_name, str) and cache_name.strip():
            return cache_name.strip()
        return "runtime_cache"

    def app_metadata(self) -> dict[str, str]:
        """Return application display metadata from profiles.json."""
        section = self._raw.get("app", {})
        if not isinstance(section, dict):
            section = {}
        name = str(section.get("name") or "SoH Bridge").strip()
        version = str(section.get("version") or "V1.0").strip()
        return {"name": name, "version": version, "title": f"{name} {version}"}

    def runtime_cache(self) -> dict[str, Any]:
        cache = self._raw.get(self._cache_section_name(), {})
        return cache if isinstance(cache, dict) else {}

    def _profile_module_names(self, profile: dict[str, Any]) -> set[str]:
        module_names: set[str] = set()
        for value in profile.values():
            if isinstance(value, dict):
                module_name = value.get("module")
                if isinstance(module_name, str) and module_name.strip():
                    module_names.add(module_name.strip().lower())
        return module_names

    def _process_names(self, profile: dict[str, Any] | None = None) -> list[str]:
        names: list[str] = []
        if profile:
            raw_names = profile.get("process_names")
            if isinstance(raw_names, list):
                names.extend(str(name).strip().lower() for name in raw_names if str(name).strip())

        runtime_names = self._runtime_resolution().get("process_names")
        if isinstance(runtime_names, list):
            names.extend(str(name).strip().lower() for name in runtime_names if str(name).strip())

        if not names:
            names = [name.lower() for name in self.DEFAULT_PROCESS_NAMES]
        return list(dict.fromkeys(names))

    def _is_process_compatible(self, profile: dict[str, Any] | None, fingerprint: BuildFingerprint) -> bool:
        process_name = fingerprint.process_name.lower()
        names = set(self._process_names(profile))
        if names and process_name not in names:
            return False

        if profile:
            module_names = self._profile_module_names(profile)
            if module_names and process_name not in module_names:
                return False
        return True

    def _is_dynamic_hash_enabled(self, profile: dict[str, Any] | None = None) -> bool:
        runtime = self._runtime_resolution()
        if bool(runtime.get("enabled", True)):
            return True
        if profile is None:
            return False
        build_hash = str(profile.get("build_hash", "")).strip().lower()
        return bool(profile.get("allow_dynamic_build_hash")) or build_hash in {"*", "auto", "dynamic"}

    def _hex(self, value: Any, fallback: str) -> str:
        if value is None:
            return fallback
        if isinstance(value, int):
            return f"0x{value:X}"
        raw = str(value).strip()
        return raw if raw else fallback

    def _normalized_from_sections(
        self,
        fingerprint: BuildFingerprint,
        source_profile: dict[str, Any] | None,
        dynamic_match: bool,
        exact_legacy_match: bool,
    ) -> dict[str, Any]:
        """Build the compatibility profile consumed by existing adapters."""
        source = copy.deepcopy(source_profile or {})
        structure = self._structure_offsets()
        save = structure.get("save_context", {}) if isinstance(structure.get("save_context"), dict) else {}
        play = structure.get("play_state", {}) if isinstance(structure.get("play_state"), dict) else {}
        link = structure.get("link_state", {}) if isinstance(structure.get("link_state"), dict) else {}
        runtime = self._runtime_resolution()

        module = str(runtime.get("module", "soh.exe"))
        version_label = source.get("version_label") or runtime.get("version_label") or "SoH dynamic runtime"

        profile: dict[str, Any] = {
            "name": source.get("name") or "SoH Dynamic Runtime",
            "build_hash": fingerprint.sha256_prefix,
            "runtime_build_hash": fingerprint.sha256_prefix,
            "runtime_hash_source": "sha256_prefix",
            "runtime_exe_path": fingerprint.exe_path,
            "runtime_process_name": fingerprint.process_name,
            "runtime_config_schema": int(self._raw.get("schema_version", 2)),
            "version_label": version_label,
            "process_names": self._process_names(source),
            "dynamic_profile_match": dynamic_match,
            "exact_legacy_match": exact_legacy_match,
            "_profile_path": str(self.profile_path),
            "_cache_section": self._cache_section_name(),
            "runtime_resolution": copy.deepcopy(runtime),
            "structure_offsets": copy.deepcopy(structure),
            "health": {
                "strategy": "dynamic_runtime",
                "module": module,
                "current_offset": self._hex(save.get("health_current"), "0x0030"),
                "max_offset": self._hex(save.get("health_max"), "0x002E"),
            },
            "rupees": {
                "strategy": "dynamic_runtime",
                "module": module,
                "offset": self._hex(save.get("rupees"), "0x0034"),
            },
            "save_context": {
                "strategy": "dynamic_runtime",
                "module": module,
                "base_offset": "0x0",
                "inventory_items_offset": self._hex(save.get("items"), "0x008C"),
                "inventory_ammo_offset": self._hex(save.get("ammo"), "0x00A4"),
                "equipment_offset": self._hex(save.get("equipped_equipment"), "0x0088"),
                "owned_equipment_offset": self._hex(save.get("owned_equipment"), "0x00B4"),
                "upgrades_offset": self._hex(save.get("upgrades"), "0x00B8"),
                "quest_items_offset": self._hex(save.get("quest_items"), "0x00BC"),
            },
            "items_runtime": {
                "strategy": "dynamic_runtime",
                "module": module,
                "base_offset": self._hex(save.get("items"), "0x008C"),
            },
            "ammo_runtime": {
                "strategy": "dynamic_runtime",
                "module": module,
                "base_offset": self._hex(save.get("ammo"), "0x00A4"),
            },
            "gplaystate_ptr": f"{module}+0x0",
            "gplaystate": {
                "strategy": "dynamic_runtime",
                "module": module,
                "pointer_offset": "0x0",
            },
            "play_state": {
                "transition_trigger_offset": self._hex(play.get("transition_trigger"), "0x21061"),
                "next_entrance_offset": self._hex(play.get("next_entrance"), "0x21066"),
                "transition_type_offset": self._hex(play.get("transition_type"), "0x210AA"),
            },
            "link_state": {
                "player_offset": self._hex(link.get("player_offset"), "0x400"),
                "freeze_timer_offset": self._hex(link.get("freeze_timer"), "0x0110"),
                "shock_timer_offset": self._hex(link.get("shock_timer"), "0x0891"),
                "burn_flag_offset": self._hex(link.get("burn_flag"), "0x0A60"),
                "burn_flames_offset": self._hex(link.get("burn_flames"), "0x0A61"),
            },
            "dynamic_offsets": {
                "enabled": bool(runtime.get("enabled", True)),
                "strategy": runtime.get("strategy", "pdb_symbols"),
            },
            "allow_dynamic_build_hash": True,
            "allow_dynamic_offsets": bool(runtime.get("enabled", True)),
        }

        # Keep legacy-only fields around for fallback/debug, without letting them drive the normal path.
        profile["legacy_profile"] = source
        return profile

    def match(self, fingerprint: BuildFingerprint) -> Optional[dict[str, Any]]:
        """Return a normalized profile for the running SoH process."""
        exact_profile: dict[str, Any] | None = None
        for profile in self._legacy_profiles:
            if profile.get("build_hash") == fingerprint.sha256_prefix:
                exact_profile = profile
                break

        if exact_profile is not None and self._is_process_compatible(exact_profile, fingerprint):
            return self._normalized_from_sections(
                fingerprint=fingerprint,
                source_profile=exact_profile,
                dynamic_match=False,
                exact_legacy_match=True,
            )

        if self._is_dynamic_hash_enabled(None) and self._is_process_compatible(None, fingerprint):
            fallback_source = self._legacy_profiles[0] if self._legacy_profiles else None
            return self._normalized_from_sections(
                fingerprint=fingerprint,
                source_profile=fallback_source,
                dynamic_match=True,
                exact_legacy_match=False,
            )

        for profile in self._legacy_profiles:
            if self._is_dynamic_hash_enabled(profile) and self._is_process_compatible(profile, fingerprint):
                return self._normalized_from_sections(
                    fingerprint=fingerprint,
                    source_profile=profile,
                    dynamic_match=True,
                    exact_legacy_match=False,
                )

        return None
