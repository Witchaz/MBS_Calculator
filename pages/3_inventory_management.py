import streamlit as st


from infrastructure.firebase_client import init_firebase
from infrastructure.firestore_repository import FirestoreRepository
from application.inventory_planning_service import InventoryPlanningService


@st.cache_resource
def get_service():
    db = init_firebase()
    repo = FirestoreRepository(db)
    return InventoryPlanningService(repo)

# =====================================================
# REQUIRE GAME
# =====================================================
if "game_id" not in st.session_state:
    st.error("Please select a game first.")
    st.stop()

game_id = st.session_state["game_id"]

service = get_service()

df = service.get_full_dataset(game_id)

if df.empty:
    st.warning("No data found.")
    st.stop()

st.write(df)

rounds = sorted(df["round"].unique())
selected_round = st.selectbox("Select Round", rounds)

df_round = df[df["round"] == selected_round].copy()

snapshot = service.get_snapshot(df_round)

if snapshot:

    fg_inventory = snapshot["fg_inventory"]
    capacity = snapshot["capacity"]

    forecast_demand = st.number_input(
        "Forecast Demand",
        min_value=0,
        step=1000
    )

    target_ratio = st.slider(
        "Target Ending Inventory %",
        0.0, 0.5, 0.1, 0.05
    )

    if forecast_demand > 0:

        plan = service.compute_production_plan(
            snapshot,
            forecast_demand,
            target_ratio
        )

        st.metric(
            "Required Production",
            f"{plan['required_production']:,.0f}"
        )

        st.metric(
            "Capacity Utilization %",
            f"{plan['utilization_pct']:.2f}%"
        )