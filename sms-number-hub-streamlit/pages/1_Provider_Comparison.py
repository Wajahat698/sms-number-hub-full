import pandas as pd
import streamlit as st

from lib.db import init_db
from lib.session import auth_sidebar, require_login


st.set_page_config(page_title="Provider Comparison", page_icon="📊", layout="wide")
init_db()

require_login()
auth_sidebar()

st.title("Provider Comparison")

st.write(
    "This page helps shortlist vendors that can provision multiple SMS-capable virtual numbers and centralize inbound messages for 2FA workflows."
)

providers = pd.DataFrame(
    [
        {
            "Provider": "Twilio",
            "Direct Inbound SMS": "Yes",
            "Programmable API": "Yes",
            "Shared Inbox": "Build/Partner",
            "Notes": "Strong ecosystem, good docs; compliance varies by country and use-case.",
        },
        {
            "Provider": "Telnyx",
            "Direct Inbound SMS": "Yes",
            "Programmable API": "Yes",
            "Shared Inbox": "Build/Partner",
            "Notes": "Competitive pricing; good API; number availability varies.",
        },
        {
            "Provider": "MessageBird",
            "Direct Inbound SMS": "Yes",
            "Programmable API": "Yes",
            "Shared Inbox": "Some products",
            "Notes": "Omnichannel tooling; check number procurement requirements for US/CA.",
        },
        {
            "Provider": "Plivo",
            "Direct Inbound SMS": "Yes",
            "Programmable API": "Yes",
            "Shared Inbox": "Build/Partner",
            "Notes": "Developer-focused; verify inbound support for each target country.",
        },
        {
            "Provider": "Vonage",
            "Direct Inbound SMS": "Yes",
            "Programmable API": "Yes",
            "Shared Inbox": "Build/Partner",
            "Notes": "Large provider; offerings vary by region.",
        },
    ]
)

st.dataframe(providers, use_container_width=True, hide_index=True)

st.divider()

st.subheader("Scoring")

st.write(
    "Adjust weights to reflect what matters most for your use-case (multiple unique 2FA numbers per person, centralized access, US/CA coverage, and auditability)."
)

col1, col2, col3, col4 = st.columns(4)

with col1:
    w_cost = st.slider("Cost", 0, 10, 6)
with col2:
    w_compliance = st.slider("Compliance / KYC", 0, 10, 8)
with col3:
    w_us_ca = st.slider("US/CA Availability", 0, 10, 9)
with col4:
    w_inbox = st.slider("Centralized Inbox", 0, 10, 8)

st.write(
    {
        "weights": {
            "cost": w_cost,
            "compliance": w_compliance,
            "us_ca_availability": w_us_ca,
            "centralized_inbox": w_inbox,
        }
    }
)

st.divider()

st.subheader("Recommended decision")

st.write(
    "If you want a fast, reliable company-scale solution, the typical path is to choose a carrier-grade API provider (Twilio/Telnyx/etc.) and build a small inbox + assignment layer (this app) with controlled access."
)
