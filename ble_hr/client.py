from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Callable

try:
    from bleak import BleakClient, BleakScanner
    _BLEAK_IMPORT_ERROR: Exception | None = None
except ImportError as exc:  # pragma: no cover - depends on local environment
    BleakClient = None  # type: ignore[assignment]
    BleakScanner = None  # type: ignore[assignment]
    _BLEAK_IMPORT_ERROR = exc

HEART_RATE_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
HEART_RATE_MEASUREMENT_UUID = "00002a37-0000-1000-8000-00805f9b34fb"


@dataclass(frozen=True)
class BleHeartRateDevice:
    address: str
    name: str
    rssi: int | None = None


class BleHeartRateClient:
    def __init__(
        self,
        config_loader: Callable[[], dict[str, Any]],
        on_heart_rate: Callable[[int, int | None], None],
        on_status: Callable[[str], None],
        on_device: Callable[[BleHeartRateDevice], None],
    ) -> None:
        self._config_loader = config_loader
        self._on_heart_rate = on_heart_rate
        self._on_status = on_status
        self._on_device = on_device
        self._thread = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._stop_event: asyncio.Event | None = None
        self._connected = False
        self._last_status = ""
        self._last_scan_summary = ""

    @property
    def is_running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    @property
    def is_connected(self) -> bool:
        return self._connected

    def connect(self) -> None:
        import threading

        if _BLEAK_IMPORT_ERROR is not None:
            raise RuntimeError(
                "Bluetooth support requires the 'bleak' package. Install requirements.txt and restart the app."
            ) from _BLEAK_IMPORT_ERROR
        if self.is_running:
            raise RuntimeError("Bluetooth HR client is already running")
        self._thread = threading.Thread(target=self._run_thread, name="ble-heart-rate", daemon=True)
        self._thread.start()

    def disconnect(self) -> None:
        if self._loop and self._stop_event:
            self._loop.call_soon_threadsafe(self._stop_event.set)
        self._connected = False
        self._emit_status("Disconnected")

    def _emit_status(self, status: str) -> None:
        if status == self._last_status:
            return
        self._last_status = status
        self._on_status(status)

    def _run_thread(self) -> None:
        self._prepare_windows_ble_thread()
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._stop_event = asyncio.Event()
        try:
            self._loop.run_until_complete(self._main())
        except Exception as exc:
            self._connected = False
            self._emit_status(f"Bluetooth HR error: {exc}")
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

    def _prepare_windows_ble_thread(self) -> None:
        try:
            from bleak.backends.winrt.util import uninitialize_sta

            uninitialize_sta()
        except Exception:
            pass

    async def _main(self) -> None:
        while not self._stop_event.is_set():
            config = self._runtime_config()
            reconnect_delay_seconds = config["reconnect_delay_ms"] / 1000.0

            try:
                device = await self._find_candidate_device(config)
            except Exception as exc:
                self._connected = False
                self._emit_status(f"Bluetooth scan failed: {exc}")
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=reconnect_delay_seconds)
                    break
                except asyncio.TimeoutError:
                    continue

            if device is None:
                self._connected = False
                summary = self._last_scan_summary.strip()
                if summary:
                    self._emit_status(f"No compatible Bluetooth heart-rate monitor found ({summary})")
                else:
                    self._emit_status("No compatible Bluetooth heart-rate monitor found")
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=reconnect_delay_seconds)
                    break
                except asyncio.TimeoutError:
                    continue

            try:
                await self._connect_and_stream(device)
            except Exception as exc:
                self._connected = False
                self._emit_status(f"Bluetooth HR retrying after error: {exc}")
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=reconnect_delay_seconds)
                    break
                except asyncio.TimeoutError:
                    continue

    async def _find_candidate_device(self, config: dict[str, Any]) -> BleHeartRateDevice | None:
        self._last_scan_summary = ""
        scan_timeout_seconds = config["scan_timeout_ms"] / 1000.0
        preferred_address = str(config.get("preferred_address", "")).strip()
        preferred_device_name = str(config.get("preferred_device_name", "")).strip()
        filtered_entries: list[tuple[Any, Any]] = []
        fallback_entries: list[tuple[Any, Any]] = []
        direct_probe_attempted = False
        probed_candidates = 0

        if preferred_address:
            self._emit_status(f"Looking for saved device {preferred_address}...")
            device = await BleakScanner.find_device_by_address(preferred_address, timeout=scan_timeout_seconds)
            if device is not None:
                return BleHeartRateDevice(
                    address=str(device.address or preferred_address),
                    name=str(device.name or config.get("preferred_device_name") or "Bluetooth HR"),
                )
            direct_probe_attempted = True
            direct_candidate = await self._probe_saved_address_for_heart_rate_service(
                preferred_address,
                preferred_device_name or "Bluetooth HR",
            )
            if direct_candidate is not None:
                return direct_candidate

        self._emit_status("Scanning for Bluetooth heart-rate monitor...")
        filtered_entries = await self._discover_with_advertisements(
            scan_timeout_seconds,
            service_filter=[HEART_RATE_SERVICE_UUID],
        )
        selected = self._select_candidate(filtered_entries, config)
        if selected is not None:
            return selected

        self._emit_status("Fallback scan without service filter...")
        fallback_entries = await self._discover_with_advertisements(
            scan_timeout_seconds,
            service_filter=None,
        )
        selected = self._select_candidate(fallback_entries, config)
        if selected is not None:
            return selected

        merged_entries = self._merge_discovery_entries(filtered_entries, fallback_entries)
        probed, probed_candidates = await self._probe_candidates_for_heart_rate_service(merged_entries, config)
        if probed is not None:
            return probed

        self._last_scan_summary = self._format_scan_summary(
            preferred_address_used=bool(preferred_address),
            direct_probe_attempted=direct_probe_attempted,
            filtered_count=len(filtered_entries),
            fallback_count=len(fallback_entries),
            probed_candidates=probed_candidates,
        )
        return None

    async def _discover_with_advertisements(
        self,
        timeout_seconds: float,
        *,
        service_filter: list[str] | None,
    ) -> list[tuple[Any, Any]]:
        async with BleakScanner(service_uuids=service_filter) as scanner:
            await asyncio.sleep(timeout_seconds)
        return list(scanner.discovered_devices_and_advertisement_data.values())

    def _select_candidate(self, entries: list[tuple[Any, Any]], config: dict[str, Any]) -> BleHeartRateDevice | None:
        if not entries:
            return None

        preferred_address = str(config.get("preferred_address", "")).strip().lower()
        preferred_device_name = str(config.get("preferred_device_name", "")).strip().lower()
        preferred_name_substrings = [
            str(item).strip().lower()
            for item in config.get("preferred_name_substrings", [])
            if str(item).strip()
        ]

        best_candidate: BleHeartRateDevice | None = None
        best_key: tuple[int, int, int] | None = None

        for device, advertisement in entries:
            address = str(getattr(device, "address", "") or "").strip()
            if not address:
                continue

            name = str(
                getattr(advertisement, "local_name", None)
                or getattr(device, "name", None)
                or "Unknown BLE device"
            ).strip()
            name_lower = name.lower()
            service_uuids = {
                str(item).strip().lower()
                for item in (getattr(advertisement, "service_uuids", None) or [])
                if str(item).strip()
            }
            rssi = getattr(advertisement, "rssi", None)

            score = 0
            if preferred_address and address.lower() == preferred_address:
                score += 1000
            if preferred_device_name and name_lower == preferred_device_name:
                score += 400
            elif preferred_device_name and (
                preferred_device_name in name_lower or name_lower in preferred_device_name
            ):
                score += 250
            if any(token in name_lower for token in preferred_name_substrings):
                score += 200
            if HEART_RATE_SERVICE_UUID.lower() in service_uuids or "180d" in service_uuids:
                score += 100
            if name and name != "Unknown BLE device":
                score += 10

            if score < 100:
                continue

            rssi_value = int(rssi) if isinstance(rssi, int) else -127
            candidate_key = (score, rssi_value, 1 if name != "Unknown BLE device" else 0)
            if best_key is None or candidate_key > best_key:
                best_key = candidate_key
                best_candidate = BleHeartRateDevice(
                    address=address,
                    name=name,
                    rssi=rssi_value if isinstance(rssi_value, int) else None,
                )

        return best_candidate

    def _rank_probe_candidates(self, entries: list[tuple[Any, Any]], config: dict[str, Any]) -> list[BleHeartRateDevice]:
        preferred_address = str(config.get("preferred_address", "")).strip().lower()
        preferred_device_name = str(config.get("preferred_device_name", "")).strip().lower()
        preferred_name_substrings = [
            str(item).strip().lower()
            for item in config.get("preferred_name_substrings", [])
            if str(item).strip()
        ]

        ranked_rows: list[tuple[tuple[int, int, int], BleHeartRateDevice]] = []
        seen_addresses: set[str] = set()

        for device, advertisement in entries:
            address = str(getattr(device, "address", "") or "").strip()
            if not address:
                continue

            normalized_address = address.lower()
            if normalized_address in seen_addresses:
                continue
            seen_addresses.add(normalized_address)

            name = str(
                getattr(advertisement, "local_name", None)
                or getattr(device, "name", None)
                or "Unknown BLE device"
            ).strip()
            name_lower = name.lower()
            service_uuids = {
                str(item).strip().lower()
                for item in (getattr(advertisement, "service_uuids", None) or [])
                if str(item).strip()
            }
            raw_rssi = getattr(advertisement, "rssi", None)
            rssi_value = int(raw_rssi) if isinstance(raw_rssi, int) else -127

            score = 0
            if preferred_address and normalized_address == preferred_address:
                score += 1000
            if preferred_device_name and name_lower == preferred_device_name:
                score += 400
            elif preferred_device_name and (
                preferred_device_name in name_lower or name_lower in preferred_device_name
            ):
                score += 250
            if any(token in name_lower for token in preferred_name_substrings):
                score += 200
            if HEART_RATE_SERVICE_UUID.lower() in service_uuids or "180d" in service_uuids:
                score += 100
            if name and name != "Unknown BLE device":
                score += 10

            ranked_rows.append((
                (score, rssi_value, 1 if name != "Unknown BLE device" else 0),
                BleHeartRateDevice(
                    address=address,
                    name=name,
                    rssi=rssi_value if isinstance(rssi_value, int) else None,
                ),
            ))

        ranked_rows.sort(key=lambda row: row[0], reverse=True)
        return [candidate for _key, candidate in ranked_rows]

    async def _probe_candidates_for_heart_rate_service(
        self,
        entries: list[tuple[Any, Any]],
        config: dict[str, Any],
    ) -> tuple[BleHeartRateDevice | None, int]:
        candidates = self._rank_probe_candidates(entries, config)
        if not candidates:
            return None, 0

        probe_limit = min(6, len(candidates))
        self._emit_status(f"Probing {probe_limit} scanned device(s) for heart-rate service...")

        for candidate in candidates[:probe_limit]:
            if await self._address_exposes_heart_rate_service(candidate.address):
                return candidate, probe_limit

        return None, probe_limit

    async def _probe_saved_address_for_heart_rate_service(
        self,
        address: str,
        fallback_name: str,
    ) -> BleHeartRateDevice | None:
        self._emit_status(f"Trying saved device {address} directly...")
        if not await self._address_exposes_heart_rate_service(address):
            return None
        return BleHeartRateDevice(address=address, name=fallback_name or "Bluetooth HR")

    async def _address_exposes_heart_rate_service(self, address: str) -> bool:
        client = BleakClient(address)
        try:
            await asyncio.wait_for(client.connect(), timeout=6.0)
            services = client.services
            return bool(services is not None and services.get_service(HEART_RATE_SERVICE_UUID))
        except Exception:
            return False
        finally:
            try:
                if client.is_connected:
                    await client.disconnect()
            except Exception:
                pass

    def _merge_discovery_entries(self, *entry_groups: list[tuple[Any, Any]]) -> list[tuple[Any, Any]]:
        merged: list[tuple[Any, Any]] = []
        seen_addresses: set[str] = set()

        for entries in entry_groups:
            for device, advertisement in entries:
                address = str(getattr(device, "address", "") or "").strip().lower()
                if not address or address in seen_addresses:
                    continue
                seen_addresses.add(address)
                merged.append((device, advertisement))

        return merged

    def _format_scan_summary(
        self,
        *,
        preferred_address_used: bool,
        direct_probe_attempted: bool,
        filtered_count: int,
        fallback_count: int,
        probed_candidates: int,
    ) -> str:
        details = [
            f"filtered scan: {filtered_count}",
            f"fallback scan: {fallback_count}",
        ]
        if preferred_address_used:
            details.append(
                "saved device direct probe attempted"
                if direct_probe_attempted
                else "saved device lookup only"
            )
        if probed_candidates > 0:
            details.append(f"service probes: {probed_candidates}")
        return ", ".join(details)

    async def _connect_and_stream(self, device: BleHeartRateDevice) -> None:
        disconnect_event = asyncio.Event()

        def on_disconnect(_client: BleakClient) -> None:
            if self._loop:
                self._loop.call_soon_threadsafe(disconnect_event.set)

        client = BleakClient(device.address, disconnected_callback=on_disconnect)
        await client.connect()
        self._connected = True
        self._on_device(device)
        self._emit_status(f"Connected to {device.name} ({device.address})")

        def notification_handler(_sender: Any, data: bytearray) -> None:
            try:
                heart_rate = self._parse_heart_rate_measurement(data)
            except Exception:
                return
            self._on_heart_rate(heart_rate, int(time.time() * 1000))

        try:
            await client.start_notify(HEART_RATE_MEASUREMENT_UUID, notification_handler)
            while not self._stop_event.is_set() and client.is_connected and not disconnect_event.is_set():
                await asyncio.sleep(0.25)
        finally:
            self._connected = False
            if not self._stop_event.is_set():
                self._emit_status("Bluetooth HR disconnected, scanning again...")
            try:
                if client.is_connected:
                    await client.stop_notify(HEART_RATE_MEASUREMENT_UUID)
            except Exception:
                pass
            try:
                if client.is_connected:
                    await client.disconnect()
            except Exception:
                pass

    def _parse_heart_rate_measurement(self, data: bytearray) -> int:
        if not data or len(data) < 2:
            raise ValueError("Heart rate notification is too short")

        flags = data[0]
        if flags & 0x01:
            if len(data) < 3:
                raise ValueError("Heart rate notification missing UINT16 payload")
            return int.from_bytes(data[1:3], "little", signed=False)
        return int(data[1])

    def _runtime_config(self) -> dict[str, Any]:
        config = self._config_loader()
        return {
            "scan_timeout_ms": self._read_int(config.get("scan_timeout_ms"), default=8000, minimum=1000),
            "reconnect_delay_ms": self._read_int(config.get("reconnect_delay_ms"), default=3000, minimum=1000),
            "preferred_address": str(config.get("preferred_address", "")).strip(),
            "preferred_device_name": str(config.get("preferred_device_name", "")).strip(),
            "preferred_name_substrings": list(config.get("preferred_name_substrings", []) or []),
        }

    def _read_int(self, value: Any, *, default: int, minimum: int) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            parsed = default
        return max(minimum, parsed)
