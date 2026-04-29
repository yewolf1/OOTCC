from __future__ import annotations

from core.definitions.inventory_definitions import AMMO_SLOTS, EQUIPMENT_GROUPS, ITEM_SLOTS, QUEST_FLAGS, UPGRADE_GROUPS
from core.definitions.teleport_definitions import WARP_SONG_DESTINATIONS


def _slug(text: str) -> str:
    return (
        text.lower()
        .replace("'", "")
        .replace(".", "")
        .replace("-", "_")
        .replace(" ", "_")
    )


ITEM_TOGGLE_NAMES = {
    _slug(item_def["label"]): slot
    for slot, item_def in ITEM_SLOTS.items()
}
ITEM_TOGGLE_NAMES.update({
    "lens": 13,
    "beans": 14,
    "hammer": 15,
    "bottle1": 18,
    "bottle2": 19,
    "bottle3": 20,
    "bottle4": 21,
    "adult_trade": 22,
    "child_trade": 23,
})

AMMO_NAME_TO_SLOT = {
    "sticks": 0,
    "nuts": 1,
    "bombs": 2,
    "arrows": 3,
    "seeds": 6,
    "bombchu": 8,
}

EQUIPMENT_TOGGLE_NAMES = {
    "kokiri_tunic": ("tunics", "kokiri_tunic"),
    "goron_tunic": ("tunics", "goron_tunic"),
    "zora_tunic": ("tunics", "zora_tunic"),
    "kokiri_boots": ("boots", "kokiri_boots"),
    "iron_boots": ("boots", "iron_boots"),
    "hover_boots": ("boots", "hover_boots"),
    "deku_shield": ("shields", "deku_shield"),
    "hylian_shield": ("shields", "hylian_shield"),
    "mirror_shield": ("shields", "mirror_shield"),
}

UPGRADE_NAMES = {key: key for key in ("wallet", "bomb_bag", "quiver", "bullet_bag", "strength", "scale")}

TELEPORT_REWARD_NAMES = {
    "minuet": "minuet_of_forest",
    "bolero": "bolero_of_fire",
    "serenade": "serenade_of_water",
    "requiem": "requiem_of_spirit",
    "nocturne": "nocturne_of_shadow",
    "prelude": "prelude_of_light",
}

QUEST_STATUS_NAMES = {
    "forest": "forest_medallion",
    "fire": "fire_medallion",
    "water": "water_medallion",
    "spirit": "spirit_medallion",
    "shadow": "shadow_medallion",
    "light": "light_medallion",
    "minuet": "minuet_of_forest",
    "bolero": "bolero_of_fire",
    "serenade": "serenade_of_water",
    "requiem": "requiem_of_spirit",
    "nocturne": "nocturne_of_shadow",
    "prelude": "prelude_of_light",
    "lullaby": "zeldas_lullaby",
    "epona": "eponas_song",
    "saria": "sarias_song",
    "sun": "suns_song",
    "time": "song_of_time",
    "storms": "song_of_storms",
    "emerald": "kokiri_emerald",
    "ruby": "goron_ruby",
    "sapphire": "zora_sapphire",
    "agony": "stone_of_agony",
    "gerudo": "gerudo_card",
}

REWARD_UI_HELP = {
    "Kill Link": "No input required.",
    "1/4 heart": "No input required.",
    "Unequip all slots": "No input required.",
    "Rupees -50": "No input required.",
    "Magic Fill": "Allowed: full, half, empty",
    "Magic Capacity": "Allowed: normal, double, none",
    "Heart Fill": "Allowed: full, half, quarter, empty",
    "Heart Capacity": "Allowed: +1, -1",
    "Heart Remove Permanent": "No input required.",
    "Item Toggle": "Items: " + ", ".join(sorted(ITEM_TOGGLE_NAMES.keys())),
    "Ammo": "Ammo: sticks, nuts, bombs, arrows, seeds, bombchu | Format: <ammo> +10 or <ammo> -10",
    "Equipment": "Equipment: " + ", ".join(EQUIPMENT_TOGGLE_NAMES.keys()),
    "Upgrade": "Format: add <upgrade> or remove <upgrade> | Upgrades: " + ", ".join(UPGRADE_NAMES.keys()),
    "Clear Buttons": "No input required.",
    "Sword Mode": "Allowed: swordless, kokiri, ms, biggoron",
    "Teleport": "Allowed: " + ", ".join(list(TELEPORT_REWARD_NAMES.keys()) + ["random"]) + " | 10s global cooldown",
    "Link Status": "Allowed: burn, freeze, shock",
    "Link Special Status": "Allowed: invisible on, invisible off, reverse on, reverse off",
    "Special Spawn": "Allowed: bomb, bomb_rain, explosion, cucco, darklink",
    "Quest Status": "Format: add <name> or remove <name> | Names: " + ", ".join(QUEST_STATUS_NAMES.keys()),
}

DEFAULT_REWARD_CONFIG = {
    "Kill Link": {"action": "kill_link"},
    "1/4 heart": {"action": "quarter_heart"},
    "Unequip all slots": {"action": "unequip_all_slots"},
    "Rupees -50": {"action": "rupees_delta", "amount": -50},
    "Magic Fill": {"action": "magic_fill"},
    "Magic Capacity": {"action": "magic_capacity"},
    "Heart Fill": {"action": "heart_fill"},
    "Heart Capacity": {"action": "heart_capacity"},
    "Heart Remove Permanent": {"action": "heart_remove_permanent"},
    "Item Toggle": {"action": "item_toggle"},
    "Ammo": {"action": "ammo"},
    "Equipment": {"action": "equipment_toggle"},
    "Upgrade": {"action": "upgrade"},
    "Clear Buttons": {"action": "clear_buttons"},
    "Sword Mode": {"action": "sword_mode"},
    "Teleport": {"action": "teleport"},
    "Link Status": {"action": "link_status"},
    "Link Special Status": {"action": "link_special_status"},
    "Special Spawn": {"action": "special_spawn"},
    "Quest Status": {"action": "quest_status"},
}
