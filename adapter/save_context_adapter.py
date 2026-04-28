from __future__ import annotations

import ctypes
import struct

from adapter.windows_memory import WindowsProcessMemory
from adapter.dynamic_offset_resolver import DynamicOffsetResolver


kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
ReadProcessMemory = kernel32.ReadProcessMemory
ReadProcessMemory.argtypes = [
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_size_t),
]
ReadProcessMemory.restype = ctypes.c_int


class SaveContextAdapter:
    _SAVE_MAGIC_LEVEL_OFFSET = 0x0032
    _SAVE_MAGIC_CURRENT_OFFSET = 0x0033
    _SAVE_MAGIC_ACQUIRED_OFFSET = 0x003A
    _SAVE_DOUBLE_MAGIC_ACQUIRED_OFFSET = 0x003C
    _SAVE_MAGIC_STATE_OFFSET = 0x13F0
    _SAVE_PREV_MAGIC_STATE_OFFSET = 0x13F2
    _SAVE_MAGIC_CAPACITY_OFFSET = 0x13F4
    _SAVE_MAGIC_FILL_TARGET_OFFSET = 0x13F6
    _SAVE_MAGIC_TARGET_OFFSET = 0x13F8
    _SAVE_ENTRANCE_INDEX_OFFSET = 0x0000
    _SAVE_RESPAWN_FLAG_OFFSET = 0x1364
    _SAVE_RESPAWN_DOWN_OFFSET = 0x1368
    _SAVE_NEXT_TRANSITION_TYPE_OFFSET = 0x141D

    _RESPAWN_POS_X_OFFSET = 0x00
    _RESPAWN_POS_Y_OFFSET = 0x04
    _RESPAWN_POS_Z_OFFSET = 0x08
    _RESPAWN_YAW_OFFSET = 0x0C
    _RESPAWN_PLAYER_PARAMS_OFFSET = 0x0E
    _RESPAWN_ENTRANCE_INDEX_OFFSET = 0x10
    _RESPAWN_ROOM_INDEX_OFFSET = 0x12
    _RESPAWN_DATA_OFFSET = 0x13
    _RESPAWN_TEMP_SWCH_FLAGS_OFFSET = 0x14
    _RESPAWN_TEMP_COLLECT_FLAGS_OFFSET = 0x18

    _MAGIC_STATE_IDLE = 0
    _ITEM_EQUIPS_OFFSET = 0x70
    _BUTTON_OFFSETS: dict[str, int] = {
        "b": 0x78,
        "cleft": 0x79,
        "cdown": 0x7A,
        "cright": 0x7B,
        "dup": 0x7C,
        "ddown": 0x7D,
        "dleft": 0x7E,
        "dright": 0x7F,
    }
    _BUTTON_ITEMS: dict[str, int] = {
        "none": 0xFF,
        "stick": 0x00,
        "nut": 0x01,
        "bomb": 0x02,
        "bow": 0x03,
        "fire_arrow": 0x04,
        "dins_fire": 0x05,
        "slingshot": 0x06,
        "ocarina_fairy": 0x07,
        "ocarina_time": 0x08,
        "bombchu": 0x09,
        "hookshot": 0x0A,
        "longshot": 0x0B,
        "ice_arrow": 0x0C,
        "farores_wind": 0x0D,
        "boomerang": 0x0E,
        "lens": 0x0F,
        "beans": 0x10,
        "hammer": 0x11,
        "light_arrow": 0x12,
        "nayrus_love": 0x13,
        "bottle": 0x14,
        "letter": 0x15,
        "kokiri_sword": 0x3B,
        "master_sword": 0x3C,
        "biggoron_sword": 0x3D,
    }
    _SWORD_NIBBLES: dict[str, int] = {
        "none": 0,
        "kokiri": 1,
        "master": 2,
        "biggoron": 3,
    }
    _SWORD_B_ITEMS: dict[str, int] = {
        "kokiri": 0x3B,
        "master": 0x3C,
        "biggoron": 0x3D,
    }

    _GPLAYSTATE_PTR_RVA = 0x2098530
    _PLAYSTATE_TRANSITION_TRIGGER_OFFSET = 0x21061
    _PLAYSTATE_NEXT_ENTRANCE_OFFSET = 0x21066
    _PLAYSTATE_TRANSITION_TYPE_OFFSET = 0x210AA

    _TRANS_TRIGGER_START = 1
    _TRANS_TYPE_INSTANT = 0x0B

    _LINK_FREEZE_TIMER_OFFSET = 0x0110
    _LINK_SHOCK_TIMER_OFFSET = 0x0891
    _LINK_BURN_FLAG_OFFSET = 0x0A60
    _LINK_BURN_FLAMES_OFFSET = 0x0A61
    _LINK_BURN_FLAMES_COUNT = 18

    # ------------------------------------------------------------------
    # VALIDATED RUNTIME OFFSETS
    # Confirmed in live memory tests against the current SoH build.
    # These addresses are relative to module_base("soh.exe") and are used
    # instead of save_context offsets for the corresponding runtime fields.
    # ------------------------------------------------------------------
    _RUNTIME_OFFSETS: dict[str, int] = {
        "equipped_equipment": 0x209CEC8,
        "owned_equipment": 0x209CEF4,
        "upgrades": 0x209CEF8,
        "quest_items": 0x209CEFC,
    }

    def __init__(self, fingerprint, profile: dict) -> None:
        self.memory = WindowsProcessMemory(fingerprint.pid)
        self.profile = profile
        self.dynamic_resolver = DynamicOffsetResolver(self.memory, profile)
        self._manual_player_address: int | None = None

    def close(self) -> None:
        self.memory.close()

    # ------------------------------------------------------------------
    # PROFILE CONFIG
    # ------------------------------------------------------------------
    def _save_cfg(self) -> dict:
        cfg = self.profile.get("save_context")
        if not cfg:
            raise RuntimeError("Missing save_context in profile")
        return cfg

    def _items_cfg(self) -> dict:
        cfg = self.profile.get("items_runtime")
        if not cfg:
            raise RuntimeError("Missing items_runtime in profile")
        return cfg

    def _ammo_cfg(self) -> dict:
        cfg = self.profile.get("ammo_runtime")
        if not cfg:
            raise RuntimeError("Missing ammo_runtime in profile")
        return cfg

    def _link_state_cfg(self) -> dict:
        return self.profile.get("link_state", {})


    # ------------------------------------------------------------------
    # ADDRESS HELPERS
    # ------------------------------------------------------------------
    def _module_base(self, module_name: str) -> int:
        return self.memory.get_module_base(module_name)

    def _base_from_cfg(self, cfg: dict, offset_key: str = "base_offset") -> int:
        strategy = cfg.get("strategy")
        if strategy != "module_offset":
            raise RuntimeError(f"Unsupported save context strategy: {strategy}")
        return self._module_base(cfg["module"]) + int(cfg[offset_key], 16)

    def _save_base(self) -> int:
        return self.dynamic_resolver.runtime_map().save_base

    def _items_base(self) -> int:
        return self.dynamic_resolver.runtime_map().items_base

    def _ammo_base(self) -> int:
        return self.dynamic_resolver.runtime_map().ammo_base

    def _save_addr(self, key: str) -> int:
        cfg = self._save_cfg()
        return self._save_base() + int(cfg[key], 16)

    def _items_addr(self, slot: int) -> int:
        return self._items_base() + slot

    def _ammo_addr(self, slot: int) -> int:
        return self._ammo_base() + slot

    def _runtime_addr(self, name: str) -> int:
        mapping = {
            "equipped_equipment": "equipped_equipment",
            "owned_equipment": "owned_equipment",
            "upgrades": "upgrades",
            "quest_items": "quest_items",
        }
        try:
            return self.dynamic_resolver.resolve_global_address(mapping[name])
        except KeyError as exc:
            raise RuntimeError(f"Unknown runtime address key: {name}") from exc

    def _parse_optional_hex(self, value: str | int | None) -> int | None:
        if value is None:
            return None
        if isinstance(value, int):
            return value
        raw = str(value).strip()
        if raw == "":
            return None
        if raw.lower().startswith("0x"):
            return int(raw, 16)
        return int(raw, 16)

    def set_manual_player_address(self, address: int | None) -> None:
        self._manual_player_address = address

    def get_manual_player_address(self) -> int | None:
        return self._manual_player_address

    def get_link_state_player_address(self) -> int:
        if self._manual_player_address:
            return self._manual_player_address

        cfg = self._link_state_cfg()
        absolute_address = self._parse_optional_hex(cfg.get("player_address"))
        if absolute_address is not None:
            return absolute_address

        gplay = self.get_gplaystate_address()
        if not gplay:
            return 0

        player_offset = self._parse_optional_hex(cfg.get("player_offset"))
        if player_offset is None:
            player_offset = 0x400

        try:
            return self._read_u64(gplay + player_offset)
        except OSError:
            return 0

    def _player_addr(self, offset: int) -> int:
        return self.get_link_state_player_address() + offset

    # ------------------------------------------------------------------
    # BASE ADDRESS ACCESSORS
    # ------------------------------------------------------------------
    def get_save_base(self) -> int:
        return self._save_base()

    def get_items_base(self) -> int:
        return self._items_base()

    def get_ammo_base(self) -> int:
        return self._ammo_base()

    # ------------------------------------------------------------------
    # DEBUG / ADDRESS MAP
    # ------------------------------------------------------------------
    def get_save_address_map(self) -> dict[str, int]:
        cfg = self._save_cfg()
        keys = (
            "inventory_items_offset",
            "inventory_ammo_offset",
            "equipment_offset",
            "upgrades_offset",
            "quest_items_offset",
        )

        result = {
            key: self._save_base() + int(cfg[key], 16)
            for key in keys
            if key in cfg
        }

        result["inventory_equipment_runtime_address"] = self.get_inventory_equipment_address()
        result["equips_equipment_runtime_address"] = self.get_equips_equipment_address()
        result["upgrades_runtime_address"] = self.get_upgrades_address()
        result["quest_items_runtime_address"] = self.get_quest_items_address()

        return result

    # ------------------------------------------------------------------
    # RUNTIME ADDRESSES
    # ------------------------------------------------------------------
    def get_equipped_equipment_address(self) -> int:
        return self._runtime_addr("equipped_equipment")

    def get_equips_equipment_address(self) -> int:
        return self.get_equipped_equipment_address()

    def get_owned_equipment_address(self) -> int:
        return self._runtime_addr("owned_equipment")

    def get_inventory_equipment_address(self) -> int:
        return self.get_owned_equipment_address()

    def get_upgrades_address(self) -> int:
        return self._runtime_addr("upgrades")

    def get_quest_items_address(self) -> int:
        return self._runtime_addr("quest_items")

    def get_magic_level_address(self) -> int:
        return self._save_base() + self._SAVE_MAGIC_LEVEL_OFFSET

    def get_magic_current_address(self) -> int:
        return self._save_base() + self._SAVE_MAGIC_CURRENT_OFFSET

    def get_magic_acquired_address(self) -> int:
        return self._save_base() + self._SAVE_MAGIC_ACQUIRED_OFFSET

    def get_double_magic_acquired_address(self) -> int:
        return self._save_base() + self._SAVE_DOUBLE_MAGIC_ACQUIRED_OFFSET

    def get_magic_state_address(self) -> int:
        return self._save_base() + self._SAVE_MAGIC_STATE_OFFSET

    def get_prev_magic_state_address(self) -> int:
        return self._save_base() + self._SAVE_PREV_MAGIC_STATE_OFFSET

    def get_magic_capacity_address(self) -> int:
        return self._save_base() + self._SAVE_MAGIC_CAPACITY_OFFSET

    def get_magic_fill_target_address(self) -> int:
        return self._save_base() + self._SAVE_MAGIC_FILL_TARGET_OFFSET

    def get_magic_target_address(self) -> int:
        return self._save_base() + self._SAVE_MAGIC_TARGET_OFFSET

    def get_save_entrance_index_address(self) -> int:
        return self._save_base() + self._SAVE_ENTRANCE_INDEX_OFFSET

    def get_respawn_flag_address(self) -> int:
        return self._save_base() + self._SAVE_RESPAWN_FLAG_OFFSET

    def get_respawn_down_address(self) -> int:
        return self._save_base() + self._SAVE_RESPAWN_DOWN_OFFSET

    def get_next_transition_type_address(self) -> int:
        return self._save_base() + self._SAVE_NEXT_TRANSITION_TYPE_OFFSET

    def _read_bytes(self, addr: int, size: int) -> bytes:
        buf = (ctypes.c_ubyte * size)()
        read = ctypes.c_size_t()
        ok = ReadProcessMemory(
            self.memory.handle,
            ctypes.c_void_p(addr),
            ctypes.byref(buf),
            size,
            ctypes.byref(read),
        )
        if not ok or read.value != size:
            raise OSError(ctypes.get_last_error(), f"ReadProcessMemory failed at 0x{addr:X}")
        return bytes(buf)

    def _read_u64(self, addr: int) -> int:
        return struct.unpack("<Q", self._read_bytes(addr, 8))[0]

    def get_gplaystate_pointer_address(self) -> int:
        fallback = self._module_base("soh.exe") + self._GPLAYSTATE_PTR_RVA
        return self.dynamic_resolver.resolve_gplaystate_pointer_address(fallback)

    def get_gplaystate_address(self) -> int:
        return self._read_u64(self.get_gplaystate_pointer_address())

    def get_playstate_transition_trigger_address(self) -> int:
        gplay = self.get_gplaystate_address()
        if gplay == 0:
            raise RuntimeError("gPlayState is null")
        return gplay + self._PLAYSTATE_TRANSITION_TRIGGER_OFFSET

    def get_playstate_next_entrance_address(self) -> int:
        gplay = self.get_gplaystate_address()
        if gplay == 0:
            raise RuntimeError("gPlayState is null")
        return gplay + self._PLAYSTATE_NEXT_ENTRANCE_OFFSET

    def get_playstate_transition_type_address(self) -> int:
        gplay = self.get_gplaystate_address()
        if gplay == 0:
            raise RuntimeError("gPlayState is null")
        return gplay + self._PLAYSTATE_TRANSITION_TYPE_OFFSET


    # ------------------------------------------------------------------
    # ITEMS (runtime block from profile)
    # ------------------------------------------------------------------
    def get_item_slot(self, slot: int) -> int:
        return self.memory.read_u8(self._items_addr(slot))

    def set_item_slot(self, slot: int, value: int) -> None:
        self.memory.write_u8(self._items_addr(slot), value & 0xFF)

    # ------------------------------------------------------------------
    # AMMO (runtime block from profile)
    # ------------------------------------------------------------------
    def get_ammo(self, slot: int) -> int:
        return self.memory.read_u8(self._ammo_addr(slot))

    def set_ammo(self, slot: int, value: int) -> None:
        self.memory.write_u8(self._ammo_addr(slot), value & 0xFF)

    # ------------------------------------------------------------------
    # LEGACY SAVE-CONTEXT FIELDS
    # Kept for compatibility/debug because the UI still exposes them.
    # These are not the validated runtime fields used by the equipment tab.
    # ------------------------------------------------------------------
    def get_equipment(self) -> int:
        return self.memory.read_u16(self._save_addr("equipment_offset"))

    def set_equipment(self, value: int) -> None:
        self.memory.write_u16(self._save_addr("equipment_offset"), value & 0xFFFF)

    # ------------------------------------------------------------------
    # VALIDATED RUNTIME FIELDS
    # ------------------------------------------------------------------
    def get_equipped_equipment(self) -> int:
        return self.memory.read_u16(self.get_equipped_equipment_address())

    def set_equipped_equipment(self, value: int) -> None:
        self.memory.write_u16(self.get_equipped_equipment_address(), value & 0xFFFF)

    def get_equips_equipment(self) -> int:
        return self.get_equipped_equipment()

    def set_equips_equipment(self, value: int) -> None:
        self.set_equipped_equipment(value)

    def get_owned_equipment(self) -> int:
        return self.memory.read_u16(self.get_owned_equipment_address())

    def set_owned_equipment(self, value: int) -> None:
        self.memory.write_u16(self.get_owned_equipment_address(), value & 0xFFFF)

    def get_inventory_equipment(self) -> int:
        return self.get_owned_equipment()

    def set_inventory_equipment(self, value: int) -> None:
        self.set_owned_equipment(value)

    def get_upgrades(self) -> int:
        return self.memory.read_u32(self.get_upgrades_address())

    def set_upgrades(self, value: int) -> None:
        self.memory.write_u32(self.get_upgrades_address(), value & 0xFFFFFFFF)

    def get_quest_items(self) -> int:
        return self.memory.read_u32(self.get_quest_items_address())

    def set_quest_items(self, value: int) -> None:
        self.memory.write_u32(self.get_quest_items_address(), value & 0xFFFFFFFF)

    # ------------------------------------------------------------------
    # MAGIC (save context)
    # ------------------------------------------------------------------
    def get_magic_level(self) -> int:
        return self.memory.read_u8(self.get_magic_level_address())

    def set_magic_level(self, value: int) -> None:
        self.memory.write_u8(self.get_magic_level_address(), value & 0xFF)

    def get_magic_current(self) -> int:
        return self.memory.read_u8(self.get_magic_current_address())

    def set_magic_current(self, value: int) -> None:
        self.memory.write_u8(self.get_magic_current_address(), value & 0xFF)

    def get_magic_acquired(self) -> bool:
        return bool(self.memory.read_u8(self.get_magic_acquired_address()))

    def set_magic_acquired(self, value: bool) -> None:
        self.memory.write_u8(self.get_magic_acquired_address(), 1 if value else 0)

    def get_double_magic_acquired(self) -> bool:
        return bool(self.memory.read_u8(self.get_double_magic_acquired_address()))

    def set_double_magic_acquired(self, value: bool) -> None:
        self.memory.write_u8(self.get_double_magic_acquired_address(), 1 if value else 0)

    def get_magic_state_value(self) -> int:
        return self.memory.read_u16(self.get_magic_state_address())

    def set_magic_state_value(self, value: int) -> None:
        self.memory.write_u16(self.get_magic_state_address(), value & 0xFFFF)

    def get_prev_magic_state_value(self) -> int:
        return self.memory.read_u16(self.get_prev_magic_state_address())

    def set_prev_magic_state_value(self, value: int) -> None:
        self.memory.write_u16(self.get_prev_magic_state_address(), value & 0xFFFF)

    def get_magic_capacity_value(self) -> int:
        return self.memory.read_u16(self.get_magic_capacity_address())

    def set_magic_capacity_value(self, value: int) -> None:
        self.memory.write_u16(self.get_magic_capacity_address(), value & 0xFFFF)

    def get_magic_fill_target_value(self) -> int:
        return self.memory.read_u16(self.get_magic_fill_target_address())

    def set_magic_fill_target_value(self, value: int) -> None:
        self.memory.write_u16(self.get_magic_fill_target_address(), value & 0xFFFF)

    def get_magic_target_value(self) -> int:
        return self.memory.read_u16(self.get_magic_target_address())

    def set_magic_target_value(self, value: int) -> None:
        self.memory.write_u16(self.get_magic_target_address(), value & 0xFFFF)

    def get_save_entrance_index(self) -> int:
        return self.memory.read_u16(self.get_save_entrance_index_address())

    def set_save_entrance_index(self, value: int) -> None:
        self.memory.write_u16(self.get_save_entrance_index_address(), value & 0xFFFF)

    def get_respawn_flag(self) -> int:
        return self.memory.read_u32(self.get_respawn_flag_address())

    def set_respawn_flag(self, value: int) -> None:
        self.memory.write_u32(self.get_respawn_flag_address(), value & 0xFFFFFFFF)

    def get_next_transition_type(self) -> int:
        return self.memory.read_u8(self.get_next_transition_type_address())

    def set_next_transition_type(self, value: int) -> None:
        self.memory.write_u8(self.get_next_transition_type_address(), value & 0xFF)

    def _respawn_addr(self, offset: int) -> int:
        return self.get_respawn_down_address() + offset

    def set_respawn_down_entrance_index(self, value: int) -> None:
        self.memory.write_u16(self._respawn_addr(self._RESPAWN_ENTRANCE_INDEX_OFFSET), value & 0xFFFF)

    def get_respawn_down_entrance_index(self) -> int:
        return self.memory.read_u16(self._respawn_addr(self._RESPAWN_ENTRANCE_INDEX_OFFSET))

    def set_respawn_down_room_index(self, value: int) -> None:
        self.memory.write_u8(self._respawn_addr(self._RESPAWN_ROOM_INDEX_OFFSET), value & 0xFF)

    def get_respawn_down_room_index(self) -> int:
        return self.memory.read_u8(self._respawn_addr(self._RESPAWN_ROOM_INDEX_OFFSET))

    def set_respawn_down_player_params(self, value: int) -> None:
        self.memory.write_u16(self._respawn_addr(self._RESPAWN_PLAYER_PARAMS_OFFSET), value & 0xFFFF)

    def get_respawn_down_player_params(self) -> int:
        return self.memory.read_u16(self._respawn_addr(self._RESPAWN_PLAYER_PARAMS_OFFSET))

    def set_respawn_down_temp_flags(self, swch_flags: int = 0, collect_flags: int = 0) -> None:
        self.memory.write_u32(self._respawn_addr(self._RESPAWN_TEMP_SWCH_FLAGS_OFFSET), swch_flags & 0xFFFFFFFF)
        self.memory.write_u32(self._respawn_addr(self._RESPAWN_TEMP_COLLECT_FLAGS_OFFSET), collect_flags & 0xFFFFFFFF)

    def queue_warp_song_teleport(self, entrance_id: int, room_index: int, player_params: int = 0x0DFF) -> None:
        self.set_save_entrance_index(entrance_id)
        self.set_respawn_down_entrance_index(entrance_id)
        self.set_respawn_down_room_index(room_index)
        self.set_respawn_down_player_params(player_params)
        self.set_respawn_down_temp_flags(0, 0)
        self.set_next_transition_type(0x02)
        self.set_respawn_flag(1)

    def get_warp_queue_state(self) -> dict[str, int]:
        return {
            "entrance_index": self.get_save_entrance_index(),
            "respawn_flag": self.get_respawn_flag(),
            "respawn_entrance_index": self.get_respawn_down_entrance_index(),
            "respawn_room_index": self.get_respawn_down_room_index(),
            "respawn_player_params": self.get_respawn_down_player_params(),
            "next_transition_type": self.get_next_transition_type(),
        }

    def get_runtime_warp_state(self) -> dict[str, int]:
        """Return the live PlayState warp fields used by runtime teleport."""
        return {
            "gplaystate": self.get_gplaystate_address(),
            "next_entrance": self.memory.read_u16(self.get_playstate_next_entrance_address()),
            "transition_trigger": self.memory.read_u8(self.get_playstate_transition_trigger_address()),
            "transition_type": self.memory.read_u8(self.get_playstate_transition_type_address()),
        }

    def teleport_runtime(self, entrance_id: int, transition_type: int | None = None) -> None:
        """Write the validated PlayState warp fields and trigger the transition.

        The method clears the previous trigger first so the game consumes a
        fresh transition request on the next frame.
        """
        next_entrance_addr = self.get_playstate_next_entrance_address()
        trigger_addr = self.get_playstate_transition_trigger_address()
        transition_type_addr = self.get_playstate_transition_type_address()

        actual_transition_type = self._TRANS_TYPE_INSTANT if transition_type is None else transition_type

        self.memory.write_u8(trigger_addr, 0)
        self.memory.write_u8(transition_type_addr, 0)
        self.memory.write_u16(next_entrance_addr, entrance_id & 0xFFFF)
        self.memory.write_u8(transition_type_addr, actual_transition_type & 0xFF)
        self.memory.write_u8(trigger_addr, self._TRANS_TRIGGER_START)



    def get_link_state(self) -> dict[str, int | list[int] | str]:
        player_address = self.get_link_state_player_address()
        flames = [
            self.memory.read_u8(self._player_addr(self._LINK_BURN_FLAMES_OFFSET + index))
            for index in range(self._LINK_BURN_FLAMES_COUNT)
        ]
        return {
            "player_address": player_address,
            "player_source": "manual" if self._manual_player_address else "profile",
            "freeze_timer": self.memory.read_i16(self._player_addr(self._LINK_FREEZE_TIMER_OFFSET)),
            "shock_timer": self.memory.read_u8(self._player_addr(self._LINK_SHOCK_TIMER_OFFSET)),
            "burn_flag": self.memory.read_u8(self._player_addr(self._LINK_BURN_FLAG_OFFSET)),
            "burn_flames": flames,
        }

    def set_link_freeze(self, duration: int) -> int:
        clamped = max(-32768, min(32767, int(duration)))
        self.memory.write_i16(self._player_addr(self._LINK_FREEZE_TIMER_OFFSET), clamped)
        return clamped

    def set_link_shock(self, duration: int) -> int:
        clamped = max(0, min(255, int(duration)))
        self.memory.write_u8(self._player_addr(self._LINK_SHOCK_TIMER_OFFSET), clamped)
        return clamped

    def set_link_burn(self, flame_value: int) -> int:
        clamped = max(0, min(255, int(flame_value)))
        self.memory.write_u8(self._player_addr(self._LINK_BURN_FLAG_OFFSET), 1)
        for index in range(self._LINK_BURN_FLAMES_COUNT):
            self.memory.write_u8(self._player_addr(self._LINK_BURN_FLAMES_OFFSET + index), clamped)
        return clamped

    def clear_link_burn(self) -> None:
        self.memory.write_u8(self._player_addr(self._LINK_BURN_FLAG_OFFSET), 0)
        for index in range(self._LINK_BURN_FLAMES_COUNT):
            self.memory.write_u8(self._player_addr(self._LINK_BURN_FLAMES_OFFSET + index), 0)

    def get_effective_magic_capacity(self) -> int:
        if not self.get_magic_acquired():
            return 0
        return 96 if self.get_double_magic_acquired() else 48

    def apply_magic_reinit(self, double_magic: bool) -> None:
        self.set_magic_acquired(True)
        self.set_double_magic_acquired(double_magic)
        self.set_magic_level(0)
        self.set_magic_current(0)
        self.set_magic_capacity_value(0)
        self.set_magic_fill_target_value(0)
        self.set_magic_target_value(0)
        self.set_magic_state_value(self._MAGIC_STATE_IDLE)
        self.set_prev_magic_state_value(0)

    def disable_magic(self) -> None:
        self.set_magic_acquired(False)
        self.set_double_magic_acquired(False)
        self.set_magic_level(0)
        self.set_magic_current(0)
        self.set_magic_capacity_value(0)
        self.set_magic_fill_target_value(0)
        self.set_magic_target_value(0)
        self.set_magic_state_value(self._MAGIC_STATE_IDLE)
        self.set_prev_magic_state_value(0)

    def set_magic_current_direct(self, value: int) -> int:
        capacity = self.get_effective_magic_capacity()
        clamped = max(0, min(value, capacity))
        self.set_magic_current(clamped)
        self.set_magic_level(0 if capacity == 0 else (2 if capacity == 96 else 1))
        self.set_magic_fill_target_value(clamped)
        self.set_magic_target_value(clamped)
        self.set_magic_state_value(self._MAGIC_STATE_IDLE)
        self.set_prev_magic_state_value(0)
        return clamped

    # ------------------------------------------------------------------
    # MASK HELPERS
    # ------------------------------------------------------------------
    def read_owned_equipment_mask(self) -> int:
        return self.get_owned_equipment()

    def write_owned_equipment_mask(self, value: int) -> None:
        self.set_owned_equipment(value & 0xFFFF)

    def read_equipped_equipment_mask(self) -> int:
        return self.get_equipped_equipment()

    def write_equipped_equipment_mask(self, value: int) -> None:
        self.set_equipped_equipment(value & 0xFFFF)

    def read_upgrades_mask(self) -> int:
        return self.get_upgrades()

    def write_upgrades_mask(self, value: int) -> None:
        self.set_upgrades(value & 0xFFFFFFFF)

    def read_quest_items_mask(self) -> int:
        return self.get_quest_items()

    def write_quest_items_mask(self, value: int) -> None:
        self.set_quest_items(value & 0xFFFFFFFF)

    # Compat with current controller naming
    def read_quest_flags(self) -> int:
        return self.read_quest_items_mask()

    def write_quest_flags(self, value: int) -> None:
        self.write_quest_items_mask(value)

    # ------------------------------------------------------------------
    # DEBUG HELPERS
    # ------------------------------------------------------------------
    def read_runtime_equipment_mask(self) -> int:
        return self.memory.read_u16(self.get_equipped_equipment_address())

    def write_runtime_equipment_mask(self, value: int) -> None:
        self.memory.write_u16(self.get_equipped_equipment_address(), value & 0xFFFF)


    def get_item_equips_address(self) -> int:
        return self._save_base() + self._ITEM_EQUIPS_OFFSET

    def get_button_address(self, button_key: str) -> int:
        try:
            return self._save_base() + self._BUTTON_OFFSETS[button_key]
        except KeyError as exc:
            raise RuntimeError(f"Unknown button key: {button_key}") from exc

    def get_button_items_map(self) -> dict[str, int]:
        return dict(self._BUTTON_ITEMS)

    def get_button_item(self, button_key: str) -> int:
        return self.memory.read_u8(self.get_button_address(button_key))

    def set_button_item_raw(self, button_key: str, value: int) -> None:
        self.memory.write_u8(self.get_button_address(button_key), value & 0xFF)

    def set_button_item(self, button_key: str, item_key: str) -> None:
        try:
            value = self._BUTTON_ITEMS[item_key]
        except KeyError as exc:
            raise RuntimeError(f"Unknown button item: {item_key}") from exc
        self.set_button_item_raw(button_key, value)

    def clear_button_item(self, button_key: str) -> None:
        self.set_button_item(button_key, "none")

    def get_live_item_equips_equipment(self) -> int:
        return self.memory.read_u16(self.get_item_equips_address())

    def set_live_item_equips_equipment(self, value: int) -> None:
        self.memory.write_u16(self.get_item_equips_address(), value & 0xFFFF)

    def get_live_sword_nibble(self) -> int:
        return self.get_live_item_equips_equipment() & 0xF

    def set_live_sword_nibble(self, sword_value: int) -> None:
        equips = self.get_live_item_equips_equipment()
        equips = (equips & 0xFFF0) | (sword_value & 0xF)
        self.set_live_item_equips_equipment(equips)

    def apply_swordless(self) -> None:
        self.set_live_sword_nibble(self._SWORD_NIBBLES["none"])
        self.memory.write_u8(self.get_button_address("b"), 0xFE)

    def equip_live_sword(self, sword_key: str) -> None:
        if sword_key == "none":
            self.apply_swordless()
            return
        try:
            sword_value = self._SWORD_NIBBLES[sword_key]
            button_value = self._SWORD_B_ITEMS[sword_key]
        except KeyError as exc:
            raise RuntimeError(f"Unknown sword mode: {sword_key}") from exc
        self.set_live_sword_nibble(sword_value)
        self.set_button_item_raw("b", button_value)

    def get_button_assignments(self) -> dict[str, int]:
        return {key: self.get_button_item(key) for key in self._BUTTON_OFFSETS}
