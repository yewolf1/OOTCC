from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


BRIDGE_COMMANDS: tuple[str, ...] = (
    "inject_only",
    "freeze",
    "burn",
    "shock",
    "invisible_on",
    "invisible_off",
    "reverse_on",
    "reverse_off",
    "spawn_lit_bomb",
    "bomb_rain",
    "spawn_explosion",
    "spawn_cucco_storm",
    "spawn_darklink",
)


@dataclass(frozen=True)
class DllBridgePaths:
    host_path: Path
    dll_path: Path


class DllBridgeAdapter:
    """Runs the standalone injector/pipe bridge against the attached SoH process."""

    def __init__(self, base_dir: str) -> None:
        root = Path(base_dir)
        self.base_dir = root
        self.paths = self._resolve_paths(root)

    def _resolve_paths(self, root: Path) -> DllBridgePaths:
        bridge_root = root / "tools" / "link_state_bridge"

        candidates: list[DllBridgePaths] = [
            DllBridgePaths(
                host_path=bridge_root / "soh_bridge_host.exe",
                dll_path=bridge_root / "soh_runtime_bridge.dll",
            ),
            DllBridgePaths(
                host_path=bridge_root / "build" / "Release" / "soh_bridge_host.exe",
                dll_path=bridge_root / "build" / "Release" / "soh_runtime_bridge.dll",
            ),
            DllBridgePaths(
                host_path=bridge_root / "build" / "Debug" / "soh_bridge_host.exe",
                dll_path=bridge_root / "build" / "Debug" / "soh_runtime_bridge.dll",
            ),
            DllBridgePaths(
                host_path=bridge_root / "x64" / "Release" / "soh_bridge_host.exe",
                dll_path=bridge_root / "x64" / "Release" / "soh_runtime_bridge.dll",
            ),
            DllBridgePaths(
                host_path=bridge_root / "x64" / "Debug" / "soh_bridge_host.exe",
                dll_path=bridge_root / "x64" / "Debug" / "soh_runtime_bridge.dll",
            ),
            DllBridgePaths(
                host_path=bridge_root / "Release" / "soh_bridge_host.exe",
                dll_path=bridge_root / "Release" / "soh_runtime_bridge.dll",
            ),
            DllBridgePaths(
                host_path=bridge_root / "Debug" / "soh_bridge_host.exe",
                dll_path=bridge_root / "Debug" / "soh_runtime_bridge.dll",
            ),
        ]

        for candidate in candidates:
            if candidate.host_path.exists() and candidate.dll_path.exists():
                return candidate

        return candidates[0]

    def reload_paths(self) -> None:
        self.paths = self._resolve_paths(self.base_dir)

    def get_status(self) -> dict:
        self.reload_paths()
        return {
            "host_path": str(self.paths.host_path),
            "dll_path": str(self.paths.dll_path),
            "host_exists": self.paths.host_path.exists(),
            "dll_exists": self.paths.dll_path.exists(),
            "supported_commands": list(BRIDGE_COMMANDS),
        }

    def ensure_ready(self) -> None:
        self.reload_paths()
        missing: list[str] = []
        if not self.paths.host_path.exists():
            missing.append(f"Host executable not found: {self.paths.host_path}")
        if not self.paths.dll_path.exists():
            missing.append(f"Bridge DLL not found: {self.paths.dll_path}")
        if missing:
            raise RuntimeError("\n".join(missing))

    def _get_windows_startupinfo(self) -> subprocess.STARTUPINFO | None:
        if hasattr(subprocess, "STARTUPINFO") and hasattr(subprocess, "STARTF_USESHOWWINDOW"):
            startup_info = subprocess.STARTUPINFO()
            startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            return startup_info
        return None

    def _get_no_window_creation_flags(self) -> int:
        if hasattr(subprocess, "CREATE_NO_WINDOW"):
            return subprocess.CREATE_NO_WINDOW
        return 0

    def _run_host_payload(self, pid: int, payload: str) -> str:
        self.ensure_ready()

        completed = subprocess.run(
            [
                str(self.paths.host_path),
                str(pid),
                str(self.paths.dll_path.resolve()),
                payload,
            ],
            capture_output=True,
            text=True,
            check=False,
            creationflags=self._get_no_window_creation_flags(),
            startupinfo=self._get_windows_startupinfo(),
        )

        output_lines = [
            line.strip()
            for line in (completed.stdout.splitlines() + completed.stderr.splitlines())
            if line.strip()
        ]
        output = "\n".join(output_lines)

        if completed.returncode != 0:
            detail = output or f"Bridge host exited with code {completed.returncode}"
            raise RuntimeError(detail)

        return output

    def send_runtime_context(
        self,
        pid: int,
        *,
        module_base: int = 0,
        play_state: int,
        player: int,
        invisible_flag: int = 0,
        reverse_flag: int = 0,
        burn_fn: int = 0,
        freeze_fn: int = 0,
        shock_fn: int = 0,
        spawn_actor_fn: int = 0,
        actor_spawn_fn: int = 0,
        actor_ctx: int = 0,
    ) -> str:
        if play_state <= 0 or player <= 0:
            raise ValueError("Invalid runtime context for DLL bridge")

        payload = (
            "set_context:"
            f"moduleBase=0x{module_base:016X};"
            f"playState=0x{play_state:016X};"
            f"player=0x{player:016X};"
            f"invisibleFlag=0x{invisible_flag:016X};"
            f"reverseFlag=0x{reverse_flag:016X};"
            f"burnFn=0x{burn_fn:016X};"
            f"freezeFn=0x{freeze_fn:016X};"
            f"shockFn=0x{shock_fn:016X};"
            f"spawnActorFn=0x{spawn_actor_fn:016X};"
            f"actorSpawnFn=0x{actor_spawn_fn:016X};"
            f"actorCtx=0x{actor_ctx:016X}"
        )
        return self._run_host_payload(pid, payload)

    def execute(self, pid: int, command: str) -> str:
        normalized = command.strip().lower()
        if normalized not in BRIDGE_COMMANDS:
            raise ValueError(f"Unsupported bridge command: {command}")
        return self._run_host_payload(pid, normalized)
