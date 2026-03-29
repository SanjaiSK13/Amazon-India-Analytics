# ☁️ Deploying to Streamlit Cloud — Step-by-Step Guide

Streamlit Cloud hosts your dashboard **free** at a public URL like:
`https://your-app-name.streamlit.app`

---

## The Challenge: Large Data Files

Your database (`amazon_india.db`) is ~172MB and your CSVs are even larger.
Git/GitHub has a 100MB file size limit, so we **cannot push the DB directly**.

There are two solutions — pick whichever suits you:

- **Option A** — Lightweight deploy (recommended for portfolio): commit only the cleaned CSV, rebuild the DB on first run
- **Option B** — Full deploy with cloud storage (Google Drive / Hugging Face)

---

## Option A — Lightweight Deploy (Recommended)

This approach commits the cleaned master CSV (~50MB compressed) and rebuilds the database automatically when the app first starts on the cloud.

### Step 1 — Prepare your GitHub repository

```bash
# Inside amazon_india_project/
git init
git add .
git commit -m "Initial commit — Amazon India Analytics"
```

Create a new repo on GitHub (e.g. `amazon-india-analytics`) then push:

```bash
git remote add origin https://github.com/YOUR_USERNAME/amazon-india-analytics.git
git branch -M main
git push -u origin main
```

### Step 2 — Handle large files with Git LFS

Install Git LFS to handle the cleaned CSV:

```bash
# Install Git LFS (once per machine)
git lfs install

# Track the master CSV
git lfs track "data/cleaned/amazon_india_master_cleaned.csv"
git add .gitattributes
git add data/cleaned/amazon_india_master_cleaned.csv
git commit -m "Add cleaned dataset via LFS"
git push
```

> Git LFS is free up to 1GB on GitHub. Your CSV should be under 100MB.

### Step 3 — Add a startup script to auto-build the DB

Create `dashboard/startup.py` with this content and add it to `app.py`:

```python
# Add this at the very top of dashboard/app.py, before any other code:

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "data", "db", "amazon_india.db")

if not os.path.exists(DB_PATH):
    import streamlit as st
    with st.spinner("Setting up database for first run... (takes ~2 minutes)"):
        from src.database_setup import build_database
        build_database()
    st.rerun()
```

### Step 4 — Create Streamlit config

Create `.streamlit/config.toml` in your project root:

```toml
[server]
maxUploadSize = 500
headless = true

[theme]
primaryColor = "#FF9900"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#232F3E"
font = "sans serif"
```

### Step 5 — Deploy on Streamlit Cloud

1. Go to **[share.streamlit.io](https://share.streamlit.io)**
2. Click **"New app"**
3. Connect your GitHub account
4. Fill in:
   - **Repository**: `YOUR_USERNAME/amazon-india-analytics`
   - **Branch**: `main`
   - **Main file path**: `dashboard/app.py`
5. Click **"Deploy!"**

Your app will be live in 2–3 minutes at:
`https://amazon-india-analytics.streamlit.app`

---

## Option B — Host DB on Hugging Face (No size limits)

This is better if you want the full DB pre-built without the startup wait.

### Step 1 — Upload DB to Hugging Face

1. Create a free account at [huggingface.co](https://huggingface.co)
2. Create a new **Dataset** repository (e.g. `amazon-india-db`)
3. Upload `data/db/amazon_india.db` to that repository

### Step 2 — Add download logic to app.py

Add this at the top of `dashboard/app.py`:

```python
import os, requests

DB_PATH = "data/db/amazon_india.db"
HF_URL  = "https://huggingface.co/datasets/YOUR_HF_USERNAME/amazon-india-db/resolve/main/amazon_india.db"

if not os.path.exists(DB_PATH):
    os.makedirs("data/db", exist_ok=True)
    import streamlit as st
    with st.spinner("Downloading database... (~172MB, takes ~1 minute)"):
        r = requests.get(HF_URL, stream=True)
        with open(DB_PATH, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    st.rerun()
```

### Step 3 — Add `requests` to requirements.txt

```
requests>=2.28.0
```

Then deploy exactly as in Option A Step 5.

---

## requirements.txt for Streamlit Cloud

Make sure your `requirements.txt` contains exactly:

```
pandas>=2.0.0
numpy>=1.24.0
streamlit>=1.32.0
plotly>=5.18.0
sqlalchemy>=2.0.0
scipy>=1.10.0
requests>=2.28.0
```

> Do NOT include `matplotlib` or `seaborn` in the Streamlit Cloud requirements
> unless you use them in `app.py` — they just slow down boot time.

---

## Folder structure to push to GitHub

```
amazon-india-analytics/
├── .gitignore
├── .streamlit/
│   └── config.toml          ← theme + server config
├── README.md
├── requirements.txt
├── data/
│   ├── raw/.gitkeep         ← empty placeholder
│   ├── cleaned/
│   │   └── amazon_india_master_cleaned.csv   ← via Git LFS
│   └── db/.gitkeep          ← empty placeholder
├── src/
│   ├── data_cleaning.py
│   ├── eda_analysis.py
│   └── database_setup.py
├── dashboard/
│   └── app.py
└── reports/
    └── eda_charts/          ← optional PNG charts
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| App crashes on startup | Check `requirements.txt` has all packages |
| DB not found error | Make sure startup auto-build code is at top of `app.py` |
| Git push rejected (file too large) | Use Git LFS for CSV files |
| Slow first load | Normal — DB is being built. Subsequent loads are instant (cached) |
| `ModuleNotFoundError` | Add missing package to `requirements.txt` and redeploy |
| Streamlit secrets needed | Use `.streamlit/secrets.toml` locally, Streamlit Cloud UI for production |

---

## Updating the live app

Any `git push` to `main` automatically triggers a redeploy on Streamlit Cloud.

```bash
git add .
git commit -m "Update dashboard charts"
git push origin main
# App redeploys automatically in ~1 minute
```

---

*Your dashboard will be live and shareable as a portfolio project.*
