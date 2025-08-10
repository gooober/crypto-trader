# Small-Day-Trade Assistant (Paper Mode v1)

Plug-and-play Streamlit app for **small intraday crypto trades** (US-friendly).

## Includes
- Coinbase → Kraken → Simulated data fallback (1m candles)
- Advanced signals: EMA(9/21)+slope, RSI(14), VWAP (z-score), SuperTrend, ATR, Bollinger, swing points
- Risk-based sizing (default 1% of account) or USD sizing
- Brackets: stop models (ATR, SuperTrend, Structure, Fixed%) + TP, optional trailing
- Guardrails: max daily loss 2% (locked), max trades/day configurable
- Clean UI: live panel, signal card, sizing cards, sparkline, trade box, trade log

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Next: Live trading
- Add `.streamlit/secrets.toml` with keys (see example)
- We'll wire **ccxt** for Coinbase/Kraken market/limit + bracket management

Generated: 2025-08-10T03:07:28.726616Z


## Deploy
See `DEPLOY.md` for GitHub + Streamlit Cloud steps.
