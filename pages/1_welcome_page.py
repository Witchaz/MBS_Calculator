import streamlit as st

st.title("Welcome Page")

data_store = st.session_state["data_store"]

st.write("Current round:", data_store.round_number)
