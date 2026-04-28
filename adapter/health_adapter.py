from __future__ import annotations

from typing import Optional

from adapter.windows_memory import WindowsProcessMemory
from adapter.dynamic_offset_resolver import DynamicOffsetResolver
from core.models import BuildFingerprint, HealthState


class HealthAdapter:
    """Reads and writes health- and rupee-related runtime values from SoH memory."""

    def __init__(self, fingerprint: BuildFingerprint, profile: Optional[dict]) -> None:
        """Bind the adapter to one running SoH process and its matched profile."""
        self.fingerprint = fingerprint
        self.profile = profile
        self.memory = WindowsProcessMemory(fingerprint.pid)
        self.dynamic_resolver = DynamicOffsetResolver(self.memory, profile)

    def close(self) -> None:
        """Release the Windows process handle."""
        self.memory.close()

    def _resolve_address(self, config: dict, key_name: str) -> int:
        """Resolve an address from the profile, with dynamic fallback for moved SoH globals."""
        strategy = config.get("strategy")

        if key_name == "current":
            return self.dynamic_resolver.resolve_global_address("current_health")
        if key_name == "max":
            return self.dynamic_resolver.resolve_global_address("max_health")

        if strategy == "direct_address":
            return int(config[f"{key_name}_address"], 16)

        if strategy == "module_offset":
            module_name = config["module"]
            offset = int(config[f"{key_name}_offset"], 16)
            base = self.memory.get_module_base(module_name)
            return base + offset

        raise RuntimeError(f"Unsupported runtime strategy: {strategy}")

    def _resolve_i16_address(self, config: dict, key_prefix: str) -> int:
        """Resolve an i16-backed runtime address."""
        return self._resolve_address(config, key_prefix)

    def get_state(self) -> HealthState:
        """Return the current health state and runtime attachment status."""
        if not self.profile:
            return HealthState(
                attached=True,
                supported=False,
                process_name=self.fingerprint.process_name,
                version_label="Unsupported build",
                message=(
                    "SoH detected, but no matching profile in config/profiles.json. "
                    "Add a profile for this build hash to enable live HP control."
                ),
            )

        health_cfg = self.profile.get("health", {})
        strategy = health_cfg.get("strategy")
        if strategy not in ("direct_address", "module_offset"):
            return HealthState(
                attached=True,
                supported=False,
                process_name=self.fingerprint.process_name,
                version_label=self.profile.get("version_label", "Profile loaded"),
                message="Profile loaded but no supported runtime strategy is configured yet.",
            )

        current_address = self._resolve_i16_address(health_cfg, "current")
        max_address = self._resolve_i16_address(health_cfg, "max")

        current = self.memory.read_i16(current_address)
        maximum = self.memory.read_i16(max_address)

        return HealthState(
            current_quarters=current,
            max_quarters=maximum,
            attached=True,
            supported=True,
            process_name=self.fingerprint.process_name,
            version_label=self.profile.get("version_label", "Profile loaded"),
            message="Attached and ready",
        )

    def get_rupees(self) -> int:
        """Read the current rupee count."""
        if not self.profile:
            raise RuntimeError("No supported profile loaded")

        rupees_cfg = self.profile.get("rupees")
        if not rupees_cfg:
            raise RuntimeError("No rupees config found in profile")

        if rupees_cfg.get("strategy") in ("module_offset", "direct_address"):
            address = self.dynamic_resolver.resolve_global_address("rupees")
        else:
            raise RuntimeError("Profile rupees strategy is not supported")

        return self.memory.read_u16(address)

    def set_rupees(self, value: int) -> int:
        """Write the rupee count after clamping it to the in-game range."""
        if not self.profile:
            raise RuntimeError("No supported profile loaded")

        rupees_cfg = self.profile.get("rupees")
        if not rupees_cfg:
            raise RuntimeError("No rupees config found in profile")

        clamped = max(0, min(int(value), 9999))

        if rupees_cfg.get("strategy") in ("module_offset", "direct_address"):
            address = self.dynamic_resolver.resolve_global_address("rupees")
        else:
            raise RuntimeError("Profile rupees strategy is not supported")

        self.memory.write_u16(address, clamped)
        return clamped

    def set_health_quarters(self, value: int) -> None:
        """Write the current health value in quarter hearts."""
        if not self.profile:
            raise RuntimeError("No supported profile loaded")

        health_cfg = self.profile.get("health", {})
        strategy = health_cfg.get("strategy")
        if strategy not in ("direct_address", "module_offset"):
            raise RuntimeError("Profile strategy is not write-capable yet")

        current_address = self._resolve_i16_address(health_cfg, "current")
        self.memory.write_i16(current_address, value)

    def set_max_health_quarters(self, value: int) -> None:
        """Write the maximum health value in quarter hearts."""
        if not self.profile:
            raise RuntimeError("No supported profile loaded")

        health_cfg = self.profile.get("health", {})
        strategy = health_cfg.get("strategy")
        if strategy not in ("direct_address", "module_offset"):
            raise RuntimeError("Profile strategy is not write-capable yet")

        max_address = self._resolve_i16_address(health_cfg, "max")
        self.memory.write_i16(max_address, value)