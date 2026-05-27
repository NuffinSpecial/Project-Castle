"""Multi-word expression matching before token-by-token glossing."""

from __future__ import annotations

# Longest phrases first for greedy matching.
MWE_GLOSS: dict[tuple[str, ...], list[str]] = {
    ("look", "up"): ["LOOK-UP"],
    ("give", "up"): ["GIVE-UP"],
    ("ice", "cream"): ["ICE-CREAM"],
    ("thank", "you"): ["THANK-YOU"],
    ("good", "night"): ["GOOD-NIGHT"],
    ("good", "morning"): ["GOOD-MORNING"],
    ("right", "now"): ["NOW"],
}


def extract_mwe(lemmas: list[str]) -> tuple[list[str], list[str]]:
    """Return gloss chunks and remaining lemmas after MWE replacement."""

    gloss_chunks: list[str] = []
    remaining: list[str] = []
    index = 0
    keys = sorted(MWE_GLOSS.keys(), key=len, reverse=True)

    while index < len(lemmas):
        matched = False
        for key in keys:
            end = index + len(key)
            if lemmas[index:end] == list(key):
                gloss_chunks.extend(MWE_GLOSS[key])
                index = end
                matched = True
                break
        if not matched:
            remaining.append(lemmas[index])
            index += 1

    return gloss_chunks, remaining
