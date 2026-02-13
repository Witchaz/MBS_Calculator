import streamlit as st
import pandas as pd
import numpy as np
from mbs_utils import parse_game_text, prepare_features, run_fixed_effects, run_pooled_ols

data_store = st.session_state["data_store"]

st.title("Multiple Rounds Analysis (Panel Data)")
st.info("For each round, paste all 4 markets below, then add the full round.")



# -------------------------
# Funcitons for Managing Panel Data State
# -------------------------

def rebuild_panel_data():
    grouped = {}
    for m in st.session_state.stored_markets:
        grouped.setdefault(m["round"], []).append(m["df"])

    data_store.round_dfs = [
        pd.concat(grouped[r], ignore_index=True)
        for r in grouped
    ]


def load_market_data(market_index, raw_text):
    st.session_state[f"panel_market_{market_index}"] = raw_text

def clear_market(market_index):
    st.session_state[f"panel_market_{market_index}"] = ""

def has_within_variation(df, group_col, vars_list):
    for var in vars_list:
        # ดูว่าภายในแต่ละ company มีค่ามากกว่า 1 ค่าไหม
        if df.groupby(group_col)[var].nunique().max() <= 1:
            return False
    return True

# -------------------------
# Initialize Persistent State
# -------------------------
if "round_number" not in st.session_state:
    st.session_state.round_number = 1

if "panel_result" not in st.session_state:
    st.session_state.panel_result = None

if "panel_df_all" not in st.session_state:
    st.session_state.panel_df_all = None

if "panel_round" not in st.session_state:
    st.session_state.panel_round = 1

# ถ้ามี flag ให้เพิ่มค่า
if st.session_state.get("increment_round", False):
    st.session_state.panel_round += 1
    st.session_state.increment_round = False


# เก็บ raw text ของแต่ละตลาดที่เคย add แล้ว
if "stored_markets" not in st.session_state:
    st.session_state.stored_markets = []  
    # จะเก็บ dict:
    # {round: x, market: y, raw_text: "...", df: dataframe}

# -------------------------
# Round Number
# -------------------------
data_store.round_number = st.number_input(
    "Round number",
    min_value=1,
    key="panel_round"
)


# -------------------------
# 4 Markets Input
# -------------------------

market_inputs = {}
tabs = st.tabs([f"Market {i}" for i in range(1, 5)])

add_clicked = False  # flag ตรวจว่ากดปุ่มจาก tab ไหน

for idx, tab in enumerate(tabs, start=1):
    with tab:
        market_inputs[idx] = st.text_area(
            f"Paste data for Market {idx}",
            key=f"panel_market_{idx}",
            height=200
        )

        col1, col2 = st.columns(2)

        # -------------------------
        # Add Full Round (อยู่ใน col1)
        # -------------------------
        with col1:
            current_round = getattr(data_store, "round_number", 1)

            if st.button(
                f"Add Round {current_round} (4 Markets)",
                key=f"add_panel_tab_{idx}",
            ):
                add_clicked = True
                st.session_state.round_number += 1
                st.session_state.increment_round = True

                

        # -------------------------
        # Clear Market
        # -------------------------
        with col2:
            st.button(
                f"Clear Market {idx}",
                key=f"clear_market_{idx}",
                on_click=clear_market,
                args=(idx,)
            )

# =====================================================
# ทำ logic Add ข้างล่าง loop (รันแค่ครั้งเดียว)
# =====================================================

if add_clicked:

    try:
        round_id = data_store.round_number

        # ลบ round เดิมถ้ามี
        st.session_state.stored_markets = [
            m for m in st.session_state.stored_markets
            if m["round"] != round_id
        ]

        # Build ใหม่
        for market_id in range(1, 5):

            raw_text = st.session_state[f"panel_market_{market_id}"].strip()

            if not raw_text:
                st.error(f"Market {market_id} is empty.")
                st.stop()

            df = parse_game_text(raw_text)
            df = prepare_features(df, round_number=round_id)
            df["market_id"] = market_id

            st.session_state.stored_markets.append({
                "round": round_id,
                "market": market_id,
                "raw_text": raw_text,
                "df": df
            })

        rebuild_panel_data()

        st.session_state.panel_result = None
        st.session_state.panel_df_all = None

        st.success(f"Round {round_id} saved successfully.")

        data_store.round_number += 1
        st.rerun()

    except Exception as e:
        st.error(str(e))


# -------------------------
# Data management 
# -------------------------
st.subheader("Stored Panel Data")

if st.session_state.stored_markets:

    # ---- Group by Round ----
    grouped = {}
    for item in st.session_state.stored_markets:
        grouped.setdefault(item["round"], []).append(item)

    for round_id in sorted(grouped.keys()):

        st.markdown(f"### Round {round_id}")

        markets = grouped[round_id]

        for m in sorted(markets, key=lambda x: x["market"]):

            col1, col2, col3, col4 = st.columns([3,1,1,1])

            with col1:
                st.write(f"Market {m['market']}")

            # (อนาคต) ปุ่มไปหน้าข้อมูล
            with col2:
                st.button(
                    "Go to Data",
                    key=f"go_{round_id}_{m['market']}"
                )

            # โหลดกลับเข้า parse ช่อง
            with col3:
                st.button(
                    "Load",
                    key=f"load_{round_id}_{m['market']}",
                    on_click=lambda r=m["round"], mk=m["market"], txt=m["raw_text"]:
                        st.session_state.update(
                            {f"panel_market_{mk}": txt}
                        )
                )

            # ลบตลาดเดียว
            with col4:
                if st.button(
                    "Delete",
                    key=f"del_{round_id}_{m['market']}"
                ):
                    st.session_state.stored_markets = [
                        x for x in st.session_state.stored_markets
                        if not (x["round"] == round_id and x["market"] == m["market"])
                    ]
                    st.rerun()

        # ---- Delete Entire Round ----
        if st.button(
            f"Delete Round {round_id}",
            key=f"delete_round_{round_id}"
        ):
            st.session_state.stored_markets = [
                x for x in st.session_state.stored_markets
                if x["round"] != round_id
            ]
            st.rerun()
        st.write("---")