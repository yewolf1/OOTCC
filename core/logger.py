from __future__ import annotations

from datetime import datetime
from typing import List

from core.models import LogEntry


class RuntimeLogger:
    def __init__(self, limit: int = 250) -> None:
        self.limit = limit
        self._entries: List[LogEntry] = []

    def add(self, message: str) -> None:
        self._entries.append(LogEntry(datetime.now(), message))
        self._entries = self._entries[-self.limit:]

    def lines(self) -> list[str]:
        return [f"[{entry.timestamp.strftime('%H:%M:%S')}] {entry.message}" for entry in self._entries]
