import os

import pandas as pd
import streamlit as st

from lib.db import (
    assign_number_to_user,
    get_number_users,
    get_numbers,
    list_users,
    set_number_tags,
)
from lib.session import auth_sidebar, is_admin, require_login


st.set_page_config(page_title="Numbers", page_icon="📱", layout="wide")

u = require_login()
auth_sidebar()
admin = is_admin()

st.title("Numbers")

numbers = get_numbers()
users = list_users(active_only=True)

if not numbers:
    st.info("No numbers found yet. Add numbers in Number Inventory or via Twilio.")

st.subheader("Number tags")

if not admin:
    st.info("Number tagging is admin-only.")

if numbers:
    number_id = st.selectbox(
        "Select number",
        options=[n["id"] for n in numbers],
        format_func=lambda nid: next(n["e164"] for n in numbers if n["id"] == nid),
    )
    store_tag = st.text_input("Store tag (e.g., Walmart US)", disabled=not admin)
    purpose_tag = st.text_input("Purpose tag (e.g., 2FA)", disabled=not admin)
    if st.button("Save tags", type="primary", disabled=not admin):
        set_number_tags(int(number_id), store_tag.strip() or None, purpose_tag.strip() or None)
        st.success("Saved")

st.divider()

st.subheader("Assign numbers to users")

if not admin:
    st.info("Assigning numbers to users is admin-only.")

if not users:
    st.warning("No users exist yet. Ask an admin to create users.")
else:
    if numbers:
        assign_user_id = st.selectbox(
            "User",
            options=[usr["id"] for usr in users],
            format_func=lambda uid: next(usr["username"] for usr in users if usr["id"] == uid),
        )
        assign_number_id = st.selectbox(
            "Number",
            options=[n["id"] for n in numbers],
            format_func=lambda nid: next(n["e164"] for n in numbers if n["id"] == nid),
            disabled=not admin,
        )
        if st.button("Assign", type="primary", disabled=not admin):
            try:
                assign_number_to_user(int(assign_user_id), int(assign_number_id))
                st.success("Assigned")
            except Exception as e:
                st.error(str(e))

st.divider()

st.subheader("Assignments overview")

if numbers:
    rows = []
    for n in numbers:
        for nu in get_number_users(int(n["id"]), active_only=True):
            rows.append(
                {
                    "number": n["e164"],
                    "username": nu["username"],
                    "role": nu["role"],
                    "assigned_at": nu["created_at"],
                }
            )
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.divider()

st.subheader("Twilio (optional)")

if not (os.getenv("TWILIO_ACCOUNT_SID") and os.getenv("TWILIO_AUTH_TOKEN")):
    st.info("Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN to enable Twilio number management.")
    st.stop()

st.warning("Twilio number buying/listing UI is not implemented yet; webhook ingest works once Twilio is configured.")
