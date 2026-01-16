import pandas as pd
import streamlit as st

from lib.auth import hash_password
from lib.db import create_user, list_users, set_user_active
from lib.session import auth_sidebar, require_admin


st.set_page_config(page_title="Users", page_icon="👤", layout="wide")

require_admin()
auth_sidebar()

st.title("Users")

with st.form("create_user"):
    username = st.text_input("Username")
    email = st.text_input("Email (optional)")
    role = st.selectbox("Role", options=["user", "admin"], index=0)
    password = st.text_input("Temporary password", type="password")
    submitted = st.form_submit_button("Create user", type="primary")

if submitted:
    try:
        create_user(
            username=username,
            email=email,
            role=role,
            password_hash=hash_password(password),
        )
        st.success("Created")
        st.rerun()
    except Exception as e:
        st.error(str(e))

st.divider()

users = list_users(active_only=False)
st.dataframe(pd.DataFrame(users).drop(columns=["password_hash"], errors="ignore"), use_container_width=True, hide_index=True)

if users:
    col1, col2 = st.columns([2, 1])
    with col1:
        user_id = st.selectbox(
            "User",
            options=[u["id"] for u in users],
            format_func=lambda uid: next(u["username"] for u in users if u["id"] == uid),
        )
    with col2:
        active = st.checkbox("Active", value=True)
        if st.button("Update", type="secondary"):
            set_user_active(int(user_id), bool(active))
            st.rerun()
