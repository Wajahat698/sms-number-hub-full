import streamlit as st

from lib.db import get_events
from lib.session import auth_sidebar, require_admin


st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")

require_admin()
auth_sidebar()

st.title("Settings")

st.subheader("Event logs")

limit = st.slider("Rows", 50, 2000, 200)
rows = get_events(limit=int(limit))

if not rows:
    st.info("No events logged yet.")
    st.stop()

st.dataframe(rows, use_container_width=True, hide_index=True)
