from __future__ import annotations

import re


def normalize_input(text: str) -> str:
    value = (text or '').strip().lower()
    value = value.replace("'", '')
    value = value.replace('.', '')
    value = re.sub(r'[_\-]+', ' ', value)
    value = re.sub(r'\s+', ' ', value)
    return value.strip()


def compact_input(text: str) -> str:
    return re.sub(r'[^a-z0-9+]+', '', normalize_input(text))


def _variants(text: str) -> set[str]:
    normalized = normalize_input(text)
    compact = compact_input(normalized)
    values = {normalized, compact}

    for value in list(values):
        if value.endswith('s') and len(value) > 1:
            values.add(value[:-1])
        else:
            values.add(value + 's')

    return {value for value in values if value}


def _levenshtein_at_most_one(left: str, right: str) -> bool:
    if left == right:
        return True

    left_len = len(left)
    right_len = len(right)
    if abs(left_len - right_len) > 1:
        return False

    if left_len == right_len:
        differences = 0
        for index in range(left_len):
            if left[index] != right[index]:
                differences += 1
                if differences > 1:
                    return False
        return True

    shorter, longer = (left, right) if left_len < right_len else (right, left)
    short_index = 0
    long_index = 0
    edits = 0

    while short_index < len(shorter) and long_index < len(longer):
        if shorter[short_index] == longer[long_index]:
            short_index += 1
            long_index += 1
            continue
        edits += 1
        if edits > 1:
            return False
        long_index += 1

    return True


def resolve_input(value: str, options: dict[str, object], aliases: dict[str, str] | None = None) -> str | None:
    aliases = aliases or {}
    normalized_value = normalize_input(value)
    compact_value = compact_input(normalized_value)

    normalized_aliases = {
        alias_variant: target
        for alias, target in aliases.items()
        for alias_variant in _variants(alias)
    }

    for variant in _variants(normalized_value):
        alias_target = normalized_aliases.get(variant)
        if alias_target in options:
            return alias_target
        if variant in options:
            return variant
        underscored = variant.replace(' ', '_')
        if underscored in options:
            return underscored

    option_variants: list[tuple[str, str]] = []
    for option in options:
        option_variants.extend((option, variant) for variant in _variants(option))

    for option, variant in option_variants:
        if compact_value == compact_input(variant):
            return option

    for option, variant in option_variants:
        if _levenshtein_at_most_one(compact_value, compact_input(variant)):
            return option

    return None
