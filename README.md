# Cepeda TikTok defamation-campaign dashboard

Interactive Streamlit dashboard tracing the defamation campaign against Iván Cepeda
on TikTok — combined-term co-occurrence, the hashtag co-use network (centrality /
betweenness), and diffusion over time. Built from a pre-computed analysis pipeline;
this repo contains only what the dashboard needs to run.

Features:
- **Bilingual** (Español / English) — switch in the sidebar.
- **Defamation ↔ Abelardo integration** — a hashtag co-occurrence network and
  metrics showing the anti-Cepeda smear is embedded in the Abelardo de la Espriella
  campaign (shared posts, shared accounts), not a separate phenomenon.
- **Co-use network** with centrality / betweenness, plus co-occurrence and
  cumulative adoption views.

## Contents

```
streamlit_app.py                       # the app (deploy entry point)
config.py                              # data paths
requirements.txt                       # runtime dependencies
data/processed/posts_campaign.csv      # posts + campaign flags
data/processed/actor_campaign.csv      # actors + roles + centrality
data/processed/hashtags.csv            # post → hashtag edges
data/networks/campaign_shared_hashtag.graphml   # hashtag co-use network
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
