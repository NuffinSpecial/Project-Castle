"""ASL-oriented gloss ordering (transfer grammar)."""

from __future__ import annotations

WH_GLOSS = frozenset(
    {
        "WHY",
        "WHAT",
        "WHEN",
        "WHERE",
        "WHO",
        "WHOM",
        "WHOSE",
        "HOW",
        "WHICH",
    }
)

TIME_GLOSS = frozenset(
    {
        "PAST",
        "NOW",
        "FUTURE",
        "YESTERDAY",
        "TODAY",
        "TOMORROW",
        "MONDAY",
        "TUESDAY",
        "WEDNESDAY",
        "THURSDAY",
        "FRIDAY",
        "SATURDAY",
        "SUNDAY",
    }
)

MODAL_GLOSS = frozenset({"CAN", "MAY", "MUST", "MIGHT"})

PRONOUN_GLOSS = frozenset(
    {
        "ME",
        "YOU",
        "HE",
        "SHE",
        "WE",
        "THEY",
        "MY",
        "YOUR",
        "OUR",
        "THEIR",
        "HIS",
        "HER",
    }
)

YES_NO_MARKER = "YN-Q"

__all__ = [
    "MODAL_GLOSS",
    "PRONOUN_GLOSS",
    "TIME_GLOSS",
    "WH_GLOSS",
    "YES_NO_MARKER",
    "apply_transfer_rules",
]


def apply_transfer_rules(tokens: list[str], *, is_question: bool = False) -> list[str]:
    """Reorder gloss tokens toward common ASL surface order."""

    if not tokens:
        return tokens

    ordered = _move_time_to_front(tokens)
    ordered = _reorder_polar_question(ordered, is_question=is_question)
    ordered = _move_wh_to_end(ordered)
    if is_question and not any(token in WH_GLOSS for token in ordered):
        ordered = ordered + [YES_NO_MARKER]
    return ordered


def _move_time_to_front(tokens: list[str]) -> list[str]:
    time_buffer: list[str] = []
    rest: list[str] = []
    for token in tokens:
        if token in TIME_GLOSS:
            if not time_buffer or token != time_buffer[-1]:
                time_buffer.append(token)
        else:
            rest.append(token)
    if time_buffer:
        return time_buffer + rest
    return tokens


def _reorder_polar_question(tokens: list[str], *, is_question: bool) -> list[str]:
    """Yes/no questions: subject before modal (e.g. YOU CAN, not CAN YOU)."""

    if not is_question:
        return tokens

    modals = [token for token in tokens if token in MODAL_GLOSS]
    pronouns = [token for token in tokens if token in PRONOUN_GLOSS]
    if not modals or not pronouns:
        return tokens

    rest = [token for token in tokens if token not in MODAL_GLOSS and token not in PRONOUN_GLOSS]
    return pronouns + modals + rest


def _move_wh_to_end(tokens: list[str]) -> list[str]:
    """WH-questions in ASL typically place the question sign at the end."""

    wh_tokens: list[str] = []
    rest: list[str] = []
    for token in tokens:
        if token in WH_GLOSS:
            wh_tokens.append(token)
        else:
            rest.append(token)
    if wh_tokens:
        return rest + wh_tokens
    return tokens
