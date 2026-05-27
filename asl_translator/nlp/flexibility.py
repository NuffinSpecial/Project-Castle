"""Detect gloss token groups where sign order is commonly flexible in ASL."""

from __future__ import annotations

from dataclasses import dataclass

from .transfer import MODAL_GLOSS, PRONOUN_GLOSS, TIME_GLOSS, WH_GLOSS, YES_NO_MARKER

# Tokens that anchor order (not part of mutable pairs)
_FIXED_EDGE = WH_GLOSS | {YES_NO_MARKER}


@dataclass(frozen=True)
class MutableGroup:
    """Indices into gloss_tokens that may be reordered."""

    indices: tuple[int, ...]
    alternatives: tuple[tuple[str, ...], ...]
    note: str

    def to_dict(self) -> dict:
        return {
            "indices": list(self.indices),
            "alternatives": [list(alt) for alt in self.alternatives],
            "note": self.note,
        }


def find_mutable_groups(gloss_tokens: list[str]) -> list[MutableGroup]:
    """Return groups of adjacent glosses with attested alternate orderings."""

    groups: list[MutableGroup] = []
    used: set[int] = set()
    length = len(gloss_tokens)

    for index in range(length - 1):
        if index in used or index + 1 in used:
            continue
        left, right = gloss_tokens[index], gloss_tokens[index + 1]
        if left in _FIXED_EDGE or right in _FIXED_EDGE:
            continue

        group: MutableGroup | None = None
        if left in PRONOUN_GLOSS and right in MODAL_GLOSS:
            group = MutableGroup(
                indices=(index, index + 1),
                alternatives=((left, right), (right, left)),
                note="Subject and modal are often interchangeable in yes/no questions.",
            )
        elif left in TIME_GLOSS and right in PRONOUN_GLOSS:
            group = MutableGroup(
                indices=(index, index + 1),
                alternatives=((left, right), (right, left)),
                note="Time expression and subject can sometimes be signed in either order.",
            )

        if group is not None:
            groups.append(group)
            used.update(group.indices)

    return groups
