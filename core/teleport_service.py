from __future__ import annotations

import random
from typing import Any

from adapter.save_context_adapter import SaveContextAdapter
from core.inventory_definitions import (
    ALL_TELEPORT_DESTINATIONS,
    RANDOM_TELEPORT_DESTINATIONS,
    RANDOM_TELEPORT_KEYS,
    WARP_SONG_DESTINATIONS,
)


class TeleportService:
    """
    Encapsulates all teleport-related logic.

    Responsibilities:
    - expose destination pools (all / safe / warp songs)
    - resolve runtime state into human-readable destinations
    - execute teleports through SaveContextAdapter (PlayState runtime)
    - keep track of last triggered teleport for UI fallback

    This service isolates teleport behavior from the controller and keeps
    all destination-related rules in one place.
    """

    def __init__(self) -> None:
        # Used when runtime state cannot be resolved (fallback for UI)
        self._last_runtime_teleport_key: str = ""

    def get_warp_song_destinations(self) -> dict[str, dict[str, Any]]:
        """Return a detached copy of the warp-song destinations."""
        return {key: dict(value) for key, value in WARP_SONG_DESTINATIONS.items()}

    def get_all_destinations(self) -> dict[str, dict[str, Any]]:
        """Return a detached copy of every configured teleport destination."""
        return {key: dict(value) for key, value in ALL_TELEPORT_DESTINATIONS.items()}

    def get_safe_random_destinations(self) -> dict[str, dict[str, Any]]:
        """Return the conservative destination pool used by the random warp."""
        return {key: dict(value) for key, value in RANDOM_TELEPORT_DESTINATIONS.items()}

    def get_runtime_state(self, adapter: SaveContextAdapter) -> dict[str, Any]:
        """
        Read the live PlayState warp fields and map them to a known destination.

        Raw runtime only exposes numeric values (entrance id, trigger, etc.).
        This method resolves them back into a configured destination so the UI
        can display meaningful labels instead of raw memory values.
        """
        runtime = adapter.get_runtime_warp_state()

        destination_key = self._resolve_runtime_destination_key(
            runtime.get("next_entrance")
        )
        destination = ALL_TELEPORT_DESTINATIONS.get(destination_key) if destination_key else None

        runtime["destination_key"] = destination_key
        runtime["destination_label"] = destination["label"] if destination else "Unknown"

        # Useful when runtime values are not yet updated or temporarily invalid
        runtime["last_runtime_teleport_key"] = self._last_runtime_teleport_key

        return runtime

    def teleport_to_destination(
        self,
        adapter: SaveContextAdapter,
        destination_key: str,
    ) -> dict[str, Any]:
        """
        Execute a runtime teleport using PlayState.

        This is the primary teleport path:
        - writes nextEntrance
        - sets transition
        - triggers warp
        """
        destination = self._require_destination(destination_key)

        adapter.teleport_runtime(
            entrance_id=int(destination["entrance_id"])
        )

        self._last_runtime_teleport_key = destination_key

        return dict(destination)

    def teleport_to_warp_song(
        self,
        adapter: SaveContextAdapter,
        destination_key: str,
    ) -> dict[str, Any]:
        """
        Teleport using a warp-song destination subset.

        This is logically identical to a normal teleport but constrained
        to validated song destinations for safety and UX clarity.
        """
        if destination_key not in WARP_SONG_DESTINATIONS:
            raise ValueError(f"Unknown warp destination: {destination_key}")

        return self.teleport_to_destination(adapter, destination_key)

    def teleport_random_safe(self, adapter: SaveContextAdapter) -> dict[str, Any]:
        """
        Teleport to a random destination from the safe pool.

        The safe pool excludes:
        - cutscenes
        - boss rooms
        - unstable or scripted locations
        """
        if not RANDOM_TELEPORT_KEYS:
            raise RuntimeError("No safe random teleport destinations are configured")

        destination_key = random.choice(tuple(RANDOM_TELEPORT_KEYS))

        return self.teleport_to_destination(adapter, destination_key)

    def _resolve_runtime_destination_key(self, entrance_id: Any) -> str | None:
        """
        Map a runtime entrance id back to a configured destination.

        If no match is found:
        - fallback to last known teleport
        - prevents UI from losing context
        """
        try:
            normalized_entrance = int(entrance_id)
        except (TypeError, ValueError):
            return self._last_runtime_teleport_key or None

        for key, value in ALL_TELEPORT_DESTINATIONS.items():
            if int(value["entrance_id"]) == normalized_entrance:
                return key

        return self._last_runtime_teleport_key or None

    def _require_destination(self, destination_key: str) -> dict[str, Any]:
        """Return a destination definition or raise a clear error."""
        try:
            return ALL_TELEPORT_DESTINATIONS[destination_key]
        except KeyError as exc:
            raise ValueError(f"Unknown teleport destination: {destination_key}") from exc