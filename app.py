import streamlit as st
import json
import time
import random
from collections import Counter
from datetime import datetime, timezone

st.set_page_config(page_title="BEASTMODE PRO", page_icon="👑", layout="wide")

st.markdown("""
<style>
.stApp {background: #0b1020; color: #f4f6ff;}
.block-container {padding-top: 1.6rem; max-width: 1250px;}
.hero {padding: 22px 24px; border: 1px solid #29334f; border-radius: 18px;
       background: linear-gradient(120deg,#151d35,#101629); margin-bottom: 18px;}
.hero h1 {margin: 0; letter-spacing: 1px;}
.hero p {color: #aab6d3; margin-bottom: 0;}
.metric-card {background:#131b30;border:1px solid #29334f;border-radius:14px;padding:16px;}
.small-note {color:#aab6d3;font-size:0.9rem;}
div[data-testid="stMetric"] {background:#131b30;border:1px solid #29334f;padding:14px;border-radius:12px;}
.stButton button {border-radius:10px;font-weight:700;}
</style>
""", unsafe_allow_html=True)

if "ticks" not in st.session_state:
    st.session_state.ticks = []
if "history" not in st.session_state:
    st.session_state.history = []
if "demo_balance" not in st.session_state:
    st.session_state.demo_balance = 1000.0
if "ws_status" not in st.session_state:
    st.session_state.ws_status = "Not connected"

st.markdown("""
<div class="hero">
  <h1>👑 BEASTMODE PRO</h1>
  <p>Deriv market analyzer • Digit strategies • Demo testing • Risk-first design</p>
</div>
""", unsafe_allow_html=True)

st.warning("This first version is an analyzer prototype. It does not place trades or promise winning predictions. Connect to Deriv's official market-data API in the next setup step; never enter your Deriv password or API token into this demo.")

with st.sidebar:
    st.header("⚙️ Settings")
    market = st.selectbox("Market", ["Volatility 100 (1s) Index", "Volatility 75 Index", "Volatility 50 Index"])
    strategy = st.selectbox("Strategy to analyze", ["Even / Odd", "Over / Under"])
    threshold = st.selectbox("Digit threshold", ["Over 4 / Under 5", "Over 5 / Under 6", "Over 6 / Under 7"])
    st.caption("Signals are statistical summaries of the sample, not reliable predictions of the next tick.")
    st.divider()
    st.subheader("Demo risk controls")
    stake = st.number_input("Virtual stake (R)", min_value=1.0, max_value=10000.0, value=10.0, step=1.0)
    stop_loss = st.number_input("Demo stop-loss (R)", min_value=1.0, max_value=100000.0, value=100.0, step=10.0)
    st.caption("Demo values only. No real money is used.")

left, right = st.columns([1.3, 1])
with left:
    st.subheader("📡 Market connection")
    st.info("Connection status: **Not connected yet**")
    st.write("Market selected:", market)
    st.write("Data mode: **Sample data for interface testing**")
    if st.button("Generate sample ticks", type="primary", use_container_width=True):
        # Sample data is clearly labelled and must not be mistaken for live market data.
        new_ticks = [random.randint(0, 9) for _ in range(100)]
        st.session_state.ticks = new_ticks
        st.session_state.ws_status = "Sample data loaded"
        st.rerun()
    st.caption("This button creates synthetic sample digits only. It does not connect to Deriv.")
with right:
    st.subheader("🛡️ System status")
    st.metric("Connection", st.session_state.ws_status)
    st.metric("Sample size", len(st.session_state.ticks))
    st.metric("Demo balance", f"R{st.session_state.demo_balance:,.2f}")

st.divider()
st.subheader("🧠 Digit analysis")
if not st.session_state.ticks:
    st.info("Generate sample ticks to preview the dashboard. Live Deriv data will be added after we confirm the site deploys correctly.")
else:
    ticks = st.session_state.ticks
    counts = Counter(ticks)
    even_count = sum(1 for d in ticks if d % 2 == 0)
    odd_count = len(ticks) - even_count
    over4 = sum(1 for d in ticks if d > 4)
    under5 = len(ticks) - over4
    a, b, c, d = st.columns(4)
    a.metric("Even digits", f"{even_count / len(ticks) * 100:.1f}%")
    b.metric("Odd digits", f"{odd_count / len(ticks) * 100:.1f}%")
    c.metric("Over 4", f"{over4 / len(ticks) * 100:.1f}%")
    d.metric("Under 5", f"{under5 / len(ticks) * 100:.1f}%")
    st.write("**Digit counts (sample data):**")
    st.bar_chart({str(i): counts.get(i, 0) for i in range(10)})
    st.write("**Most recent sample digits:**", " · ".join(map(str, ticks[-20:])))
    st.caption("A past sample frequency does not establish a predictive edge. In a fair digit process, recent digits may not predict the next digit.")

st.divider()
st.subheader("🧪 Demo performance log")
col1, col2 = st.columns(2)
with col1:
    demo_result = st.selectbox("Record a demo outcome", ["Win", "Loss"])
    if st.button("Record demo result", use_container_width=True):
        if demo_result == "Win":
            st.session_state.demo_balance += stake
        else:
            st.session_state.demo_balance -= stake
        st.session_state.history.append({
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "result": demo_result,
            "stake": stake,
            "balance": st.session_state.demo_balance
        })
        if st.session_state.demo_balance <= 1000.0 - stop_loss:
            st.error("Your configured demo stop-loss has been reached. Stop testing and review the strategy.")
        st.rerun()
with col2:
    if st.button("Clear demo history", use_container_width=True):
        st.session_state.history = []
        st.session_state.demo_balance = 1000.0
        st.rerun()

if st.session_state.history:
    st.dataframe(st.session_state.history, use_container_width=True, hide_index=True)
    wins = sum(1 for x in st.session_state.history if x["result"] == "Win")
    total = len(st.session_state.history)
    x, y, z = st.columns(3)
    x.metric("Recorded demo trades", total)
    y.metric("Wins", wins)
    z.metric("Win rate", f"{wins / total * 100:.1f}%")
else:
    st.caption("No demo results recorded yet.")

st.divider()
st.markdown('<p class="small-note">BEASTMODE PRO • Prototype only • No financial advice • Use demo mode while testing.</p>', unsafe_allow_html=True)
