from __future__ import annotations

import re
import time
from typing import TYPE_CHECKING

from core.definitions.inventory_definitions import ITEM_SLOTS
from twitch.input_matching import normalize_input, resolve_input
from twitch.reward_catalog import (
    AMMO_NAME_TO_SLOT,
    EQUIPMENT_TOGGLE_NAMES,
    ITEM_TOGGLE_NAMES,
    QUEST_STATUS_NAMES,
    TELEPORT_REWARD_NAMES,
    UPGRADE_NAMES,
)

if TYPE_CHECKING:
    from core.controllers.app_controller import AppController


MAGIC_FILL_CHOICES = {name: name for name in ('full', 'half', 'empty')}
MAGIC_FILL_ALIASES = {
    'max': 'full',
    'maximum': 'full',
    'vide': 'empty',
    'zero': 'empty',
    '0': 'empty',
}

MAGIC_CAPACITY_CHOICES = {name: name for name in ('normal', 'double', 'none', 'nevermore')}
MAGIC_CAPACITY_ALIASES = {
    'basic': 'normal',
    'simple': 'normal',
    'x2': 'double',
    'no magic': 'none',
    'no magie': 'none',
    'never more': 'nevermore',
    'forever none': 'nevermore',
    'perma none': 'nevermore',
}

HEART_FILL_CHOICES = {name: name for name in ('full', 'half', 'quarter', 'empty')}
HEART_FILL_ALIASES = {
    'max': 'full',
    'maximum': 'full',
    '1/4': 'quarter',
    'quarter heart': 'quarter',
    'quarter hearts': 'quarter',
    'vide': 'empty',
    'zero': 'empty',
    '0': 'empty',
}

HEART_CAPACITY_CHOICES = {
    '+1': '+1',
    '-1': '-1',
}
HEART_CAPACITY_ALIASES = {
    '+ 1': '+1',
    '- 1': '-1',
    'plus1': '+1',
    'plus 1': '+1',
    'add1': '+1',
    'add 1': '+1',
    'minus1': '-1',
    'minus 1': '-1',
    'remove1': '-1',
    'remove 1': '-1',
}

AMMO_NAME_ALIASES = {
    'stick': 'sticks',
    'deku stick': 'sticks',
    'dekustick': 'sticks',
    'nut': 'nuts',
    'deku nut': 'nuts',
    'dekunut': 'nuts',
    'bomb': 'bombs',
    'arrow': 'arrows',
    'seed': 'seeds',
    'deku seed': 'seeds',
    'dekuseed': 'seeds',
    'bomb chu': 'bombchu',
    'bomb chus': 'bombchu',
    'bombchu': 'bombchu',
    'bombchus': 'bombchu',
}

ACTION_VERB_CHOICES = {
    'add': 'add',
    'remove': 'remove',
}

SWORD_MODE_CHOICES = {
    'swordless': 'none',
    'kokiri': 'kokiri',
    'ms': 'master',
    'biggoron': 'biggoron',
}
SWORD_MODE_ALIASES = {
    'no sword': 'swordless',
    'master': 'ms',
    'master sword': 'ms',
    'big goron': 'biggoron',
}

TELEPORT_CHOICES = {
    **TELEPORT_REWARD_NAMES,
    'random': 'random',
}
TELEPORT_ALIASES = {
    'minuet of forest': 'minuet',
    'forest': 'minuet',
    'sacred forest meadow': 'minuet',
    'meadow': 'minuet',
    'bolero of fire': 'bolero',
    'fire': 'bolero',
    'death mountain crater': 'bolero',
    'crater': 'bolero',
    'serenade of water': 'serenade',
    'water': 'serenade',
    'lake hylia': 'serenade',
    'lake': 'serenade',
    'requiem of spirit': 'requiem',
    'spirit': 'requiem',
    'desert colossus': 'requiem',
    'desert': 'requiem',
    'nocturne of shadow': 'nocturne',
    'shadow': 'nocturne',
    'graveyard': 'nocturne',
    'prelude of light': 'prelude',
    'light': 'prelude',
    'temple of time': 'prelude',
    'tot': 'prelude',
    'rand': 'random',
}

