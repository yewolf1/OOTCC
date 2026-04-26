from __future__ import annotations

import re
import time
from typing import TYPE_CHECKING

from core.inventory_definitions import ITEM_SLOTS
from twitch.input_matching import normalize_user_text, resolve_close_text
from twitch.reward_catalog import (
    AMMO_NAME_TO_SLOT,
    EQUIPMENT_TOGGLE_NAMES,
    ITEM_TOGGLE_NAMES,
    QUEST_STATUS_NAMES,
    TELEPORT_REWARD_NAMES,
    UPGRADE_NAMES,
)

if TYPE_CHECKING:
    from core.controller import AppController


class TwitchRewardExecutor:
    def __init__(self, controller: 'AppController') -> None:
        self.controller = controller
        self._temporary_disabled_items: dict[int, dict[str, float | int | str]] = {}
        self._heart_capacity_effects: list[dict[str, float | str]] = []
        self._heart_capacity_duration_seconds: float = 60.0
        self._item_toggle_duration_seconds: float = 60.0
        self._magic_none_duration_seconds: float = 120.0
        self._magic_none_effects: list[dict[str, float | str | int | bool]] = []
        self._magic_none_restore_state: dict[str, int | bool] | None = None
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
        normalized = normalize_user_text(user_input)

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
            handler_input = user_input if action == 'ammo' else normalized
            message = handler(handler_input)
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
        self._restore_expired_items()
        self._restore_expired_heart_capacity_effects()
        self._restore_expired_magic_none_effects()
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

        for effect in self._magic_none_effects:
            remaining_seconds = max(0, int(float(effect['expires_at']) - now + 0.999))
            if remaining_seconds <= 0:
                continue
            entries.append({
                'viewer': str(effect.get('viewer', '')),
                'title': 'Magic Capacity',
                'detail': 'none',
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
        if action in {'heart_capacity', 'item_toggle', 'magic_capacity'}:
            return

        normalized_input = normalize_user_text(user_input)
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
            self.controller._log(f'Temporary item restored: {item_name}')

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
        if value == 'full':
            self.controller.fill_magic()
        elif value == 'half':
            adapter = self.controller._require_save_adapter()
            self.controller.set_magic_current(adapter.get_effective_magic_capacity() // 2)
        elif value == 'empty':
            self.controller.empty_magic()
        else:
            raise ValueError('Magic Fill expects one of: full, half, empty')
        return f'Twitch redeem applied: magic fill {value}'

    def _capture_magic_restore_state(self) -> dict[str, int | bool]:
        adapter = self.controller._require_save_adapter()
        return {
            'magic_acquired': adapter.get_magic_acquired(),
            'double_magic_acquired': adapter.get_double_magic_acquired(),
            'magic_level': adapter.get_magic_level(),
            'magic_current': adapter.get_magic_current(),
            'magic_capacity': adapter.get_magic_capacity_value(),
            'magic_fill_target': adapter.get_magic_fill_target_value(),
            'magic_target': adapter.get_magic_target_value(),
            'magic_state': adapter.get_magic_state_value(),
            'prev_magic_state': adapter.get_prev_magic_state_value(),
        }

    def _restore_magic_state(self, state: dict[str, int | bool]) -> None:
        adapter = self.controller._require_save_adapter()
        adapter.set_magic_acquired(bool(state['magic_acquired']))
        adapter.set_double_magic_acquired(bool(state['double_magic_acquired']))
        adapter.set_magic_level(int(state['magic_level']))
        adapter.set_magic_current(int(state['magic_current']))
        adapter.set_magic_capacity_value(int(state['magic_capacity']))
        adapter.set_magic_fill_target_value(int(state['magic_fill_target']))
        adapter.set_magic_target_value(int(state['magic_target']))
        adapter.set_magic_state_value(int(state['magic_state']))
        adapter.set_prev_magic_state_value(int(state['prev_magic_state']))

    def _restore_expired_magic_none_effects(self) -> None:
        if not self._magic_none_effects:
            return
        if not self.controller.save_adapter:
            return

        now = time.monotonic()
        self._magic_none_effects = [
            effect for effect in self._magic_none_effects
            if now < float(effect['expires_at'])
        ]
        if self._magic_none_effects:
            return

        restore_state = self._magic_none_restore_state
        self._magic_none_restore_state = None
        if restore_state is None:
            return

        self._restore_magic_state(restore_state)
        self.controller._log('Temporary magic none expired: restored previous magic state')

    def _clear_magic_none_pipeline(self) -> None:
        self._magic_none_effects.clear()
        self._magic_none_restore_state = None

    def _magic_capacity(self, value: str) -> str:
        mapping = {'normal': 1, 'double': 2, 'none': 0, 'nevermore': 0}
        value = resolve_close_text(value, mapping.keys())
        if value not in mapping:
            raise ValueError('Magic Capacity expects one of: normal, double, none, nevermore')

        if value in ('normal', 'double'):
            self._clear_magic_none_pipeline()
            self.controller.set_magic_level(mapping[value])
            return f'Twitch redeem applied: magic capacity {value}'

        if value == 'nevermore':
            self._clear_magic_none_pipeline()
            self.controller.set_magic_level(0)
            return 'Twitch redeem applied: magic capacity nevermore'

        now = time.monotonic()
        if self._magic_none_restore_state is None:
            self._magic_none_restore_state = self._capture_magic_restore_state()

        pipeline_start = now
        if self._magic_none_effects:
            pipeline_start = max(now, max(float(effect['expires_at']) for effect in self._magic_none_effects))
        expires_at = pipeline_start + self._magic_none_duration_seconds
        self._magic_none_effects.append({
            'id': self._allocate_effect_id(),
            'created_at': now,
            'starts_at': pipeline_start,
            'expires_at': expires_at,
            'viewer': self._current_user_name,
        })
        self.controller.set_magic_level(0)
        remaining_seconds = max(1, int(expires_at - now + 0.999))
        return f'Twitch redeem applied: temporary magic capacity none queued for {remaining_seconds}s'

    def _heart_fill(self, value: str) -> str:
        mapping = {'full': None, 'half': 0.5, 'quarter': 0.25, 'empty': 0.0}
        if value not in mapping:
            raise ValueError('Heart Fill expects one of: full, half, quarter, empty')
        if value == 'full':
            state = self.controller.refresh()
            self.controller.set_health_hearts(state.max_hearts)
        else:
            self.controller.set_health_hearts(mapping[value])
        return f'Twitch redeem applied: heart fill {value}'

    def _heart_capacity(self, value: str) -> str:
        if value not in ('+1', '-1'):
            raise ValueError('Heart Capacity expects one of: +1, -1')

        now = time.monotonic()
        delta = 1.0 if value == '+1' else -1.0
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
        return f'Twitch redeem applied: temporary heart capacity {value} for 60s'

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
        value = resolve_close_text(value, ITEM_TOGGLE_NAMES.keys())
        slot = ITEM_TOGGLE_NAMES.get(value)
        if slot is None:
            raise ValueError('Item Toggle expects a valid item name')

        now = time.monotonic()
        active_effect = self._temporary_disabled_items.get(slot)
        if active_effect is not None:
            active_effect['expires_at'] = now + self._item_toggle_duration_seconds
            active_effect['created_at'] = now
            active_effect['viewer'] = self._current_user_name
            self.controller.clear_item(slot)
            return f'Twitch redeem applied: refreshed temporary item removal {value} for 60s'

        current_inventory = self.controller.get_inventory()
        current_value = current_inventory.get(slot, ITEM_SLOTS[slot]['clear_value'])
        clear_value = ITEM_SLOTS[slot]['clear_value']
        if current_value == clear_value:
            return f'Twitch redeem ignored: item {value} is not currently owned'

        self._temporary_disabled_items[slot] = {
            'restore_value': current_value,
            'expires_at': now + self._item_toggle_duration_seconds,
            'item_name': value,
            'created_at': now,
            'viewer': self._current_user_name,
        }
        self.controller.clear_item(slot)
        return f'Twitch redeem applied: temporarily removed item {value} for 60s'

    def _resolve_ammo_name(self, value: str) -> str:
        aliases = {
            'stick': 'sticks',
            'deku stick': 'sticks',
            'deku sticks': 'sticks',
            'dekustick': 'sticks',
            'dekusticks': 'sticks',
            'nut': 'nuts',
            'deku nut': 'nuts',
            'deku nuts': 'nuts',
            'dekunut': 'nuts',
            'dekunuts': 'nuts',
            'bomb': 'bombs',
            'arrow': 'arrows',
            'seed': 'seeds',
            'deku seed': 'seeds',
            'deku seeds': 'seeds',
            'dekuseed': 'seeds',
            'dekuseeds': 'seeds',
            'chu': 'bombchu',
            'bombchu': 'bombchu',
            'bombchus': 'bombchu',
        }
        normalized = normalize_user_text(value)
        compact = normalized.replace(' ', '')

        direct = aliases.get(normalized) or aliases.get(compact)
        if direct is not None:
            return direct

        candidates = list(AMMO_NAME_TO_SLOT.keys()) + list(aliases.keys())
        matched = resolve_close_text(normalized, candidates)
        matched_normalized = normalize_user_text(matched)
        matched_compact = matched_normalized.replace(' ', '')
        return aliases.get(matched_normalized) or aliases.get(matched_compact) or matched

    def _ammo(self, value: str) -> str:
        match = re.fullmatch(r'\s*(?P<ammo>.+?)\s*(?P<delta>[+-]\s*10)\s*', value)
        if match is None:
            raise ValueError('Ammo expects: <ammo> +10 or <ammo> -10')

        ammo_name = self._resolve_ammo_name(match.group('ammo'))
        delta_text = match.group('delta').replace(' ', '')
        slot = AMMO_NAME_TO_SLOT.get(ammo_name)
        if slot is None:
            raise ValueError('Ammo expects a valid ammo name')
        current = self.controller.get_ammo().get(slot, 0)
        delta = 10 if delta_text == '+10' else -10
        self.controller.set_ammo(slot, max(0, current + delta))
        return f'Twitch redeem applied: ammo {ammo_name} {delta_text}'
    def _equipment_toggle(self, value: str) -> str:
        value = resolve_close_text(value, EQUIPMENT_TOGGLE_NAMES.keys())
        target = EQUIPMENT_TOGGLE_NAMES.get(value)
        if target is None:
            raise ValueError('Equipment expects a valid equipment name')
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
            return f'Twitch redeem applied: equipment removed {value}'
        self.controller.add_equipment_item(group_key, item_key, auto_equip=True)
        return f'Twitch redeem applied: equipment added {value}'

    def _upgrade(self, value: str) -> str:
        parts = value.split()
        if len(parts) != 2 or parts[0] not in ('add', 'remove'):
            raise ValueError('Upgrade expects: add <upgrade> or remove <upgrade>')
        verb, upgrade_name = parts
        upgrade_name = resolve_close_text(upgrade_name, UPGRADE_NAMES.keys())
        upgrade_key = UPGRADE_NAMES.get(upgrade_name)
        if upgrade_key is None:
            raise ValueError('Upgrade expects a valid upgrade name')
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
        mapping = {'swordless': 'none', 'kokiri': 'kokiri', 'ms': 'master', 'biggoron': 'biggoron'}
        value = resolve_close_text(value, mapping.keys())
        mode = mapping.get(value)
        if mode is None:
            raise ValueError('Sword Mode expects one of: swordless, kokiri, ms, biggoron')
        self.controller.set_sword_mode(mode)
        return f'Twitch redeem applied: sword mode {value}'

    def _teleport(self, value: str) -> str:
        value = resolve_close_text(value, list(TELEPORT_REWARD_NAMES.keys()) + ['random'])
        now = time.monotonic()
        if now - self._last_teleport_at < 10.0:
            remaining = max(1, int(10 - (now - self._last_teleport_at)))
            raise ValueError(f'Teleport is on cooldown for {remaining}s')
        if value == 'random':
            destination = self.controller.teleport_random_safe()
            label = destination['label']
        else:
            destination_key = TELEPORT_REWARD_NAMES.get(value)
            if destination_key is None:
                raise ValueError('Teleport expects one of: minuet, bolero, serenade, requiem, nocturne, prelude, random')
            self.controller.teleport_to_warp_song(destination_key)
            label = value
        self._last_teleport_at = now
        return f'Twitch redeem applied: teleport {label}'

    def _link_status(self, value: str) -> str:
        value = resolve_close_text(value, ('burn', 'freeze', 'shock'))
        if value == 'burn':
            self.controller.execute_dll_bridge_command('burn')
        elif value == 'freeze':
            self.controller.execute_dll_bridge_command('freeze')
        elif value == 'shock':
            self.controller.execute_dll_bridge_command('shock')
        else:
            raise ValueError('Link Status expects one of: burn, freeze, shock')
        return f'Twitch redeem applied: link status {value}'

    def _link_special_status(self, value: str) -> str:
        value = resolve_close_text(value, ('invisible on', 'invisible off', 'reverse on', 'reverse off'))
        if value == 'invisible on':
            self.controller.execute_dll_bridge_command('invisible_on')
        elif value == 'invisible off':
            self.controller.execute_dll_bridge_command('invisible_off')
        elif value == 'reverse on':
            self.controller.execute_dll_bridge_command('reverse_on')
        elif value == 'reverse off':
            self.controller.execute_dll_bridge_command('reverse_off')
        else:
            raise ValueError('Link Special Status expects one of: invisible on, invisible off, reverse on, reverse off')
        return f'Twitch redeem applied: link special status {value}'

    def _special_spawn(self, value: str) -> str:
        value = resolve_close_text(value, ('bomb', 'bomb rain', 'explosion', 'cucco', 'darklink'))
        if value == 'bomb':
            self.controller.execute_dll_bridge_command('spawn_lit_bomb')
        elif value == 'bomb rain':
            self.controller.execute_dll_bridge_command('bomb_rain')
        elif value == 'explosion':
            self.controller.execute_dll_bridge_command('spawn_explosion')
        elif value == 'cucco':
            self.controller.execute_dll_bridge_command('spawn_cucco_storm')
        elif value == 'darklink':
            self.controller.execute_dll_bridge_command('spawn_darklink')
        else:
            raise ValueError('Special Spawn expects one of: bomb, bomb rain, explosion, cucco, darklink')

        return f'Twitch redeem applied: special spawn {value}'

    def _quest_status(self, value: str) -> str:
        parts = value.split()
        if len(parts) != 2 or parts[0] not in ('add', 'remove'):
            raise ValueError('Quest Status expects: add <name> or remove <name>')
        verb, name = parts
        name = resolve_close_text(name, QUEST_STATUS_NAMES.keys())
        flag_key = QUEST_STATUS_NAMES.get(name)
        if flag_key is None:
            raise ValueError('Quest Status expects a valid quest name')
        self.controller.set_quest_flag(flag_key, verb == 'add')
        return f'Twitch redeem applied: quest status {verb} {name}'
