"""Evaluation helpers for gloss quality."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .pipeline import TranslationPipeline


@dataclass
class EvalReport:
    total: int
    exact_matches: int
    token_accuracy: float

    @property
    def exact_match_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return self.exact_matches / self.total


def load_eval_set(path: Path | None = None) -> list[dict]:
    eval_path = path or Path(__file__).resolve().parents[1] / "data" / "eval" / "gloss_pairs.json"
    return json.loads(eval_path.read_text(encoding="utf-8"))


def run_eval(pipeline: TranslationPipeline | None = None) -> EvalReport:
    pipeline = pipeline or TranslationPipeline()
    pairs = load_eval_set()
    exact = 0
    token_hits = 0
    token_total = 0

    for pair in pairs:
        result = pipeline.translate(pair["sentence"])
        expected = pair["gloss"]
        if result.gloss_tokens == expected:
            exact += 1
        token_total += len(expected)
        for index, gloss in enumerate(expected):
            if index < len(result.gloss_tokens) and result.gloss_tokens[index] == gloss:
                token_hits += 1

    accuracy = token_hits / token_total if token_total else 0.0
    return EvalReport(total=len(pairs), exact_matches=exact, token_accuracy=accuracy)
