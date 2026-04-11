from __future__ import annotations

from typing import Dict, Iterable


# Warp song destinations are exposed as a dedicated subset because the UI and
# future Twitch actions may want to target only song warps.
WARP_SONG_DESTINATIONS: dict[str, dict[str, object]] = {
    "minuet_of_forest": {
        "key": "minuet_of_forest",
        "label": "Minuet of Forest",
        "entrance_name": "ENTR_SACRED_FOREST_MEADOW_WARP_PAD",
        "entrance_id": 0x0600,
        "room_index": 2,
        "player_params": 0x0DFF,
        "safe_random": True,
        "category": "warp_song",
    },
    "bolero_of_fire": {
        "key": "bolero_of_fire",
        "label": "Bolero of Fire",
        "entrance_name": "ENTR_DEATH_MOUNTAIN_CRATER_WARP_PAD",
        "entrance_id": 0x04F6,
        "room_index": 4,
        "player_params": 0x0DFF,
        "safe_random": False,
        "category": "warp_song",
    },
    "serenade_of_water": {
        "key": "serenade_of_water",
        "label": "Serenade of Water",
        "entrance_name": "ENTR_LAKE_HYLIA_WARP_PAD",
        "entrance_id": 0x0604,
        "room_index": 8,
        "player_params": 0x0DFF,
        "safe_random": True,
        "category": "warp_song",
    },
    "requiem_of_spirit": {
        "key": "requiem_of_spirit",
        "label": "Requiem of Spirit",
        "entrance_name": "ENTR_DESERT_COLOSSUS_WARP_PAD",
        "entrance_id": 0x01F1,
        "room_index": 5,
        "player_params": 0x0DFF,
        "safe_random": True,
        "category": "warp_song",
    },
    "nocturne_of_shadow": {
        "key": "nocturne_of_shadow",
        "label": "Nocturne of Shadow",
        "entrance_name": "ENTR_GRAVEYARD_WARP_PAD",
        "entrance_id": 0x0568,
        "room_index": 7,
        "player_params": 0x0DFF,
        "safe_random": True,
        "category": "warp_song",
    },
    "prelude_of_light": {
        "key": "prelude_of_light",
        "label": "Prelude of Light",
        "entrance_name": "ENTR_TEMPLE_OF_TIME_WARP_PAD",
        "entrance_id": 0x05F4,
        "room_index": 7,
        "player_params": 0x0DFF,
        "safe_random": True,
        "category": "warp_song",
    },
}


