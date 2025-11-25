---
title: Granted Digital Twin
emoji: 🧪
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 4.38.0
app_file: app.py
pinned: false
---

# Granted Digital Twin — Live Scenario Runner

This repo packages the **Digital Twin simulator** with a **Gradio UI**. It supports **Scenario A (Shadow Mode)** and **Scenario B (Scrape Mode)**.

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Deploy to GitHub Codespaces ("codex")

1. Create a new repo and push:
   ```bash
   git init
   git add .
   git commit -m "init: Granted Digital Twin live runner"
   gh repo create granted-digital-twin --public --source . --remote origin --push
   ```
2. Open in **Codespaces** (GitHub → Code → Codespaces → "Create codespace on main").
3. In the codespace terminal:
   ```bash
   pip install -r requirements.txt
   python app.py
   ```
   You’ll get a forwarded port URL to share publicly.

## Deploy to Hugging Face Spaces (Gradio)

1. Create a **Space** (Gradio SDK), then push this repo:
   ```bash
   huggingface-cli login        # paste your token
   git init
   git add .
   git commit -m "init: Granted Digital Twin (Gradio Space)"
   git branch -M main
   git remote add origin https://huggingface.co/spaces/<your-namespace>/granted-digital-twin
   git push -u origin main
   ```
2. The Space will auto-build and serve `app.py`.

## Using the app

- Click **Load Template**, edit config values (replace placeholders with real numbers from your docs), then **Run Scenarios**.
- The results JSON includes summary stats for `revenue_usd`, `churn_rate`, `gross_margin`, and `legal_veto_rate` per scenario.

## Files

- `app.py` — Gradio UI
- `dt_simulator.py` — Monte Carlo engine
- `dt_schema.py` — Pydantic config schema
- `dt_config_template.json` / `.yaml` — config templates
- `requirements.txt` — dependencies
- `runtime.txt` — Python version hint for Spaces
