from __future__ import annotations
from core.definitions.teleport_definitions import (
    SAFE_RANDOM_KEYS,
    SAFE_RANDOM_POOL,
    TELEPORT_DESTINATIONS,
    WARP_SONG_DESTINATIONS,
)

RANDOM_TELEPORT_DESTINATIONS = SAFE_RANDOM_POOL
RANDOM_TELEPORT_KEYS = SAFE_RANDOM_KEYS
ALL_TELEPORT_DESTINATIONS = TELEPORT_DESTINATIONS

BOTTLE_CHOICES = {
    20: "Empty Bottle",
    21: "Red Potion",
    22: "Green Potion",
    23: "Blue Potion",
    24: "Fairy",
    25: "Fish",
    26: "Milk",
    27: "Ruto's Letter",
    28: "Blue Fire",
    29: "Bugs",
    30: "Big Poe",
    31: "Half Milk",
    32: "Poe",
}

CHILD_TRADE_CHOICES = {
    33: "Weird Egg",
    34: "Chicken",
    35: "Zelda's Letter",
    36: "Keaton Mask",
    37: "Skull Mask",
    38: "Spooky Mask",
    39: "Bunny Hood",
    40: "Goron Mask",
    41: "Zora Mask",
    42: "Gerudo Mask",
    43: "Mask of Truth",
    44: "Sold Out",
}

ADULT_TRADE_CHOICES = {
    45: "Pocket Egg",
    46: "Pocket Cucco",
    47: "Cojiro",
    48: "Odd Mushroom",
    49: "Odd Potion",
    50: "Poacher's Saw",
    51: "Broken Goron's Sword",
    52: "Prescription",
    53: "Eyeball Frog",
    54: "Eye Drops",
    55: "Claim Check",
    56: "Adult Trade 56",
}

ITEM_SLOTS = {
    0: {"label": "Deku Stick", "choices": {0: "Deku Stick"}, "clear_value": 0xFF},
    1: {"label": "Deku Nut", "choices": {1: "Deku Nut"}, "clear_value": 0xFF},
    2: {"label": "Bomb", "choices": {2: "Bomb"}, "clear_value": 0xFF},
    3: {"label": "Bow", "choices": {3: "Bow"}, "clear_value": 0xFF},
    4: {"label": "Fire Arrow", "choices": {4: "Fire Arrow"}, "clear_value": 0xFF},
    5: {"label": "Din's Fire", "choices": {5: "Din's Fire"}, "clear_value": 0xFF},
    6: {"label": "Slingshot", "choices": {6: "Slingshot"}, "clear_value": 0xFF},
    7: {"label": "Ocarina", "choices": {7: "Fairy Ocarina", 8: "Ocarina of Time"}, "clear_value": 0xFF},
    8: {"label": "Bombchu", "choices": {9: "Bombchu"}, "clear_value": 0xFF},
    9: {"label": "Hookshot", "choices": {10: "Hookshot", 11: "Longshot"}, "clear_value": 0xFF},
    10: {"label": "Ice Arrow", "choices": {12: "Ice Arrow"}, "clear_value": 0xFF},
    11: {"label": "Farore's Wind", "choices": {13: "Farore's Wind"}, "clear_value": 0xFF},
    12: {"label": "Boomerang", "choices": {14: "Boomerang"}, "clear_value": 0xFF},
    13: {"label": "Lens of Truth", "choices": {15: "Lens of Truth"}, "clear_value": 0xFF},
    14: {"label": "Magic Beans", "choices": {16: "Magic Beans"}, "clear_value": 0xFF},
    15: {"label": "Megaton Hammer", "choices": {17: "Megaton Hammer"}, "clear_value": 0xFF},
    16: {"label": "Light Arrow", "choices": {18: "Light Arrow"}, "clear_value": 0xFF},
    17: {"label": "Nayru's Love", "choices": {19: "Nayru's Love"}, "clear_value": 0xFF},
    18: {"label": "Bottle 1", "choices": dict(BOTTLE_CHOICES), "clear_value": 0xFF},
    19: {"label": "Bottle 2", "choices": dict(BOTTLE_CHOICES), "clear_value": 0xFF},
    20: {"label": "Bottle 3", "choices": dict(BOTTLE_CHOICES), "clear_value": 0xFF},
    21: {"label": "Bottle 4", "choices": dict(BOTTLE_CHOICES), "clear_value": 0xFF},
    22: {"label": "Adult Trade", "choices": dict(ADULT_TRADE_CHOICES), "clear_value": 0xFF},
    23: {"label": "Child Trade", "choices": dict(CHILD_TRADE_CHOICES), "clear_value": 0xFF},
}

