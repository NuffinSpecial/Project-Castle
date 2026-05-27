"""Simple command line interface for the ASL translation pipeline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from asl_translator.pipeline import TranslationPipeline


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "sentence",
        nargs="*",
        help="Sentence(s) to translate. If omitted the input file must be provided.",
    )
    parser.add_argument(
        "-f",
        "--file",
        type=Path,
        help="Path to a text file with one sentence per line.",
    )
    parser.add_argument("-o", "--output", type=Path, help="Optional path to write the JSON result.")
    return parser.parse_args(argv)


def load_sentences(args: argparse.Namespace) -> list[str]:
    sentences: list[str] = []
    if args.sentence:
        sentences.extend(args.sentence)

    if args.file:
        if not args.file.exists():
            raise SystemExit(f"Input file not found: {args.file}")
        sentences.extend(
            [
                line.strip()
                for line in args.file.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        )

    if not sentences:
        raise SystemExit("No sentences provided.")

    return sentences


def main(argv: list[str] | None = None) -> int:
    args = parse_arguments(argv)
    sentences = load_sentences(args)

    pipeline = TranslationPipeline()
    results = [result.__dict__ for result in pipeline.translate_many(sentences)]

    output = json.dumps(results, indent=2, ensure_ascii=False)

    if args.output:
        args.output.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
