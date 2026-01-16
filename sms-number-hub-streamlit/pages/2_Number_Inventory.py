import json

import pandas as pd
import streamlit as st

from lib.db import (
    add_assignment,
    add_number,
    add_person,
    add_store_account,
    deactivate_assignment,
    delete_row,
    export_all,
    get_assignments,
    get_numbers,
    get_people,
    get_store_accounts,
    import_table,
    init_db,
)

from lib.session import auth_sidebar, require_login


st.set_page_config(page_title="Number Inventory", page_icon="📇", layout="wide")
init_db()

require_login()
auth_sidebar()

st.title("Number Inventory")

people_tab, numbers_tab, accounts_tab, assignments_tab, import_export_tab = st.tabs(
    ["People", "Numbers", "Store Accounts", "Assignments", "Import/Export"]
)

with people_tab:
    st.subheader("People")
    with st.form("add_person"):
        name = st.text_input("Name")
        email = st.text_input("Email (optional)")
        submitted = st.form_submit_button("Add person", type="primary")

    if submitted:
        try:
            add_person(name=name, email=email)
            st.success("Added")
            st.rerun()
        except Exception as e:
            st.error(str(e))

    people = get_people()
    st.dataframe(pd.DataFrame(people), use_container_width=True, hide_index=True)

    if people:
        col1, col2 = st.columns([2, 1])
        with col1:
            person_to_delete = st.selectbox(
                "Delete person (danger)",
                options=[p["id"] for p in people],
                format_func=lambda pid: next(p["name"] for p in people if p["id"] == pid),
            )
        with col2:
            if st.button("Delete", type="secondary"):
                try:
                    delete_row("people", person_to_delete)
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

with numbers_tab:
    st.subheader("Numbers")

    with st.form("add_number"):
        e164 = st.text_input("E.164 number (e.g., +14155552671)")
        provider = st.text_input("Provider (optional)")
        country = st.text_input("Country (optional)")
        capabilities = st.text_input("Capabilities (optional)")
        status = st.selectbox("Status", options=["active", "paused", "released"], index=0)
        notes = st.text_area("Notes (optional)")
        submitted = st.form_submit_button("Add number", type="primary")

    if submitted:
        try:
            add_number(
                e164=e164,
                provider=provider,
                country=country,
                capabilities=capabilities,
                status=status,
                notes=notes,
            )
            st.success("Added")
            st.rerun()
        except Exception as e:
            st.error(str(e))

    numbers = get_numbers()
    st.dataframe(pd.DataFrame(numbers), use_container_width=True, hide_index=True)

    if numbers:
        col1, col2 = st.columns([2, 1])
        with col1:
            number_to_delete = st.selectbox(
                "Delete number (danger)",
                options=[n["id"] for n in numbers],
                format_func=lambda nid: next(n["e164"] for n in numbers if n["id"] == nid),
            )
        with col2:
            if st.button("Delete number", type="secondary"):
                try:
                    delete_row("numbers", number_to_delete)
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

with accounts_tab:
    st.subheader("Store Accounts")

    with st.form("add_store_account"):
        platform = st.selectbox(
            "Platform",
            options=[
                "Walmart Retail Link (US)",
                "Walmart Canada",
                "Sam's Club",
                "Other",
            ],
        )
        store_name = st.text_input("Store name (optional)")
        store_id = st.text_input("Store ID (optional)")
        login_email = st.text_input("Login email (optional)")
        notes = st.text_area("Notes (optional)")
        submitted = st.form_submit_button("Add store account", type="primary")

    if submitted:
        try:
            add_store_account(
                platform=platform,
                store_name=store_name,
                store_id=store_id,
                login_email=login_email,
                notes=notes,
            )
            st.success("Added")
            st.rerun()
        except Exception as e:
            st.error(str(e))

    accounts = get_store_accounts()
    st.dataframe(pd.DataFrame(accounts), use_container_width=True, hide_index=True)

    if accounts:
        col1, col2 = st.columns([2, 1])
        with col1:
            acc_to_delete = st.selectbox(
                "Delete store account (danger)",
                options=[a["id"] for a in accounts],
                format_func=lambda aid: f"{next(a['platform'] for a in accounts if a['id'] == aid)} | {next((a['store_name'] or '') for a in accounts if a['id'] == aid)} | {next((a['store_id'] or '') for a in accounts if a['id'] == aid)}",
            )
        with col2:
            if st.button("Delete store account", type="secondary"):
                try:
                    delete_row("store_accounts", acc_to_delete)
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

with assignments_tab:
    st.subheader("Assignments")

    people = get_people()
    numbers = get_numbers()
    accounts = get_store_accounts()

    if not people or not numbers or not accounts:
        st.warning("Add at least one person, number, and store account first.")
    else:
        with st.form("add_assignment"):
            person_id = st.selectbox(
                "Person",
                options=[p["id"] for p in people],
                format_func=lambda pid: next(p["name"] for p in people if p["id"] == pid),
            )
            number_id = st.selectbox(
                "Number",
                options=[n["id"] for n in numbers],
                format_func=lambda nid: next(n["e164"] for n in numbers if n["id"] == nid),
            )
            store_account_id = st.selectbox(
                "Store account",
                options=[a["id"] for a in accounts],
                format_func=lambda aid: f"{next(a['platform'] for a in accounts if a['id'] == aid)} | {next((a['store_name'] or '') for a in accounts if a['id'] == aid)} | {next((a['store_id'] or '') for a in accounts if a['id'] == aid)}",
            )
            purpose = st.selectbox("Purpose", options=["2fa", "recovery", "ops"], index=0)
            submitted = st.form_submit_button("Assign", type="primary")

        if submitted:
            try:
                add_assignment(
                    person_id=int(person_id),
                    number_id=int(number_id),
                    store_account_id=int(store_account_id),
                    purpose=purpose,
                )
                st.success("Assigned")
                st.rerun()
            except Exception as e:
                st.error(str(e))

    st.divider()

    active_only = st.checkbox("Show active only", value=True)
    assignments = get_assignments(active_only=active_only)
    st.dataframe(pd.DataFrame(assignments), use_container_width=True, hide_index=True)

    if assignments:
        col1, col2 = st.columns([2, 1])
        with col1:
            to_deactivate = st.selectbox(
                "Deactivate assignment",
                options=[a["id"] for a in assignments],
                format_func=lambda aid: f"{next(a['person_name'] for a in assignments if a['id'] == aid)} | {next(a['number_e164'] for a in assignments if a['id'] == aid)} | {next(a['platform'] for a in assignments if a['id'] == aid)}",
            )
        with col2:
            if st.button("Deactivate", type="secondary"):
                try:
                    deactivate_assignment(to_deactivate)
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

with import_export_tab:
    st.subheader("Export")
    export = export_all()
    export_json = json.dumps(export, indent=2)
    st.download_button(
        "Download JSON export",
        data=export_json,
        file_name="sms_number_hub_export.json",
        mime="application/json",
    )

    st.divider()
    st.subheader("Import")

    uploaded = st.file_uploader("Upload JSON export", type=["json"])
    if uploaded is not None:
        try:
            data = json.loads(uploaded.getvalue().decode("utf-8"))
            if not isinstance(data, dict):
                raise ValueError("Invalid JSON structure")

            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Import (merge)", type="primary"):
                    try:
                        for table in ["people", "numbers", "store_accounts", "assignments"]:
                            rows = data.get(table, [])
                            if rows:
                                import_table(table, rows)
                        st.success("Imported")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

            with col2:
                st.info("Import uses INSERT OR IGNORE to avoid overwriting existing rows.")

        except Exception as e:
            st.error(str(e))