AMMO_SLOTS = {
    0: "Deku Stick",
    1: "Deku Nut",
    2: "Bomb",
    3: "Arrow",
    6: "Seed",
    8: "Bombchu",
}

EQUIPMENT_GROUPS = {
    "swords": {
        "label": "Swords",
        "shift": 0,
        "clear_mask": 0xFFF0,
        "entries": {
            "kokiri_sword": {
                "label": "Kokiri Sword",
                "index": 0,
                "owned_bit": 0x0001,
                "equip_value": 1,
            },
            "master_sword": {
                "label": "Master Sword",
                "index": 1,
                "owned_bit": 0x0002,
                "equip_value": 2,
            },
            "biggoron_sword": {
                "label": "Biggoron Sword",
                "index": 2,
                "owned_bit": 0x0004,
                "equip_value": 3,
            },
        },
    },
    "shields": {
        "label": "Shields",
        "shift": 4,
        "clear_mask": 0xFF0F,
        "entries": {
            "deku_shield": {
                "label": "Deku Shield",
                "index": 0,
                "owned_bit": 0x0010,
                "equip_value": 1,
            },
            "hylian_shield": {
                "label": "Hylian Shield",
                "index": 1,
                "owned_bit": 0x0020,
                "equip_value": 2,
            },
            "mirror_shield": {
                "label": "Mirror Shield",
                "index": 2,
                "owned_bit": 0x0040,
                "equip_value": 3,
            },
        },
    },
    "tunics": {
        "label": "Tunics",
        "shift": 8,
        "clear_mask": 0xF0FF,
        "entries": {
            "kokiri_tunic": {
                "label": "Kokiri Tunic",
                "index": 0,
                "owned_bit": 0x0100,
                "equip_value": 1,
            },
            "goron_tunic": {
                "label": "Goron Tunic",
                "index": 1,
                "owned_bit": 0x0200,
                "equip_value": 2,
            },
            "zora_tunic": {
                "label": "Zora Tunic",
                "index": 2,
                "owned_bit": 0x0400,
                "equip_value": 3,
            },
        },
    },
    "boots": {
        "label": "Boots",
        "shift": 12,
        "clear_mask": 0x0FFF,
        "entries": {
            "kokiri_boots": {
                "label": "Kokiri Boots",
                "index": 0,
                "owned_bit": 0x1000,
                "equip_value": 1,
            },
            "iron_boots": {
                "label": "Iron Boots",
                "index": 1,
                "owned_bit": 0x2000,
                "equip_value": 2,
            },
            "hover_boots": {
                "label": "Hover Boots",
                "index": 2,
                "owned_bit": 0x4000,
                "equip_value": 3,
            },
        },
    },
}

