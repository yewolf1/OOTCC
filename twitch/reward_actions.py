from __future__ import annotations

import time
from typing import TYPE_CHECKING

from core.definitions.inventory_definitions import ITEM_SLOTS
from twitch.input_matching import resolve_input
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


class TwitchRewardExecutor:
    def __init__(self, controller: 'AppController') -> None:
        self.controller = controller
        self._temporary_disabled_items: dict[int, dict[str, float | int | str]] = {}
        self._heart_capacity_effects: list[dict[str, float | str]] = []
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
        normalized = (user_input or '').strip().lower()

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

        normalized_input = (user_input or '').strip().lower()
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
            self.controller._log(f'Temporary item restored without button reassignment: {item_name}')

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

    def _magic_capacity(self, value: str) -> str:
        mapping = {'normal': 1, 'double': 2, 'none': 0}
        if value not in mapping:
            raise ValueError('Magic Capacity expects one of: normal, double, none')
        self.controller.set_magic_level(mapping[value])
        return f'Twitch redeem applied: magic capacity {value}'

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
        parts = value.split()
        if len(parts) != 2 or parts[1] not in ('+10', '-10'):
            raise ValueError('Ammo expects: <ammo> +10 or <ammo> -10')
        ammo_name, delta_text = parts
        slot = AMMO_NAME_TO_SLOT.get(ammo_name)
        if slot is None:
            raise ValueError('Ammo expects a valid ammo name')
        current = self.controller.get_ammo().get(slot, 0)
        delta = 10 if delta_text == '+10' else -10
        self.controller.set_ammo(slot, max(0, current + delta))
        return f'Twitch redeem applied: ammo {ammo_name} {delta_text}'

    def _equipment_toggle(self, value: str) -> str:
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
        mode = mapping.get(value)
        if mode is None:
            raise ValueError('Sword Mode expects one of: swordless, kokiri, ms, biggoron')
        self.controller.set_sword_mode(mode)
        return f'Twitch redeem applied: sword mode {value}'

    def _teleport(self, value: str) -> str:
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
        if value == 'bomb':
            self.controller.execute_dll_bridge_command('spawn_lit_bomb')
        elif value == 'bomb_rain':
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
        flag_key = QUEST_STATUS_NAMES.get(name)
        if flag_key is None:
            raise ValueError('Quest Status expects a valid quest name')
        self.controller.set_quest_flag(flag_key, verb == 'add')
        return f'Twitch redeem applied: quest status {verb} {name}'
