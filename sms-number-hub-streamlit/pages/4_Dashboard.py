import streamlit as st

from lib.db import get_dashboard_stats, init_db
from lib.session import auth_sidebar, require_login


st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
init_db()

u = require_login()
auth_sidebar()

st.title("Dashboard")

stats = get_dashboard_stats(viewer_user_id=int(u["id"]), viewer_role=str(u.get("role")))

col1, col2, col3, col4 = st.columns(4)
col1.metric("Active Numbers", stats["active_phone_numbers"])
col2.metric("SMS Today", stats["sms_today"])
col3.metric("OTP Today", stats["otp_today"])
col4.metric("Unread", stats["unread"])

st.divider()

st.write("Use the Inbox page to view incoming messages and filter by number, store tag, and date range.")
