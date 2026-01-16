from datetime import datetime, timedelta, timezone

import pandas as pd
import streamlit as st

from lib.db import mark_sms_read, query_sms_messages
from lib.session import auth_sidebar, require_login


st.set_page_config(page_title="Inbox", page_icon="💬", layout="wide")

u = require_login()
auth_sidebar()

st.title("Inbox")

with st.sidebar:
    st.subheader("Filters")
    assigned_only = st.checkbox("Assigned numbers only", value=True)
    unread_only = st.checkbox("Unread only", value=False)
    to_number = st.text_input("To number (E.164)", value="")
    from_number = st.text_input("From number (E.164)", value="")
    store_tag = st.text_input("Store tag", value="")
    purpose_tag = st.text_input("Purpose tag", value="")

    now = datetime.now(timezone.utc)
    default_since = now - timedelta(days=2)
    date_range = st.date_input(
        "Date range (UTC)",
        value=(default_since.date(), now.date()),
    )

    auto_refresh = st.checkbox("Auto-refresh", value=True)
    refresh_seconds = st.slider("Refresh interval (sec)", 5, 120, 15)

if auto_refresh:
    st.autorefresh(interval=refresh_seconds * 1000, key="inbox_refresh")

since_iso = None
until_iso = None
try:
    start_date, end_date = date_range
    since_iso = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc).isoformat()
    until_iso = datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc).isoformat()
except Exception:
    pass

rows = query_sms_messages(
    viewer_user_id=int(u["id"]),
    viewer_role=str(u.get("role")),
    assigned_only=assigned_only,
    to_number=to_number.strip() or None,
    from_number=from_number.strip() or None,
    store_tag=store_tag.strip() or None,
    purpose_tag=purpose_tag.strip() or None,
    unread_only=unread_only,
    since_iso=since_iso,
    until_iso=until_iso,
    limit=500,
)

df = pd.DataFrame(rows)

if df.empty:
    st.info("No messages found for the selected filters.")
    st.stop()

col1, col2 = st.columns([3, 1])
with col1:
    st.caption("Tip: OTP codes are detected automatically when present.")
with col2:
    msg_id = st.number_input("Message ID to mark read", min_value=0, value=0, step=1)
    if st.button("Mark as read") and msg_id:
        mark_sms_read(int(msg_id), True)
        st.rerun()

st.dataframe(
    df[[
        "id",
        "received_at",
        "to_number",
        "from_number",
        "store_tag",
        "purpose_tag",
        "otp_code",
        "is_read",
        "body",
    ]],
    use_container_width=True,
    hide_index=True,
)
