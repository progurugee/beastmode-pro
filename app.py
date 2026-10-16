import streamlit as st
import pandas as pd
import numpy as np
import json
import websocket
import threading
import time
from collections import Counter, deque
from datetime import datetime

# ============================================================
# BEASTMODE PRO | LIVE MARKET ANALYSIS DASHBOARD
# ============================================================

st.set_page_config(
    page_title="BEASTMODE PRO",
    page_icon="🦁",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.stApp {
    background: #080d17;
    color: #f2f5fa;
}
[data-testid="stSidebar"] {
    background: #101827;
}
h1, h2, h3 {
    color: #f5b82e !important;
}
.metric-card {
    background: #111c2d;
    border: 1px solid #263650;
    border-radius: 12px;
    padding: 18px;
    margin-bottom: 10px;
}
.small-text {
    color: #a7b5c9;
    font-size: 13px;
}
.signal-box {
    background: #142238;
    border-left: 4px solid #f5b82e;
    padding: 15px;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# SESSION STATE
# ------------------------------------------------------------

if "ticks" not in st.session_state:
    st.session_state.ticks = {}

if "prices" not in st.session_state:
    st.session_state.prices = {}

if "demo_log" not in st.session_state:
    st.session_state.demo_log = []

if "last_update" not in st.session_state:
    st.session_state.last_update = None

# ------------------------------------------------------------
# MARKET DEFINITIONS
# ------------------------------------------------------------

DERIV_MARKETS = {
    "Volatility 10 Index": "R_10",
    "Volatility 25 Index": "R_25",
    "Volatility 50 Index": "R_50",
    "Volatility 75 Index": "R_75",
    "Volatility 100 Index": "R_100",
}

# Gold may not be available through the same public tick feed.
GOLD_SYMBOLS = ["XAUUSD", "frxXAUUSD"]

# ------------------------------------------------------------
# HEADER
# ------------------------------------------------------------

st.title("🦁 BEASTMODE PRO")
st.markdown(
    "**MULTI-MARKET ANALYSIS SYSTEM**  |  "
    "SYNTHETIC INDICES • GOLD • DEMO SIGNALS"
)

st.warning(
    "ANALYSIS ONLY: This application does not place trades. "
    "Signals are educational estimates, not guaranteed predictions."
)

# ------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------

st.sidebar.title("⚙️ CONTROL PANEL")

market_choice = st.sidebar.selectbox(
    "Choose Market",
    list(DERIV_MARKETS.keys()) + ["GOLD (XAU/USD)"]
)

mode = st.sidebar.selectbox(
    "Analysis Mode",
    ["Live Data", "Analyze Saved Data"]
)

window_size = st.sidebar.slider(
    "Analysis Window (ticks)",
    min_value=20,
    max_value=500,
    value=100,
    step=10
)

st.sidebar.markdown("---")
st.sidebar.caption("BEASTMODE PRO v2.0")
st.sidebar.caption("Live data requires a working market feed.")

# ------------------------------------------------------------
# DERIV PUBLIC WEBSOCKET
# ------------------------------------------------------------

APP_ID = 1089
DERIV_WS_URL = f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}"


def digit_from_quote(quote):
    """
    Extract the final displayed decimal digit.
    This is a basic digit-analysis method.
    """
    text = str(quote)

    if "." in text:
        decimals = text.split(".")[1]
        if decimals:
            return int(decimals[-1])

    return int(text[-1]) if text else 0


def load_saved_data():
    return st.session_state.ticks.get(market_choice, [])


def analyze_digits(values):
    if not values:
        return None

    digits = [digit_from_quote(v) for v in values]
    counts = Counter(digits)
    total = len(digits)

    table = pd.DataFrame({
        "Digit": list(range(10)),
        "Count": [counts.get(i, 0) for i in range(10)]
    })

    table["Frequency %"] = (
        table["Count"] / total * 100
    ).round(2)

    even_count = sum(1 for d in digits if d % 2 == 0)
    odd_count = total - even_count

    over_count = sum(1 for d in digits if d >= 5)
    under_count = total - over_count

    return {
        "digits": digits,
        "table": table,
        "total": total,
        "even": even_count / total * 100,
        "odd": odd_count / total * 100,
        "over": over_count / total * 100,
        "under": under_count / total * 100,
        "counts": counts,
    }


def make_demo_signal(values):
    """
    A simple descriptive signal based on recent price movement.
    It is NOT a validated predictive model.
    """
    if len(values) < 15:
        return "WAIT", "Not enough observations for analysis."

    numbers = np.array(values, dtype=float)

    recent = numbers[-5:]
    previous = numbers[-15:-5]

    recent_mean = np.mean(recent)
    previous_mean = np.mean(previous)

    if recent_mean > previous_mean:
        return "UPWARD MOMENTUM", (
            "Recent prices average higher than the previous sample. "
            "This is not a buy recommendation."
        )

    if recent_mean < previous_mean:
        return "DOWNWARD MOMENTUM", (
            "Recent prices average lower than the previous sample. "
            "This is not a sell recommendation."
        )

    return "NEUTRAL", "No clear average-price difference in this sample."


# ------------------------------------------------------------
# LIVE CONNECTION
# ------------------------------------------------------------

st.subheader("📡 Market Data")

if market_choice == "GOLD (XAU/USD)":
    st.info(
        "Gold requires a compatible live data provider or a Deriv feed "
        "that offers the instrument. This prototype does not assume "
        "that XAU/USD is available from the synthetic-index feed."
    )

    gold_provider = st.selectbox(
        "Gold data status",
        [
            "Not connected",
            "I have a compatible provider"
        ]
    )

    st.metric("Gold feed", gold_provider)

    st.write(
        "To display real Gold prices, the app must be connected to "
        "a supported Gold market-data source. No fake live price is shown."
    )

else:
    symbol = DERIV_MARKETS[market_choice]

    st.write(f"Selected market: **{market_choice}**")
    st.code(f"Deriv symbol: {symbol}")

    st.info(
        "Use the connection control below to request a one-time snapshot "
        "from Deriv's public market feed."
    )

    if st.button("🔄 Request Live Tick Snapshot", use_container_width=True):
        status = st.empty()

        try:
            ws = websocket.create_connection(
                DERIV_WS_URL,
                timeout=12
            )

            ws.send(json.dumps({
                "ticks_history": symbol,
                "count": window_size,
                "end": "latest",
                "style": "ticks"
            }))

            received = False
            start = time.time()

            while time.time() - start < 10:
                raw = ws.recv()
                data = json.loads(raw)

                if "error" in data:
                    raise RuntimeError(
                        data["error"].get("message", "Deriv API error")
                    )

                if "history" in data:
                    prices = data["history"].get("prices", [])

                    st.session_state.ticks[market_choice] = [
                        float(p) for p in prices
                    ]

                    st.session_state.prices[market_choice] = (
                        float(prices[-1]) if prices else None
                    )

                    st.session_state.last_update = datetime.now()
                    received = True
                    break

            ws.close()

            if received:
                status.success(
                    f"Received {len(prices)} observations from Deriv."
                )
            else:
                status.warning("No market data returned. Try again.")

        except Exception as e:
            status.error(
                "Unable to connect to Deriv right now. "
                f"Details: {e}"
            )

# ------------------------------------------------------------
# CURRENT DATA
# ------------------------------------------------------------

st.markdown("---")
st.subheader("📊 Analysis Dashboard")

values = load_saved_data()

if market_choice in st.session_state.prices:
    current_price = st.session_state.prices[market_choice]
else:
    current_price = None

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Latest Price",
    f"{current_price:.5f}" if current_price is not None else "N/A"
)

