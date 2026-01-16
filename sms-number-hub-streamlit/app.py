import streamlit as st

from lib.session import auth_sidebar, require_login

st.set_page_config(page_title="SMS Number Hub", page_icon="📲", layout="wide")

u = require_login()
auth_sidebar()

st.title("SMS Number Hub")

st.write(
    "Use the pages in the sidebar to compare SMS providers and manage a centralized inventory of 2FA numbers, store logins, and assignments."
)

col1, col2 = st.columns(2)
with col1:
    st.page_link("pages/1_Provider_Comparison.py", label="Provider Comparison", icon="📊")
    st.page_link("pages/4_Dashboard.py", label="Dashboard", icon="📊")
    st.page_link("pages/5_Inbox.py", label="Inbox", icon="💬")

with col2:
    st.page_link("pages/6_Numbers.py", label="Numbers", icon="📱")
    st.page_link("pages/7_Users.py", label="Users", icon="👤")
    st.page_link("pages/8_Settings.py", label="Settings", icon="⚙️")

st.divider()

st.subheader("Inventory (legacy scaffold)")
st.write(
    "The original inventory pages are still available while the new RBAC+Inbox workflow is being finalized."
)
st.page_link("pages/2_Number_Inventory.py", label="Number Inventory", icon="📇")
st.page_link("pages/3_Inbound_SMS_Log.py", label="Inbound SMS Log (optional)", icon="🧪")

st.divider()

st.subheader("How this helps")

st.write(
    "Retail Link (and related portals) require unique SMS numbers per store login. This app tracks which number is assigned to which store/account and (optionally) surfaces inbound SMS in one place if you connect a provider."
)
