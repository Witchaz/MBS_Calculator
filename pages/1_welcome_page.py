import streamlit as st
from core.datastore import DataStore
st.title("Welcome Page")

if "data_store" not in st.session_state:
    st.session_state["data_store"] = DataStore()

data_store = st.session_state["data_store"]

st.write("Current round:", data_store.round_number)