LINK_STATUS_CHOICES = {
    'burn': 'burn',
    'freeze': 'freeze',
    'shock': 'shock',
}

LINK_SPECIAL_STATUS_CHOICES = {
    'invisible on': 'invisible_on',
    'invisible off': 'invisible_off',
    'reverse on': 'reverse_on',
    'reverse off': 'reverse_off',
}
LINK_SPECIAL_STATUS_ALIASES = {
    'invis on': 'invisible on',
    'invis off': 'invisible off',
    'reverse controls on': 'reverse on',
    'reverse controls off': 'reverse off',
}

SPECIAL_SPAWN_CHOICES = {
    'bomb': 'spawn_lit_bomb',
    'bomb rain': 'bomb_rain',
    'explosion': 'spawn_explosion',
    'cucco': 'spawn_cucco_storm',
    'darklink': 'spawn_darklink',
}
SPECIAL_SPAWN_ALIASES = {
    'bomb_rain': 'bomb rain',
    'bombrain': 'bomb rain',
    'dark link': 'darklink',
}

QUEST_STATUS_ALIASES = {
    'forest medallion': 'forest',
    'fire medallion': 'fire',
    'water medallion': 'water',
    'spirit medallion': 'spirit',
    'shadow medallion': 'shadow',
    'light medallion': 'light',
    'minuet of forest': 'minuet',
    'bolero of fire': 'bolero',
    'serenade of water': 'serenade',
    'requiem of spirit': 'requiem',
    'nocturne of shadow': 'nocturne',
    'prelude of light': 'prelude',
    'zeldas lullaby': 'lullaby',
    'zeldas song': 'lullaby',
    'eponas song': 'epona',
    'sarias song': 'saria',
    'suns song': 'sun',
    'sun song': 'sun',
    'song of time': 'time',
    'song of storms': 'storms',
    'kokiri emerald': 'emerald',
    'goron ruby': 'ruby',
    'zora sapphire': 'sapphire',
    'stone of agony': 'agony',
    'gerudo card': 'gerudo',
}


