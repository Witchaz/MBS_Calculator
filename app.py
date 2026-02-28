import streamlit as st
from core.datastore import DataStore
from datetime import datetime

from infrastructure.firebase_client import init_firebase
from infrastructure.firestore_repository import FirestoreRepository
from application.round_service import RoundService

st.set_page_config(page_title="MBS Game Manager", layout="wide")
st.title("📊 MBS Game Manager")


# =====================================================
# SERVICES
# =====================================================
@st.cache_resource
def get_round_service():
    db = init_firebase()
    repo = FirestoreRepository(db)
    return RoundService(repo)

round_service = get_round_service()

# =====================================================
# DATASTORE INIT
# =====================================================
if "datastore" not in st.session_state:
    st.session_state.datastore = DataStore()

ds = st.session_state.datastore


# =====================================================
# INIT STATE KEYS
# =====================================================
if "current_game_id" not in st.session_state:
    st.session_state["current_game_id"] = None

if "rounds_data" not in st.session_state:
    st.session_state["rounds_data"] = {}


# =====================================================
# CREATE GAME
# =====================================================
def create_game(new_game_name, company_name, seasonal_indicator):

    if company_name.strip() == "":
        st.error("Company name is empty")
        return

    if new_game_name.strip() == "":
        new_game_name = f"game_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    ds.create_new_game(
        game_id=new_game_name,
        company_name=company_name,
        seasonal_indicator=seasonal_indicator
    )

    st.session_state["game_id"] = new_game_name
    st.session_state["company_name"] = company_name

    ds.game_id = new_game_name
    ds.set_company_name(company_name)

    # reset cache
    st.session_state["rounds_data"] = {}
    st.session_state["current_game_id"] = new_game_name

    st.success(f"Game created: {new_game_name}")
    st.rerun()


# =====================================================
# CURRENT GAME DISPLAY
# =====================================================
if "game_id" in st.session_state:

    game_id = st.session_state["game_id"]
    st.markdown(f"### 🎮 Current Game: `{game_id}`")

    # detect game switch
    if st.session_state["current_game_id"] != game_id:
        st.session_state["rounds_data"] = {}
        st.session_state["current_game_id"] = game_id

    # preload rounds once
    if not st.session_state["rounds_data"]:
        raw_rounds = round_service.get_all_rounds(game_id)

        st.session_state["rounds_data"] = {
            r["round_number"]: r
            for r in raw_rounds
        }
    # 🔥 โหลด seasonal จาก service layer
    seasonal_map = round_service.get_seasonal_indicator(game_id)

    st.session_state["seasonal_indicator"] = seasonal_map
    st.session_state["seasonal_factor"] = {
        k: v / 100 for k, v in seasonal_map.items()
        }

else:
    st.warning("No game selected.")

st.divider()


# =====================================================
# SECTION 1: SELECT EXISTING GAME
# =====================================================
st.subheader("📂 Select Existing Game")

games = ds.list_games()

if games:

    game_options = {
        g["game_id"]: g["game_id"]
        for g in games
    }

    selected_game = st.selectbox(
        "Choose a game",
        options=list(game_options.keys())
    )

    if st.button("Load Game"):

        st.session_state["game_id"] = selected_game
        st.session_state["company_name"] = ds.get_company_name(selected_game)

        ds.game_id = selected_game

        st.success(f"Loaded game: {selected_game}")
        st.rerun()

else:
    st.info("No existing games found.")


# =====================================================
# SECTION 2: CREATE NEW GAME
# =====================================================
st.divider()
st.subheader("➕ Create New Game")

new_game_name = st.text_input("Game Name (optional)")
company_name = st.text_input("Company Name")

c1, c2, c3, c4 = st.columns(4)

c1.number_input("Spring", value=100, key="spring_input")
c2.number_input("Summer", value=100, key="summer_input")
c3.number_input("Autumn", value=100, key="autumn_input")
c4.number_input("Winter", value=100, key="winter_input")

if st.button("Create Game"):

    seasonal_indicator = {
        "spring": st.session_state["spring_input"],
        "summer": st.session_state["summer_input"],
        "autumn": st.session_state["autumn_input"],
        "winter": st.session_state["winter_input"],
    }

    create_game(
        new_game_name,
        company_name,
        seasonal_indicator
    )