from datetime import datetime
import pandas as pd


class FirestoreRepository:

    def __init__(self, db):
        self.db = db

    # ---------------------------
    # GAME
    # ---------------------------

    def create_game(self, game_id: str, company_name: str):

        self.db.collection("mbs_games").document(game_id).set({
            "company_name": company_name,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "status": "active"
        })

    def get_company_name(self, game_id: str):

        doc = (
            self.db.collection("mbs_games")
            .document(game_id)
            .get()
        )

        if doc.exists:
            return doc.to_dict().get("company_name")

        return None

    def list_games(self):
        games = self.db.collection("mbs_games").stream()
        return [g.id for g in games]

    # ---------------------------
    # ROUND
    # ---------------------------

    def save_round(self, game_id, round_number,
                   market_df: pd.DataFrame,
                   profit_df: pd.DataFrame,
                   production_df:pd.DataFrame,
                   potential_demand_df:pd.DataFrame
                   ):

        round_ref = (
            self.db.collection("mbs_games")
            .document(game_id)
            .collection("rounds")
            .document(f"round_{round_number}")
        )
        round_ref.set({
            "round_number": round_number,
            "market_data": market_df.to_dict("records"),
            "net_profit": profit_df.to_dict("records"),
            "production":production_df,
            "potential_demand":potential_demand_df,
            "updated_at": datetime.utcnow()
        })
        self.db.collection("mbs_games").document(game_id).update({
            "updated_at": datetime.utcnow()
        })

    def load_round(self, game_id, round_number):

        doc_ref = (
            self.db.collection("mbs_games")
            .document(game_id)
            .collection("rounds")
            .document(f"round_{round_number}")
        )

        doc = doc_ref.get()

        if not doc.exists:
            return None

        data = doc.to_dict()

        df_market = pd.DataFrame(data.get("market_data", []))
        df_profit = pd.DataFrame(data.get("net_profit", []))

        return df_market, df_profit

    def load_all_rounds(self, game_id):

        rounds_ref = (
            self.db.collection("mbs_games")
            .document(game_id)
            .collection("rounds")
            .stream()
        )

        all_market = []
        all_profit = []
        
        for doc in rounds_ref:
            data = doc.to_dict()
            all_market.extend(data.get("market_data", []))
            all_profit.extend(data.get("net_profit", []))
        
        df_market = pd.DataFrame(all_market)
        df_profit = pd.DataFrame(all_profit)

        if df_profit.empty:
            return df_market
        
        return pd.merge(
            df_market,
            df_profit,
            on=["company", "round"],
            how="left"
        )
    
    def load_round_raw(self, game_id, round_number):

        doc_ref = (
            self.db.collection("mbs_games")
            .document(game_id)
            .collection("rounds")
            .document(f"round_{round_number}")
        )

        doc = doc_ref.get()

        if not doc.exists:
            return None

        return doc.to_dict()
    
    