class TwitchRewardExecutor:
    def __init__(self, controller: 'AppController') -> None:
        self.controller = controller
        self._temporary_disabled_items: dict[int, dict[str, float | int | str]] = {}
        self._magic_capacity_none_effects: list[dict[str, float | int | str | bool]] = []
        self._magic_capacity_restore_state: dict[str, int | bool] | None = None
        self._heart_capacity_effects: list[dict[str, float | str]] = []
        self._magic_capacity_none_duration_seconds: float = 120.0
        self._heart_capacity_duration_seconds: float = 60.0
        self._item_toggle_duration_seconds: float = 60.0
        self._last_teleport_at: float = 0.0
        self._next_effect_id: int = 1
        self._current_user_name: str = ''
        self._current_reward_title: str = ''
        self._overlay_events: list[dict[str, float | str]] = []
        self._overlay_event_duration_seconds: float = 8.0

    def execute(self, reward_title: str, user_input: str = '', user_name: str = '') -> str:
        self.tick()
        self._current_user_name = user_name or ''
        self._current_reward_title = reward_title or ''

        config = self.controller.get_twitch_config()
        rewards = config.get('rewards', {})
        reward = rewards.get(reward_title)
        if not reward:
            message = f'Twitch redeem ignored: unknown reward "{reward_title}"'
            self.controller._log(message)
            return message

        action = reward.get('action', '')
        normalized = normalize_input(user_input)

        handlers = {
            'kill_link': self._kill_link,
            'quarter_heart': self._quarter_heart,
            'unequip_all_slots': self._unequip_all_slots,
            'rupees_delta': lambda value: self._rupees_delta(int(reward.get('amount', 0))),
            'magic_fill': self._magic_fill,
            'magic_capacity': self._magic_capacity,
            'heart_fill': self._heart_fill,
            'heart_capacity': self._heart_capacity,
            'heart_remove_permanent': self._heart_remove_permanent,
            'item_toggle': self._item_toggle,
            'ammo': self._ammo,
            'equipment_toggle': self._equipment_toggle,
            'upgrade': self._upgrade,
            'clear_buttons': self._clear_buttons,
            'sword_mode': self._sword_mode,
            'teleport': self._teleport,
            'link_status': self._link_status,
            'link_special_status': self._link_special_status,
            'special_spawn': self._special_spawn,
            'quest_status': self._quest_status,
        }

        handler = handlers.get(action)
        if handler is None:
            raise ValueError(f'Unsupported Twitch action: {action}')

        try:
            message = handler(normalized)
            self._register_overlay_event(
                reward_title=reward_title,
                action=action,
                user_input=user_input,
                user_name=user_name,
            )
        finally:
            self._current_user_name = ''
            self._current_reward_title = ''
        viewer_text = f' by {user_name}' if user_name else ''
        self.controller._log(message + viewer_text)
        self.controller.set_last_twitch_event(user_name=user_name, reward_title=reward_title, user_input=user_input, status='applied')
        return message

    def tick(self) -> None:
        self._restore_expired_magic_capacity_effects()
        self._restore_expired_items()
        self._restore_expired_heart_capacity_effects()
        self._prune_overlay_events()

    def get_overlay_entries(self) -> list[dict[str, str | int]]:
        now = time.monotonic()
        entries: list[dict[str, str | int | float]] = []

        for effect in self._heart_capacity_effects:
            remaining_seconds = max(0, int(float(effect['expires_at']) - now + 0.999))
            if remaining_seconds <= 0:
                continue
            delta = float(effect['delta'])
            entries.append({
                'viewer': str(effect.get('viewer', '')),
                'title': 'Heart Capacity',
                'detail': f"{delta:+.0f} heart",
                'remaining_seconds': remaining_seconds,
                'created_at': float(effect.get('created_at', 0.0)),
            })

        if self._magic_capacity_none_effects:
            queue_end = max(float(effect['expires_at']) for effect in self._magic_capacity_none_effects)
            remaining_seconds = max(0, int(queue_end - now + 0.999))
            if remaining_seconds > 0:
                queue_count = len(self._magic_capacity_none_effects)
                latest_effect = self._magic_capacity_none_effects[-1]
                detail = 'none'
                if queue_count > 1:
                    detail = f'none x{queue_count}'
                entries.append({
                    'viewer': str(latest_effect.get('viewer', '')),
                    'title': 'Magic Capacity',
                    'detail': detail,
                    'remaining_seconds': remaining_seconds,
                    'created_at': float(latest_effect.get('created_at', 0.0)),
                })

        for effect in self._temporary_disabled_items.values():
            remaining_seconds = max(0, int(float(effect['expires_at']) - now + 0.999))
            if remaining_seconds <= 0:
                continue
            entries.append({
                'viewer': str(effect.get('viewer', '')),
                'title': 'Item Toggle',
                'detail': str(effect.get('item_name', '')),
                'remaining_seconds': remaining_seconds,
                'created_at': float(effect.get('created_at', 0.0)),
            })

        for event in self._overlay_events:
            remaining_seconds = max(0, int(float(event['expires_at']) - now + 0.999))
            if remaining_seconds <= 0:
                continue
            entries.append({
                'viewer': str(event.get('viewer', '')),
                'title': str(event.get('title', '')),
                'detail': str(event.get('detail', '')),
                'remaining_seconds': remaining_seconds,
                'created_at': float(event.get('created_at', 0.0)),
            })

        entries.sort(key=lambda row: float(row['created_at']), reverse=True)
        return [
            {
                'viewer': str(entry['viewer']),
                'title': str(entry['title']),
                'detail': str(entry['detail']),
                'remaining_seconds': int(entry['remaining_seconds']),
            }
            for entry in entries[:8]
        ]

    def _allocate_effect_id(self) -> int:
        effect_id = self._next_effect_id
        self._next_effect_id += 1
        return effect_id

    def _prune_overlay_events(self) -> None:
        now = time.monotonic()
        self._overlay_events = [
            event for event in self._overlay_events
            if now < float(event['expires_at'])
        ]

    def _register_overlay_event(self, reward_title: str, action: str, user_input: str, user_name: str) -> None:
        if action in {'heart_capacity', 'item_toggle'}:
            return

        normalized_input = normalize_input(user_input)
        detail = self._build_overlay_detail(action, normalized_input)
        now = time.monotonic()
        self._overlay_events.append({
            'viewer': user_name or '',
            'title': reward_title,
            'detail': detail,
            'created_at': now,
            'expires_at': now + self._overlay_event_duration_seconds,
        })
        self._prune_overlay_events()

    def _build_overlay_detail(self, action: str, normalized_input: str) -> str:
        if action == 'rupees_delta':
            return '-50 rupees'
        if action == 'kill_link':
            return 'Instant KO'
        if action == 'quarter_heart':
            return 'Set to 1/4 heart'
        if action == 'unequip_all_slots':
            return 'Clear every slot'
        if action == 'clear_buttons':
            return 'Clear buttons'
        if action == 'heart_remove_permanent':
            return '-1 max heart permanently'
        if action == 'teleport':
            return normalized_input or 'random'
        if normalized_input:
            return normalized_input
        return 'Applied'

    def _resolve_choice(
        self,
        value: str,
        options: dict[str, object],
        error_message: str,
        aliases: dict[str, str] | None = None,
    ) -> str:
        resolved = resolve_input(value, options, aliases)
        if resolved is None:
            raise ValueError(error_message)
        return resolved

    def _resolve_action_target(
        self,
        value: str,
        targets: dict[str, object],
        *,
        format_error: str,
        target_error: str,
        target_aliases: dict[str, str] | None = None,
    ) -> tuple[str, str]:
        normalized = normalize_input(value)
        parts = normalized.split(maxsplit=1)
        if len(parts) != 2:
            raise ValueError(format_error)

        action = self._resolve_choice(parts[0], ACTION_VERB_CHOICES, format_error)
        target = self._resolve_choice(parts[1], targets, target_error, target_aliases)
        return action, target

    def _parse_signed_delta(self, value: str, *, error_message: str) -> tuple[str, str]:
        normalized = normalize_input(value)
        match = re.fullmatch(r'(.+?)\s*([+-]\s*\d+)', normalized)
        if not match:
            raise ValueError(error_message)
        name = match.group(1).strip()
        delta_text = match.group(2).replace(' ', '')
        if not name:
            raise ValueError(error_message)
        return name, delta_text

    def _clear_magic_capacity_queue(self) -> int:
        cleared = len(self._magic_capacity_none_effects)
        self._magic_capacity_none_effects = []
        self._magic_capacity_restore_state = None
        return cleared

    def _capture_magic_restore_state(self) -> dict[str, int | bool]:
        adapter = self.controller._require_save_adapter()
        return {
            'acquired': adapter.get_magic_acquired(),
            'double_acquired': adapter.get_double_magic_acquired(),
            'current': adapter.get_magic_current(),
        }

    def _restore_magic_capacity_state(self, snapshot: dict[str, int | bool]) -> str:
        adapter = self.controller._require_save_adapter()
        acquired = bool(snapshot.get('acquired', False))
        double_acquired = bool(snapshot.get('double_acquired', False))
        current = int(snapshot.get('current', 0))

        if not acquired:
            adapter.disable_magic()
            return 'none'

        adapter.apply_magic_reinit(double_magic=double_acquired)
        adapter.set_magic_current_direct(current)
        return 'double' if double_acquired else 'normal'

    def _get_current_state(self):
        if not self.controller.adapter:
            raise RuntimeError('SoH is not attached')
        return self.controller.adapter.get_state()

    def _remove_expired_heart_effects(self, now: float) -> list[dict[str, float]]:
        expired: list[dict[str, float]] = []
        remaining: list[dict[str, float]] = []
        for effect in self._heart_capacity_effects:
            if now >= float(effect['expires_at']):
                expired.append(effect)
            else:
                remaining.append(effect)
        self._heart_capacity_effects = remaining
        return expired

    def _get_active_heart_capacity_delta(self, now: float | None = None) -> float:
        current_time = time.monotonic() if now is None else now
        return sum(float(effect['delta']) for effect in self._heart_capacity_effects if current_time < float(effect['expires_at']))

    def _get_base_max_hearts(self, current_max_hearts: float, now: float | None = None) -> float:
        active_delta = self._get_active_heart_capacity_delta(now)
        return max(1.0, current_max_hearts - active_delta)

    def _restore_expired_items(self) -> None:
        if not self.controller.save_adapter:
            return

        now = time.monotonic()
        expired_slots = [
            slot
            for slot, effect in self._temporary_disabled_items.items()
            if now >= float(effect['expires_at'])
        ]
        for slot in expired_slots:
            effect = self._temporary_disabled_items.pop(slot)
            restore_value = int(effect['restore_value'])
            item_name = str(effect['item_name'])
            self.controller.set_item_value(slot, restore_value)
            self.controller._log(f'Temporary item restored without button reassignment: {item_name}')

    def _restore_expired_magic_capacity_effects(self) -> None:
        if not self.controller.save_adapter or not self._magic_capacity_none_effects:
            return

        now = time.monotonic()
        remaining_effects = [
            effect
            for effect in self._magic_capacity_none_effects
            if now < float(effect['expires_at'])
        ]
        if len(remaining_effects) == len(self._magic_capacity_none_effects):
            return

        self._magic_capacity_none_effects = remaining_effects
        if self._magic_capacity_none_effects:
            return

        snapshot = self._magic_capacity_restore_state
        self._magic_capacity_restore_state = None
        if snapshot is None:
            return

        restored_choice = self._restore_magic_capacity_state(snapshot)
        self.controller._log(f'Temporary magic capacity restored: {restored_choice}')

    def _clear_buttons_using_item_value(self, item_value: int) -> list[str]:
        button_state = self.controller.get_button_state()
        cleared_buttons: list[str] = []
        for button_key in ('cleft', 'cdown', 'cright', 'dup', 'ddown', 'dleft', 'dright'):
            assignment = button_state.get(button_key, {})
            if int(assignment.get('value', 0xFF)) != item_value:
                continue
            self.controller.clear_button_assignment(button_key)
            cleared_buttons.append(button_key)
        return cleared_buttons

    def _restore_expired_heart_capacity_effects(self) -> None:
        if not self.controller.adapter:
            return

        now = time.monotonic()
        total_delta_before = sum(float(effect['delta']) for effect in self._heart_capacity_effects)
        expired_effects = self._remove_expired_heart_effects(now)
        if not expired_effects:
            return

        state = self._get_current_state()
        base_max_hearts = max(1.0, state.max_hearts - total_delta_before)
        remaining_delta = self._get_active_heart_capacity_delta(now)
        target = max(1.0, base_max_hearts + remaining_delta)
        self.controller.set_max_health_hearts(target)

        for effect in expired_effects:
            delta = float(effect['delta'])
            self.controller._log(f'Temporary heart capacity restored: {delta:+.0f} expired')

    def _kill_link(self, _value: str) -> str:
        self.controller.set_health_hearts(0.0)
        return 'Twitch redeem applied: current health set to 0'

    def _quarter_heart(self, _value: str) -> str:
        self.controller.set_health_hearts(0.25)
        return 'Twitch redeem applied: current health set to 1/4 heart'

    def _unequip_all_slots(self, _value: str) -> str:
        self.controller.set_sword_mode('none')
        for button_key in ('cleft', 'cdown', 'cright', 'dup', 'ddown', 'dleft', 'dright'):
            self.controller.clear_button_assignment(button_key)
        return 'Twitch redeem applied: cleared B/C/D-Pad assignments'

    def _rupees_delta(self, amount: int) -> str:
        self.controller.adjust_rupees(amount)
        return f'Twitch redeem applied: rupees {amount:+d}'

    def _magic_fill(self, value: str) -> str:
        choice = self._resolve_choice(
            value,
            MAGIC_FILL_CHOICES,
            'Magic Fill expects one of: full, half, empty',
            MAGIC_FILL_ALIASES,
        )
        if choice == 'full':
            self.controller.fill_magic()
        elif choice == 'half':
            adapter = self.controller._require_save_adapter()
            self.controller.set_magic_current(adapter.get_effective_magic_capacity() // 2)
        elif choice == 'empty':
            self.controller.empty_magic()
        return f'Twitch redeem applied: magic fill {choice}'

    def _magic_capacity(self, value: str) -> str:
        choice = self._resolve_choice(
            value,
            MAGIC_CAPACITY_CHOICES,
            'Magic Capacity expects one of: normal, double, none, nevermore',
            MAGIC_CAPACITY_ALIASES,
        )

        if choice == 'none':
            now = time.monotonic()
            if not self._magic_capacity_none_effects:
                self._magic_capacity_restore_state = self._capture_magic_restore_state()
            queue_end = max(
                now,
                max((float(effect['expires_at']) for effect in self._magic_capacity_none_effects), default=now),
            )
            expires_at = queue_end + self._magic_capacity_none_duration_seconds
            self._magic_capacity_none_effects.append({
                'id': float(self._allocate_effect_id()),
                'expires_at': expires_at,
                'created_at': now,
                'viewer': self._current_user_name,
            })
            self.controller.set_magic_level(0)
            queue_count = len(self._magic_capacity_none_effects)
            total_seconds = int(expires_at - now + 0.999)
            return (
                'Twitch redeem applied: magic capacity none for 120s '
                f'(queue: {queue_count}, total remaining: {total_seconds}s)'
            )

        canceled_queue = self._clear_magic_capacity_queue()
        if choice == 'nevermore':
            self.controller.set_magic_level(0)
        else:
            mapping = {'normal': 1, 'double': 2}
            self.controller.set_magic_level(mapping[choice])

        queue_detail = f' and cleared {canceled_queue} queued none effect(s)' if canceled_queue else ''
        return f'Twitch redeem applied: magic capacity {choice}{queue_detail}'

    def _heart_fill(self, value: str) -> str:
        choice = self._resolve_choice(
            value,
            HEART_FILL_CHOICES,
            'Heart Fill expects one of: full, half, quarter, empty',
            HEART_FILL_ALIASES,
        )
        mapping = {'full': None, 'half': 0.5, 'quarter': 0.25, 'empty': 0.0}
        if choice == 'full':
            state = self.controller.refresh()
            self.controller.set_health_hearts(state.max_hearts)
        else:
            self.controller.set_health_hearts(mapping[choice])
        return f'Twitch redeem applied: heart fill {choice}'

    def _heart_capacity(self, value: str) -> str:
        choice = self._resolve_choice(
            value,
            HEART_CAPACITY_CHOICES,
            'Heart Capacity expects one of: +1, -1',
            HEART_CAPACITY_ALIASES,
        )

        now = time.monotonic()
        delta = 1.0 if choice == '+1' else -1.0
        state = self.controller.refresh()
        base_max_hearts = self._get_base_max_hearts(state.max_hearts, now)
        active_delta = self._get_active_heart_capacity_delta(now)
        target = base_max_hearts + active_delta + delta
        if target < 1.0:
            raise ValueError('Heart Capacity cannot remove the last remaining heart')

        self.controller.set_max_health_hearts(target)
        self._heart_capacity_effects.append({
            'id': float(self._allocate_effect_id()),
            'delta': delta,
            'expires_at': now + self._heart_capacity_duration_seconds,
            'created_at': now,
            'viewer': self._current_user_name,
        })
        return f'Twitch redeem applied: temporary heart capacity {choice} for 60s'

    def _heart_remove_permanent(self, _value: str) -> str:
        now = time.monotonic()
        state = self.controller.refresh()
        active_delta = self._get_active_heart_capacity_delta(now)
        base_max_hearts = self._get_base_max_hearts(state.max_hearts, now)
        if base_max_hearts <= 1.0:
            raise ValueError('Heart Remove Permanent cannot remove the last remaining heart')
        new_base_max_hearts = base_max_hearts - 1.0
        target = max(1.0, new_base_max_hearts + active_delta)
        self.controller.set_max_health_hearts(target)
        if state.current_hearts > target:
            self.controller.set_health_hearts(target)
        return 'Twitch redeem applied: removed 1 permanent max heart'

    def _item_toggle(self, value: str) -> str:
        aliases = {
            'stick': 'deku_stick',
            'sticks': 'deku_stick',
            'deku stick': 'deku_stick',
            'dekustick': 'deku_stick',
            'nut': 'deku_nut',
            'nuts': 'deku_nut',
            'deku nut': 'deku_nut',
            'dekunut': 'deku_nut',
            'bean': 'magic_beans',
            'beans': 'magic_beans',
            'magic bean': 'magic_beans',
            'magicbean': 'magic_beans',
            'hammer': 'megaton_hammer',
            'megatonhammer': 'megaton_hammer',
            'lens': 'lens_of_truth',
            'lens truth': 'lens_of_truth',
            'lenstruth': 'lens_of_truth',
            'firearrow': 'fire_arrow',
            'icearrow': 'ice_arrow',
            'lightarrow': 'light_arrow',
            'dins fire': 'dins_fire',
            'dinsfire': 'dins_fire',
            'farores wind': 'farores_wind',
            'faroreswind': 'farores_wind',
            'nayrus love': 'nayrus_love',
            'nayruslove': 'nayrus_love',
            'hook shot': 'hookshot',
            'hookshot': 'hookshot',
            'long shot': 'hookshot',
            'longshot': 'hookshot',
            'bomb chu': 'bombchu',
            'bombchu': 'bombchu',
            'bombchus': 'bombchu',
        }
        matched_name = resolve_input(value, ITEM_TOGGLE_NAMES, aliases)
        if matched_name is None:
            raise ValueError('Item Toggle expects a valid item name')

        slot = ITEM_TOGGLE_NAMES[matched_name]
        display_name = matched_name.replace('_', ' ')
        now = time.monotonic()
        active_effect = self._temporary_disabled_items.get(slot)
        if active_effect is not None:
            active_effect['expires_at'] = now + self._item_toggle_duration_seconds
            active_effect['created_at'] = now
            active_effect['viewer'] = self._current_user_name
            self.controller.clear_item(slot)
            return f'Twitch redeem applied: refreshed temporary item removal {display_name} for 60s'

        current_inventory = self.controller.get_inventory()
        current_value = current_inventory.get(slot, ITEM_SLOTS[slot]['clear_value'])
        clear_value = ITEM_SLOTS[slot]['clear_value']
        if current_value == clear_value:
            return f'Twitch redeem ignored: item {display_name} is not currently owned'

        cleared_buttons = self._clear_buttons_using_item_value(int(current_value))
        self._temporary_disabled_items[slot] = {
            'restore_value': current_value,
            'expires_at': now + self._item_toggle_duration_seconds,
            'item_name': display_name,
            'created_at': now,
            'viewer': self._current_user_name,
        }
        self.controller.clear_item(slot)
        button_detail = f' and cleared {len(cleared_buttons)} button assignment(s)' if cleared_buttons else ''
        return f'Twitch redeem applied: temporarily removed item {display_name} for 60s{button_detail}'

    def _ammo(self, value: str) -> str:
        ammo_name_input, delta_text = self._parse_signed_delta(
            value,
            error_message='Ammo expects: <ammo> +10 or <ammo> -10',
        )
        if delta_text not in ('+10', '-10'):
            raise ValueError('Ammo expects: <ammo> +10 or <ammo> -10')
        ammo_name = self._resolve_choice(
            ammo_name_input,
            AMMO_NAME_TO_SLOT,
            'Ammo expects a valid ammo name',
            AMMO_NAME_ALIASES,
        )
        slot = AMMO_NAME_TO_SLOT[ammo_name]
        current = self.controller.get_ammo().get(slot, 0)
        delta = 10 if delta_text == '+10' else -10
        self.controller.set_ammo(slot, max(0, current + delta))
        return f'Twitch redeem applied: ammo {ammo_name} {delta_text}'

    def _equipment_toggle(self, value: str) -> str:
        matched_name = self._resolve_choice(
            value,
            EQUIPMENT_TOGGLE_NAMES,
            'Equipment expects a valid equipment name',
        )
        target = EQUIPMENT_TOGGLE_NAMES[matched_name]
        group_key, item_key = target
        snapshot = self.controller.get_equipment_snapshot()
        for entry in snapshot['groups'][group_key]['entries']:
            if entry['key'] == item_key:
                owned = bool(entry['owned'])
                break
        else:
            raise ValueError('Equipment state lookup failed')
        if owned:
            self.controller.remove_equipment_item(group_key, item_key)
            return f'Twitch redeem applied: equipment removed {matched_name}'
        self.controller.add_equipment_item(group_key, item_key, auto_equip=True)
        return f'Twitch redeem applied: equipment added {matched_name}'

    def _upgrade(self, value: str) -> str:
        verb, upgrade_name = self._resolve_action_target(
            value,
            UPGRADE_NAMES,
            format_error='Upgrade expects: add <upgrade> or remove <upgrade>',
            target_error='Upgrade expects a valid upgrade name',
        )
        upgrade_key = UPGRADE_NAMES[upgrade_name]
        if verb == 'add':
            self.controller.increase_upgrade_level(upgrade_key)
        else:
            self.controller.decrease_upgrade_level(upgrade_key)
        return f'Twitch redeem applied: upgrade {verb} {upgrade_name}'

    def _clear_buttons(self, _value: str) -> str:
        for button_key in ('cleft', 'cdown', 'cright', 'dup', 'ddown', 'dleft', 'dright'):
            self.controller.clear_button_assignment(button_key)
        return 'Twitch redeem applied: cleared non-sword buttons'

    def _sword_mode(self, value: str) -> str:
        choice = self._resolve_choice(
            value,
            SWORD_MODE_CHOICES,
            'Sword Mode expects one of: swordless, kokiri, ms, biggoron',
            SWORD_MODE_ALIASES,
        )
        mode = SWORD_MODE_CHOICES[choice]
        self.controller.set_sword_mode(mode)
        return f'Twitch redeem applied: sword mode {choice}'

    def _teleport(self, value: str) -> str:
        now = time.monotonic()
        if now - self._last_teleport_at < 10.0:
            remaining = max(1, int(10 - (now - self._last_teleport_at)))
            raise ValueError(f'Teleport is on cooldown for {remaining}s')
        choice = self._resolve_choice(
            value,
            TELEPORT_CHOICES,
            'Teleport expects one of: minuet, bolero, serenade, requiem, nocturne, prelude, random',
            TELEPORT_ALIASES,
        )
        if choice == 'random':
            destination = self.controller.teleport_random_safe()
            label = destination['label']
        else:
            destination_key = TELEPORT_CHOICES[choice]
            self.controller.teleport_to_warp_song(destination_key)
            label = choice
        self._last_teleport_at = now
        return f'Twitch redeem applied: teleport {label}'

    def _link_status(self, value: str) -> str:
        choice = self._resolve_choice(
            value,
            LINK_STATUS_CHOICES,
            'Link Status expects one of: burn, freeze, shock',
        )
        self.controller.execute_dll_bridge_command(LINK_STATUS_CHOICES[choice])
        return f'Twitch redeem applied: link status {choice}'

    def _link_special_status(self, value: str) -> str:
        choice = self._resolve_choice(
            value,
            LINK_SPECIAL_STATUS_CHOICES,
            'Link Special Status expects one of: invisible on, invisible off, reverse on, reverse off',
            LINK_SPECIAL_STATUS_ALIASES,
        )
        self.controller.execute_dll_bridge_command(LINK_SPECIAL_STATUS_CHOICES[choice])
        return f'Twitch redeem applied: link special status {choice}'

    def _special_spawn(self, value: str) -> str:
        choice = self._resolve_choice(
            value,
            SPECIAL_SPAWN_CHOICES,
            'Special Spawn expects one of: bomb, bomb rain, explosion, cucco, darklink',
            SPECIAL_SPAWN_ALIASES,
        )
        self.controller.execute_dll_bridge_command(SPECIAL_SPAWN_CHOICES[choice])
        return f'Twitch redeem applied: special spawn {choice}'

    def _quest_status(self, value: str) -> str:
        verb, name = self._resolve_action_target(
            value,
            QUEST_STATUS_NAMES,
            format_error='Quest Status expects: add <name> or remove <name>',
            target_error='Quest Status expects a valid quest name',
            target_aliases=QUEST_STATUS_ALIASES,
        )
        flag_key = QUEST_STATUS_NAMES[name]
        self.controller.set_quest_flag(flag_key, verb == 'add')
        return f'Twitch redeem applied: quest status {verb} {name}'
