# Project Castle (Contextual ASL Translator)

[![CI](https://github.com/NuffinSpecial/Project-Castle/actions/workflows/ci.yml/badge.svg)](https://github.com/NuffinSpecial/Project-Castle/actions/workflows/ci.yml)

English-to-ASL gloss translation powered by NLP, with **crowdsourced sign videos** for playback.

## Project overview

The pipeline:

1. **Analyzes** English (spaCy `en_core_web_sm`, regex fallback)
2. **Applies** multi-word expressions and rule-based gloss transfer
3. **Resolves** each gloss token to a **community-submitted video** when available

Submissions on the web UI are published immediately to the sign catalog—no third-party sign dictionary.

## Getting started

1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   python scripts/download_nlp_models.py
   ```
3. Run tests:
   ```bash
   python -m pytest
   ```
4. Translate from the CLI:
   ```bash
   python main.py "I will eat an apple tomorrow"
   ```

## Web interface

### Quick local preview

```bat
dev.bat
```

or

```bash
python scripts/dev.py
```

Open http://127.0.0.1:5000/

### Crowdsourced signs

- Submit English + video on **Submit Translation** → sign goes live in `data/signs/catalog.json`
- Videos are served at `/api/signs/<GLOSS>/video`
- Translation page plays community videos when available; otherwise links to submit

## NLP & evaluation

- Analysis: `asl_translator/nlp/analyzer.py`
- Gloss rules: `asl_translator/gloss.py`
- Eval set: `data/eval/gloss_pairs.json`
- Run eval: `python -c "from asl_translator.eval import run_eval; print(run_eval())"`

## Example API output

```json
{
  "glossTokens": ["FUTURE", "ME", "EAT", "APPLE"],
  "lemmas": ["i", "will", "eat", "an", "apple", "tomorrow"],
  "links": [null, null, null, null],
  "signAvailable": [false, false, false, false],
  "analysisEngine": "en_core_web_sm"
}
```

When a community video exists for `HELLO`, `links` contains `"/api/signs/HELLO/video"` and `signAvailable` is `true`.

> The gloss is a research prototype—not a certified ASL interpretation.