col2.metric(
    "Observations",
    len(values)
)

col3.metric(
    "Data Status",
    "Connected" if values else "Waiting"
)

col4.metric(
    "Last Update",
    st.session_state.last_update.strftime("%H:%M:%S")
    if st.session_state.last_update else "N/A"
)

# ------------------------------------------------------------
# SYNTHETIC DIGIT ANALYSIS
# ------------------------------------------------------------

if market_choice != "GOLD (XAU/USD)":
    st.markdown("---")
    st.subheader("🔢 Digit Frequency Analysis")

    if values:
        analysis = analyze_digits(values)

        a, b, c, d = st.columns(4)

        a.metric("Even Digits", f"{analysis['even']:.1f}%")
        b.metric("Odd Digits", f"{analysis['odd']:.1f}%")
        c.metric("Over (5–9)", f"{analysis['over']:.1f}%")
        d.metric("Under (0–4)", f"{analysis['under']:.1f}%")

        st.write("### Digit Distribution")

        st.bar_chart(
            analysis["table"].set_index("Digit")["Frequency %"]
        )

        st.dataframe(
            analysis["table"],
            use_container_width=True,
            hide_index=True
        )

        st.write("### Recent Last Digits")

        recent_digits = analysis["digits"][-30:]

        digit_text = "  •  ".join(
            str(digit) for digit in recent_digits
        )

        st.code(digit_text)

        st.caption(
            "Digit frequencies describe the observed sample. "
            "They do not establish the probability of the next digit."
        )

    else:
        st.info(
            "No observations loaded yet. Choose a synthetic index "
            "and request a live tick snapshot."
        )

# ------------------------------------------------------------
# GOLD TECHNICAL ANALYSIS
# ------------------------------------------------------------

else:
    st.markdown("---")
    st.subheader("🥇 GOLD Technical Analysis")
st.write(
    "Once a supported Gold data source is connected, this section "
    "can display moving averages, RSI, volatility and price charts."
)
