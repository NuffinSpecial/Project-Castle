# Project Castle (Contextual ASL Translator)

[![CI](https://github.com/NuffinSpecial/Project-Castle/actions/workflows/ci.yml/badge.svg)](https://github.com/NuffinSpecial/Project-Castle/actions/workflows/ci.yml)

English-to-ASL gloss translation powered by NLP, with **crowdsourced sign videos** for playback.

## Project overview

The pipeline:

1. **Analyzes** English (spaCy `en_core_web_sm`, regex fallback)
2. **Applies** multi-word expressions and rule-based gloss transfer
3. **Resolves** each gloss token to a **community-submitted video** when available

Submissions on the web UI stay **pending** until an administrator approves them; approved signs join the community catalog—no third-party sign dictionary.

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

- **Register** and **sign in** to submit signs
- Submit English + video on **Submit Translation** → submission stays **pending** until an admin approves it
- Videos are served at `/api/signs/<GLOSS>/video` after approval
- Translation page plays community videos when available; otherwise links to submit

### Accounts & admin review

Set these environment variables before first run to create an administrator:

```bat
set CASTLE_ADMIN_EMAIL=you@example.com
set CASTLE_ADMIN_PASSWORD=your-secure-password
set CASTLE_ADMIN_USERNAME=admin
```

The first account registered also becomes admin if no users exist yet. Admins see an **Admin** link in the nav to approve or reject pending submissions at `/admin/`.

For production, set a strong `FLASK_SECRET_KEY` environment variable.

## Public hosting (Render)

This repo includes a `render.yaml` Blueprint and a `Dockerfile`.

- **Render**: create a new Render service from this GitHub repo. Render will detect `render.yaml`,
  provision a **persistent disk**, and run the app with `gunicorn`.
- **Persistent data**: submissions + SQLite DB live under `CASTLE_DATA_DIR` (Render sets this to `/var/data`).

After deploy, set these optional env vars in Render to bootstrap your first admin:

```text
CASTLE_ADMIN_EMAIL=you@example.com
CASTLE_ADMIN_PASSWORD=your-secure-password
CASTLE_ADMIN_USERNAME=admin
```

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
