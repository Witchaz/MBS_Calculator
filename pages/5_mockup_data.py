import streamlit as st
import pandas as pd
import json
from core.datastore import DataStore


if "data_store" not in st.session_state:
    st.session_state["data_store"] = DataStore()

st.title("Data Manager")

ds = st.session_state["data_store"]

# ========================
# Export Section
# ========================
st.subheader("Export Data (JSON)")
json_data = ds.export_json()

st.download_button(
    label="Download JSON",
    data=json_data,
    file_name="round_data.json",
    mime="application/json"
)

st.code(json_data, language="json")


# ========================
# Load Section
# ========================
st.subheader("Load JSON")

uploaded_file = st.file_uploader("Upload JSON file", type=["json"])

if uploaded_file is not None:
    content = uploaded_file.read().decode("utf-8")
    ds.load_json(content)
    st.success("Data Loaded Successfully")


# ========================
# Edit Section
# ========================
st.subheader("Edit Data")

df = ds.get_all_rounds_df()

if not df.empty:
    edited_df = st.data_editor(df, num_rows="dynamic")

    if st.button("Save Changes"):
        ds.round_dfs = [edited_df]
        st.success("Changes Saved")
else:
    st.info("No data available")


# ========================
# Add Row Section
# ========================
st.subheader("Add New Row")

if not df.empty:
    new_row = {}

    for col in df.columns:
        new_row[col] = st.text_input(f"{col}")

    if st.button("Add Row"):
        new_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        ds.round_dfs = [new_df]
        st.success("Row Added")