# Conservative pool for random teleports. Everything listed here is either
# already validated in-game or intentionally limited to non-boss, non-cutscene
# interiors and overworld locations.
SAFE_RANDOM_DESTINATIONS: dict[str, dict[str, object]] = {
    "links_house_bed": {
        "key": "links_house_bed",
        "label": "Link House - Bed",
        "entrance_name": "ENTR_LINKS_HOUSE_CHILD_SPAWN",
        "entrance_id": 0x00BB,
        "scene": "SCENE_LINKS_HOUSE",
        "category": "safe_interior",
        "validated": True,
    },
    "links_house_door": {
        "key": "links_house_door",
        "label": "Link House - Door",
        "entrance_name": "ENTR_LINKS_HOUSE_1",
        "entrance_id": 0x0272,
        "scene": "SCENE_LINKS_HOUSE",
        "category": "safe_interior",
        "validated": True,
    },
    "hyrule_field_drawbridge_front": {
        "key": "hyrule_field_drawbridge_front",
        "label": "Hyrule Field - Drawbridge Front",
        "entrance_name": "ENTR_HYRULE_FIELD_PAST_BRIDGE_SPAWN",
        "entrance_id": 0x00CD,
        "scene": "SCENE_HYRULE_FIELD",
        "category": "overworld",
        "validated": True,
    },
    "hyrule_field_drawbridge_bridge": {
        "key": "hyrule_field_drawbridge_bridge",
        "label": "Hyrule Field - On Bridge",
        "entrance_name": "ENTR_HYRULE_FIELD_ON_BRIDGE_SPAWN",
        "entrance_id": 0x01FD,
        "scene": "SCENE_HYRULE_FIELD",
        "category": "overworld",
        "validated": True,
    },
    "kokiri_forest_main": {
        "key": "kokiri_forest_main",
        "label": "Kokiri Forest - Main",
        "entrance_name": "ENTR_KOKIRI_FOREST_0",
        "entrance_id": 0x00EE,
        "scene": "SCENE_KOKIRI_FOREST",
        "category": "overworld",
        "validated": False,
    },
    "kokiri_forest_deku_tree": {
        "key": "kokiri_forest_deku_tree",
        "label": "Kokiri Forest - Outside Deku Tree",
        "entrance_name": "ENTR_KOKIRI_FOREST_OUTSIDE_DEKU_TREE",
        "entrance_id": 0x0209,
        "scene": "SCENE_KOKIRI_FOREST",
        "category": "overworld",
        "validated": False,
    },
    "kokiri_forest_links_house": {
        "key": "kokiri_forest_links_house",
        "label": "Kokiri Forest - Outside Link House",
        "entrance_name": "ENTR_KOKIRI_FOREST_OUTSIDE_LINKS_HOUSE",
        "entrance_id": 0x0211,
        "scene": "SCENE_KOKIRI_FOREST",
        "category": "overworld",
        "validated": False,
    },
    "kokiri_forest_upper_exit": {
        "key": "kokiri_forest_upper_exit",
        "label": "Kokiri Forest - Upper Exit",
        "entrance_name": "ENTR_KOKIRI_FOREST_UPPER_EXIT",
        "entrance_id": 0x0286,
        "scene": "SCENE_KOKIRI_FOREST",
        "category": "overworld",
        "validated": False,
    },
    "sacred_forest_meadow_south_exit": {
        "key": "sacred_forest_meadow_south_exit",
        "label": "Sacred Forest Meadow - South Exit",
        "entrance_name": "ENTR_SACRED_FOREST_MEADOW_SOUTH_EXIT",
        "entrance_id": 0x00FC,
        "scene": "SCENE_SACRED_FOREST_MEADOW",
        "category": "overworld",
        "validated": False,
    },
    "sacred_forest_meadow_temple": {
        "key": "sacred_forest_meadow_temple",
        "label": "Sacred Forest Meadow - Outside Temple",
        "entrance_name": "ENTR_SACRED_FOREST_MEADOW_OUTSIDE_TEMPLE",
        "entrance_id": 0x0215,
        "scene": "SCENE_SACRED_FOREST_MEADOW",
        "category": "overworld",
        "validated": False,
    },
    "lake_hylia_north_exit": {
        "key": "lake_hylia_north_exit",
        "label": "Lake Hylia - North Exit",
        "entrance_name": "ENTR_LAKE_HYLIA_NORTH_EXIT",
        "entrance_id": 0x0102,
        "scene": "SCENE_LAKE_HYLIA",
        "category": "overworld",
        "validated": False,
    },
    "lake_hylia_river_exit": {
        "key": "lake_hylia_river_exit",
        "label": "Lake Hylia - River Exit",
        "entrance_name": "ENTR_LAKE_HYLIA_RIVER_EXIT",
        "entrance_id": 0x0219,
        "scene": "SCENE_LAKE_HYLIA",
        "category": "overworld",
        "validated": False,
    },
    "zoras_domain_main": {
        "key": "zoras_domain_main",
        "label": "Zora's Domain - Main",
        "entrance_name": "ENTR_ZORAS_DOMAIN_ENTRANCE",
        "entrance_id": 0x0108,
        "scene": "SCENE_ZORAS_DOMAIN",
        "category": "overworld",
        "validated": False,
    },
    "zoras_domain_king_zora": {
        "key": "zoras_domain_king_zora",
        "label": "Zora's Domain - King Zora",
        "entrance_name": "ENTR_ZORAS_DOMAIN_KING_ZORA_EXIT",
        "entrance_id": 0x01A1,
        "scene": "SCENE_ZORAS_DOMAIN",
        "category": "overworld",
        "validated": False,
    },
    "zoras_river_west_exit": {
        "key": "zoras_river_west_exit",
        "label": "Zora's River - West Exit",
        "entrance_name": "ENTR_ZORAS_RIVER_WEST_EXIT",
        "entrance_id": 0x00EA,
        "scene": "SCENE_ZORAS_RIVER",
        "category": "overworld",
        "validated": False,
    },
    "zoras_river_waterfall_exit": {
        "key": "zoras_river_waterfall_exit",
        "label": "Zora's River - Waterfall Exit",
        "entrance_name": "ENTR_ZORAS_RIVER_WATERFALL_EXIT",
        "entrance_id": 0x019D,
        "scene": "SCENE_ZORAS_RIVER",
        "category": "overworld",
        "validated": False,
    },
    "kakariko_front_gate": {
        "key": "kakariko_front_gate",
        "label": "Kakariko Village - Front Gate",
        "entrance_name": "ENTR_KAKARIKO_VILLAGE_FRONT_GATE",
        "entrance_id": 0x00DB,
        "scene": "SCENE_KAKARIKO_VILLAGE",
        "category": "overworld",
        "validated": False,
    },
    "kakariko_guard_gate": {
        "key": "kakariko_guard_gate",
        "label": "Kakariko Village - Guard Gate",
        "entrance_name": "ENTR_KAKARIKO_VILLAGE_GUARD_GATE",
        "entrance_id": 0x0191,
        "scene": "SCENE_KAKARIKO_VILLAGE",
        "category": "overworld",
        "validated": False,
    },
    "kakariko_southeast_exit": {
        "key": "kakariko_southeast_exit",
        "label": "Kakariko Village - Southeast Exit",
        "entrance_name": "ENTR_KAKARIKO_VILLAGE_SOUTHEAST_EXIT",
        "entrance_id": 0x0195,
        "scene": "SCENE_KAKARIKO_VILLAGE",
        "category": "overworld",
        "validated": False,
    },
    "graveyard_main": {
        "key": "graveyard_main",
        "label": "Graveyard - Main",
        "entrance_name": "ENTR_GRAVEYARD_ENTRANCE",
        "entrance_id": 0x00E4,
        "scene": "SCENE_GRAVEYARD",
        "category": "overworld",
        "validated": False,
    },
    "graveyard_temple_side": {
        "key": "graveyard_temple_side",
        "label": "Graveyard - Outside Temple",
        "entrance_name": "ENTR_GRAVEYARD_OUTSIDE_TEMPLE",
        "entrance_id": 0x0205,
        "scene": "SCENE_GRAVEYARD",
        "category": "overworld",
        "validated": False,
    },
    "lon_lon_ranch_main": {
        "key": "lon_lon_ranch_main",
        "label": "Lon Lon Ranch - Main",
        "entrance_name": "ENTR_LON_LON_RANCH_ENTRANCE",
        "entrance_id": 0x0157,
        "scene": "SCENE_LON_LON_RANCH",
        "category": "overworld",
        "validated": False,
    },
    "lon_lon_ranch_talon_house": {
        "key": "lon_lon_ranch_talon_house",
        "label": "Lon Lon Ranch - Outside Talon's House",
        "entrance_name": "ENTR_LON_LON_RANCH_OUTSIDE_TALONS_HOUSE",
        "entrance_id": 0x0378,
        "scene": "SCENE_LON_LON_RANCH",
        "category": "overworld",
        "validated": False,
    },
    "goron_city_upper_exit": {
        "key": "goron_city_upper_exit",
        "label": "Goron City - Upper Exit",
        "entrance_name": "ENTR_GORON_CITY_UPPER_EXIT",
        "entrance_id": 0x014D,
        "scene": "SCENE_GORON_CITY",
        "category": "overworld",
        "validated": False,
    },
    "goron_city_darunia": {
        "key": "goron_city_darunia",
        "label": "Goron City - Darunia Room Exit",
        "entrance_name": "ENTR_GORON_CITY_DARUNIA_ROOM_EXIT",
        "entrance_id": 0x01C1,
        "scene": "SCENE_GORON_CITY",
        "category": "overworld",
        "validated": False,
    },
    "gerudo_valley_east_exit": {
        "key": "gerudo_valley_east_exit",
        "label": "Gerudo Valley - East Exit",
        "entrance_name": "ENTR_GERUDO_VALLEY_EAST_EXIT",
        "entrance_id": 0x0117,
        "scene": "SCENE_GERUDO_VALLEY",
        "category": "overworld",
        "validated": False,
    },
    "gerudo_valley_west_exit": {
        "key": "gerudo_valley_west_exit",
        "label": "Gerudo Valley - West Exit",
        "entrance_name": "ENTR_GERUDO_VALLEY_WEST_EXIT",
        "entrance_id": 0x022D,
        "scene": "SCENE_GERUDO_VALLEY",
        "category": "overworld",
        "validated": False,
    },
    "desert_colossus_east_exit": {
        "key": "desert_colossus_east_exit",
        "label": "Desert Colossus - East Exit",
        "entrance_name": "ENTR_DESERT_COLOSSUS_EAST_EXIT",
        "entrance_id": 0x0123,
        "scene": "SCENE_DESERT_COLOSSUS",
        "category": "overworld",
        "validated": False,
    },
    "desert_colossus_temple": {
        "key": "desert_colossus_temple",
        "label": "Desert Colossus - Outside Temple",
        "entrance_name": "ENTR_DESERT_COLOSSUS_OUTSIDE_TEMPLE",
        "entrance_id": 0x01E1,
        "scene": "SCENE_DESERT_COLOSSUS",
        "category": "overworld",
        "validated": False,
    },
    "death_mountain_trail_bottom": {
        "key": "death_mountain_trail_bottom",
        "label": "Death Mountain Trail - Bottom Exit",
        "entrance_name": "ENTR_DEATH_MOUNTAIN_TRAIL_BOTTOM_EXIT",
        "entrance_id": 0x013D,
        "scene": "SCENE_DEATH_MOUNTAIN_TRAIL",
        "category": "overworld",
        "validated": False,
    },
    "death_mountain_trail_gc_exit": {
        "key": "death_mountain_trail_gc_exit",
        "label": "Death Mountain Trail - Goron City Exit",
        "entrance_name": "ENTR_DEATH_MOUNTAIN_TRAIL_GC_EXIT",
        "entrance_id": 0x01B9,
        "scene": "SCENE_DEATH_MOUNTAIN_TRAIL",
        "category": "overworld",
        "validated": False,
    },
    "death_mountain_trail_summit": {
        "key": "death_mountain_trail_summit",
        "label": "Death Mountain Trail - Summit Exit",
        "entrance_name": "ENTR_DEATH_MOUNTAIN_TRAIL_SUMMIT_EXIT",
        "entrance_id": 0x01BD,
        "scene": "SCENE_DEATH_MOUNTAIN_TRAIL",
        "category": "overworld",
        "validated": False,
    },
    "temple_of_time_exterior_day": {
        "key": "temple_of_time_exterior_day",
        "label": "Temple of Time Exterior - Day",
        "entrance_name": "ENTR_TEMPLE_OF_TIME_EXTERIOR_DAY_GOSSIP_STONE_EXIT",
        "entrance_id": 0x0171,
        "scene": "SCENE_TEMPLE_OF_TIME_EXTERIOR_DAY",
        "category": "overworld",
        "validated": False,
    },
    "kokiri_shop": {
        "key": "kokiri_shop",
        "label": "Kokiri Shop",
        "entrance_name": "ENTR_KOKIRI_SHOP_0",
        "entrance_id": 0x00C1,
        "scene": "SCENE_KOKIRI_SHOP",
        "category": "safe_interior",
        "validated": False,
    },
    "know_it_all_bros_house": {
        "key": "know_it_all_bros_house",
        "label": "Know It All Bros House",
        "entrance_name": "ENTR_KNOW_IT_ALL_BROS_HOUSE_0",
        "entrance_id": 0x00C9,
        "scene": "SCENE_KNOW_IT_ALL_BROS_HOUSE",
        "category": "safe_interior",
        "validated": False,
    },
    "twins_house": {
        "key": "twins_house",
        "label": "Twins House",
        "entrance_name": "ENTR_TWINS_HOUSE_0",
        "entrance_id": 0x009C,
        "scene": "SCENE_TWINS_HOUSE",
        "category": "safe_interior",
        "validated": False,
    },
    "bazaar": {
        "key": "bazaar",
        "label": "Bazaar",
        "entrance_name": "ENTR_BAZAAR_0",
        "entrance_id": 0x00B7,
        "scene": "SCENE_BAZAAR",
        "category": "safe_interior",
        "validated": False,
    },
    "lon_lon_talons_house": {
        "key": "lon_lon_talons_house",
        "label": "Lon Lon - Talon's House",
        "entrance_name": "ENTR_LON_LON_BUILDINGS_TALONS_HOUSE",
        "entrance_id": 0x004F,
        "scene": "SCENE_LON_LON_BUILDINGS",
        "category": "safe_interior",
        "validated": False,
    },
    "kakariko_guest_house": {
        "key": "kakariko_guest_house",
        "label": "Kakariko Guest House",
        "entrance_name": "ENTR_KAKARIKO_CENTER_GUEST_HOUSE_0",
        "entrance_id": 0x02FD,
        "scene": "SCENE_KAKARIKO_CENTER_GUEST_HOUSE",
        "category": "safe_interior",
        "validated": False,
    },
    "stable": {
        "key": "stable",
        "label": "Stable",
        "entrance_name": "ENTR_STABLE_0",
        "entrance_id": 0x02F9,
        "scene": "SCENE_STABLE",
        "category": "safe_interior",
        "validated": False,
    },
    "gravekeepers_hut": {
        "key": "gravekeepers_hut",
        "label": "Gravekeeper's Hut",
        "entrance_name": "ENTR_GRAVEKEEPERS_HUT_0",
        "entrance_id": 0x030D,
        "scene": "SCENE_GRAVEKEEPERS_HUT",
        "category": "safe_interior",
        "validated": False,
    },
    "goron_shop": {
        "key": "goron_shop",
        "label": "Goron Shop",
        "entrance_name": "ENTR_GORON_SHOP_0",
        "entrance_id": 0x037C,
        "scene": "SCENE_GORON_SHOP",
        "category": "safe_interior",
        "validated": False,
    },
    "zora_shop": {
        "key": "zora_shop",
        "label": "Zora Shop",
        "entrance_name": "ENTR_ZORA_SHOP_0",
        "entrance_id": 0x0380,
        "scene": "SCENE_ZORA_SHOP",
        "category": "safe_interior",
        "validated": False,
    },
    "potion_shop_kakariko_front": {
        "key": "potion_shop_kakariko_front",
        "label": "Potion Shop Kakariko",
        "entrance_name": "ENTR_POTION_SHOP_KAKARIKO_FRONT",
        "entrance_id": 0x0384,
        "scene": "SCENE_POTION_SHOP_KAKARIKO",
        "category": "safe_interior",
        "validated": False,
    },
    "potion_shop_market": {
        "key": "potion_shop_market",
        "label": "Potion Shop Market",
        "entrance_name": "ENTR_POTION_SHOP_MARKET_0",
        "entrance_id": 0x0388,
        "scene": "SCENE_POTION_SHOP_MARKET",
        "category": "safe_interior",
        "validated": False,
    },
}

