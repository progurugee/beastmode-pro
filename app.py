import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timezone

try:
    import yfinance as yf
except Exception:
    yf = None

try:
    import plotly.graph_objects as go
except Exception:
    go = None


# ------------------------------------------------------------
# BEASTMODE AI - Dashboard prototype
# IMPORTANT: This app does NOT place live trades.
# Server-side MT5/Deriv execution must be integrated and tested
# before enabling real-money trading.
# ------------------------------------------------------------

st.set_page_config(
    page_title="BEASTMODE AI",
    page_icon="🐺",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp { background: #0b0d12; color: #f4f4f5; }
    [data-testid="stSidebar"] { background: #11141c; }
    h1, h2, h3 { color: #ffffff; }
    .hero {
        padding: 22px 24px;
        border: 1px solid #3a2028;
        border-left: 5px solid #e11d48;
        border-radius: 12px;
        background: linear-gradient(120deg, #17121a, #10131b);
        margin-bottom: 18px;
    }
    .hero-title { font-size: 32px; font-weight: 800; letter-spacing: 1px; }
    .hero-sub { color: #b9bec9; font-size: 14px; margin-top: 5px; }
    .metric-card {
        background: #141821;
        border: 1px solid #292e3a;
        border-radius: 12px;
        padding: 16px;
    }
    .muted { color: #9ca3af; }
    .warning-box {
        background: #291d11;
        border: 1px solid #8b5a20;
        border-radius: 10px;
        padding: 12px 14px;
        color: #fbd38d;
    }
    .danger-box {
        background: #2b141a;
        border: 1px solid #7f1d1d;
        border-radius: 10px;
        padding: 12px 14px;
        color: #fecaca;
    }
    div.stButton > button {
        border-radius: 8px;
        font-weight: 700;
        min-height: 42px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# State initialization
defaults = {
    "bot_running": False,
    "mt5_login": "",
    "mt5_server": "",
    "selected_market": "Volatility 100 Index",
    "lot_size": 0.01,
    "risk_per_trade": 1.0,
    "daily_loss_limit": 3.0,
    "max_open_positions": 1,
    "last_action": "No action taken yet",
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


def get_yahoo_data(symbol: str, period: str = "6mo", interval: str = "1d"):
    """Fetch reference market data. This is not a Deriv synthetic feed."""
    if yf is None:
        return None
    try:
        frame = yf.download(
            symbol,
            period=period,
            interval=interval,
            progress=False,
            auto_adjust=True,
            threads=False,
        )
        if frame is None or frame.empty:
            return None
        if isinstance(frame.columns, pd.MultiIndex):
            frame.columns = frame.columns.get_level_values(0)
        frame = frame.rename(columns=str.title)
        if "Close" not in frame.columns:
            return None
        frame = frame.dropna(subset=["Close"])
        return frame
    except Exception:
        return None


def calculate_reference_signal(frame: pd.DataFrame):
    """Basic SMA reference signal. It is not financial advice or an order."""
    if frame is None or len(frame) < 50:
        return "INSUFFICIENT DATA", None, None
    data = frame.copy()
    data["SMA50"] = data["Close"].rolling(50).mean()
    last_close = float(data["Close"].iloc[-1])
    last_sma = float(data["SMA50"].iloc[-1])
    if not np.isfinite(last_sma):
        return "INSUFFICIENT DATA", last_close, last_sma
    if last_close > last_sma:
        return "BULLISH BIAS", last_close, last_sma
    if last_close < last_sma:
        return "BEARISH BIAS", last_close, last_sma
    return "NEUTRAL", last_close, last_sma


def money(value):
    try:
        return f"R {float(value):,.2f}"
    except (TypeError, ValueError):
        return "—"


# Sidebar
with st.sidebar:
    st.markdown("## 🐺 BEASTMODE AI")
    st.caption("Trading dashboard prototype")
    page = st.radio(
        "MENU",
        [
            "Trading Dashboard",
            "Strategy Engine",
            "Account Connection",
            "Trade History",
            "Risk Management",
        ],
        label_visibility="collapsed",
    )
    st.divider()
    st.markdown("**Engine status**")
    if st.session_state.bot_running:
        st.success("START requested")
    else:
        st.info("STOPPED")
    st.caption("No live orders are sent by this prototype.")


# Header
st.markdown(
    """
    <div class="hero">
      <div class="hero-title">BEASTMODE <span style="color:#fb3159;">AI</span></div>
      <div class="hero-sub">Strategy monitoring • Risk controls • Account setup</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="warning-box"><b>Prototype notice:</b> START/STOP only changes the dashboard status. '
    'This version does not connect to a Deriv MT5 account or execute trades. Do not treat signals as guaranteed profits.</div>',
    unsafe_allow_html=True,
)
st.write("")


if page == "Trading Dashboard":
    st.subheader("Trading Dashboard")
    left, middle, right = st.columns(3)
    with left:
        st.metric("Bot status", "START REQUESTED" if st.session_state.bot_running else "STOPPED")
    with middle:
        st.metric("Selected market", st.session_state.selected_market)
    with right:
        st.metric("Configured lot size", f"{st.session_state.lot_size:.2f}")

    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("### Engine controls")
        st.caption("These controls are for the interface prototype only.")
        start_col, stop_col = st.columns(2)
        with start_col:
            if st.button("▶ START", type="primary", use_container_width=True):
                st.session_state.bot_running = True
                st.session_state.last_action = f"START requested at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                st.rerun()
        with stop_col:
            if st.button("■ STOP", use_container_width=True):
                st.session_state.bot_running = False
                st.session_state.last_action = f"STOP requested at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                st.rerun()
        st.write("**Last action:**", st.session_state.last_action)

    with col2:
        st.markdown("### Account overview")
        if st.session_state.mt5_login and st.session_state.mt5_server:
            st.write("MT5 login:", st.session_state.mt5_login)
            st.write("Server:", st.session_state.mt5_server)
            st.caption("Details are only stored in this app session; no account authentication is performed.")
        else:
            st.info("No MT5 account details configured. Open **Account Connection** to enter the non-secret account details.")
        st.write("Account balance: —")
        st.write("Open positions: —")
        st.caption("Live balance and positions require a working, authenticated trading integration.")

    st.markdown("### Market watch")
    market_options = {
        "EUR/USD": "EURUSD=X",
        "GBP/USD": "GBPUSD=X",
        "USD/JPY": "JPY=X",
        "Gold (XAU/USD)": "GC=F",
        "S&P 500": "^GSPC",
        "Nasdaq 100": "^NDX",
    }
    chosen = st.selectbox("Reference market data", list(market_options.keys()))
    frame = get_yahoo_data(market_options[chosen], period="6mo", interval="1d")
    if frame is not None and not frame.empty:
        signal, last_close, last_sma = calculate_reference_signal(frame)
        a, b, c = st.columns(3)
        a.metric("Latest close", f"{last_close:,.4f}" if last_close is not None else "—")
        b.metric("SMA 50", f"{last_sma:,.4f}" if last_sma is not None else "—")
        c.metric("Reference bias", signal)
        if go is not None:
            plot_data = frame.copy()
            plot_data["SMA50"] = plot_data["Close"].rolling(50).mean()
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=plot_data.index, y=plot_data["Close"], name="Close"))
            fig.add_trace(go.Scatter(x=plot_data.index, y=plot_data["SMA50"], name="SMA 50"))
            fig.update_layout(
                template="plotly_dark",
                height=380,
                margin=dict(l=10, r=10, t=30, b=10),
                legend=dict(orientation="h"),
            )
            st.plotly_chart(fig, use_container_width=True)
        st.caption("Reference data is sourced through Yahoo Finance and may be delayed. It is not Deriv synthetic-index data.")
    else:
        st.info("Reference data is currently unavailable. Check the app's internet access or try again later.")

elif page == "Strategy Engine":
    st.subheader("Strategy Engine")
    st.markdown("### Strategy configuration")
    st.write("Strategy concept: multi-timeframe moving-average trend confirmation.")
    st.markdown(
        """
        **Reference rules**
        - Bullish bias: H1 close above its SMA 50 and M5, M15, and M30 closes above their respective SMA 50.
        - Bearish bias: H1 close below its SMA 50 and M5, M15, and M30 closes below their respective SMA 50.
        - Otherwise: no aligned signal.
        """
    )
    st.warning(
        "This page documents the intended strategy. The current prototype does not fetch Deriv MT5 multi-timeframe candles, "
        "does not calculate a complete live entry signal, and does not place orders."
    )
    st.markdown("### Market selection")
    st.session_state.selected_market = st.selectbox(
        "Synthetic index to configure",
        [
            "Volatility 10 Index",
            "Volatility 25 Index",
            "Volatility 50 Index",
            "Volatility 75 Index",
            "Volatility 100 Index",
            "Boom 500 Index",
            "Boom 1000 Index",
            "Crash 500 Index",
            "Crash 1000 Index",
            "Step Index",
        ],
        index=[
            "Volatility 10 Index",
            "Volatility 25 Index",
            "Volatility 50 Index",
            "Volatility 75 Index",
            "Volatility 100 Index",
            "Boom 500 Index",
            "Boom 1000 Index",
            "Crash 500 Index",
            "Crash 1000 Index",
            "Step Index",
        ].index(st.session_state.selected_market)
        if st.session_state.selected_market in [
            "Volatility 10 Index",
            "Volatility 25 Index",
            "Volatility 50 Index",
            "Volatility 75 Index",
            "Volatility 100 Index",
            "Boom 500 Index",
            "Boom 1000 Index",
            "Crash 500 Index",
            "Crash 1000 Index",
            "Step Index",
        ] else 4,
    )
    st.caption(f"Configured market: {st.session_state.selected_market}")
    st.markdown("### Trade parameters")
    p1, p2, p3 = st.columns(3)
    with p1:
        st.session_state.lot_size = st.number_input(
            "Lot size", min_value=0.01, max_value=100.0,
            value=float(st.session_state.lot_size), step=0.01, format="%.2f"
        )
    with p2:
        st.number_input("Stop loss (points)", min_value=1, max_value=100000, value=500, step=50)
    with p3:
        st.number_input("Take profit (points)", min_value=1, max_value=100000, value=1500, step=50)
    st.caption("These are configuration values only; they are not sent to a broker.")

elif page == "Account Connection":
    st.subheader("Account Connection")
    st.markdown("### Connect Deriv MT5 account")
    st.write("Enter non-secret account details to prepare the interface. This prototype does not authenticate or connect to MT5.")
    with st.form("account_form"):
        login = st.text_input("MT5 account login", value=st.session_state.mt5_login, placeholder="Enter your MT5 login number")
        server = st.text_input("MT5 server name", value=st.session_state.mt5_server, placeholder="Use the exact server name shown by Deriv")
        submitted = st.form_submit_button("Save account details", type="primary")
        if submitted:
            st.session_state.mt5_login = login.strip()
            st.session_state.mt5_server = server.strip()
            st.success("Account details saved for this session. No connection has been made.")
    st.markdown("### Before real trading can be enabled")
    st.markdown(
        """
        1. Confirm a supported, authorized server-side MT5 integration.
        2. Implement secure authentication and secret storage; never put account passwords in source code.
        3. Test with a demo account first.
        4. Add server-side order validation, trade-result handling, logs, and emergency stop controls.
        """
    )
    st.error("Do not enter your MT5 password on this prototype. Passwords are not requested or stored here.")

elif page == "Trade History":
    st.subheader("Trade History")
    st.info("No live trade history is available because broker execution has not been connected.")
    sample = pd.DataFrame(columns=["Time", "Market", "Direction", "Volume", "Entry", "Exit", "P/L", "Status"])
    st.dataframe(sample, use_container_width=True, hide_index=True)
    st.caption("Once an authorized trading integration exists, this page can display verified broker trade records.")

elif page == "Risk Management":
    st.subheader("Risk Management")
    st.markdown("### Configure risk limits")
    c1, c2 = st.columns(2)
    with c1:
        st.session_state.risk_per_trade = st.slider(
            "Risk per trade (%)", min_value=0.1, max_value=5.0,
            value=float(st.session_state.risk_per_trade), step=0.1
        )
        st.session_state.daily_loss_limit = st.slider(
            "Daily loss limit (%)", min_value=0.5, max_value=10.0,
            value=float(st.session_state.daily_loss_limit), step=0.5
        )
    with c2:
        st.session_state.max_open_positions = st.number_input(
            "Maximum open positions", min_value=1, max_value=20,
            value=int(st.session_state.max_open_positions), step=1
        )
        st.metric("Configured risk per trade", f"{st.session_state.risk_per_trade:.1f}%")
        st.metric("Configured daily loss limit", f"{st.session_state.daily_loss_limit:.1f}%")
        st.metric("Configured position limit", int(st.session_state.max_open_positions))
    st.warning(
        "Risk settings are currently saved only in the app session. They do not enforce real broker-side limits until "
        "the trading engine and order execution integration are implemented."
    )

st.divider()
st.caption(
    f"BEASTMODE AI • Prototype build • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} • "
    "Trading involves risk; no profit is guaranteed."
)
