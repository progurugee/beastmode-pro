
import streamlit as st
from PIL import Image
from pathlib import Path

st.set_page_config(
    page_title="BEASTMODE AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.stApp {
    background: #030813;
    color: #e9f5ff;
}
[data-testid="stSidebar"] {
    background: #050d1b;
    border-right: 1px solid #075b91;
}
.block-container {
    padding: 1.2rem 1.5rem;
    max-width: 1600px;
}
h1, h2, h3, p, label {
    color: #e9f5ff;
}
.brand {
    font-size: 32px;
    font-weight: 900;
    letter-spacing: 2px;
    text-align: center;
    color: #42dfff;
}
.sub {
    text-align: center;
    color: #8baaca;
    letter-spacing: 2px;
    font-size: 12px;
}
.panel {
    background: linear-gradient(145deg,#071629,#030a14);
    border: 1px solid #087bb9;
    border-radius: 13px;
    padding: 16px;
    margin-bottom: 12px;
    box-shadow: 0 0 15px #007bff12;
}
div.stButton > button {
    height: 52px;
    border-radius: 10px;
    font-size: 19px;
    font-weight: 900;
}
hr {
    border-color: #12334e;
}
</style>
""", unsafe_allow_html=True)

if "running" not in st.session_state:
    st.session_state.running = False

with st.sidebar:
    st.markdown("## 🤖 BEASTMODE AI")
    st.caption("INTELLIGENT TRADING CONTROL")
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
        ]
    )
    st.divider()
    st.markdown("### SYSTEM STATUS")
    st.write("🟢 Dashboard online")
    st.write("🔴 Broker not connected")
    st.write(
        "🟡 Control running" if st.session_state.running
        else "⚪ Control stopped"
    )

if page == "Dashboard":
    st.markdown(
        '<div class="brand">BEASTMODE <span style="color:#ff3155">AI</span></div>'
        '<div class="sub">INTELLIGENT TRADING CONTROL SYSTEM</div>',
        unsafe_allow_html=True
    )
    st.write("")

    left, center, right = st.columns([1, 2.2, 1])

    with center:
        image_path = Path("beastmode_robot.png")

        if image_path.exists():
            try:
                image = Image.open(image_path).convert("RGB")
                w, h = image.size

                # Crop the central robot from the full mockup.
                robot = image.crop((
                    int(w * 0.30),
                    0,
                    int(w * 0.73),
                    int(h * 0.48)
                ))
                st.image(robot, use_container_width=True)
            except Exception:
                st.error("Could not read the robot image.")
        else:
            st.error(
                "Robot image not found. Check that "
                "beastmode_robot.png is in the repository root."
            )

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

        if st.session_state.running:
            st.success("Dashboard control enabled — trading is not connected.")
        else:
            st.info("Standby — broker not connected.")

        st.caption(
            "These buttons control the dashboard display only. "
            "They do not place trades."
        )

    with left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("### SYSTEM")
        st.write("Dashboard: Online")
        st.write("Broker: Not connected")
        st.write("Strategy: Not active")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("### MARKET PRICES")
        st.write("Live prices: Not connected")
        st.write("BTC/USD — unavailable")
        st.write("EUR/USD — unavailable")
        st.write("XAU/USD — unavailable")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("### ACCOUNT")
        st.write("Balance: Not connected")
        st.write("Open trades: 0")
        st.write("Profit/Loss: —")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("### 📊 LIVE TRADES")
    st.write("No trades yet. Broker execution is not implemented.")
    st.markdown("</div>", unsafe_allow_html=True)

elif page == "Live Trades":
    st.title("📊 Live Trades")
    st.info("Trade records will appear after broker execution is integrated.")

elif page == "Strategy":
    st.title("🧠 Strategy")
    st.write("Planned: DESPERADO-style multi-timeframe trend confirmation.")
    st.warning("The original strategy source has not yet been verified.")

elif page == "Market Analysis":
    st.title("📈 Market Analysis")
    st.info("Market data connection is not implemented.")

elif page == "Trade History":
    st.title("📚 Trade History")
    st.info("Completed trade history will appear after execution is integrated.")

elif page == "Connect Broker":
    st.title("🔌 Connect Broker")
    st.write("Deriv API integration is planned.")
    st.warning("Do not enter broker passwords or API tokens on this preview.")

elif page == "Settings":
    st.title("⚙️ Settings")
    st.info("Trading settings will be added after demo testing.")

st.divider()
st.caption("BEASTMODE AI · Dashboard preview · No live trading enabled")
