import json
import time
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st
import websocket


# =========================================================
# BEASTMODE PRO
# Live market data diagnostic dashboard
# =========================================================

st.set_page_config(
    page_title="BEASTMODE PRO",
    page_icon="🐺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------------
# Configuration
# -------------------------

DERIV_APP_ID = 1089

DERIV_WS_URL = (
    f"wss://ws.derivws.com/websockets/v3"
    f"?app_id={DERIV_APP_ID}"
)

MARKETS = {
    "Volatility 10 Index": "R_10",
    "Volatility 25 Index": "R_25",
    "Volatility 50 Index": "R_50",
    "Volatility 75 Index": "R_75",
    "Volatility 100 Index": "R_100",
}


# -------------------------
# Styling
# -------------------------

st.markdown(
    """
    <style>
    .stApp {
        background-color: #080d18;
        color: #f3f6fc;
    }

    [data-testid="stSidebar"] {
        background-color: #101827;
    }

    .hero {
        padding: 24px;
        border-radius: 16px;
        background: linear-gradient(120deg, #13233d, #172d26);
        border: 1px solid #30415c;
        margin-bottom: 20px;
    }

    .hero h1 {
        margin: 0;
        color: #ffffff;
        font-size: 34px;
    }

    .hero p {
        color: #a8b8ce;
        margin-bottom: 0;
    }

    .metric-card {
        padding: 18px;
        background-color: #111b2b;
        border: 1px solid #28364b;
        border-radius: 12px;
        margin-bottom: 10px;
    }

    .metric-label {
        color: #9aaec7;
        font-size: 13px;
    }

    .metric-value {
        color: #ffffff;
        font-size: 24px;
        font-weight: bold;
    }

    .small-note {
        color: #9aaec7;
        font-size: 13px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -------------------------
# Header
# -------------------------

st.markdown(
    """
    <div class="hero">
        <h1>🐺 BEASTMODE PRO</h1>
        <p>
            Market data • Digit analysis • Historical statistics
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# -------------------------
# Connection functions
# -------------------------

def fetch_history(symbol, count=500):
    """
    Connect to Deriv and request historical tick data.

    Returns:
        Dictionary containing prices and diagnostic details.
    """

    ws = None
    started = time.time()

    try:
        ws = websocket.create_connection(
            DERIV_WS_URL,
            timeout=20,
            origin="https://deriv.com",
        )

        request = {
            "ticks_history": symbol,
            "count": int(count),
            "end": "latest",
            "style": "ticks",
            "req_id": 1,
        }

        ws.send(json.dumps(request))

        while time.time() - started < 25:
            raw_response = ws.recv()

            if not raw_response:
                continue

            response = json.loads(raw_response)

            if response.get("error"):
                error = response["error"]

                return {
                    "ok": False,
                    "error": (
                        f"Deriv API error: "
                        f"{error.get('code', 'Unknown')}: "
                        f"{error.get('message', 'Unknown error')}"
                    ),
                }

            if "history" in response:
                history = response["history"]

                prices = history.get("prices", [])
                times = history.get("times", [])

                if not prices:
                    return {
                        "ok": False,
                        "error": (
                            "Deriv connected, but no tick prices "
                            "were returned for this request."
                        ),
                    }

                return {
                    "ok": True,
                    "prices": prices,
                    "times": times,
                    "symbol": symbol,
                    "received": len(prices),
                }

        return {
            "ok": False,
            "error": (
                "The connection opened, but no usable history "
                "response arrived before the timeout."
            ),
        }

    except websocket.WebSocketBadStatusException as exc:
        status = getattr(exc, "status_code", "unknown")

        return {
            "ok": False,
            "error": (
                f"WebSocket handshake rejected. "
                f"HTTP status: {status}. "
                "The connection did not reach the data request."
            ),
        }

    except websocket.WebSocketTimeoutException:
        return {
            "ok": False,
            "error": (
                "Connection timed out. Check the network "
                "or the availability of the Deriv WebSocket service."
            ),
        }

    except Exception as exc:
        return {
            "ok": False,
            "error": (
                f"{type(exc).__name__}: {str(exc)[:500]}"
            ),
        }

    finally:
        if ws is not None:
            try:
                ws.close()
            except Exception:
                pass


# -------------------------
# Analysis
# -------------------------

def analyze_prices(prices):
    """Calculate descriptive statistics from received prices."""

    values = pd.to_numeric(
        pd.Series(prices),
        errors="coerce",
    ).dropna()

    if values.empty:
        return None

    latest = float(values.iloc[-1])

    previous = (
        float(values.iloc[-2])
        if len(values) > 1
        else latest
    )

    if latest > previous:
        movement = "UP"
    elif latest < previous:
        movement = "DOWN"
    else:
        movement = "UNCHANGED"

    digits = (
        values.astype(str)
        .str.replace(".", "", regex=False)
        .str.replace("-", "", regex=False)
        .str[-1:]
    )

    digits = pd.to_numeric(
        digits,
        errors="coerce",
    ).dropna().astype(int)

    distribution = (
        digits.value_counts()
        .reindex(range(10), fill_value=0)
        .sort_index()
    )

    percentages = (
        distribution / max(len(digits), 1) * 100
    )

    digit_table = pd.DataFrame({
        "Digit": range(10),
        "Count": distribution.values,
        "Percentage": percentages.values.round(2),
    })

    average = float(values.mean())

    if len(values) >= 20:
        recent_average = float(values.tail(20).mean())
    else:
        recent_average = average

    if recent_average > average:
        trend = "Recent average above overall average"
    elif recent_average < average:
        trend = "Recent average below overall average"
    else:
        trend = "Averages are equal"

    return {
        "latest": latest,
        "previous": previous,
        "movement": movement,
        "average": average,
        "trend": trend,
        "digit_table": digit_table,
        "count": len(values),
    }


# -------------------------
# Sidebar
# -------------------------

st.sidebar.title("🐺 BEASTMODE PRO")

selected_market = st.sidebar.selectbox(
    "Select Synthetic Market",
    list(MARKETS.keys()),
)

tick_count = st.sidebar.select_slider(
    "Historical tick count",
    options=[100, 250, 500, 750, 1000],
    value=500,
)

st.sidebar.markdown("---")

st.sidebar.write("**Available markets**")

for market_name in MARKETS:
    st.sidebar.write(f"• {market_name}")

st.sidebar.markdown("---")

st.sidebar.caption(
    "Gold (XAU/USD) is not connected in this version."
)

st.sidebar.caption(
    "This dashboard does not execute trades."
)


# -------------------------
# Main controls
# -------------------------

st.subheader(selected_market)

st.caption(
    f"Deriv symbol: `{MARKETS[selected_market]}`"
)

col1, col2 = st.columns(2)

with col1:
    request_data = st.button(
        "📡 REQUEST LIVE TICK DATA",
        type="primary",
        use_container_width=True,
    )

with col2:
    test_connection = st.button(
        "🔌 TEST CONNECTION",
        use_container_width=True,
    )


# -------------------------
# Connection test
# -------------------------

if test_connection:
    st.info("Testing the Deriv WebSocket connection...")

    test_result = fetch_history(
        MARKETS[selected_market],
        count=10,
    )

    if test_result["ok"]:
        st.success(
            "Connection successful! Deriv returned "
            f"{test_result['received']} ticks."
        )

        st.write(
            "Latest received price:",
            test_result["prices"][-1],
        )

    else:
        st.error("Connection test failed.")

        st.code(
            test_result["error"],
            language=None,
        )

        st.warning(
            "This diagnostic message helps identify the "
            "connection failure. It does not guarantee that "
            "the server or network issue can be fixed by code."
        )


# -------------------------
# Request market history
# -------------------------

if request_data:
    with st.spinner(
        "Connecting to Deriv and requesting tick history..."
    ):
        result = fetch_history(
            MARKETS[selected_market],
            count=tick_count,
        )

    if not result["ok"]:
        st.error("Unable to retrieve live market data.")

        st.markdown("### Connection diagnostic")

        st.code(
            result["error"],
            language=None,
        )

        st.markdown(
            """
            **What this means**

            - A handshake error means the WebSocket connection
              was rejected before market data could be requested.
            - A timeout means the connection or response did
              not arrive within the allowed time.
            - A Deriv API error means a response was received
              but the API reported a problem.
            """
        )

        st.info(
            "No live prices or predictions are being fabricated. "
            "Try again later if the service or network is unavailable."
        )

    else:
        prices = result["prices"]
        times = result["times"]

        analysis = analyze_prices(prices)

        if analysis is None:
            st.error("The returned price data could not be analysed.")

        else:
            st.success(
                f"Connected successfully. "
                f"Received {result['received']} historical ticks."
            )

            st.caption(
                "Data source: Deriv WebSocket API. "
                "Prices below are based on the response received."
            )

            # Metrics
            m1, m2, m3 = st.columns(3)

            with m1:
                st.metric(
                    "Latest received price",
                    f"{analysis['latest']:.5f}",
                )

            with m2:
                st.metric(
                    "Previous received price",
                    f"{analysis['previous']:.5f}",
                    delta=(
                        f"{analysis['latest'] - analysis['previous']:.5f}"
                    ),
                )

            with m3:
                st.metric(
                    "Ticks received",
                    analysis["count"],
                )

            st.markdown("---")

            # Historical price chart
            st.subheader("📈 Historical Tick Prices")

            chart_df = pd.DataFrame({
                "Price": pd.to_numeric(
                    pd.Series(prices),
                    errors="coerce",
                )
            })

            if len(times) == len(chart_df):
                chart_df["Time"] = pd.to_datetime(
                    pd.to_numeric(
                        pd.Series(times),
                        errors="coerce",
                    ),
                    unit="s",
                    errors="coerce",
                )

                chart_df = chart_df.set_index("Time")

            st.line_chart(
                chart_df["Price"],
                use_container_width=True,
            )

            # Statistics
            st.subheader("📊 Descriptive Statistics")

            s1, s2, s3 = st.columns(3)

            with s1:
                st.metric(
                    "Average price",
                    f"{analysis['average']:.5f}",
                )

            with s2:
                st.metric(
                    "Last movement",
                    analysis["movement"],
                )

            with s3:
                st.metric(
                    "Recent average comparison",
                    analysis["trend"],
                )

            # Digit distribution
            st.subheader("🔢 Last-Digit Distribution")

            st.caption(
                "These percentages describe the received sample. "
                "They do not establish which digit will occur next."
            )

            st.bar_chart(
                analysis["digit_table"].set_index("Digit")[
                    "Percentage"
                ],
                use_container_width=True,
            )

            st.dataframe(
                analysis["digit_table"],
                use_container_width=True,
                hide_index=True,
            )

            # Raw data
            with st.expander("View received tick data"):
                raw_df = pd.DataFrame({
                    "Time": times,
                    "Price": prices,
                })

                st.dataframe(
                    raw_df,
                    use_container_width=True,
                    hide_index=True,
                )

            st.success(
                "Analysis complete. No trades were placed."
            )


# -------------------------
# Footer
# -------------------------

st.markdown("---")

st.markdown(
    """
    <p class="small-note">
        BEASTMODE PRO • Market-data analysis dashboard
    </p>
    """,
    unsafe_allow_html=True,
)

st.caption(
    "Historical patterns and digit frequencies do not guarantee "
    "future outcomes. This tool does not place trades."
)
