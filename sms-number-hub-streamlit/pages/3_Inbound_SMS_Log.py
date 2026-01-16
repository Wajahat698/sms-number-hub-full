import streamlit as st

from lib.db import init_db
from lib.session import auth_sidebar, require_login


st.set_page_config(page_title="Inbound SMS Log", page_icon="💬", layout="wide")
init_db()

require_login()
auth_sidebar()

st.title("Inbound SMS Log")

provider = st.selectbox("Provider", options=["Not configured", "Twilio"], index=0)

if provider == "Not configured":
    st.info(
        "This page is optional. If you decide to connect a provider (e.g., Twilio), we can display inbound SMS messages for your provisioned numbers here."
    )
    st.stop()

st.warning("Twilio integration is not enabled yet in this scaffold.")

st.write(
    "If you want this enabled, tell me whether you'll use Twilio and whether everyone should see all messages or only the ones assigned to them."
)
