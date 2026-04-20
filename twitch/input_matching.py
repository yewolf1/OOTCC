from __future__ import annotations

import re
from typing import Iterable


_WHITESPACE_RE = re.compile(r"\s+")


def normalize_user_text(text: str) -> str:
    """Normalize viewer text to a forgiving canonical form."""
    normalized = (text or '').strip().lower().replace('_', ' ').replace('-', ' ')
    normalized = _WHITESPACE_RE.sub(' ', normalized)
    return normalized


def _compact(text: str) -> str:
    return normalize_user_text(text).replace(' ', '')


def _remove_plural_suffix(word: str) -> str:
    if len(word) > 3 and word.endswith('ies'):
        return word[:-3] + 'y'
    if len(word) > 2 and word.endswith('es'):
        return word[:-2]
    if len(word) > 1 and word.endswith('s'):
        return word[:-1]
    return word


def _plural_stem(text: str) -> str:
    words = normalize_user_text(text).split()
    if not words:
        return ''
    words[-1] = _remove_plural_suffix(words[-1])
    return ' '.join(words)


def _is_distance_at_most_one(left: str, right: str) -> bool:
    if left == right:
        return True

    left_len = len(left)
    right_len = len(right)
    if abs(left_len - right_len) > 1:
        return False

    if left_len > right_len:
        left, right = right, left
        left_len, right_len = right_len, left_len

    i = 0
    j = 0
    mismatch_count = 0

    while i < left_len and j < right_len:
        if left[i] == right[j]:
            i += 1
            j += 1
            continue

        mismatch_count += 1
        if mismatch_count > 1:
            return False

        if left_len == right_len:
            i += 1
            j += 1
        else:
            j += 1

    if j < right_len or i < left_len:
        mismatch_count += 1

    return mismatch_count <= 1


def resolve_close_text(user_text: str, candidates: Iterable[str]) -> str:
    """Return the closest accepted value using exact, singular/plural, then distance-1 matching."""
    normalized_input = normalize_user_text(user_text)
    if not normalized_input:
        return normalized_input

    candidate_list = list(dict.fromkeys(candidates))
    normalized_map = {normalize_user_text(candidate): candidate for candidate in candidate_list}

    exact = normalized_map.get(normalized_input)
    if exact is not None:
        return exact

    input_stem = _plural_stem(normalized_input)
    for candidate in candidate_list:
        if _plural_stem(candidate) == input_stem:
            return candidate

    compact_input = _compact(normalized_input)
    best_candidate = ''
    for candidate in candidate_list:
        compact_candidate = _compact(candidate)
        if _is_distance_at_most_one(compact_input, compact_candidate):
            if not best_candidate or len(compact_candidate) < len(_compact(best_candidate)):
                best_candidate = candidate

    if best_candidate:
        return best_candidate

    return normalized_input
