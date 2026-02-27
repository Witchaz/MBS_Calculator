import streamlit as st
import pandas as pd

from infrastructure.firebase_client import init_firebase
from infrastructure.firestore_repository import FirestoreRepository
from application.round_service import RoundService


def normalize_by_round(records: list, round_key: str = "round_number"):
    """
    Convert flat list of dicts into dict keyed by round_number.
    """

    normalized = {}

    for row in records:
        rnd = row.get(round_key)

        if rnd is None:
            continue

        normalized.setdefault(rnd, []).append(row)

    return normalized

# =====================================================
# INIT SERVICES
# =====================================================
@st.cache_resource
def get_service():
    db = init_firebase()
    repo = FirestoreRepository(db)
    return RoundService(repo)

round_service = get_service()

# =====================================================
# REQUIRE GAME
# =====================================================
if "game_id" not in st.session_state:
    st.error("Please select a game first.")
    st.stop()

game_id = st.session_state["game_id"]


# =====================================================
# HANDLE GAME SWITCH
# =====================================================
if "current_game_id" not in st.session_state:
    st.session_state["current_game_id"] = None

if st.session_state["current_game_id"] != game_id:
    st.session_state["rounds_data"] = {}
    st.session_state["current_game_id"] = game_id


# =====================================================
# LOAD ALL ROUNDS (ONCE PER GAME)
# =====================================================
if "rounds_data" not in st.session_state or not st.session_state["rounds_data"]:

    raw_rounds = round_service.get_all_rounds(game_id)

    st.session_state["rounds_data"] = {
        r["round_number"]: r
        for r in raw_rounds
    }

rounds_data = st.session_state["rounds_data"]

if not rounds_data:
    st.warning("No data found in this game.")
    st.stop()

st.write(st.session_state)

# =====================================================
# UI
# =====================================================
round_numbers = sorted(rounds_data.keys())
round_tabs = st.tabs([f"Round {r}" for r in round_numbers])

ordered_columns = [
    "round_number",
    "next_production_capacity",
    "production_volume",
    "sales_volume",
    "fg_inventory_1",
    "fg_inventory_2",
    "fg_inventory_3",
    "fg_inventory_4",
    "finished_goods_inventory_total",
    "raw_material_inventory",
]
# =====================================================
# USE LATEST ROUND ONLY
# =====================================================
latest_round = max(rounds_data.keys())
round_doc = rounds_data[latest_round]

st.header(f"📊 Round {latest_round} Overview")

# =====================================================
# INVENTORY
# =====================================================
st.subheader("📦 Inventory Overview")

production_records = round_doc.get("production", [])
df_inventory = pd.DataFrame(production_records)

if not df_inventory.empty:

    ordered_columns = [
        "round_number",
        "next_production_capacity",
        "production_volume",
        "sales_volume",
        "fg_inventory_1",
        "fg_inventory_2",
        "fg_inventory_3",
        "fg_inventory_4",
        "finished_goods_inventory_total",
        "raw_material_inventory",
    ]

    df_inventory = df_inventory.sort_values("round_number")
    df_inventory = df_inventory[ordered_columns]

    df_inventory = df_inventory.rename(columns={
        "round_number": "Round",
        "next_production_capacity": "Next Capacity",
        "production_volume": "Production",
        "sales_volume": "Sales",
        "fg_inventory_1": "FG Inv M1",
        "fg_inventory_2": "FG Inv M2",
        "fg_inventory_3": "FG Inv M3",
        "fg_inventory_4": "FG Inv M4",
        "finished_goods_inventory_total": "FG Total",
        "raw_material_inventory": "Raw Material Inv",
    })

    st.dataframe(
        df_inventory.style.format({
            "Next Capacity": "{:,.0f}",
            "Production": "{:,.0f}",
            "Sales": "{:,.0f}",
            "FG Inv M1": "{:,.0f}",
            "FG Inv M2": "{:,.0f}",
            "FG Inv M3": "{:,.0f}",
            "FG Inv M4": "{:,.0f}",
            "FG Total": "{:,.0f}",
            "Raw Material Inv": "{:,.0f}",
        }),
        width="stretch",
        hide_index=True
    )

else:
    st.info("No inventory data available.")

st.divider()

# =====================================================
# POTENTIAL DEMAND
# =====================================================
st.subheader("📈 Potential Demand Overview")

demand_data = round_doc.get("potential_demand", [])
df_demand = pd.DataFrame(demand_data)

if not df_demand.empty:

    df_demand["unsatisfied_demand"] = (
        df_demand["potential_demand"]
        - df_demand["actual_sales_volume"]
    )

    df_demand = df_demand.sort_values("market_id")

    demand_columns = [
        "market_id",
        "potential_demand",
        "actual_sales_volume",
        "unsatisfied_demand",
        "finished_goods_inventory",
        "market_share_pct",
    ]

    df_demand = df_demand[demand_columns]

    df_demand = df_demand.rename(columns={
        "market_id": "Market",
        "potential_demand": "Potential Demand",
        "actual_sales_volume": "Actual Sales",
        "unsatisfied_demand": "Unsatisfied Demand",
        "market_share_pct": "Market Share (%)",
        "finished_goods_inventory": "Ending FG Inventory",
    })

    st.dataframe(
        df_demand.style.format({
            "Potential Demand": "{:,.0f}",
            "Actual Sales": "{:,.0f}",
            "Unsatisfied Demand": "{:,.0f}",
            "Market Share (%)": "{:.2f}%",
            "Ending FG Inventory": "{:,.0f}",
        }),
        width="stretch",
        hide_index=True
    )

else:
    st.info("No demand data available.")