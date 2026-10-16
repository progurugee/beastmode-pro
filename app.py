import json
import time
from datetime import datetime
from collections import Counter

import numpy as np
import pandas as pd
import streamlit as st
import websocket

# ==========================================
# BEASTMODE PRO
# ==========================================

st.set_page_config(
    page_title="BEASTMODE PRO",
    page_icon="🦁",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background-color: #080d17;
    color: #f2f5fa;
}
[data-testid="stSidebar"] {
    background-color: #101827;
}
h1, h2, h3 {
    color: #f5b82e !important;
}
div[data-testid="stMetric"] {
    background: #111c2d;
    border: 1px solid #263650;
    padding: 14px;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# DERIV CONNECTION
# ==========================================

DERIV_APP_ID = 1089

DERIV_WS_URL = (
    f"wss://ws.derivws.com/websockets/v3"
    f"?app_id={DERIV_APP_ID}"
)

# ==========================================
# AVAILABLE MARKETS
# ==========================================

MARKETS = {
    "Volatility 10 Index": "R_10",
    "Volatility 25 Index": "R_25",
    "Volatility 50 Index": "R_50",
    "Volatility 75 Index": "R_75",
    "Volatility 100 Index": "R_100",
}

# ==========================================
# SESSION DATA
# ==========================================

if "market_data" not in st.session_state:
    st.session_state.market_data = {}

if "analysis_log" not in st.session_state:
    st.session_state.analysis_log = []

# ==========================================
# HEADER
# ==========================================

st.title("🦁 BEASTMODE PRO")

st.markdown(
    "**LIVE MARKET ANALYSIS** "
    "| SYNTHETIC INDICES | GOLD"
)

st.warning(
    "ANALYSIS ONLY: This application does not place trades. "
    "Market analysis cannot guarantee profitable results."
)

# ==========================================
# SIDEBAR
# ==========================================

st.sidebar.title("⚙️ CONTROL PANEL")

market = st.sidebar.selectbox(
    "Select Market",
    list(MARKETS.keys()) + ["Gold (XAU/USD)"]
)

tick_count = st.sidebar.slider(
    "Number of ticks to analyze",
    20,
    500,
    100,
    10
)

st.sidebar.markdown("---")
st.sidebar.caption("BEASTMODE PRO v2.1")

# ==========================================
# FETCH DERIV MARKET DATA
# ==========================================

def fetch_history(symbol, count):

    connection = None

    try:
        connection = websocket.create_connection(
            DERIV_WS_URL,
            timeout=15,
            origin="https://deriv.com"
        )

        connection.settimeout(12)

        request = {
            "ticks_history": symbol,
            "count": int(count),
            "end": "latest",
            "style": "ticks"
        }

        connection.send(json.dumps(request))

        deadline = time.time() + 12

        while time.time() < deadline:

            message = json.loads(connection.recv())

            if "error" in message:

                error_message = message["error"].get(
                    "message",
                    "Deriv API error"
                )

                raise RuntimeError(error_message)

            if "history" in message:

                prices = message["history"].get(
                    "prices",
                    []
                )

                times = message["history"].get(
                    "times",
                    []
                )

                if not prices:
                    raise RuntimeError(
                        "No prices were returned."
                    )

                return (
                    [float(price) for price in prices],
                    times
                )

        raise TimeoutError(
            "Deriv did not return data in time."
        )

    finally:

        if connection is not None:

            try:
                connection.close()
            except Exception:
                pass

# ==========================================
# LAST DIGIT ANALYSIS
# ==========================================

def get_last_digit(price):

    price_text = str(price)

    if "." in price_text:

        decimals = price_text.split(".", 1)[1]

        if decimals:
            return int(decimals[-1])

    return int(price_text[-1]) if price_text else 0

# ==========================================
# PRICE MOVEMENT SUMMARY
# ==========================================

def analyze_trend(prices):

    if len(prices) < 15:

        return (
            "INSUFFICIENT DATA",
            "Load at least 15 price observations."
        )

    numbers = np.asarray(
        prices,
        dtype=float
    )

    recent_average = np.mean(
        numbers[-5:]
    )

    previous_average = np.mean(
        numbers[-15:-5]
    )

    if recent_average > previous_average:

        return (
            "UPWARD MOMENTUM",
            "The recent average is higher than "
            "the previous average."
        )

    if recent_average < previous_average:

        return (
            "DOWNWARD MOMENTUM",
            "The recent average is lower than "
            "the previous average."
        )

    return (
        "NEUTRAL",
        "The averages are equal."
    )

# ==========================================
# MARKET DATA SECTION
# ==========================================

st.header("📡 MARKET DATA")

if market == "Gold (XAU/USD)":

    st.info(
        "Gold is included in this dashboard, but its live "
        "price feed is not connected yet. A supported data "
        "provider and confirmed Gold instrument symbol are "
        "required. No fake Gold prices will be displayed."
    )

    st.metric(
        "Gold Feed",
        "Not Connected"
    )

else:

    symbol = MARKETS[market]

    st.write("Selected Market:", market)

    st.caption(
        f"Deriv symbol: {symbol}"
    )

    if st.button(
        "🔄 REQUEST LIVE TICK DATA",
        use_container_width=True
    ):

        with st.spinner(
            "Connecting to Deriv..."
        ):

            try:

                prices, times = fetch_history(
                    symbol,
                    tick_count
                )

                st.session_state.market_data[market] = {
                    "prices": prices,
                    "times": times,
                    "updated": datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                }

                st.success(
                    f"Received {len(prices)} observations."
                )

            except Exception as error:

                st.error(
                    "LIVE CONNECTION FAILED: "
                    f"{type(error).__name__}: {error}"
                )

                st.info(
                    "No sample prices are substituted for "
                    "live data. If HTTP 520 continues, the "
                    "hosting network or WebSocket service "
                    "may be failing the connection."
                )

# ==========================================
# DASHBOARD
# ==========================================

st.divider()

st.header("📊 ANALYSIS DASHBOARD")

market_data = st.session_state.market_data.get(
    market
)

prices = (
    market_data["prices"]
    if market_data
    else []
)

latest_price = (
    prices[-1]
    if prices
    else None
)

last_updated = (
    market_data["updated"]
    if market_data
    else "Not available"
)

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Latest Price",
    f"{latest_price:.5f}"
    if latest_price is not None
    else "N/A"
)

