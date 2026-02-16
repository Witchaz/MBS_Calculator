import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from core.datastore import DataStore

if "data_store" not in st.session_state:
    st.session_state["data_store"] = DataStore()

def submit_net_profit():
    if st.session_state["team_name_input"] == "":
        st.warning("Please enter a team name.")
        return
    st.session_state["data_store"].add_net_profit_text(
    round_number=st.session_state["round_number_input"],
    raw_text=st.session_state["net_profit_input"]
)    

col1, col2 = st.columns(2)

with col1:
    st.text_input("Enter Team Name", key="team_name_input")
with col2:
    st.number_input("Enter Round Number", key="round_number_input", min_value=1, step=1)

st.header("Enter Net profit")
st.text_area("Net profit", key="net_profit_input")

st.button("Submit", on_click=submit_net_profit)

st.dataframe(st.session_state["data_store"].get_full_performance_df().drop(columns=["log_price","log_quality","log_marketing","log_share"], errors="ignore"))
