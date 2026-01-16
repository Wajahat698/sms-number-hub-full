from __future__ import annotations

from typing import Any

import streamlit as st

from lib.auth import authenticate_user, ensure_bootstrap_admin


def init_auth() -> None:
    ensure_bootstrap_admin()
    st.session_state.setdefault("auth", {"user": None})


def current_user() -> dict[str, Any] | None:
    auth = st.session_state.get("auth") or {}
    return auth.get("user")


def is_admin() -> bool:
    u = current_user()
    return bool(u and str(u.get("role") or "").lower() == "admin")


def logout() -> None:
    st.session_state["auth"] = {"user": None}


def login_screen(title: str = "Sign in") -> None:
    st.title(title)
    st.info("Use your username and password to access the SMS inbox.")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", type="primary")

    if submitted:
        u = authenticate_user(username=username, password=password)
        if not u:
            st.error("Invalid credentials")
            st.stop()

        st.session_state["auth"] = {"user": {k: u.get(k) for k in ["id", "username", "email", "role", "is_active"]}}
        st.rerun()

    st.stop()


def require_login() -> dict[str, Any]:
    init_auth()
    u = current_user()
    if not u:
        login_screen()
    return u


def require_admin() -> dict[str, Any]:
    u = require_login()
    if str(u.get("role") or "").lower() != "admin":
        st.error("You do not have access to this page.")
        st.stop()
    return u


def auth_sidebar() -> None:
    u = current_user()
    with st.sidebar:
        st.divider()
        if not u:
            st.caption("Not signed in")
            return
        st.caption(f"Signed in as: {u.get('username')} ({u.get('role')})")
        if st.button("Sign out"):
            logout()
            st.rerun()
