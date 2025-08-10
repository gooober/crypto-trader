# Crypto Daytrade App (Streamlit)

## Deploy to Streamlit Cloud

1. **Push to GitHub**
   - Extract this folder and push it to a new GitHub repository.

2. **Deploy**
   - Go to [Streamlit Cloud](https://share.streamlit.io), click **New app**, and select your repo.
   - Main file: `app.py`
   - Branch: `main`

3. **Paper Mode**
   - Works without any API keys.

4. **Live Mode**
   - Add your exchange API keys in Streamlit Cloud's **Secrets** section in this format:

```toml
COINBASE_API_KEY = "your_key"
COINBASE_API_SECRET = "your_secret"
COINBASE_API_PASSPHRASE = "your_passphrase"
KRAKEN_API_KEY = "your_key"
KRAKEN_API_SECRET = "your_secret"
```

5. **Requirements**
   - All Python dependencies are listed in `requirements.txt`.