col2.metric(
    "Ticks Loaded",
    len(prices)
)

col3.metric(
    "Feed Status",
    "Data Loaded"
    if prices
    else "Not Connected"
)

col4.metric(
    "Last Update",
    last_updated
)

# ==========================================
# DIGIT ANALYSIS
# ==========================================

if market != "Gold (XAU/USD)":

    st.divider()

    st.header("🔢 DIGIT ANALYSIS")

    if prices:

        digits = [
            get_last_digit(price)
            for price in prices
        ]

        digit_counts = Counter(digits)

        table = pd.DataFrame({
            "Digit": list(range(10)),
            "Count": [
                digit_counts.get(number, 0)
                for number in range(10)
            ]
        })

        table["Frequency %"] = (
            table["Count"] / len(digits) * 100
        ).round(2)

        even_percentage = (
            sum(digit % 2 == 0 for digit in digits)
            / len(digits) * 100
        )

        over_percentage = (
            sum(digit >= 5 for digit in digits)
            / len(digits) * 100
        )

        a, b, c, d = st.columns(4)

        a.metric(
            "EVEN",
            f"{even_percentage:.1f}%"
        )

        b.metric(
            "ODD",
            f"{100 - even_percentage:.1f}%"
        )

        c.metric(
            "OVER (5–9)",
            f"{over_percentage:.1f}%"
        )

        d.metric(
            "UNDER (0–4)",
            f"{100 - over_percentage:.1f}%"
        )

        st.subheader("Digit Frequency Chart")

        st.bar_chart(
            table.set_index("Digit")["Frequency %"]
        )

        st.subheader("Digit Statistics")

        st.dataframe(
            table,
            use_container_width=True,
            hide_index=True
        )

        st.caption(
            "These statistics describe the observed sample. "
            "They do not predict the next digit."
        )

        st.subheader("Recent Last Digits")

        st.code(
            " | ".join(
                str(digit)
                for digit in digits[-30:]
            )
        )

    else:

        st.info(
            "No live data loaded. Select a synthetic index "
            "and request live tick data."
        )

# ==========================================
# PRICE TREND ANALYSIS
# ==========================================

st.divider()

st.header("🧠 PRICE MOVEMENT ANALYSIS")

if prices:

    trend, explanation = analyze_trend(
        prices
    )

    st.subheader(trend)

    st.write(explanation)

else:

    st.info(
        "Price movement analysis will appear "
        "after market data is loaded."
    )

# ==========================================
# DEMO ANALYSIS LOG
# ==========================================

st.divider()

st.header("🧪 DEMO ANALYSIS LOG")

st.caption(
    "This records analysis only. "
    "It does not place broker orders."
)

if st.button("SAVE CURRENT ANALYSIS"):

    if prices:

        trend, explanation = analyze_trend(
            prices
        )

    else:

        trend = "NO DATA"

        explanation = (
            "No market observations loaded."
        )

    st.session_state.analysis_log.append({
        "Time": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "Market": market,
        "Ticks": len(prices),
        "Summary": trend,
        "Notes": explanation
    })

    st.success(
        "Analysis saved for this session."
    )

if st.session_state.analysis_log:

    st.dataframe(
        pd.DataFrame(
            st.session_state.analysis_log
        ),
        use_container_width=True,
        hide_index=True
    )

    if st.button("CLEAR ANALYSIS LOG"):

        st.session_state.analysis_log = []

        st.rerun()

# ==========================================
# FOOTER
# ==========================================

st.divider()

st.caption(
    "BEASTMODE PRO | Analysis prototype | "
    "No automatic trading | No guaranteed outcomes."
)
