
import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="BEASTMODE AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "running" not in st.session_state:
    st.session_state.running = False
if "trades" not in st.session_state:
    st.session_state.trades = []

st.markdown("""
<style>
.stApp {
    background: radial-gradient(ellipse at 50% 0%, #19213a 0%, #080b12 55%);
    color: white;
}
[data-testid="stSidebar"] {
    background: #0c111c;
    border-right: 1px solid #252d40;
}
.block-container {
    max-width: 1450px;
    padding-top: 1.5rem;
}
h1, h2, h3, p, label { color: #f4f7ff; }
.robot {
    margin: 12px auto;
    width: 230px;
    height: 205px;
    border: 3px solid #4e8cff;
    border-radius: 48% 48% 40% 40%;
    background: linear-gradient(145deg,#283d62,#111827 70%);
    box-shadow: 0 0 35px #2767ff55, inset 0 0 25px #61a5ff33;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    position: relative;
}
.eyes {
    display: flex;
    gap: 36px;
    margin: 12px 0 20px;
}
.eye {
    width: 35px;
    height: 27px;
    border-radius: 50%;
    background: #54eaff;
    box-shadow: 0 0 18px #54eaff;
}
.mouth {
    width: 76px;
    height: 12px;
    border-radius: 5px;
    background: #ff783d;
    box-shadow: 0 0 15px #ff783d;
}
.antenna {
    width: 7px;
    height: 27px;
    background: #ff9b43;
    border-radius: 5px;
    position: absolute;
    top: -27px;
}
.brand {
    text-align: center;
    font-size: 34px;
    font-weight: 900;
    letter-spacing: 3px;
}
.brand span { color: #ff3e62; }
.sub {
    text-align: center;
    color: #9eacc6;
    letter-spacing: 2px;
    font-size: 12px;
}
.panel {
    background: #101725;
    border: 1px solid #29354a;
    border-radius: 14px;
    padding: 18px;
    margin-bottom: 12px;
}
.small { color: #9eacc6; font-size: 13px; }
div.stButton > button {
    min-height: 48px;
    border-radius: 10px;
    font-weight: 800;
}
hr { border-color: #29354a; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 🤖 BEASTMODE")
    st.markdown("### AI CONTROL")
    page = st.radio(
        "Navigation",
        [
            "Dashboard",
            "Live Trades",
            "Strategy",
            "Market Analysis",
            "Trade History",
            "Connect Broker",
            "Settings"
        ],
        label_visibility="collapsed"
    )
    st.divider()
    st.caption("SYSTEM STATUS")
    st.markdown("🟡 Broker: Not connected")
    st.markdown(
        "🟢 Control: Running" if st.session_state.running
        else "⚪ Control: Stopped"
    )
    st.caption("Dashboard preview — no live orders are sent.")

st.markdown(
    '<div class="brand">BEASTMODE <span>AI</span></div>'
    '<div class="sub">INTELLIGENT TRADING CONTROL SYSTEM</div>',
    unsafe_allow_html=True
)
st.write("")

if page == "Dashboard":
    left, center, right = st.columns([1, 1.5, 1])

    with center:
        st.markdown("""
        <div class="robot">
            <div class="antenna"></div>
            <div style="color:#9dbdff;font-size:12px;letter-spacing:4px">
                B M - 01
            </div>
            <div class="eyes">
                <div class="eye"></div>
                <div class="eye"></div>
            </div>
            <div class="mouth"></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(
            '<div style="text-align:center;font-weight:800;'
            'font-size:20px">BEASTMODE ROBOT</div>',
            unsafe_allow_html=True
        )
        status = "DEMO PREVIEW — RUNNING" if st.session_state.running \
            else "STANDBY — NOT TRADING"
        st.markdown(
            f'<div class="sub">{status}</div>',
            unsafe_allow_html=True
        )
        st.write("")

        start_col, stop_col = st.columns(2)
        with start_col:
            if st.button("▶ START", type="primary",
                         use_container_width=True):
                st.session_state.running = True
                st.rerun()
        with stop_col:
            if st.button("■ STOP", use_container_width=True):
                st.session_state.running = False
                st.rerun()

        st.caption(
            "START and STOP currently control the dashboard preview only. "
            "Trading execution is not connected."
        )

    st.divider()
    st.markdown("### 📊 LIVE TRADES")

    if st.session_state.trades:
        st.dataframe(
            pd.DataFrame(st.session_state.trades),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info(
            "No trades yet. Real or demo trades will appear here "
            "after the strategy and broker are integrated."
        )

    st.divider()
    st.markdown("### 🌐 MARKET WATCH")
    st.caption(
        "Market prices will appear here after we connect a live data source. "
        "No live prices are being shown in this preview."
    )
    m1, m2, m3 = st.columns(3)
    m1.metric("Market data", "Not connected")
    m2.metric("Broker", "Not connected")
    m3.metric("Strategy", "Not active")

elif page == "Live Trades":
    st.title("📊 Live Trades")
    st.info("Trade records will appear here when demo execution is integrated.")

elif page == "Strategy":
    st.title("🧠 BEASTMODE Strategy")
    st.markdown("""
    **Planned strategy reference: DESPERADO-inspired trend confirmation**

    - H1: determine the main trend using the 50-period SMA.
    - M5, M15 and M30: confirm trend direction.
    - BUY candidate: all required timeframes are above their SMAs.
    - SELL candidate: all required timeframes are below their SMAs.
    - Otherwise: WAIT.

    These rules still need to be verified against the original strategy.
    No signals or orders are generated by this preview.
    """)

elif page == "Market Analysis":
    st.title("📈 Market Analysis")
    st.info("Live analysis will be available after a market data connection is added.")

elif page == "Trade History":
    st.title("📚 Trade History")
    st.info("Completed trade records will appear here after demo execution is implemented.")

elif page == "Connect Broker":
    st.title("🔌 Connect Broker")
    st.markdown("Broker connections have not been implemented yet.")
    st.warning(
        "Do not enter API tokens or broker passwords on this preview page."
    )
    st.markdown("Planned integration: Deriv API, subject to compatibility testing.")

elif page == "Settings":
    st.title("⚙️ Settings")
    st.markdown("Trading settings will be added after the strategy and demo testing.")
    st.caption("Risk limits must be configured before any order execution is enabled.")

st.divider()
st.caption(
    f"BEASTMODE AI · Dashboard preview · "
    f"{datetime.now().strftime('%d %b %Y')}"
)
