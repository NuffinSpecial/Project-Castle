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

## Self-hosting (Cloudflare Tunnel)

This keeps the app running on your PC and exposes it publicly through Cloudflare without opening router ports.

### Quick start (random public URL)

1. Install `cloudflared` (pick one):

```powershell
# Option A: winget (then open a NEW PowerShell window)
winget install --id Cloudflare.cloudflared

# Option B: local copy in this repo (no admin)
.\scripts\install_cloudflared.ps1
```

Verify:

```powershell
cloudflared --version
```

Optional (only needed for a stable custom hostname later):

```powershell
cloudflared tunnel login
```

2. Run the tunnel + local dev server:

```powershell
.\scripts\cloudflare_tunnel.ps1
```

Cloudflare prints a public URL in the output (it changes each time in this quick mode).

### Stable domain (recommended)

1. Create a tunnel and configure a hostname (one-time):

```powershell
cloudflared tunnel create project-castle
cloudflared tunnel route dns project-castle castle.yourdomain.com
```

2. Copy `cloudflared/config.yml.example` to `cloudflared/config.yml` and fill in:
- `tunnel` (name or id)
- `credentials-file` (path to the generated json)
- `hostname`

3. Run:

```powershell
.\dev.bat
cloudflared tunnel run project-castle
```

### Notes

- **Persistence**: your SQLite DB + uploaded videos live under `data/` on your machine. Keep your machine on.
- **Admin**: set `CASTLE_ADMIN_EMAIL`, `CASTLE_ADMIN_PASSWORD`, `CASTLE_ADMIN_USERNAME` in your shell before starting to bootstrap an admin.
- **Security**: Cloudflare can also add Access policies in front of your app if you want an extra gate.
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
