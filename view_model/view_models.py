from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class StatusViewModel:
    status_text: str
    build_text: str
    hearts_text: str
    message_text: str


@dataclass(frozen=True)
class HealthViewModel:
    summary_text: str
    current_hearts: float
    max_hearts: float
    current_slider_max: float
    max_slider_max: float
    current_steps: int
    max_steps: int


@dataclass(frozen=True)
class RupeesViewModel:
    current_value: str
    summary_text: str


@dataclass(frozen=True)
class InventoryViewModel:
    item_texts: dict[int, str] = field(default_factory=dict)
    item_selected_labels: dict[int, str] = field(default_factory=dict)
    ammo_texts: dict[int, str] = field(default_factory=dict)


@dataclass(frozen=True)
class MagicViewModel:
    current_value: str
    level_label: str
    summary_text: str


@dataclass(frozen=True)
class EquipmentViewModel:
    summary_text: str
    raw_field_values: dict[str, str] = field(default_factory=dict)
    group_texts: dict[str, str] = field(default_factory=dict)
    entry_texts: dict[str, str] = field(default_factory=dict)
    upgrade_texts: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ButtonsViewModel:
    summary_text: str
    sword_mode_label: str
    value_texts: dict[str, str] = field(default_factory=dict)
    selected_labels: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class TeleportViewModel:
    summary_text: str
    random_result_text: str
    status_texts: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class LinkStateViewModel:
    summary_text: str
    bridge_summary_text: str
    player_address_text: str
    burn_value_text: str
    freeze_value_text: str
    shock_value_text: str


@dataclass(frozen=True)
class QuestStatusViewModel:
    flags: dict[str, bool] = field(default_factory=dict)




@dataclass(frozen=True)
class TwitchViewModel:
    status_text: str
    config_path: str
    channel_login: str
    last_event_text: str


@dataclass(frozen=True)
class AppViewModel:
    status: StatusViewModel
    health: HealthViewModel
    rupees: RupeesViewModel
    inventory: InventoryViewModel
    magic: MagicViewModel
    equipment: EquipmentViewModel
    buttons: ButtonsViewModel
    teleport: TeleportViewModel
    link_state: LinkStateViewModel
    quest_status: QuestStatusViewModel
    twitch: TwitchViewModel
    logs: list[str] = field(default_factory=list)
