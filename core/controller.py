from __future__ import annotations

from pathlib import Path
from typing import Optional

from adapter.health_adapter import HealthAdapter
from adapter.process_scanner import ProcessScanner
from adapter.profile_manager import ProfileManager
from adapter.save_context_adapter import SaveContextAdapter
from adapter.dll_bridge_adapter import DllBridgeAdapter
from core.controller_debug_quest import DebugQuestControllerMixin
from core.controller_equipment import EquipmentControllerMixin
from core.controller_magic_buttons_teleport import MagicButtonsTeleportControllerMixin
from core.controller_rupees_inventory import RupeeInventoryControllerMixin
from core.logger import RuntimeLogger
from core.models import HealthState
from core.teleport_service import TeleportService
from twitch.client import TwitchBridgeClient
from twitch.config_store import TwitchConfigStore
from twitch.reward_actions import TwitchRewardExecutor


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


    def get_app_metadata(self) -> dict[str, str]:
        return self.profile_manager.app_metadata()

    def process_twitch_timers(self) -> None:
        self.twitch_rewards.tick()

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

    def _handle_twitch_redeem(self, reward_title: str, user_input: str, user_name: str) -> None:
        self.set_last_twitch_event(user_name=user_name, reward_title=reward_title, user_input=user_input, status='received')
        self._log(f'Twitch redeem received: {user_name or "viewer"} -> {reward_title} ({user_input or "no input"})')
        try:
            self.twitch_rewards.execute(reward_title, user_input, user_name)
        except Exception as exc:
            self.set_last_twitch_event(user_name=user_name, reward_title=reward_title, user_input=user_input, status=f'error: {exc}')
            self._log(f'Twitch redeem failed: {exc}')
