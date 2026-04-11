from __future__ import annotations

import asyncio
import threading
from typing import Any, Callable

from twitchAPI.eventsub.websocket import EventSubWebsocket
from twitchAPI.helper import first
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.object.eventsub import ChannelPointsCustomRewardRedemptionAddEvent
from twitchAPI.twitch import Twitch
from twitchAPI.type import AuthScope


class TwitchBridgeClient:
    def __init__(
        self,
        config_loader: Callable[[], dict[str, Any]],
        tokens_loader: Callable[[], dict[str, Any] | None],
        tokens_saver: Callable[[dict[str, Any]], None],
        on_redeem: Callable[[str, str, str], None],
        on_status: Callable[[str], None],
    ) -> None:
        self._config_loader = config_loader
        self._tokens_loader = tokens_loader
        self._tokens_saver = tokens_saver
        self._on_redeem = on_redeem
        self._on_status = on_status
        self._thread: threading.Thread | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._stop_event: asyncio.Event | None = None
        self._connected = False

    @property
    def is_running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def connect(self) -> None:
        if self.is_running:
            raise RuntimeError('Twitch client is already running')
        self._thread = threading.Thread(target=self._run_thread, name='twitch-eventsub', daemon=True)
        self._thread.start()

    def disconnect(self) -> None:
        if self._loop and self._stop_event:
            self._loop.call_soon_threadsafe(self._stop_event.set)
        self._connected = False
        self._on_status('Disconnected')

    def _run_thread(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._stop_event = asyncio.Event()
        try:
            self._loop.run_until_complete(self._main())
        except Exception as exc:
            self._connected = False
            self._on_status(f'Error: {exc}')
        finally:
            try:
                pending = asyncio.all_tasks(self._loop)
                for task in pending:
                    task.cancel()
            except Exception:
                pass
            self._loop.close()
            self._loop = None
            self._stop_event = None

    async def _main(self) -> None:
        config = self._config_loader()
        client_id = (config.get('client_id') or '').strip()
        client_secret = (config.get('client_secret') or '').strip()
        if not client_id or not client_secret:
            raise RuntimeError('Twitch client_id and client_secret are required')

        scope_names = config.get('scopes') or ['CHANNEL_READ_REDEMPTIONS']
        scopes = [getattr(AuthScope, name) for name in scope_names if getattr(AuthScope, name, None) is not None]
        if not scopes:
            raise RuntimeError('No valid Twitch scopes configured')

        self._on_status('Connecting...')
        twitch = await Twitch(client_id, client_secret)
        tokens = self._tokens_loader()
        if tokens:
            await twitch.set_user_authentication(tokens['access_token'], scopes, tokens.get('refresh_token'))
            user_id = tokens['user_id']
            login = tokens.get('login', '')
        else:
            auth = UserAuthenticator(twitch, scopes)
            token, refresh_token = await auth.authenticate()
            await twitch.set_user_authentication(token, scopes, refresh_token)
            user = await first(twitch.get_users())
            user_id = user.id
            login = user.login
            self._tokens_saver({
                'access_token': token,
                'refresh_token': refresh_token,
                'user_id': user.id,
                'login': user.login,
                'display_name': user.display_name,
            })

        eventsub = EventSubWebsocket(twitch)

        async def on_event(event: ChannelPointsCustomRewardRedemptionAddEvent) -> None:
            try:
                title = event.event.reward.title
                user_input = event.event.user_input
                user_name = event.event.user_name
            except AttributeError:
                data = event.to_dict()
                payload = data.get('event', {})
                title = payload.get('reward', {}).get('title', '')
                user_input = payload.get('user_input', '')
                user_name = payload.get('user_name') or payload.get('user_login') or ''
            self._on_redeem(title, user_input, user_name)

        eventsub.start()
        await eventsub.listen_channel_points_custom_reward_redemption_add(user_id, on_event)
        self._connected = True
        self._on_status(f'Connected as {login or user_id}')
        await self._stop_event.wait()
        self._connected = False
        await eventsub.stop()
        await twitch.close()
