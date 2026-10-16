import json
import time

import pandas as pd
import streamlit as st
import websocket


# ==========================================
# BEASTMODE PRO
# Read-only Deriv market data dashboard
# ==========================================

st.set_page_config(
    page_title="BEASTMODE PRO",
    page_icon="🐺",
    layout="wide",
)

# New public WebSocket endpoint from Deriv.
# No login or trading token is needed for public data.
DERIV_WS_URL = (
    "wss://api.derivws.com/trading/v1/options/ws/public"
)

MARKETS = {
    "Volatility 10 Index": "R_10",
    "Volatility 25 Index": "R_25",
    "Volatility 50 Index": "R_50",
    "Volatility 75 Index": "R_75",
    "Volatility 100 Index": "R_100",
}


# ==========================================
# Styling
# ==========================================

st.markdown(
    """
    <style>
    .stApp {
        background: #080d18;
        color: #f3f6fc;
    }

    [data-testid="stSidebar"] {
        background: #101827;
    }

    .hero {
        padding: 24px;
        border-radius: 16px;
        background: linear-gradient(120deg, #13233d, #172d26);
        border: 1px solid #30415c;
        margin-bottom: 20px;
    }

    .hero h1 {
        color: #ffffff;
        margin: 0;
    }

    .hero p {
        color: #b2c1d5;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==========================================
# Header
# ==========================================

st.markdown(
    """
    <div class="hero">
        <h1>🐺 BEASTMODE PRO</h1>
        <p>Live market data • Digit analysis • Statistics</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ==========================================
# Connection and request functions
# ==========================================

def request_deriv(payload):
    """
    Open a fresh WebSocket connection, send one request,
    and wait for its response.

    Returns a dictionary with either a response or
    a diagnostic error message.
    """

    ws = None
    started = time.time()

    try:
        ws = websocket.create_connection(
            DERIV_WS_URL,
            timeout=15,
            origin="https://deriv.com",
        )

        ws.settimeout(10)

        ws.send(json.dumps(payload))

        while time.time() - started < 20:
            raw = ws.recv()

            if not raw:
                continue

            response = json.loads(raw)

            if response.get("error"):
                err = response["error"]

                return {
                    "ok": False,
                    "error": (
                        f"Deriv API error: "
                        f"{err.get('code', 'Unknown')} — "
                        f"{err.get('message', 'No details provided')}"
                    ),
                }

            # Match the response to this request.
            if response.get("req_id") == payload.get("req_id"):
                return {
                    "ok": True,
                    "data": response,
                }

            # Some responses may not include req_id.
            if (
                "msg_type" in response
                and response.get("msg_type") in (
                    "history",
                    "active_symbols",
                    "ping",
                    "time",
                    "tick",
                )
            ):
                return {
                    "ok": True,
                    "data": response,
                }

        return {
            "ok": False,
            "error": "Timed out waiting for the Deriv response.",
        }

    except websocket.WebSocketBadStatusException as exc:
        status = getattr(exc, "status_code", "unknown")

        return {
            "ok": False,
            "error": (
                f"WebSocket handshake failed with HTTP {status}. "
                "The server or an intermediary rejected the connection."
            ),
        }

    except websocket.WebSocketTimeoutException:
        return {
            "ok": False,
            "error": (
                "The WebSocket connection timed out while waiting "
                "for a response."
            ),
        }

    except Exception as exc:
        return {
            "ok": False,
            "error": f"{type(exc).__name__}: {str(exc)[:400]}",
        }

    finally:
        if ws is not None:
            try:
                ws.close()
            except Exception:
                pass


def test_connection():
    """
    Check the public connection using a ping request.
    """

    return request_deriv({
        "ping": 1,
        "req_id": 101,
    })


def fetch_history(symbol, count):
    """
    Request historical ticks for the selected symbol.
    """

    return request_deriv({
        "ticks_history": symbol,
        "count": int(count),
        "end": "latest",
        "style": "ticks",
        "req_id": 202,
    })


# ==========================================
# Sidebar
# ==========================================

st.sidebar.title("🐺 BEASTMODE PRO")

market_name = st.sidebar.selectbox(
    "Choose a market",
    list(MARKETS.keys()),
)

symbol = MARKETS[market_name]

count = st.sidebar.selectbox(
    "Historical ticks",
    [100, 250, 500, 750, 1000],
    index=2,
)

st.sidebar.caption("Gold is not connected in this version.")
st.sidebar.caption("This app does not place trades.")


# ==========================================
# Main dashboard
# ==========================================

st.subheader(market_name)
st.caption(f"Deriv symbol: {symbol}")

left, right = st.columns(2)

with left:
    test_button = st.button(
        "🔌 TEST CONNECTION",
        use_container_width=True,
    )

with right:
    data_button = st.button(
        "📡 REQUEST LIVE TICK DATA",
        type="primary",
        use_container_width=True,
    )


# ==========================================
# Connection test
# ==========================================

if test_button:
    with st.spinner("Testing the new Deriv endpoint..."):
        result = test_connection()

    if not result["ok"]:
        st.error("Connection test failed.")
        st.code(result["error"], language=None)

        st.info(
            "If this is another HTTP 520 error, the new endpoint "
            "is also being rejected. We will then investigate "
            "the hosting or network path instead of repeatedly "
            "changing the analysis code."
        )

    else:
        response = result["data"]
        symbols = response.get("active_symbols", [])

        st.success("Connected to Deriv's public market-data endpoint.")

        if symbols:
            st.write(f"Available symbols returned: {len(symbols)}")
        else:
            st.write("Deriv returned a response:", response)


# ==========================================
# Request historical market data
# ==========================================

if data_button:
    with st.spinner("Requesting historical ticks from Deriv..."):
        result = fetch_history(symbol, count)

    if not result["ok"]:
        st.error("Could not retrieve market data.")
        st.code(result["error"], language=None)

        st.warning(
            "No sample prices have been substituted for live data."
        )

    else:
        response = result["data"]
        history = response.get("history", {})

        prices = history.get("prices", [])
        times = history.get("times", [])

        if not prices:
            st.error(
                "The request succeeded, but no historical prices "
                "were returned. Check the selected market symbol."
            )

        else:
            prices = pd.to_numeric(
                pd.Series(prices),
                errors="coerce",
            ).dropna()

            st.success(
                f"Received {len(prices)} historical tick prices."
            )

            if prices.empty:
                st.error("No usable numeric prices were returned.")

            else:
                latest = float(prices.iloc[-1])

                previous = (
                    float(prices.iloc[-2])
                    if len(prices) > 1
                    else latest
                )

                average = float(prices.mean())

                c1, c2, c3 = st.columns(3)

                c1.metric(
                    "Latest received price",
                    f"{latest:.5f}",
                )

                c2.metric(
                    "Previous received price",
                    f"{previous:.5f}",
                    delta=f"{latest - previous:.5f}",
                )

                c3.metric(
                    "Average price",
                    f"{average:.5f}",
                )

                st.subheader("📈 Historical Prices")

                chart_df = pd.DataFrame({
                    "Price": prices.reset_index(drop=True)
                })

                st.line_chart(
                    chart_df,
                    use_container_width=True,
                )

                st.subheader("🔢 Last-digit distribution")

                digit_strings = (
                    prices.astype(str)
                    .str.replace(".", "", regex=False)
                    .str.replace("-", "", regex=False)
                    .str[-1:]
                )

                digits = pd.to_numeric(
                    digit_strings,
                    errors="coerce",
                ).dropna().astype(int)

                counts = (
                    digits.value_counts()
                    .reindex(range(10), fill_value=0)
                    .sort_index()
                )

                percentages = (
                    counts / max(len(digits), 1) * 100
                )

                digit_df = pd.DataFrame({
                    "Digit": range(10),
                    "Count": counts.values,
                    "Percentage": percentages.values.round(2),
                })

                st.bar_chart(
                    digit_df.set_index("Digit")["Percentage"],
                    use_container_width=True,
                )

                st.dataframe(
                    digit_df,
                    use_container_width=True,
                    hide_index=True,
                )

                if len(times) == len(history.get("prices", [])):
                    with st.expander("View received timestamps"):
                        st.dataframe(
                            pd.DataFrame({
                                "Timestamp": times,
                                "Price": history["prices"],
                            }),
                            use_container_width=True,
                            hide_index=True,
                        )

                st.caption(
                    "These are historical statistics, not predictions. "
                    "They do not guarantee future market outcomes."
                )


# ==========================================
# Footer
# ==========================================

st.markdown("---")

st.caption(
    "BEASTMODE PRO • Read-only market data analyzer • "
    "No automatic trading"
        )
