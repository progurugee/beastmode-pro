import streamlit as st
import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

# ==========================================
# BEASTMODE AI V2
# Licensing dashboard prototype
# ==========================================

st.set_page_config(
    page_title="BEASTMODE AI",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

DB = "beastmode_licenses.db"
UTC = timezone.utc


# ==========================================
# DATABASE
# ==========================================

def connect_db():
    con = sqlite3.connect(DB, check_same_thread=False)
    con.row_factory = sqlite3.Row

    con.execute("""
        CREATE TABLE IF NOT EXISTS licenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            login_hash TEXT NOT NULL UNIQUE,
            robot_hash TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            revoked INTEGER DEFAULT 0
        )
    """)

    con.commit()
    return con


db = connect_db()


# ==========================================
# SECURITY HELPERS
# ==========================================

def hash_key(key):
    return hashlib.sha256(key.strip().encode()).hexdigest()


def generate_key(prefix):
    token = secrets.token_hex(12).upper()
    return f"{prefix}-{token[:8]}-{token[8:16]}-{token[16:24]}"


def utc_now():
    return datetime.now(UTC)


def get_expiry(value):
    try:
        result = datetime.fromisoformat(value)
        if result.tzinfo is None:
            result = result.replace(tzinfo=UTC)
        return result
    except (ValueError, TypeError):
        return None


def get_admin_password():
    try:
        return st.secrets["ADMIN_PASSWORD"]
    except Exception:
        return ""


# ==========================================
# DESIGN
# ==========================================

st.markdown("""
<style>
.stApp {
    background:
        radial-gradient(
            circle at top,
            rgba(180, 15, 45, 0.20),
            transparent 45%
        ),
        #08090d;
    color: white;
}

[data-testid="stMainBlockContainer"] {
    max-width: 800px;
    padding-top: 1.5rem;
}

.brand {
    padding: 25px 20px;
    border-radius: 16px;
    border: 1px solid #40202a;
    border-left: 5px solid #ed174c;
    background: linear-gradient(
        135deg,
        #211017,
        #0d0f15
    );
    margin-bottom: 25px;
}

.brand h1 {
    font-size: clamp(2rem, 7vw, 3.1rem);
    font-weight: 900;
    margin: 0;
    color: white;
}

.brand span {
    color: #ff315b;
}

.subtitle {
    color: #b9bbc5;
    font-size: 13px;
    margin-top: 8px;
    letter-spacing: 1px;
}

.panel {
    padding: 18px;
    border: 1px solid #30303b;
    background: #12141c;
    border-radius: 14px;
    margin-bottom: 15px;
}

div.stButton > button {
    min-height: 46px;
    border-radius: 10px;
    font-weight: bold;
}

div.stButton > button[kind="primary"] {
    background: #df1743;
    color: white;
    border: 1px solid #ff315b;
}

footer {
    visibility: hidden;
}
</style>
""", unsafe_allow_html=True)


st.markdown("""
<div class="brand">
    <h1>BEASTMODE <span>AI</span></h1>
    <div class="subtitle">
        INTELLIGENT TRADING CONTROL SYSTEM
    </div>
</div>
""", unsafe_allow_html=True)


# ==========================================
# SESSION STATE
# ==========================================

defaults = {
    "customer_id": None,
    "robot_activated": False,
    "running_request": False,
    "admin_logged_in": False,
    "saved_login": "",
    "saved_server": ""
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ==========================================
# LICENSE FUNCTIONS
# ==========================================

def validate_login(email, key):
    row = db.execute("""
        SELECT *
        FROM licenses
        WHERE lower(email) = lower(?)
        AND login_hash = ?
    """, (email.strip(), hash_key(key))).fetchone()

    if not row:
        return None, "Incorrect email or login license."

    if row["revoked"]:
        return None, "This license has been suspended."

    expiry = get_expiry(row["expires_at"])

    if not expiry or utc_now() >= expiry:
        return None, "This license has expired."

    return row, ""


def validate_robot(row, key):
    if not secrets.compare_digest(
        row["robot_hash"],
        hash_key(key)
    ):
        return False, "Incorrect robot license."

    if row["revoked"]:
        return False, "Robot license suspended."

    expiry = get_expiry(row["expires_at"])

    if not expiry or utc_now() >= expiry:
        return False, "Robot license expired."

    return True, ""


# ==========================================
# NAVIGATION
# ==========================================

page = st.radio(
    "Access",
    ["Customer Login", "Owner Admin"],
    horizontal=True,
    label_visibility="collapsed"
)


# ==========================================
# CUSTOMER AREA
# ==========================================

if page == "Customer Login":

    st.subheader("Customer Login")

    st.write(
        "Enter your email and the login license "
        "provided by BEASTMODE."
    )

    if st.session_state.customer_id is None:

        with st.form("login_form"):

            email = st.text_input(
                "Email address",
                placeholder="customer@example.com"
            )

            login_key = st.text_input(
                "Login license",
                type="password"
            )

            login = st.form_submit_button(
                "VERIFY LICENSE",
                type="primary",
                use_container_width=True
            )

        if login:

            if not email.strip() or not login_key.strip():
                st.error("Enter your email and license.")

            else:
                row, error = validate_login(email, login_key)

                if error:
                    st.error(error)

                else:
                    st.session_state.customer_id = row["id"]
                    st.session_state.robot_activated = False
                    st.session_state.running_request = False
                    st.rerun()

    else:

        row = db.execute(
            "SELECT * FROM licenses WHERE id = ?",
            (st.session_state.customer_id,)
        ).fetchone()

        if (
            not row
            or row["revoked"]
            or not get_expiry(row["expires_at"])
            or utc_now() >= get_expiry(row["expires_at"])
        ):
            st.session_state.customer_id = None
            st.session_state.robot_activated = False
            st.session_state.running_request = False

            st.error("Your license is no longer active.")
            st.rerun()

        st.markdown('<div class="panel">', unsafe_allow_html=True)

        st.write("**Customer:**", row["email"])

        st.write(
            "**License expiry:**",
            get_expiry(row["expires_at"]).astimezone().strftime(
                "%d %B %Y, %H:%M"
            )
        )

        st.markdown("</div>", unsafe_allow_html=True)

        # ROBOT ACTIVATION

        if not st.session_state.robot_activated:

            st.subheader("Activate BEASTMODE")

            with st.form("robot_form"):

                robot_key = st.text_input(
                    "Robot activation license",
                    type="password"
                )

                activate = st.form_submit_button(
                    "ACTIVATE ROBOT",
                    type="primary",
                    use_container_width=True
                )

            if activate:

                valid, error = validate_robot(row, robot_key)

                if valid:
                    st.session_state.robot_activated = True
                    st.success("Robot license verified.")
                    st.rerun()

                else:
                    st.error(error)

        else:

            st.subheader("Trading Control")

            st.success("Robot license active.")

            st.markdown("""
            <div class="panel">
                <b>MT5 CONNECTION</b><br><br>
                <span style="color:#ffbd45">
                    NOT CONNECTED
                </span><br><br>
                <span style="color:#aaa">
                    The trading execution bridge still needs
                    to be connected and tested.
                </span>
            </div>
            """, unsafe_allow_html=True)

            with st.form("account_form"):

                account = st.text_input(
                    "Deriv MT5 account number",
                    value=st.session_state.saved_login
                )

                server = st.text_input(
                    "MT5 server name",
                    value=st.session_state.saved_server
                )

                save = st.form_submit_button(
                    "SAVE ACCOUNT DETAILS",
                    use_container_width=True
                )

            if save:

                st.session_state.saved_login = account.strip()
                st.session_state.saved_server = server.strip()

                st.info(
                    "Details saved for this browser session. "
                    "No broker connection has been made."
                )

            st.divider()

            left, right = st.columns(2)

            with left:

                if st.button(
                    "▶ START ROBOT",
                    type="primary",
                    use_container_width=True
                ):

                    st.session_state.running_request = True

                    st.warning(
                        "Start request recorded only. "
                        "Live trading is not connected."
                    )

            with right:

                if st.button(
                    "■ STOP ROBOT",
                    use_container_width=True
                ):

                    st.session_state.running_request = False

                    st.info(
                        "Stop request recorded only. "
                        "Existing broker positions are not managed."
                    )

            if st.session_state.running_request:
                st.write("Control request: START REQUESTED")
            else:
                st.write("Control request: STOPPED")

            st.caption(
                "Never enter your MT5 password into this prototype. "
                "Secure account authentication and a trading bridge "
                "must be implemented before live use."
            )

            if st.button("LOG OUT", use_container_width=True):

                st.session_state.customer_id = None
                st.session_state.robot_activated = False
                st.session_state.running_request = False
                st.session_state.saved_login = ""
                st.session_state.saved_server = ""

                st.rerun()


# ==========================================
# OWNER ADMIN AREA
# ==========================================

else:

    st.subheader("Owner Admin Panel")

    admin_password = get_admin_password()

    if not admin_password:

        st.error(
            "Admin access is disabled. Configure "
            "ADMIN_PASSWORD in Streamlit Secrets first."
        )

        st.code(
            'ADMIN_PASSWORD = "your-long-unique-password"',
            language="toml"
        )

    elif not st.session_state.admin_logged_in:

        with st.form("admin_login_form"):

            password = st.text_input(
                "Owner password",
                type="password"
            )

            unlock = st.form_submit_button(
                "UNLOCK ADMIN",
                type="primary",
                use_container_width=True
            )

        if unlock:

            if secrets.compare_digest(password, admin_password):

                st.session_state.admin_logged_in = True
                st.rerun()

            else:
                st.error("Incorrect admin password.")

    else:

        st.subheader("Generate Customer License")

        with st.form("create_license_form"):

            customer_email = st.text_input(
                "Customer email"
            )

            duration = st.selectbox(
                "License duration",
                [
                    "1 day",
                    "2 weeks",
                    "1 month",
                    "6 months",
                    "1 year"
                ]
            )

            create = st.form_submit_button(
                "GENERATE LICENSES",
                type="primary",
                use_container_width=True
            )

        if create:

            if (
                "@" not in customer_email
                or "." not in customer_email.split("@")[-1]
            ):

                st.error("Enter a valid email address.")

            else:

                durations = {
                    "1 day": timedelta(days=1),
                    "2 weeks": timedelta(days=14),
                    "1 month": timedelta(days=30),
                    "6 months": timedelta(days=182),
                    "1 year": timedelta(days=365)
                }

                login_key = generate_key("BM-LOGIN")
                robot_key = generate_key("BM-ROBOT")

                created = utc_now()
                expiry = created + durations[duration]

                try:

                    db.execute("""
                        INSERT INTO licenses (
                            email,
                            login_hash,
                            robot_hash,
                            created_at,
                            expires_at,
                            revoked
                        )
                        VALUES (?, ?, ?, ?, ?, 0)
                    """, (
                        customer_email.strip(),
                        hash_key(login_key),
                        hash_key(robot_key),
                        created.isoformat(),
                        expiry.isoformat()
                    ))

                    db.commit()

                    st.session_state.generated_keys = {
                        "email": customer_email.strip(),
                        "login": login_key,
                        "robot": robot_key,
                        "expiry": expiry.isoformat()
                    }

                except sqlite3.IntegrityError:

                    st.error("Please generate the license again.")

        if st.session_state.get("generated_keys"):

            keys = st.session_state.generated_keys

            st.success("License package created.")

            st.code(
                f"Customer: {keys['email']}\n"
                f"Login License: {keys['login']}\n"
                f"Robot License: {keys['robot']}\n"
                f"Expiry: {keys['expiry']}"
            )

            st.warning(
                "Copy and securely save both keys now. "
                "The database stores their hashes, not the original keys."
            )

        st.divider()

        st.subheader("Customer License Management")

        licenses = db.execute("""
            SELECT *
            FROM licenses
            ORDER BY id DESC
        """).fetchall()

        if not licenses:

            st.info("No customer licenses created yet.")

        for license_row in licenses:

            expiry = get_expiry(license_row["expires_at"])

            if license_row["revoked"]:
                status = "SUSPENDED"

            elif not expiry or utc_now() >= expiry:
                status = "EXPIRED"

            else:
                status = "ACTIVE"

            with st.container(border=True):

                st.write("**" + license_row["email"] + "**")

                st.write("Status:", status)

                st.caption(
                    "Expires: " + license_row["expires_at"]
                )

                if not license_row["revoked"]:

                    if st.button(
                        "SUSPEND LICENSE",
                        key=f"suspend_{license_row['id']}",
                        use_container_width=True
                    ):

                        db.execute(
                            "UPDATE licenses SET revoked=1 WHERE id=?",
                            (license_row["id"],)
                        )

                        db.commit()
                        st.rerun()

                else:

                    if st.button(
                        "REACTIVATE LICENSE",
                        key=f"reactivate_{license_row['id']}",
                        use_container_width=True
                    ):

                        db.execute(
                            "UPDATE licenses SET revoked=0 WHERE id=?",
                            (license_row["id"],)
                        )

                        db.commit()
                        st.rerun()

        if st.button("LOCK ADMIN PANEL"):

            st.session_state.admin_logged_in = False
            st.rerun()


# ==========================================
# FOOTER
# ==========================================

st.divider()

st.caption(
    "BEASTMODE AI | Licensing prototype. "
    "No live Deriv MT5 execution is connected. "
    "Trading involves risk; profits are not guaranteed."
                        )
