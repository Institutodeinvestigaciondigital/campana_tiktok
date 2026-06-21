# Cepeda TikTok defamation-campaign dashboard

A simple, accessible Streamlit dashboard (Spanish) showing, with TikTok data, that
defamation of Iván Cepeda is **structurally more likely** than defamation of Abelardo
de la Espriella, and that the anti-Cepeda smear **travels with the Abelardo campaign
hashtags**. It presents the evidence plainly — no verdict, no legal claims.

Three panels:
1. **El conjunto de datos** — volume (posts, accounts, views), occurrences of the
   hashtags of interest, and how defamation of each candidate develops over time.
2. **La co-ocurrencia** — the core: "1 in 12" posts about Cepeda defame him vs "1 in 39"
   about Abelardo; how often each smear co-occurs with the opposing campaign's hashtags;
   and a simple network of how the smear hashtags connect to the Abelardo campaign tags.
3. **Cómo se construyó** — plain-language method, the exact (editable) term definitions,
   and honest limitations.

The defamation term definitions are editable under "Ajustes avanzados" in the sidebar.
Built from a pre-computed pipeline; this repo holds only what the dashboard needs.

## Contents

```
streamlit_app.py                  # the app (deploy entry point), 3 panels
detection_config.py               # editable term definitions + plain-language texts
config.py                         # data paths
requirements.txt                  # runtime dependencies
data/processed/posts_campaign.csv # posts (slim: id, user, timestamp, search_text, engagement)
data/processed/hashtags.csv       # post → hashtag edges
```

## Run locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Opens at http://localhost:8501.

## Deploy on Streamlit Community Cloud

1. Push this folder to a **private** GitHub repo (see "Privacy" below).
2. Go to <https://share.streamlit.io> → **Create app** → **Deploy a public app from
   GitHub** (private repos work once you authorise Streamlit on GitHub).
3. Settings:
   - **Repository:** your repo
   - **Branch:** `main`
   - **Main file path:** `streamlit_app.py`
4. Click **Deploy**. Streamlit installs `requirements.txt` and launches the app.
5. Restrict viewers: app **⋮ → Settings → Sharing** → set to specific people /
   "only people I invite" so the data stays private.

## Privacy & ethics

This dashboard names real, public TikTok accounts active in a political campaign and
includes personal data (handles, follower counts, captions). Keep the repo and app
**private / invite-only**. Account-level labels (origin / amplifier) are statistical
(coordination and content co-use), **not** proof of intent or coordination off-platform.
Respect TikTok's Terms of Service regarding redistribution of scraped data.

## Updating the data

The CSV / GraphML files are produced by the analysis pipeline (separate project).
To refresh: regenerate them there and copy the four files into `data/` here, then push.