UPGRADE_GROUPS = {
    "quiver": {
        "key": "quiver",
        "label": "Quiver",
        "shift": 0,
        "mask_bits": 0b111,
        "levels": (
            "None",
            "30 Arrows",
            "40 Arrows",
            "50 Arrows",
        ),
    },
    "bomb_bag": {
        "key": "bomb_bag",
        "label": "Bomb Bag",
        "shift": 3,
        "mask_bits": 0b111,
        "levels": (
            "None",
            "20 Bombs",
            "30 Bombs",
            "40 Bombs",
        ),
    },
    "strength": {
        "key": "strength",
        "label": "Strength",
        "shift": 6,
        "mask_bits": 0b111,
        "levels": (
            "None",
            "Goron's Bracelet",
            "Silver Gauntlets",
            "Golden Gauntlets",
        ),
    },
    "scale": {
        "key": "scale",
        "label": "Scale",
        "shift": 9,
        "mask_bits": 0b111,
        "levels": (
            "None",
            "Silver Scale",
            "Golden Scale",
        ),
    },
    "wallet": {
        "key": "wallet",
        "label": "Wallet",
        "shift": 12,
        "mask_bits": 0b11,
        "levels": (
            "Child Wallet",
            "Adult's Wallet",
            "Giant's Wallet",
            "Tycoon's Wallet",
        ),
    },
    "bullet_bag": {
        "key": "bullet_bag",
        "label": "Bullet Bag",
        "shift": 14,
        "mask_bits": 0b111,
        "levels": (
            "None",
            "30 Seeds",
            "40 Seeds",
            "50 Seeds",
        ),
    },
    "sticks": {
        "key": "sticks",
        "label": "Deku Sticks",
        "shift": 17,
        "mask_bits": 0b111,
        "levels": (
            "None",
            "10 Sticks",
            "20 Sticks",
            "30 Sticks",
        ),
    },
    "nuts": {
        "key": "nuts",
        "label": "Deku Nuts",
        "shift": 20,
        "mask_bits": 0b111,
        "levels": (
            "None",
            "20 Nuts",
            "30 Nuts",
            "40 Nuts",
        ),
    },
}

QUEST_FLAGS = {
    "medallions": {
        "forest_medallion": 0,
        "fire_medallion": 1,
        "water_medallion": 2,
        "spirit_medallion": 3,
        "shadow_medallion": 4,
        "light_medallion": 5,
    },
    "warp_songs": {
        "minuet_of_forest": 6,
        "bolero_of_fire": 7,
        "serenade_of_water": 8,
        "requiem_of_spirit": 9,
        "nocturne_of_shadow": 10,
        "prelude_of_light": 11,
    },
    "songs": {
        "zeldas_lullaby": 12,
        "eponas_song": 13,
        "sarias_song": 14,
        "suns_song": 15,
        "song_of_time": 16,
        "song_of_storms": 17,
    },
    "stones": {
        "kokiri_emerald": 18,
        "goron_ruby": 19,
        "zora_sapphire": 20,
    },
    "misc": {
        "stone_of_agony": 21,
        "gerudo_card": 22,
        "gs_unlocked": 23,
        "heart_piece_icon": 24,
    },
}

BUTTON_LAYOUT = (
    ("b", "B"),
    ("cleft", "C-Left"),
    ("cdown", "C-Down"),
    ("cright", "C-Right"),
    ("dup", "D-Pad Up"),
    ("ddown", "D-Pad Down"),
    ("dleft", "D-Pad Left"),
    ("dright", "D-Pad Right"),
)

BUTTON_ASSIGNABLE_ITEMS = {
    "none": "None",
    "stick": "Deku Stick",
    "nut": "Deku Nut",
    "bomb": "Bomb",
    "bow": "Bow",
    "fire_arrow": "Fire Arrow",
    "dins_fire": "Din's Fire",
    "slingshot": "Slingshot",
    "ocarina_fairy": "Fairy Ocarina",
    "ocarina_time": "Ocarina of Time",
    "bombchu": "Bombchu",
    "hookshot": "Hookshot",
    "longshot": "Longshot",
    "ice_arrow": "Ice Arrow",
    "farores_wind": "Farore's Wind",
    "boomerang": "Boomerang",
    "lens": "Lens of Truth",
    "beans": "Magic Beans",
    "hammer": "Megaton Hammer",
    "light_arrow": "Light Arrow",
    "nayrus_love": "Nayru's Love",
    "bottle": "Bottle",
    "letter": "Letter",
    "kokiri_sword": "Kokiri Sword",
    "master_sword": "Master Sword",
    "biggoron_sword": "Biggoron Sword",
}

SWORD_BUTTON_MODES = {
    "none": "Swordless",
    "kokiri": "Kokiri Sword",
    "master": "Master Sword",
    "biggoron": "Biggoron Sword",
}
