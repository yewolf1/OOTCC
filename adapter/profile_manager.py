from __future__ import annotations

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

    def match(self, fingerprint: BuildFingerprint) -> Optional[dict[str, Any]]:
        """
        Return the profile matching the running build hash.

        The hash is a short SHA256 prefix computed from the executable,
        allowing stable identification across different builds of SoH.
        """
        for profile in self._profiles:
            if profile.get("build_hash") == fingerprint.sha256_prefix:
                return profile
        return None