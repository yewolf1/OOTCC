from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from ble_hr.client import BleHeartRateClient, BleHeartRateDevice
from ble_hr.config_store import BleHrConfigStore
from adapter.runtime.health_adapter import HealthAdapter
from adapter.process.process_scanner import ProcessScanner
from adapter.profile.profile_manager import ProfileManager
from adapter.runtime.save_context_adapter import SaveContextAdapter
from adapter.dll.dll_bridge_adapter import DllBridgeAdapter
from core.controllers.debug_quest_controller import DebugQuestControllerMixin
from core.controllers.equipment_controller import EquipmentControllerMixin
from core.controllers.magic_buttons_teleport_controller import MagicButtonsTeleportControllerMixin
from core.controllers.rupees_inventory_controller import RupeeInventoryControllerMixin
from core.logger import RuntimeLogger
from core.models import HealthState
from services.teleport_service import TeleportService
from twitch.client import TwitchBridgeClient
from twitch.config_store import TwitchConfigStore
from twitch.reward_actions import TwitchRewardExecutor

BLE_HR_LEVEL_COLORS = (
    "#F8FAFC",
    "#22945B",
    "#2477EB",
    "#FFC61E",
    "#E33446",
)


class AppController(
    RupeeInventoryControllerMixin,
    MagicButtonsTeleportControllerMixin,
    EquipmentControllerMixin,
    DebugQuestControllerMixin,
):
    """High-level application controller coordinating UI actions and services."""

    def __init__(self, base_dir: str) -> None:
        root = Path(base_dir)
        self.logger = RuntimeLogger()
        self.scanner = ProcessScanner(str(root / "config" / "process_names.json"))
        self.profile_manager = ProfileManager(str(root / "config" / "profiles.json"))
        self.dll_bridge = DllBridgeAdapter(str(root))
        self.adapter: Optional[HealthAdapter] = None
        self.save_adapter: Optional[SaveContextAdapter] = None
        self.profile: Optional[dict] = None
        self.teleport_service = TeleportService()

        self.twitch_store = TwitchConfigStore(str(root))
        self.twitch_store.ensure_config()
        self.ble_hr_store = BleHrConfigStore(str(root))
        ble_hr_config = self.ble_hr_store.ensure_config()
        self._last_twitch_event = {
            'user_name': '',
            'reward_title': '',
            'user_input': '',
            'status': 'idle',
        }
        self._twitch_status = 'Disconnected'
        self.twitch_rewards = TwitchRewardExecutor(self)
        self.twitch_client = TwitchBridgeClient(
            config_loader=self.get_twitch_config,
            tokens_loader=self.twitch_store.load_tokens,
            tokens_saver=self.twitch_store.save_tokens,
            on_redeem=self._handle_twitch_redeem,
            on_status=self._set_twitch_status,
        )
        self._ble_hr_status = 'Disconnected'
        self._ble_hr_last_heart_rate: int | None = None
        self._ble_hr_last_measured_at_ms: int | None = None
        self._ble_hr_applied_speed_percent = 100
        self._ble_hr_last_action_text = '100%, waiting for Bluetooth heart rate'
        self._ble_hr_last_toggle_at = 0.0
        self._ble_hr_accept_samples = False
        self._ble_hr_device_name = str(ble_hr_config.get('preferred_device_name', '')).strip()
        self._ble_hr_device_address = str(ble_hr_config.get('preferred_address', '')).strip()
        self.ble_hr_client = BleHeartRateClient(
            config_loader=self.get_ble_hr_config,
            on_heart_rate=self._handle_ble_hr_heart_rate,
            on_status=self._set_ble_hr_status,
            on_device=self._handle_ble_hr_device,
        )
        if self._ble_hr_runtime_config().get('auto_connect_on_launch', False):
            self.connect_ble_hr()
            self._log('Bluetooth HR auto-connect requested from config')

    def process_twitch_timers(self) -> None:
        self.twitch_rewards.tick()

    def shutdown_services(self) -> None:
        try:
            self.disconnect_ble_hr()
        except Exception:
            pass
        try:
            self.disconnect_twitch()
        except Exception:
            pass
        self._dispose_adapter()

    def refresh(self, force_runtime_scan: bool = False) -> HealthState:
        fingerprint = self.scanner.find_soh()
        if not fingerprint:
            self._dispose_adapter()
            return HealthState(message="SoH not detected", attached=False, supported=False)

        if self.adapter and self.adapter.fingerprint.pid != fingerprint.pid:
            self._dispose_adapter()

        if self.adapter is None:
            self.profile = self.profile_manager.match(fingerprint)
            self.adapter = HealthAdapter(fingerprint, self.profile)

            if self.profile and self.profile.get("save_context"):
                self.save_adapter = SaveContextAdapter(fingerprint, self.profile)
            else:
                self.save_adapter = None

            if self.profile:
                dynamic_note = " via dynamic hash fallback" if self.profile.get("dynamic_profile_match") else ""
                self.logger.add(
                    f"Attached to {fingerprint.process_name} "
                    f"(profile: {self.profile.get('version_label', 'unknown')}, "
                    f"build: {self.profile.get('build_hash', fingerprint.sha256_prefix)}{dynamic_note})"
                )
            else:
                self.logger.add(
                    f"Attached to {fingerprint.process_name}, unsupported build hash {fingerprint.sha256_prefix}."
                )

        if force_runtime_scan and self.adapter is not None:
            self.force_refresh_runtime_offsets()

        try:
            return self.adapter.get_state()
        except Exception as exc:
            self.logger.add(f"Refresh failed: {exc}")
            return HealthState(
                attached=True,
                supported=False,
                process_name=fingerprint.process_name,
                message=str(exc),
            )

    def force_refresh_runtime_offsets(self) -> None:
        if not self.profile:
            return
        if self.adapter is not None:
            self.adapter.force_refresh_runtime_offsets()
        if self.save_adapter is not None:
            self.save_adapter.force_refresh_runtime_offsets()
        self.logger.add("Runtime offsets refreshed from PDB/cache/profile validation")

    def set_health_hearts(self, hearts: float) -> None:
        if not self.adapter:
            raise RuntimeError("SoH is not attached")

        state = self.refresh()
        quarters = int(round(hearts * 16))
        clamped = max(0, min(state.max_quarters, quarters))
        self.adapter.set_health_quarters(clamped)
        self.logger.add(f"Set current health to {clamped / 16.0:.2f} hearts")

    def set_max_health_hearts(self, hearts: float) -> None:
        if not self.adapter:
            raise RuntimeError("SoH is not attached")

        quarters = max(0, int(round(hearts * 16)))
        self.adapter.set_max_health_quarters(quarters)

        state_after_max = self.refresh()
        if state_after_max.current_quarters > quarters:
            self.adapter.set_health_quarters(quarters)
            self.logger.add(f"Clamped current health to {quarters / 16.0:.2f} hearts after max health update")

        self.logger.add(f"Set max health to {quarters / 16.0:.2f} hearts")

    def full_heal(self) -> None:
        if not self.adapter:
            raise RuntimeError("SoH is not attached")

        state = self.refresh()
        self.adapter.set_health_quarters(state.max_quarters)
        self.logger.add(f"Full heal to {state.max_quarters / 16.0:.2f} hearts")

    def simulate_reward(self, viewer: str, reward_title: str, hearts_delta: float) -> None:
        self.logger.add(f"Reward received: {viewer} -> {reward_title} ({hearts_delta:+.2f} hearts)")
        state = self.refresh()
        if not state.attached or not state.supported:
            self.logger.add("Reward ignored: build not attached or not supported yet")
            return
        target = max(0.0, min(state.max_hearts, state.current_hearts + hearts_delta))
        self.set_health_hearts(target)

    def _require_save_adapter(self) -> SaveContextAdapter:
        if not self.save_adapter:
            raise RuntimeError("SaveContext is not available for this attached build")
        return self.save_adapter

    def _log(self, message: str) -> None:
        self.logger.add(message)

    def _dispose_adapter(self) -> None:
        if self.adapter:
            self.adapter.close()
            self.adapter = None

        if self.save_adapter:
            self.save_adapter.close()
            self.save_adapter = None

        self.profile = None

    def log_lines(self) -> list[str]:
        return self.logger.lines()

    def get_twitch_config(self) -> dict:
        return self.twitch_store.ensure_config()

    def get_ble_hr_config(self) -> dict:
        return self.ble_hr_store.ensure_config()

    def get_twitch_overlay_entries(self) -> list[dict[str, str | int]]:
        self.process_twitch_timers()
        return self.twitch_rewards.get_overlay_entries()

    def get_twitch_config_path(self) -> str:
        return str(self.twitch_store.config_path)

    def reset_twitch_tokens(self) -> None:
        self.twitch_store.reset_tokens()
        self._set_twitch_status('Disconnected')
        self._log('Twitch OAuth tokens cleared')

    def connect_twitch(self) -> None:
        self.twitch_client.connect()
        self._log('Twitch connection requested')

    def disconnect_twitch(self) -> None:
        self.twitch_client.disconnect()
        self._log('Twitch disconnected')

    def connect_ble_hr(self) -> None:
        self._ble_hr_accept_samples = True
        self.ble_hr_client.connect()
        self._log('Bluetooth heart-rate connection requested')

    def disconnect_ble_hr(self) -> None:
        self._ble_hr_accept_samples = False
        self.ble_hr_client.disconnect()
        self._reset_ble_hr_enemy_speed('Bluetooth HR disconnected')
        self._log('Bluetooth heart-rate disconnected')

    def clear_ble_hr_preferred_device(self) -> None:
        if self.ble_hr_client.is_running:
            self.disconnect_ble_hr()
        self.ble_hr_store.clear_preferred_device()
        self._ble_hr_device_name = ''
        self._ble_hr_device_address = ''
        self._log('Bluetooth HR preferred device cleared')

    def get_twitch_state(self) -> dict:
        config = self.get_twitch_config()
        last = self._last_twitch_event
        if last.get('reward_title'):
            last_event_text = (
                f"Viewer: {last.get('user_name') or 'Unknown'}\n"
                f"Reward: {last.get('reward_title', '')}\n"
                f"Input: {last.get('user_input') or '-'}\n"
                f"Status: {last.get('status', 'unknown')}"
            )
        else:
            last_event_text = 'No Twitch redeem received yet'
        return {
            'status_text': self._twitch_status,
            'config_path': str(self.twitch_store.config_path),
            'channel_login': config.get('channel_login', ''),
            'last_event_text': last_event_text,
            'connected': self.twitch_client.is_running,
        }

    def get_ble_hr_state(self) -> dict:
        config = self._ble_hr_runtime_config()
        device_text = self._format_ble_hr_device_text(config)
        return {
            'status_text': self._ble_hr_status,
            'config_path': str(self.ble_hr_store.config_path),
            'device_text': device_text,
            'live_bpm_text': self._format_ble_hr_live_bpm_text(self._ble_hr_last_heart_rate),
            'live_bpm_color': self._resolve_ble_hr_live_bpm_color(
                self._ble_hr_last_heart_rate,
                config['levels'],
            ),
            'live_detail_text': self._format_ble_hr_live_detail_text(
                self._ble_hr_last_heart_rate,
                self._ble_hr_last_measured_at_ms,
            ),
            'sample_text': self._format_heart_rate_sample_text(
                self._ble_hr_last_heart_rate,
                self._ble_hr_last_measured_at_ms,
            ),
            'rule_text': self._format_ble_hr_rule_text(config),
            'hyper_state_text': f"{self._ble_hr_applied_speed_percent}% | {self._ble_hr_last_action_text}",
            'level_rows': self._build_ble_hr_level_rows(config['levels']),
            'connected': self.ble_hr_client.is_connected,
            'running': self.ble_hr_client.is_running,
        }

    def save_ble_hr_enemy_speed_levels(self, rows: list[tuple[str, str]]) -> dict:
        normalized_levels: list[dict[str, int]] = []

        for index, row in enumerate(rows, start=1):
            raw_bpm, raw_speed_percent = row
            bpm_text = str(raw_bpm).strip()
            speed_text = str(raw_speed_percent).strip()

            if bpm_text == '' and speed_text == '':
                continue
            if bpm_text == '' or speed_text == '':
                raise ValueError(f'Level {index}: BPM and speed % are both required')

            normalized_levels.append({
                'bpm': self._parse_user_int(bpm_text, label=f'Level {index} BPM', minimum=1, maximum=260),
                'speed_percent': self._parse_user_int(
                    speed_text,
                    label=f'Level {index} speed %',
                    minimum=100,
                    maximum=1000,
                ),
            })

        normalized_levels.sort(key=lambda level: (level['bpm'], level['speed_percent']))

        current = self.get_ble_hr_config()
        enemy_speed = dict(current.get('enemy_speed', {})) if isinstance(current.get('enemy_speed', {}), dict) else {}
        enemy_speed['levels'] = normalized_levels
        current['enemy_speed'] = enemy_speed
        saved = self.ble_hr_store.save_config(current)

        if normalized_levels:
            levels_text = ', '.join(
                f">={level['bpm']} BPM => {level['speed_percent']}%"
                for level in normalized_levels
            )
        else:
            levels_text = 'no active threshold'

        self._ble_hr_last_action_text = 'Enemy speed levels saved'
        self._log(f'Bluetooth HR enemy speed levels saved: {levels_text}')

        if self._ble_hr_accept_samples and self._ble_hr_last_heart_rate is not None:
            self._ble_hr_last_toggle_at = 0.0
            self._apply_ble_hr_enemy_speed_for_sample(self._ble_hr_last_heart_rate)

        return saved

    def set_last_twitch_event(self, user_name: str, reward_title: str, user_input: str, status: str) -> None:
        self._last_twitch_event = {
            'user_name': user_name,
            'reward_title': reward_title,
            'user_input': user_input,
            'status': status,
        }

    def _set_twitch_status(self, status: str) -> None:
        self._twitch_status = status
        self._log(f'Twitch status: {status}')

    def _set_ble_hr_status(self, status: str) -> None:
        if status == self._ble_hr_status:
            return
        self._ble_hr_status = status
        self._log(f'Bluetooth HR status: {status}')

    def _handle_twitch_redeem(self, reward_title: str, user_input: str, user_name: str) -> None:
        self.set_last_twitch_event(user_name=user_name, reward_title=reward_title, user_input=user_input, status='received')
        self._log(f'Twitch redeem received: {user_name or "viewer"} -> {reward_title} ({user_input or "no input"})')
        try:
            self.twitch_rewards.execute(reward_title, user_input, user_name)
        except Exception as exc:
            self.set_last_twitch_event(user_name=user_name, reward_title=reward_title, user_input=user_input, status=f'error: {exc}')
            self._log(f'Twitch redeem failed: {exc}')

    def _handle_ble_hr_device(self, device: BleHeartRateDevice) -> None:
        self._ble_hr_device_name = device.name
        self._ble_hr_device_address = device.address

        config = self.get_ble_hr_config()
        saved_address = str(config.get('preferred_address', '')).strip()
        saved_name = str(config.get('preferred_device_name', '')).strip()
        if device.address != saved_address or device.name != saved_name:
            self.ble_hr_store.save_preferred_device(address=device.address, name=device.name)
            self._log(f'Bluetooth HR preferred device saved: {device.name} ({device.address})')

    def _handle_ble_hr_heart_rate(self, heart_rate: int, measured_at_ms: int | None) -> None:
        if not self._ble_hr_accept_samples:
            return

        self._ble_hr_last_heart_rate = int(heart_rate)
        self._ble_hr_last_measured_at_ms = int(measured_at_ms) if measured_at_ms is not None else None
        self._apply_ble_hr_enemy_speed_for_sample(int(heart_rate))

    def _apply_ble_hr_enemy_speed_for_sample(self, heart_rate: int) -> None:
        config = self._ble_hr_runtime_config()
        if not config['enemy_speed_enabled']:
            if self._ble_hr_applied_speed_percent > 100:
                self._reset_ble_hr_enemy_speed('Bluetooth HR automation disabled in config')
            else:
                self._ble_hr_last_action_text = 'Automation disabled in config'
            return

        desired_speed_percent = self._compute_ble_hr_target_speed_percent(heart_rate, config['levels'])
        if desired_speed_percent == self._ble_hr_applied_speed_percent:
            self._ble_hr_last_action_text = self._describe_ble_hr_speed_state(
                heart_rate,
                config['levels'],
                desired_speed_percent,
            )
            return

        now = time.monotonic()
        elapsed = now - self._ble_hr_last_toggle_at
        cooldown_seconds = config['command_cooldown_ms'] / 1000.0
        if elapsed < cooldown_seconds:
            self._ble_hr_last_action_text = (
                f"Cooldown before {desired_speed_percent}% "
                f"({cooldown_seconds - elapsed:.1f}s)"
            )
            return

        command = f'enemy_speed_percent:{desired_speed_percent}'
        self._ble_hr_last_toggle_at = now
        try:
            self.execute_dll_bridge_command(command)
        except Exception as exc:
            self._ble_hr_last_action_text = f'Bridge command failed: {exc}'
            self._log(f'Bluetooth HR bridge command failed at {heart_rate} BPM: {exc}')
            return

        self._ble_hr_applied_speed_percent = desired_speed_percent
        self._ble_hr_last_action_text = f'Applied at {heart_rate} BPM'
        self._log(
            f'Bluetooth HR applied enemy speed {desired_speed_percent}% at {heart_rate} BPM '
            f'({self._format_ble_hr_level_summary(config["levels"])})'
        )

    def _reset_ble_hr_enemy_speed(self, reason: str) -> None:
        if self._ble_hr_applied_speed_percent <= 100:
            self._ble_hr_applied_speed_percent = 100
            self._ble_hr_last_action_text = reason
            return

        try:
            self.execute_dll_bridge_command('enemy_speed_percent:100')
            self._log(f'{reason}: enemy speed reset to 100%')
        except Exception as exc:
            self._log(f'{reason}: failed to reset enemy speed ({exc})')
        finally:
            self._ble_hr_applied_speed_percent = 100
            self._ble_hr_last_action_text = f'Reset to 100% ({reason})'
            self._ble_hr_last_toggle_at = time.monotonic()

    def _ble_hr_runtime_config(self) -> dict[str, object]:
        config = self.get_ble_hr_config()
        enemy_speed = config.get('enemy_speed', {})
        if not isinstance(enemy_speed, dict):
            enemy_speed = {}

        preferred_name_substrings = config.get('preferred_name_substrings', [])
        if isinstance(preferred_name_substrings, list):
            parsed_name_substrings = [
                str(item).strip()
                for item in preferred_name_substrings
                if str(item).strip()
            ]
        else:
            parsed_name_substrings = ['H303', 'MAGENE']

        return {
            'auto_connect_on_launch': self._parse_config_bool(config.get('auto_connect_on_launch'), False),
            'scan_timeout_ms': self._parse_config_int(config.get('scan_timeout_ms'), 8000, minimum=1000),
            'reconnect_delay_ms': self._parse_config_int(config.get('reconnect_delay_ms'), 3000, minimum=1000),
            'preferred_address': str(config.get('preferred_address', '')).strip(),
            'preferred_device_name': str(config.get('preferred_device_name', '')).strip(),
            'preferred_name_substrings': parsed_name_substrings or ['H303', 'MAGENE'],
            'enemy_speed_enabled': self._parse_config_bool(enemy_speed.get('enabled'), True),
            'command_cooldown_ms': self._parse_config_int(
                enemy_speed.get('command_cooldown_ms'),
                2000,
                minimum=0,
            ),
            'levels': self._parse_ble_hr_levels(enemy_speed.get('levels')),
        }

    def _parse_ble_hr_levels(self, levels: object) -> list[dict[str, int]]:
        if not isinstance(levels, list):
            return []

        parsed_levels: list[dict[str, int]] = []
        for item in levels:
            if not isinstance(item, dict):
                continue

            bpm = self._parse_optional_config_int(item.get('bpm'), minimum=1)
            speed_percent = self._parse_optional_config_int(item.get('speed_percent'), minimum=100, maximum=1000)
            if bpm is None or speed_percent is None:
                continue

            parsed_levels.append({
                'bpm': bpm,
                'speed_percent': speed_percent,
            })

        parsed_levels.sort(key=lambda level: (level['bpm'], level['speed_percent']))
        return parsed_levels

    def _build_ble_hr_level_rows(self, levels: list[dict[str, int]], row_count: int = 4) -> list[tuple[str, str]]:
        rows = [
            (str(level['bpm']), str(level['speed_percent']))
            for level in levels[:row_count]
        ]
        while len(rows) < row_count:
            rows.append(('', ''))
        return rows

    def _compute_ble_hr_target_speed_percent(self, heart_rate: int, levels: list[dict[str, int]]) -> int:
        target_speed_percent = 100
        for level in levels:
            if heart_rate >= level['bpm']:
                target_speed_percent = level['speed_percent']
            else:
                break
        return max(100, target_speed_percent)

    def _compute_ble_hr_level_index(self, heart_rate: int | None, levels: list[dict[str, int]]) -> int:
        if heart_rate is None:
            return 0

        level_index = 0
        for level in levels:
            if heart_rate >= level['bpm']:
                level_index += 1
            else:
                break
        return level_index

    def _resolve_ble_hr_live_bpm_color(self, heart_rate: int | None, levels: list[dict[str, int]]) -> str:
        level_index = self._compute_ble_hr_level_index(heart_rate, levels)
        capped_index = max(0, min(level_index, len(BLE_HR_LEVEL_COLORS) - 1))
        return BLE_HR_LEVEL_COLORS[capped_index]

    def _describe_ble_hr_speed_state(
        self,
        heart_rate: int,
        levels: list[dict[str, int]],
        applied_speed_percent: int,
    ) -> str:
        if not levels:
            return 'No levels configured, staying at 100%'

        current_level: dict[str, int] | None = None
        next_level: dict[str, int] | None = None
        for level in levels:
            if heart_rate >= level['bpm']:
                current_level = level
                continue
            next_level = level
            break

        if applied_speed_percent <= 100:
            if next_level is not None:
                return f"Waiting for >= {next_level['bpm']} BPM"
            return 'Base speed locked at 100%'

        if next_level is not None:
            return (
                f"Tier {applied_speed_percent}% active | "
                f"next {next_level['speed_percent']}% at {next_level['bpm']} BPM"
            )

        if current_level is not None:
            return f"Top tier active (threshold {current_level['bpm']} BPM)"
        return f'{applied_speed_percent}% active'

    def _format_ble_hr_level_summary(self, levels: list[dict[str, int]]) -> str:
        if not levels:
            return 'no thresholds'
        return ' | '.join(
            f">={level['bpm']} BPM => {level['speed_percent']}%"
            for level in levels
        )

    def _format_ble_hr_rule_text(self, config: dict[str, object]) -> str:
        return (
            f"Scan {config['scan_timeout_ms']} ms | "
            f"reconnect {config['reconnect_delay_ms']} ms | "
            f"cooldown {config['command_cooldown_ms']} ms\n"
            f"{self._format_ble_hr_level_summary(config['levels'])}"
        )

    def _parse_config_int(self, value: object, default: int, *, minimum: int) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            parsed = default
        return max(minimum, parsed)

    def _parse_optional_config_int(self, value: object, *, minimum: int, maximum: int | None = None) -> int | None:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return None
        parsed = max(minimum, parsed)
        if maximum is not None:
            parsed = min(maximum, parsed)
        return parsed

    def _parse_config_bool(self, value: object, default: bool) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return default
        text = str(value).strip().lower()
        if text in {'1', 'true', 'yes', 'on'}:
            return True
        if text in {'0', 'false', 'no', 'off'}:
            return False
        return default

    def _parse_user_int(
        self,
        raw_value: str,
        *,
        label: str,
        minimum: int,
        maximum: int | None = None,
    ) -> int:
        try:
            value = int(str(raw_value).strip())
        except (TypeError, ValueError) as exc:
            raise ValueError(f'{label} must be an integer') from exc

        if value < minimum:
            raise ValueError(f'{label} must be >= {minimum}')
        if maximum is not None and value > maximum:
            raise ValueError(f'{label} must be <= {maximum}')
        return value

    def _format_heart_rate_sample_text(self, heart_rate: int | None, measured_at_ms: int | None) -> str:
        if heart_rate is None:
            return 'No heart-rate sample received yet'

        text = f'{heart_rate} BPM'
        if measured_at_ms is not None:
            timestamp = datetime.fromtimestamp(measured_at_ms / 1000.0)
            text += f" at {timestamp.strftime('%H:%M:%S')}"
        return text

    def _format_ble_hr_live_bpm_text(self, heart_rate: int | None) -> str:
        if heart_rate is None:
            return '--'
        return str(max(0, int(heart_rate)))

    def _format_ble_hr_live_detail_text(self, heart_rate: int | None, measured_at_ms: int | None) -> str:
        if heart_rate is None:
            if self.ble_hr_client.is_connected:
                return 'Connected, waiting for first sample'
            if self.ble_hr_client.is_running:
                return 'Searching for Bluetooth heart-rate device'
            return 'Waiting for Bluetooth heart rate'

        if measured_at_ms is not None:
            timestamp = datetime.fromtimestamp(measured_at_ms / 1000.0)
            return f"Updated at {timestamp.strftime('%H:%M:%S')}"
        return 'Live heart-rate sample received'

    def _format_ble_hr_device_text(self, config: dict[str, object]) -> str:
        name = self._ble_hr_device_name.strip()
        address = self._ble_hr_device_address.strip()
        if name and address:
            return f'{name} ({address})'
        if name:
            return name
        if address:
            return address

        preferred_name_substrings = config.get('preferred_name_substrings', [])
        if isinstance(preferred_name_substrings, list):
            tokens = [
                str(item).strip()
                for item in preferred_name_substrings
                if str(item).strip()
            ]
            if tokens:
                return f"Auto scan: {', '.join(tokens)}"
        return 'No preferred device saved yet'
