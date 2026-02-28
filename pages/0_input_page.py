import streamlit as st
import pandas as pd
import re
from io import StringIO

from infrastructure.firebase_client import init_firebase
from infrastructure.firestore_repository import FirestoreRepository
from application.round_service import RoundService


# =====================================================
# INIT SERVICES
# =====================================================
@st.cache_resource
def get_round_service():
    db = init_firebase()
    repo = FirestoreRepository(db)
    return RoundService(repo)


round_service = get_round_service()


# =====================================================
# REQUIRE GAME
# =====================================================
if "game_id" not in st.session_state:
    st.error("Please select a game from Home page first.")
    st.stop()

game_id = st.session_state["game_id"]
round_numbers = round_service.get_round_numbers(game_id)
st.session_state["input_round_number"] = round_numbers[-1] if round_numbers else 1

# =====================================================
# ROUND INPUT
# =====================================================
round_number = st.number_input(
    "Round number",
    min_value=1,
    step=1,
    key="input_round_number",
    value=1
)


# =====================================================
# MARKET SPLITTER
# =====================================================
def split_markets(raw_text: str):
    markets = {}
    blocks = re.split(r"Market\s+(\d+)", raw_text)

    for i in range(1, len(blocks), 2):
        market_id = int(blocks[i])
        market_body = blocks[i + 1].strip()
        markets[market_id] = market_body
    return markets


# =====================================================
# 1️⃣ MARKET SECTION
# =====================================================
st.header("📊 Market Sale Status")

raw_market_text = st.text_area(
    "Paste All Market Data",
    key="input_all_markets",
    height=150
)

# =====================================================
# OTHER INPUTS
# =====================================================
st.header("💰 Net Profit")
st.text_area("Paste Net Profit", key="input_net_profit", height=150)

st.header("Production/Inventory")
st.text_area("Paste Production/Inventory", key="input_production", height=150)

st.header("potential demand")
st.text_area("Paste Potential Demand", key="input_potential_demand",height=150)

# =====================================================
# SAVE LOGIC (CLEAN)
# =====================================================
def save_round():

    if st.session_state.get("input_net_profit") == "":
        st.error("Net profit is empty")
    if st.session_state.get("input_production") == "":
        st.error("Production/Inventory is empty")
    if st.session_state.get("input_potential_demand") == "":
        st.error("potential demand is empty")

    raw_text = st.session_state.get("input_all_markets", "").strip()
    market_blocks = split_markets(raw_text)

    net_profit_text = st.session_state.get("input_net_profit", "").strip()
    production_text = st.session_state.get("input_production","").strip()
    potential_demand_text = st.session_state.get("input_potential_demand","").strip()
    

    try:
        round_service.save_round(
            game_id=game_id,
            round_number=round_number,
            market_blocks=market_blocks,
            net_profit_text=net_profit_text,
            production_text=production_text,
            potential_demand_text=potential_demand_text
        )
        st.success(f"Round {round_number} saved successfully.")

        st.session_state["input_round_number"] = round_number + 1
        st.rerun()

    except Exception as e:
        st.error(str(e))


st.button("Save Round", on_click=save_round)