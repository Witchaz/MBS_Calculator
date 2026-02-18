import streamlit as st
import pandas as pd
from core.datastore import DataStore
from mbs_utils import parse_game_text, prepare_features



# -------------------------
# INIT DATASTORE
# -------------------------
if "data_store" not in st.session_state:
    st.session_state["data_store"] = DataStore()

if "company_name" not in st.session_state:
    st.session_state["company_name"] = ""

if "round_number_input" not in st.session_state:
    st.session_state["round_number_input"] = 1

# sync จาก datastore ถ้ามีค่า
if st.session_state["data_store"].get_company_name() != "":
    st.session_state["company_name"] = \
        st.session_state["data_store"].get_company_name()

if st.session_state["data_store"].get_round_number() != 1:
    st.session_state["round_number_input"] = \
        st.session_state["data_store"].get_round_number()

# -------------------------
# ROUND INPUT
# -------------------------
round_number = st.number_input(
    "Round number",
    min_value=1,
    step=1,
    key="input_round_number",
    value=st.session_state["round_number_input"]
)
# =====================================================
# COMPANY NAME
# =====================================================
st.header("🏢 Team Information")

st.text_input(
    "Enter Company Name",
    key="input_company_name",
    value=st.session_state["company_name"]
)
# =====================================================
# 1️⃣ MARKET INPUT SECTION
# =====================================================
st.header("📊 Market Sale Status")

tabs = st.tabs([f"Market {i}" for i in range(1, 5)])

for idx, tab in enumerate(tabs, start=1):
    with tab:
        st.text_area(
            f"Paste data for Market {idx}",
            key=f"input_market_{idx}",
            height=250
        )

# =====================================================
# 2️⃣ NET PROFIT SECTION
# =====================================================
st.header("💰 Net Profit")

st.text_area(
    "Paste Net Profit (same format as Team Performance page)",
    key="input_net_profit",
    height=200
)
def save_round():

    data_store = st.session_state["data_store"]

    company_name = st.session_state["input_company_name"].strip()
    round_number = st.session_state["input_round_number"]

    # -------------------------
    # Validate Company
    # -------------------------
    if company_name == "":
        st.error("Please enter a company name.")
        return

    data_store.set_round_number(round_number)
    data_store.set_company_name(company_name)   

    round_dfs = []

    # -------------------------
    # Process 4 Markets
    # -------------------------
    for market_id in range(1, 5):

        raw_text = st.session_state[f"input_market_{market_id}"].strip()

        if not raw_text:
            st.error(f"Market {market_id} is empty.")
            return

        df = parse_game_text(raw_text)
        df = prepare_features(df, round_number=round_number)
        df["market_id"] = market_id

        round_dfs.append(df)

    round_df = pd.concat(round_dfs, ignore_index=True)
    data_store.round_dfs.append(round_df)

    # -------------------------
    # Net Profit
    # -------------------------
    net_profit_text = st.session_state["input_net_profit"].strip()

    if net_profit_text != "":
        data_store.add_net_profit_text(
            round_number=round_number,
            raw_text=net_profit_text
        )

    # -------------------------
    # RESET INPUTS
    # -------------------------
    for i in range(1, 5):
        st.session_state[f"input_market_{i}"] = ""

    st.session_state["input_net_profit"] = ""

    st.success(f"Round {round_number} saved successfully.")
    st.session_state["round_number_input"] += 1
    data_store.add_round_number(1)
    
    st.rerun()

st.button("Save Round", on_click=save_round)