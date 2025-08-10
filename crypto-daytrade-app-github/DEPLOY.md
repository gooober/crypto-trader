# Deploy to Streamlit Cloud (via GitHub)

## 1) Push this folder to a new GitHub repo
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<YourUsername>/crypto-daytrade-app.git
git push -u origin main
```

## 2) Create the app on Streamlit Cloud
- Go to https://share.streamlit.io → **New app**
- Select your repo
- **Main file path:** `app.py`
- **Branch:** `main`
- **Deploy**

## 3) (Optional) Add secrets for Live trading later
In Streamlit Cloud → **Settings → Secrets**, paste:
```toml
COINBASE_API_KEY=""
COINBASE_API_SECRET=""
COINBASE_API_PASSPHRASE=""
KRAKEN_API_KEY=""
KRAKEN_API_SECRET=""
```

Paper Mode works without any keys. Live trading will be enabled once we add the broker module.
Generated: 2025-08-10T03:26:41.852996Z
