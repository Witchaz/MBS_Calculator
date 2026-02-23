import streamlit as st
import pandas as pd
import re

from core.datastore import DataStore
from mbs_utils import parse_game_text, prepare_features
from io import StringIO

def split_markets(raw_text: str):
    markets = re.split(r"(Market \d+)", raw_text)
    
    result = {}
    for i in range(1, len(markets), 2):
        market_name = markets[i].strip()  # Market 1
        market_body = markets[i+1].strip()
        market_id = int(market_name.split()[1])
        result[market_id] = market_name + "\n" + market_body

    return result

# ----------------------------------
# REQUIRE GAME SELECTION
# ----------------------------------
if "game_id" not in st.session_state:
    st.error("Please select a game from Home page first.")
    st.stop()

# sync game_id เข้า datastore
st.session_state["datastore"].game_id = st.session_state["game_id"]
# -------------------------
# INIT DATASTORE
# -------------------------
if "datastore" not in st.session_state:
    st.session_state["datastore"] = DataStore()

if "company_name" not in st.session_state:
    st.session_state["company_name"] = ""

if "round_number_input" not in st.session_state:
    st.session_state["round_number_input"] = 1

ds = st.session_state["datastore"]

# sync จาก datastore ถ้ามีค่า
if ds.get_company_name(ds.game_id) != "" :
    st.session_state["company_name"] = \
        ds.get_company_name(ds.game_id)

if ds.get_round_number() != 1:
    st.session_state["round_number_input"] = \
        ds.get_round_number()

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

with st.expander("ℹ️ Debug Info", expanded=False):
    st.write(st.session_state)

# =====================================================
# 1️⃣ MARKET INPUT SECTION
# =====================================================

def parse_all_markets(raw_text):
    markets = {}

    # Split by Market blocks
    blocks = re.split(r"Market\s+\d+", raw_text)
    market_ids = re.findall(r"Market\s+(\d+)", raw_text)

    for market_id, block in zip(market_ids, blocks[1:]):  
        block = block.strip()
        if not block:
            continue

        # Convert block to dataframe
        df = pd.read_csv(
            StringIO(block),
            sep="\t"
        )

        # Clean columns
        df.columns = df.columns.str.strip()

        # Clean numeric columns
        if "Price" in df.columns:
            df["Price"] = df["Price"].replace("[\$,]", "", regex=True).astype(float)

        if "Sales volume" in df.columns:
            df["Sales volume"] = df["Sales volume"].replace(",", "", regex=True).astype(float)

        if "Market share" in df.columns:
            df["Market share"] = df["Market share"].replace("%", "", regex=True).astype(float)

        markets[int(market_id)] = df

    return markets


st.header("📊 Market Sale Status")

raw_text = st.text_area(
    "Paste All Market Data",
    key="input_all_markets",
    height=400
)

if raw_text:
    market_data = parse_all_markets(raw_text)

    for m, df in market_data.items():
        st.write(f"Market {m}")
        st.dataframe(df)
        st.session_state[f"input_market_{m}"] = raw_text  # store raw text for each market


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

    datastore = st.session_state["datastore"]
    round_number = st.session_state["input_round_number"]
    datastore.set_round_number(round_number)

    round_dfs = []

    # -------------------------
    # Process Markets
    # -------------------------
    raw_text = st.session_state.get("input_all_markets", "").strip()
    
    all_markets = split_markets(raw_text)

    for market_id, market_text in all_markets.items():
        df = parse_game_text(market_text, round_number=round_number)
        df = prepare_features(df, round_number=round_number)
        df["market_id"] = market_id
        round_dfs.append(df)
    # รวม dataframe ของรอบนี้
    round_df = pd.concat(round_dfs, ignore_index=True)

    # overwrite รอบนี้แทน append
    datastore.round_dfs = [round_df]

    # -------------------------
    # Net Profit
    # -------------------------
    net_profit_text = st.session_state["input_net_profit"].strip()

    datastore.round_net_profit = []  # reset ก่อน

    if net_profit_text != "":
        datastore.add_net_profit_text(
            round_number=round_number,
            raw_text=net_profit_text
        )

    # -------------------------
    # 🔥 SAVE TO FIRESTORE
    # -------------------------
    datastore.save_current_round()

    # -------------------------
    # RESET INPUTS
    # -------------------------
    for i in range(1, 5):
        st.session_state[f"input_market_{i}"] = ""

    st.session_state["input_net_profit"] = ""

    st.success(f"Round {round_number} saved to Firebase.")
    
    # auto next round
    st.session_state["round_number_input"] += 1
    datastore.add_round_number(1)

    st.rerun()

st.button("Save Round", on_click=save_round)