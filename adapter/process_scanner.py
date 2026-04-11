from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Optional

import psutil

from core.models import BuildFingerprint


class ProcessScanner:
    """Finds a running SoH process and builds a fingerprint from its executable."""

    def __init__(self, config_path: str) -> None:
        """Load the candidate process names from the scanner config file."""
        self.config_path = Path(config_path)
        self.candidates = self._load_candidates()

    def _load_candidates(self) -> list[str]:
        """Load and normalize all candidate process names."""
        data = json.loads(self.config_path.read_text(encoding="utf-8"))
        return [name.lower() for name in data.get("candidates", [])]

    def find_soh(self) -> Optional[BuildFingerprint]:
        """Return the first matching SoH process with a stable executable fingerprint."""
        for proc in psutil.process_iter(["pid", "name", "exe"]):
            try:
                name = (proc.info.get("name") or "").lower()
                if name not in self.candidates:
                    continue

                exe_path = proc.info.get("exe") or ""
                path = Path(exe_path)
                if not path.exists():
                    continue

                # The executable hash prefix is used to match the running build
                # against a profile entry in config/profiles.json.
                digest = hashlib.sha256(path.read_bytes()).hexdigest()[:16]

                return BuildFingerprint(
                    pid=int(proc.info["pid"]),
                    exe_path=str(path),
                    process_name=path.name,
                    sha256_prefix=digest,
                    file_size=path.stat().st_size,
                )
            except (psutil.Error, PermissionError, OSError):
                # Process enumeration is inherently racy on Windows, so transient
                # access and lifetime errors are ignored during the scan.
                continue

        return None