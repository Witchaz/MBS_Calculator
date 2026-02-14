import pandas as pd
import json

class DataStore:
    def __init__(self):
        self.round_dfs = []
        self.round_number = 1
        self.round_net_profit = []

    def add_net_profit(self, value):
        try:
            self.round_net_profit.append(float(value))
        except:
            pass  # กัน error แบบง่าย ๆ ไม่ให้ app crash

    def get_all_rounds_df(self):
        if not self.round_dfs:
            return pd.DataFrame()
        return pd.concat(self.round_dfs, ignore_index=True)

    def get_all_rounds_net_profit(self):
        if not self.round_net_profit:
            return pd.DataFrame()
        return pd.concat(self.round_net_profit, ignore_index=True)

    def export_json(self):
        df = self.get_all_rounds_df()
        return df.to_json(orient="records", indent=2)

    def load_json(self, json_str):
        try:
            data = json.loads(json_str)
            df = pd.DataFrame(data)
            self.round_dfs = [df]
        except Exception as e:
            print("Load error:", e)

    def to_stored_markets_format(self):
        df = self.get_all_rounds_df()

        results = []

        for _, row in df.iterrows():
            results.append({
                "round": int(row["Round"]),   
                "market_id": row["market_id"],
                "raw_text": row.to_json()
            })

        return results

