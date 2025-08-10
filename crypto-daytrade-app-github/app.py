import asyncio, math
import streamlit as st
import pandas as pd
from data import get_candles
from indicators import compute_indicators, generate_signal, stop_price
from trading import PaperEngine, Bracket
from utils import format_usd, percent

st.set_page_config(page_title="📈 Small-Day-Trade Assistant", layout="wide")

if "engine" not in st.session_state:
    st.session_state.engine = PaperEngine(10000.0)

with st.sidebar:
    st.header("⚙️ Configuration")
    symbol = st.selectbox("Symbol", ["BTC-USD", "ETH-USD", "SOL-USD"], index=0)
    refresh_sec = st.slider("Refresh (s)", 1, 5, 2, help="REST fallback interval")

    st.subheader("Risk & Sizing")
    mode_size = st.radio("Sizing mode", ["USD amount", "Risk % of account"], index=1, horizontal=True)
    if mode_size == "USD amount":
        usd_size = st.number_input("USD size", min_value=10.0, value=50.0, step=10.0)
        risk_pct = None
    else:
        risk_pct = st.number_input("Risk per trade (%)", min_value=0.1, max_value=5.0, value=1.0, step=0.1) / 100.0
        usd_size = None

    fee_bps = st.number_input("Fees (bps)", min_value=0, max_value=50, value=10, step=1)
    slip_bps = st.number_input("Slippage (bps)", min_value=0, max_value=50, value=5, step=1)

    st.subheader("Stops & Targets")
    stop_model = st.selectbox("Stop model", ["ATR", "SuperTrend", "Structure", "Fixed%"], index=0)
    atr_mult = st.slider("ATR multiple (stop)", 0.5, 3.0, 1.5, 0.1)
    trail_on = st.checkbox("Enable trailing stop (ATR 1.0×)", value=True)
    tp_pct = st.slider("Take-profit (%)", 0.2, 5.0, 1.0, 0.1) / 100.0

    st.subheader("Guardrails")
    st.write("Max daily loss: 2% (locked)")
    max_trades_day = st.number_input("Max trades today", min_value=1, max_value=100, value=20, step=1)

    st.divider()
    place_with_bracket = st.checkbox("Place with bracket (TP+SL)", value=True)

st.session_state.engine.max_trades_per_day = max_trades_day

async def load_data(sym: str):
    df, src = await get_candles(sym, 600)
    return df, src

df, source = asyncio.run(load_data(symbol))
dfi = compute_indicators(df)
sig = generate_signal(dfi)
last = dfi.iloc[-1]
last_price = float(last['close'])
vwapd = float(last['vwap']) if not math.isnan(last['vwap']) else None

st.title("📈 Small-Day-Trade Assistant — Paper Mode v1")
st.caption(f"Data source: **{source}** • Refresh: every {refresh_sec}s • Advanced signals (1m TF + filters)")
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("Last Price", format_usd(last_price))
with c2: st.metric("1m Change", percent((last_price / dfi['close'].iloc[-2] - 1.0)))
with c3: st.metric("VWAP", format_usd(vwapd) if vwapd else "-")
with c4: st.metric("Signal / Score", f"{sig['signal']} / {sig['score']}", help=sig['rationale'])

st.line_chart(dfi.set_index('time')[['close']].rename(columns={'close':'Price'}))

st.subheader("Position Sizing & Projections")
side_default = "BUY" if sig['signal'] != "SELL" else "SELL"
stop_px = stop_price(stop_model, dfi, side_default, atr_mult=atr_mult)

if risk_pct is not None and stop_px:
    risk_per_unit = abs(last_price - stop_px)
    account = st.session_state.engine.cash
    risk_usd = account * risk_pct
    qty_est = max(risk_usd / max(risk_per_unit, 1e-6), 0.0)
    sizing_note = f"Risk {risk_pct*100:.2f}% of ${account:,.2f} = ${risk_usd:,.2f}"
else:
    qty_est = (usd_size or 50.0) / max(last_price, 1e-9)
    sizing_note = f"Manual USD sizing: ${usd_size or 50.0:,.2f}"

tp_px = last_price * (1 + tp_pct) if side_default == "BUY" else last_price * (1 - tp_pct)
st.write(sizing_note)
cA, cB, cC, cD = st.columns(4)
with cA: st.metric("Qty (est.)", f"{qty_est:.6f}")
with cB: st.metric("Stop @", format_usd(stop_px) if stop_px else "-")
with cC: st.metric("Take Profit @", format_usd(tp_px))
with cD:
    if stop_px:
        risk = (stop_px - last_price) if side_default=="BUY" else (last_price - stop_px)
        st.metric("Risk/Unit", format_usd(abs(risk)))
    else:
        st.metric("Risk/Unit", "-")

st.subheader("Paper Trade")
side = st.radio("Side", ["BUY","SELL"], index=0 if side_default=="BUY" else 1, horizontal=True)
qty_in = st.number_input("Quantity", min_value=0.0, value=float(qty_est), step=max(qty_est/50, 0.000001))
if st.button("Place Order (Paper)"):
    br = Bracket(
        stop=stop_px if place_with_bracket else None,
        take_profit=tp_px if place_with_bracket else None,
        trailing_atr_mult=1.0 if trail_on else None,
    )
    try:
        order = st.session_state.engine.place(symbol, side, qty_in, last_price, fee_bps, slip_bps, br)
        st.success(f"Paper order filled: {side} {qty_in:.6f} {symbol} @ {last_price:.2f}")
    except Exception as e:
        st.error(str(e))

st.subheader("Trade Log")
st.dataframe(st.session_state.engine.to_frame(), use_container_width=True, height=320)

st.markdown(f"<meta http-equiv='refresh' content='{refresh_sec}'>", unsafe_allow_html=True)
