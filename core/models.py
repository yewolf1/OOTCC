from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class BuildFingerprint:
    pid: int
    exe_path: str
    process_name: str
    sha256_prefix: str
    file_size: int


@dataclass
class HealthState:
    current_quarters: int = 0
    max_quarters: int = 0
    attached: bool = False
    supported: bool = False
    process_name: str = ""
    version_label: str = "Unknown build"
    message: str = "Not attached"

    @property
    def current_hearts(self) -> float:
        return self.current_quarters / 16.0

    @property
    def max_hearts(self) -> float:
        return self.max_quarters / 16.0


@dataclass(frozen=True)
class EquipmentEntryState:
    key: str
    label: str
    status_text: str = "Unknown"
    owned: bool = False
    equipped: bool = False
    can_add: bool = False
    can_remove: bool = False
    can_equip: bool = False
    level: Optional[int] = None
    max_level: Optional[int] = None


@dataclass(frozen=True)
class EquipmentGroupState:
    key: str
    label: str
    entries: List[EquipmentEntryState] = field(default_factory=list)
    raw_value_text: str = "n/a"
    group_type: str = "equipment"


@dataclass(frozen=True)
class EquipmentState:
    equipped_mask: int = 0
    inventory_mask: int = 0
    upgrades_mask: int = 0
    groups: List[EquipmentGroupState] = field(default_factory=list)
    available: bool = False
    message: str = "SaveContext unavailable"


@dataclass
class LogEntry:
    timestamp: datetime
    message: str


@dataclass
class RewardEvent:
    viewer: str
    reward_title: str
    command: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AppState:
    health: HealthState = field(default_factory=HealthState)
    equipment: EquipmentState = field(default_factory=EquipmentState)
    logs: List[LogEntry] = field(default_factory=list)
    rewards: List[RewardEvent] = field(default_factory=list)
    fingerprint: Optional[BuildFingerprint] = None
    
@dataclass    
class QuestStatusState:
    def __init__(self) -> None:
        self.flags: dict[str, bool] = {}

    def set_flag(self, key: str, value: bool) -> None:
        self.flags[key] = value

    def get_flag(self, key: str) -> bool:
        return self.flags.get(key, False)
