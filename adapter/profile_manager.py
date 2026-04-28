from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Optional

from core.models import BuildFingerprint


class ProfileManager:
    """Loads runtime profiles and matches them against a build fingerprint."""

    def __init__(self, profile_path: str) -> None:
        """Load all profiles from the JSON configuration file."""
        self.profile_path = Path(profile_path)
        self._profiles = self._load_profiles()

    def _load_profiles(self) -> list[dict[str, Any]]:
        """Parse the profiles list from disk."""
        data = json.loads(self.profile_path.read_text(encoding="utf-8"))
        return list(data.get("profiles", []))

    def _profile_module_names(self, profile: dict[str, Any]) -> set[str]:
        """Collect module names referenced by a profile to validate process compatibility."""
        module_names: set[str] = set()
        for value in profile.values():
            if isinstance(value, dict):
                module_name = value.get("module")
                if isinstance(module_name, str) and module_name.strip():
                    module_names.add(module_name.strip().lower())
        return module_names

    def _is_dynamic_hash_enabled(self, profile: dict[str, Any]) -> bool:
        """Return whether a profile may follow the currently detected executable hash."""
        build_hash = str(profile.get("build_hash", "")).strip().lower()
        return bool(profile.get("allow_dynamic_build_hash")) or build_hash in {"*", "auto", "dynamic"}

    def _is_process_compatible(self, profile: dict[str, Any], fingerprint: BuildFingerprint) -> bool:
        """Avoid applying a dynamic profile to an unrelated executable."""
        process_name = fingerprint.process_name.lower()
        configured_names = profile.get("process_names")

        if isinstance(configured_names, list):
            normalized_names = {str(name).strip().lower() for name in configured_names if str(name).strip()}
            if normalized_names:
                return process_name in normalized_names

        module_names = self._profile_module_names(profile)
        if module_names:
            return process_name in module_names

        return process_name == "soh.exe"

    def _clone_with_runtime_hash(self, profile: dict[str, Any], fingerprint: BuildFingerprint) -> dict[str, Any]:
        """Return a profile copy bound to the hash detected for the running process."""
        runtime_profile = copy.deepcopy(profile)
        runtime_profile["build_hash"] = fingerprint.sha256_prefix
        runtime_profile["runtime_build_hash"] = fingerprint.sha256_prefix
        runtime_profile["runtime_hash_source"] = "sha256_prefix"
        runtime_profile["dynamic_profile_match"] = True
        return runtime_profile

    def match(self, fingerprint: BuildFingerprint) -> Optional[dict[str, Any]]:
        """
        Return the profile matching the running build hash.

        Exact build_hash matches are kept as the safest path. If no exact match is
        found, profiles explicitly marked with allow_dynamic_build_hash can follow
        the current SoH executable hash while reusing the same validated offsets.
        """
        for profile in self._profiles:
            if profile.get("build_hash") == fingerprint.sha256_prefix:
                return profile

        for profile in self._profiles:
            if self._is_dynamic_hash_enabled(profile) and self._is_process_compatible(profile, fingerprint):
                return self._clone_with_runtime_hash(profile, fingerprint)

        return None
