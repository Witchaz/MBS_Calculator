import pandas as pd
import streamlit as st
import os
import firebase_admin
from io import StringIO
from datetime import datetime
from domain.parsers import parse_net_profit_text
from firebase_admin import credentials, firestore


class DataStore:
    def __init__(self, game_id="current_game"):

        self.company_name = ""
        self.round_dfs = []
        self.round_number = 1
        self.round_net_profit = []
        self.round_potential_demand = []
        self.round_label_cost = []
        self.game_id = game_id

        # -------------------------
        # Firebase setup (Hybrid Version)
        # -------------------------
        try:
            if not firebase_admin._apps:
                # 1. ระบุชื่อไฟล์ JSON ที่ใช้บนเครื่องคอมคุณ
                local_key_path = "mbs-calculator-firebase-adminsdk-fbsvc-86153c9e06.json"

                if os.path.exists(local_key_path):
                    # --- กรณีรันบนคอมตัวเอง (Local) ---
                    cred = credentials.Certificate(local_key_path)
                    firebase_admin.initialize_app(cred)
                else:
                    # --- กรณีรันบน Streamlit Cloud ---
                    # ดึงค่าจาก st.secrets["firebase_service_account"]
                    firebase_secrets = dict(st.secrets["firebase_service_account"])
                    # ล้างค่า \n ให้ถูกต้อง (ป้องกัน Error เวลา Copy วาง)
                    firebase_secrets["private_key"] = firebase_secrets["private_key"].replace("\\n", "\n")
                    
                    cred = credentials.Certificate(firebase_secrets)
                    firebase_admin.initialize_app(cred)

            self.db = firestore.client()
            

        except Exception as e:
            st.error(f"Firebase init error: {e}")
            self.db = None

    # =====================================================
    # 🔥 FIRESTORE METHODS
    # =====================================================

    def create_new_game(self, game_id,company_name):
        self.game_id = game_id

        self.db.collection("mbs_games").document(game_id).set({
            "company_name" : company_name, 
            "created_at": datetime.utcnow(),
            "updated_at" : datetime.utcnow(),
            "status": "active"
        })

    def save_current_round(self):

        if not self.db:
            print("Firebase not initialized")
            return

        df_market = self.get_all_rounds_df()
        df_profit = self.get_all_rounds_net_profit()

        round_ref = (
            self.db.collection("mbs_games")
            .document(self.game_id)
            .collection("rounds")
            .document(f"round_{self.round_number}")
        )

        round_ref.set({
            "round_number": self.round_number,
            "market_data": df_market.to_dict(orient="records"),
            "net_profit": df_profit.to_dict(orient="records"),
            "updated_at": datetime.utcnow()
        })

        self.db.collection("mbs_games").document(self.game_id).update
        ({
            "updated_at" : datetime.utcnow(),
            
        })

        print(f"Round {self.round_number} saved.")

    def load_round(self, round_number):

        doc_ref = (
            self.db.collection("mbs_games")
            .document(self.game_id)
            .collection("rounds")
            .document(f"round_{round_number}")
        )

        doc = doc_ref.get()

        if doc.exists:
            data = doc.to_dict()

            self.round_dfs = [
                pd.DataFrame(data.get("market_data", []))
            ]

            self.round_net_profit = data.get("net_profit", [])
            self.round_number = round_number

            print(f"Loaded round {round_number}")
        else:
            print("Round not found")

    def list_games(self):
        games = self.db.collection("mbs_games").stream()
        return [g.id for g in games]

    def list_rounds(self):
        rounds = (
            self.db.collection("mbs_games")
            .document(self.game_id)
            .collection("rounds")
            .stream()
        )
        return [r.id for r in rounds]

    # =====================================================
    # DATA HANDLING 
    # =====================================================

    def _clean_currency(self, value):
        value = str(value)
        value = value.replace(",", "").replace("$", "")
        if "(" in value:
            value = "-" + value.replace("(", "").replace(")", "")
        return float(value)

    def add_net_profit_text(self, round_number, raw_text):

        df_profit = parse_net_profit_text(raw_text, round_number)

        for _, row in df_profit.iterrows():
            self.round_net_profit.append({
                "round": row["round"],
                "company": row["Company"],
                "Net profit": row["Net profit"]
            })

    def get_all_rounds_df(self):
        if not self.round_dfs:
            return pd.DataFrame()
        return pd.concat(self.round_dfs, ignore_index=True)

    def get_all_rounds_net_profit(self):
        if not self.round_net_profit:
            return pd.DataFrame()
        return pd.DataFrame(self.round_net_profit)
    
    def get_all_rounds_potential_demand(self):
        if not self.round_potential_demand:
            return pd.DataFrame()
        return pd.DataFrame(self.round_potential_demand)

    def get_full_performance_df(self):

        df_main = self.get_all_rounds_df()
        df_profit = self.get_all_rounds_net_profit()

        if df_main.empty and df_profit.empty:
            return pd.DataFrame()

        if df_main.empty:
            return df_profit

        if df_profit.empty:
            return df_main

        df_market = (
            pd.DataFrame(df_main)
            .drop_duplicates(["company", "round", "market_id"])
        )

        df_profit = (
            pd.DataFrame(df_profit)
            .drop_duplicates(["company", "round"])
        )

        df = pd.merge(
            df_market,
            df_profit,
            on=["company", "round"],
            how="left"
        )

        return df
    
    @st.cache_data(ttl=30)
    def load_all_rounds_from_firebase(_self):

        if not _self.db:
            print("Firebase not initialized")
            return pd.DataFrame()

        rounds_ref = (
            _self.db.collection("mbs_games")
            .document(_self.game_id)
            .collection("rounds")
            .stream()
        )

        all_market_data = []
        all_profit_data = []

        for doc in rounds_ref:
            data = doc.to_dict()

            market_data = data.get("market_data", [])
            profit_data = data.get("net_profit", [])

            all_market_data.extend(market_data)
            all_profit_data.extend(profit_data)

        if not all_market_data:
            return pd.DataFrame()

        df_market = pd.DataFrame(all_market_data)
        df_profit = pd.DataFrame(all_profit_data)

        if df_profit.empty:
            return df_market

        df = pd.merge(
            df_market,
            df_profit,
            on=["company", "round"],
            how="left"
        )

        return df
    
    # --------------------------- # company name Handler # --------------------------- 
    @st.cache_data
    def get_company_name(_self, game_id: str):
        doc = (
            _self.db
            .collection("mbs_games")
            .document(game_id)
            .get()
        )

        if doc.exists:
            return doc.to_dict().get("company_name")

        return None
    def set_company_name(self, name): 
        self.company_name = name

    # --------------------------- # Round number Handler # --------------------------- 
    def get_round_number(self):
        return self.round_number 

    def set_round_number(self, round_number):
        self.round_number = round_number

    def add_round_number(self, round_number):
        self.round_number = self.round_number + round_number