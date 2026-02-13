import streamlit as st
from core.datastore import DataStore

st.set_page_config(page_title="MBS App", layout="wide")

# --- Initialize Global State ---
if "data_store" not in st.session_state:
    st.session_state["data_store"] = DataStore()

st.title("MBS Application")
st.write("เลือกหน้าจาก sidebar")