EXCLUDED_TELEPORT_NAME_PATTERNS: tuple[str, ...] = (
    "BOSS",
    "CUTSCENE",
    "TEST",
    "UNUSED",
    "COLLAPSE",
    "OWL_DROP",
    "BLUE_WARP",
)

EXCLUDED_TELEPORT_SCENES: tuple[str, ...] = (
    "SCENE_CUTSCENE_MAP",
    "SCENE_GANONS_TOWER_COLLAPSE_INTERIOR",
    "SCENE_GANONS_TOWER_COLLAPSE_EXTERIOR",
    "SCENE_UNUSED_6E",
    "SCENE_DEPTH_TEST",
    "SCENE_TESTROOM",
    "SCENE_TEST01",
    "SCENE_SASATEST",
    "SCENE_SYOTES",
    "SCENE_SYOTES2",
)

DISABLED_RANDOM_KEYS: set[str] = {
    "bolero_of_fire",
}

TELEPORT_DESTINATIONS: dict[str, dict[str, object]] = {
    **WARP_SONG_DESTINATIONS,
    **SAFE_RANDOM_DESTINATIONS,
}


def is_name_excluded(name: str) -> bool:
    """Exclude destinations that are obviously tied to boss, test, or crash-prone flows."""
    upper_name = name.upper()
    return any(pattern in upper_name for pattern in EXCLUDED_TELEPORT_NAME_PATTERNS)


