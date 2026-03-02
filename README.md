# Titan Laser Manual Query

Search the D-Soar Plus Fiber Laser Machine Manual and the CypCut User Manual by keyword — instantly see every matching page with highlighted results.

---

## Option A — Run Locally (Windows)

1. **Make sure Python is installed** — download from [python.org](https://www.python.org/downloads/) if needed (check "Add Python to PATH" during install)
2. Copy this entire folder to your PC (keep all files together)
3. Double-click **`run.bat`**
4. The first launch installs dependencies automatically (~1 min); after that it starts instantly
5. The app opens in your default browser at `http://localhost:8501`

---

## Option B — Host Online (Streamlit Community Cloud — Free)

> Anyone with the link can use the app from any device, no install needed.

### Step 1 — Push to GitHub

1. Create a free account at [github.com](https://github.com)
2. Create a **new repository** (can be private)
3. Upload all files in this folder to the repo  
   *(Note: if the PDFs are over 25 MB, use [Git LFS](https://git-lfs.com) or upload them via the GitHub web interface)*

### Step 2 — Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with your GitHub account
2. Click **"New app"**
3. Select your repo, branch `main`, and set the file to `query_app.py`
4. Click **"Deploy"** — your app will be live in ~2 minutes
5. Share the URL with anyone

---

## Files in this folder

| File | Purpose |
|------|---------|
| `query_app.py` | The app |
| `requirements.txt` | Python dependencies |
| `run.bat` | Windows double-click launcher |
| `*.pdf` | The two manuals being searched |
