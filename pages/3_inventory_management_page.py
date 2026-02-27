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