def is_scene_excluded(scene: str) -> bool:
    """Exclude scenes that are technical, cutscene-only, or known to be unstable."""
    return scene in EXCLUDED_TELEPORT_SCENES


def build_safe_random_pool(
    destinations: Dict[str, dict[str, object]] | None = None,
    disabled_keys: Iterable[str] | None = None,
) -> dict[str, dict[str, object]]:
    """Build the conservative pool used by the random teleport button."""
    source = TELEPORT_DESTINATIONS if destinations is None else destinations
    blocked = set(DISABLED_RANDOM_KEYS)
    if disabled_keys is not None:
        blocked.update(disabled_keys)

    result: dict[str, dict[str, object]] = {}

    for key, entry in source.items():
        if key in blocked:
            continue

        entrance_name = str(entry.get("entrance_name", ""))
        scene = str(entry.get("scene", ""))

        if is_name_excluded(entrance_name):
            continue

        if scene and is_scene_excluded(scene):
            continue

        if bool(entry.get("safe_random", False)):
            result[key] = entry
            continue

        category = str(entry.get("category", ""))
        if category in {"overworld", "safe_interior"}:
            result[key] = entry

    return result


SAFE_RANDOM_POOL: dict[str, dict[str, object]] = build_safe_random_pool()
SAFE_RANDOM_KEYS: tuple[str, ...] = tuple(SAFE_RANDOM_POOL.keys())
