import streamlit as st
from core.datastore import DataStore
from datetime import datetime

st.set_page_config(page_title="MBS Game Manager", layout="wide")

st.title("📊 MBS Game Manager")


def create_game(new_game_name,company_name):
    if company_name.strip() == "":
        st.error(f"company name is empty")
        return
    if new_game_name.strip() == "":
        # ถ้าไม่ตั้งชื่อ → auto generate
        new_game_name = f"game_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    ds.create_new_game(new_game_name,company_name)

    st.session_state.game_id = new_game_name
    ds.game_id = new_game_name
    ds.set_company_name(company_name)
    

    st.success(f"Game created: {new_game_name}")
    st.rerun()


# ==========================
# Initialize DataStore
# ==========================
if "datastore" not in st.session_state:
    st.session_state.datastore = DataStore()

ds = st.session_state.datastore


# ==========================
# SECTION 3: แสดงเกมปัจจุบัน
# ==========================

if "game_id" in st.session_state:
    st.markdown(f"### 🎮 Current Game: `{st.session_state.game_id}`")
else:
    st.warning("No game selected.")

st.divider()

# ==========================
# SECTION 1: เลือกเกมที่มีอยู่
# ==========================

with st.container():

    st.subheader("📂 Select Existing Game")

    games = ds.list_games()

    if games:

        # ทำ label ให้แสดงวันที่ด้วย
        game_options = {}

        for g in games:

            ts = g["updated_at"]
            label = f"{g['game_id']}"
            game_options[label] = g["game_id"]

        selected_label = st.selectbox(
            "Choose a game",
            options=list(game_options.keys())
        )

        if st.button("Load Game"):

            selected_game = game_options[selected_label]

            st.session_state.game_id = selected_game
            ds.game_id = selected_game

            st.session_state["company_name"] = (
                st.session_state["datastore"]
                .get_company_name(selected_game)
            )

            st.success(f"Loaded game: {selected_game}")
            st.rerun()

    else:
        st.info("No existing games found.")


# ==========================
# SECTION 2: สร้างเกมใหม่
# ==========================

st.divider()
st.subheader("➕ Create New Game")

new_game_name = st.text_input("Game Name (optional)")
company_name = st.text_input("Comapany Name")

if st.button("Create Game"):
    create_game(new_game_name,company_name)

