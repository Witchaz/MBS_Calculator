import streamlit as st


from infrastructure.firebase_client import init_firebase
from infrastructure.firestore_repository import FirestoreRepository
from application.inventory_planning_service import InventoryPlanningService
from application.potential_demand_service import DemandService

@st.cache_resource
def get_inventory_service():
    db = init_firebase()
    repo = FirestoreRepository(db)
    return InventoryPlanningService(repo)

@st.cache_resource
def get_potential_demand_service():
    db = init_firebase()
    repo = FirestoreRepository(db)
    return DemandService(repo)

# =====================================================
# REQUIRE GAME
# =====================================================
if "game_id" not in st.session_state:
    st.error("Please select a game first.")
    st.stop()

game_id = st.session_state["game_id"]

inventory_service = get_inventory_service()
potential_demand_service = get_potential_demand_service()

df = inventory_service.get_full_dataset(game_id)

if df.empty:
    st.warning("No data found.")
    st.stop()
st.expander("debug")
st.write(st.session_state)

st.dataframe(df.style.format({
    "production volume": "{:,.0f}",
    "capacity": "{:,.0f}",
    "raw material inventory": "{:,.0f}",
    "finished goods inventory total": "{:,.0f}",
    "FG market 1":"{:,.0f}",
    "FG market 2":"{:,.0f}",
    "FG market 3":"{:,.0f}",
    "FG market 4":"{:,.0f}",
    }), 
    width="stretch",
    hide_index=True)

potential = potential_demand_service.load_round_demand(
    game_id=st.session_state.game_id,
    round_number=df['round'].iloc[-1]
)

st.dataframe(potential,hide_index=True)