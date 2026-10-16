import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime

# ==========================================================
# BEASTMODE AI — TRADING DASHBOARD PROTOTYPE
# DESPERADO-INSPIRED MULTI-TIMEFRAME STRATEGY
# ==========================================================

st.set_page_config(
    page_title="BEASTMODE AI",
    page_icon="🐺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------- DESIGN ------------------------------

st.markdown("""
<style>
.stApp {
    background: #080b12;
    color: #ffffff;
}
[data-testid="stSidebar"] {
    background: #101522;
}
h1, h2, h3 {
    color: #ff3030;
}
div.stButton > button {
    width: 100%;
    border-radius: 8px;
    font-weight: bold;
    min-height: 45px;
}
.status-box {
    background: #111827;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #293347;
    margin-bottom: 10px;
}
.small-note {
    color: #a8b3c7;
    font-size: 13px;
}
</style>
""", unsafe_allow_html=True)

# -------------------- SESSION STATE -----------------------

if "bot_running" not in st.session_state:
    st.session_state.bot_running = False

if "connected" not in st.session_state:
    st.session_state.connected = False

if "trade_history" not in st.session_state:
    st.session_state.trade_history = []

# -------------------- HEADER --------------------------------

st.markdown("# 🐺 BEASTMODE AI")
st.markdown("### AUTOMATED TRADING INTELLIGENCE")
st.caption("DESPERADO-inspired strategy | Dashboard prototype")

st.divider()

# -------------------- SIDEBAR -------------------------------

st.sidebar.markdown("# 🐺 BEASTMODE")
st.sidebar.caption("CONTROL CENTRE")

page = st.sidebar.radio(
    "MENU",
    [
        "Trading Dashboard",
        "Strategy Engine",
        "Account Connection",
        "Trade History",
        "Risk Management"
    ]
)

st.sidebar.divider()
st.sidebar.markdown("### SYSTEM STATUS")

if st.session_state.bot_running:
    st.sidebar.success("BOT STATUS: RUNNING")
else:
    st.sidebar.warning("BOT STATUS: STOPPED")

if st.session_state.connected:
    st.sidebar.success("ACCOUNT: DEMO CONNECTION")
else:
    st.sidebar.info("ACCOUNT: NOT CONNECTED")

st.sidebar.caption("Live trading is not enabled in this prototype.")

# -------------------- MARKET DATA ---------------------------

MARKETS = {
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "JPY=X",
    "Gold": "GC=F",
    "Nasdaq 100": "NQ=F",
    "S&P 500": "^GSPC"
}

SYNTHETIC_MARKETS = [
    "Volatility 10 Index",
    "Volatility 25 Index",
    "Volatility 50 Index",
    "Volatility 75 Index",
    "Volatility 100 Index",
    "Boom 500 Index",
    "Crash 500 Index",
    "Step Index"
]


@st.cache_data(ttl=60)
def get_market_data(symbol):
    try:
        data = yf.download(
            symbol,
            period="5d",
            interval="5m",
            progress=False,
            auto_adjust=True
        )

        if data is None or data.empty:
            return pd.DataFrame()

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        return data.dropna()

    except Exception:
        return pd.DataFrame()


def analyse_strategy(data):
    """
    Educational implementation of the DESPERADO-inspired
    moving-average strategy.

    This uses one downloaded timeframe, not actual Deriv
    multi-timeframe execution or live trading.
    """

    if data.empty or len(data) < 60:
        return {
            "signal": "INSUFFICIENT DATA",
            "price": None,
            "ma": None
        }

    close = data["Close"].astype(float)
    ma = close.rolling(50).mean()

    price = float(close.iloc[-1])
    average = float(ma.iloc[-1])

    if pd.isna(average):
        signal = "INSUFFICIENT DATA"
    elif price > average:
        signal = "BULLISH BIAS"
    elif price < average:
        signal = "BEARISH BIAS"
    else:
        signal = "NO CLEAR BIAS"

    return {
        "signal": signal,
        "price": price,
        "ma": average
    }


# -------------------- DASHBOARD PAGE -----------------------

if page == "Trading Dashboard":

    left, right = st.columns([2, 1])

    with left:
        selected_market = st.selectbox(
            "SELECT MARKET",
            list(MARKETS.keys()) + SYNTHETIC_MARKETS
        )

    with right:
        trade_size = st.number_input(
            "TRADE SIZE (DISPLAY ONLY)",
            min_value=0.01,
            max_value=100.0,
            value=0.01,
            step=0.01
        )

    if selected_market in MARKETS:
        data = get_market_data(MARKETS[selected_market])
    else:
        data = pd.DataFrame()

    st.divider()

    # Strategy analysis
    analysis = analyse_strategy(data)

    col1, col2, col3 = st.columns(3)

    with col1:
        if analysis["price"] is not None:
            st.metric(
                "LATEST REFERENCE PRICE",
                f'{analysis["price"]:.5f}'
            )
        else:
            st.metric("LATEST REFERENCE PRICE", "Unavailable")

    with col2:
        st.metric("STRATEGY BIAS", analysis["signal"])

    with col3:
        st.metric(
            "BOT STATUS",
            "RUNNING" if st.session_state.bot_running else "STOPPED"
        )

    # Chart
    st.markdown("### 📊 MARKET CHART")

    if not data.empty:
        chart = go.Figure()

        chart.add_trace(go.Candlestick(
            x=data.index,
            open=data["Open"],
            high=data["High"],
            low=data["Low"],
            close=data["Close"],
            name=selected_market
        ))

        chart.add_trace(go.Scatter(
            x=data.index,
            y=data["Close"].rolling(50).mean(),
            name="50-Period Moving Average",
            line=dict(width=2)
        ))

        chart.update_layout(
            template="plotly_dark",
            height=480,
            xaxis_rangeslider_visible=False,
            margin=dict(l=10, r=10, t=30, b=10)
        )

        st.plotly_chart(chart, use_container_width=True)

    else:
        st.warning(
            "Reference data is unavailable for this market. "
            "Synthetic-index prices are not being retrieved "
            "from Deriv in this prototype."
        )

    st.divider()

    # Start and stop controls
    st.markdown("### 🎮 BOT CONTROL")

    start_col, stop_col = st.columns(2)

    with start_col:
        if st.button("▶ START BOT", type="primary"):
            if not st.session_state.connected:
                st.error(
                    "Connect a demo account before starting. "
                    "The connection feature is currently a prototype."
                )
            else:
                st.session_state.bot_running = True
                st.warning(
                    "Prototype started. No real trades are being placed."
                )
                st.rerun()

    with stop_col:
        if st.button("⏹ STOP BOT"):
            st.session_state.bot_running = False
            st.success("Prototype stopped.")
            st.rerun()

    st.info(
        "Starting this prototype does not execute trades. "
        "Live execution requires a verified trading connection."
    )


# -------------------- STRATEGY ENGINE -----------------------

elif page == "Strategy Engine":

    st.markdown("## 🧠 BEASTMODE STRATEGY ENGINE")

    st.write(
        "The initial strategy is inspired by your DESPERADO "
        "Expert Advisor. It uses trend direction and moving-average "
        "confirmation as the starting point."
    )

    st.markdown("### Strategy configuration")

    trend_period = st.number_input(
        "Trend moving-average period",
        min_value=5,
        max_value=300,
        value=50
    )

    signal_period = st.number_input(
        "Signal moving-average period",
        min_value=5,
        max_value=300,
        value=50
    )

    st.write("**Higher timeframe:** H1")
    st.write("**Signal timeframes:** M5, M15, M30")
    st.write("**Signal type:** Trend-following")

    st.warning(
        "The settings above describe the intended strategy. "
        "A complete multi-timeframe engine has not yet been implemented."
    )

    st.markdown("### Signal rules")

    st.markdown("""
    - BUY candidates: higher-timeframe trend is bullish and
      lower timeframes confirm bullish conditions.
    - SELL candidates: higher-timeframe trend is bearish and
      lower timeframes confirm bearish conditions.
    - Otherwise: wait for a clearer setup.
    - Risk checks must pass before any real order is sent.
    """)


# -------------------- ACCOUNT CONNECTION --------------------

elif page == "Account Connection":

    st.markdown("## 🔌 CONNECT DERIV MT5 ACCOUNT")

    st.warning(
        "This form is a prototype only. It does not authenticate "
        "with Deriv or connect to an MT5 trading server."
    )

    st.markdown("### Account details")

    st.text_input(
        "MT5 LOGIN NUMBER",
        placeholder="Enter your demo MT5 login"
    )

    st.text_input(
        "MT5 SERVER",
        placeholder="Enter the exact server name"
    )

    st.selectbox(
        "ACCOUNT TYPE",
        ["Demo"]
    )

    st.info(
        "Do not enter your trading password here. "
        "Secure authentication and server-side MT5 connectivity "
        "must be implemented before account credentials are accepted."
    )

    if st.button("VERIFY DEMO CONNECTION"):
        st.error(
            "Connection is not implemented yet. "
            "No account has been connected."
        )


# -------------------- TRADE HISTORY -------------------------

elif page == "Trade History":

    st.markdown("## 📜 TRADE HISTORY")

    st.info(
        "No live trading history is available because "
        "this prototype does not execute trades."
    )

    if st.session_state.trade_history:
        st.dataframe(
            pd.DataFrame(st.session_state.trade_history),
            use_container_width=True
        )
    else:
        st.write("No trades recorded.")


# -------------------- RISK MANAGEMENT -----------------------

elif page == "Risk Management":

    st.markdown("## 🛡️ RISK MANAGEMENT")

    st.write(
        "These are configuration values for the planned trading engine. "
        "They do not currently control real trades."
    )

    lot_size = st.number_input(
        "Default lot size (MT5 only)",
        min_value=0.01,
        max_value=10.0,
        value=0.01,
        step=0.01
    )

    max_daily_loss = st.number_input(
        "Maximum daily loss (%)",
        min_value=1.0,
        max_value=50.0,
        value=3.0,
        step=0.5
    )

    max_open_positions = st.number_input(
        "Maximum open positions",
        min_value=1,
        max_value=20,
        value=1
    )

    st.write(f"Configured MT
