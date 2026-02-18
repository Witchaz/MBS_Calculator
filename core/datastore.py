import pandas as pd
import json
from io import StringIO
from mbs_utils import parse_net_profit_text

class DataStore:
    def __init__(self):
        self.company_name = ""
        self.round_dfs = []
        self.round_number = 1
        self.round_net_profit = []   # เก็บเป็น list ของ dict ดีกว่า


    # ---------------------------
    # Clean currency helper
    # ---------------------------
    def _clean_currency(self, value):
        value = str(value)
        value = value.replace(",", "").replace("$", "")
        if "(" in value:
            value = "-" + value.replace("(", "").replace(")", "")
        return float(value)


    # ---------------------------
    # Add net profit manually
    # ---------------------------

    def add_net_profit_text(self, round_number, raw_text):

        df_profit = parse_net_profit_text(raw_text, round_number)

        for _, row in df_profit.iterrows():
            self.round_net_profit.append({
                "Round": row["Round"],
                "Company": row["Company"],
                "Net profit": row["Net profit"]
            })



    # ---------------------------
    # Get round df (from JSON load)
    # ---------------------------
    def get_all_rounds_df(self):
        if not self.round_dfs:
            return pd.DataFrame()
        return pd.concat(self.round_dfs, ignore_index=True)


    # ---------------------------
    # Get net profit df
    # ---------------------------
    def get_all_rounds_net_profit(self):
        if not self.round_net_profit:
            return pd.DataFrame()
        return pd.DataFrame(self.round_net_profit)

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
        .drop_duplicates(["Company","Round","market_id"])
    )

        df_profit = (
            pd.DataFrame(df_profit)
            .drop_duplicates(["Company","Round"])
        )


        df = pd.merge(
            df_main,
            df_profit,
            on=["Company", "Round"],
            how="left"
        )

        return df


    # ---------------------------
    # Load JSON (Round + Data string)
    # ---------------------------
    def load_json(self, json_str):
        try:
            data = json.loads(json_str)

            # ถ้าเป็น list ของ dict
            if isinstance(data, list):

                # -------------------------
                # Case 1: Market Data ปกติ
                # -------------------------
                if "Company" in data[0]:
                    df = pd.DataFrame(data)
                    self.round_dfs.append(df)

                # -------------------------
                # Case 2: Net profit แบบ Round + Data
                # -------------------------
                elif "Data" in data[0]:
                    for item in data:
                        round_number = int(item["Round"])
                        csv_string = item["Data"]

                        df_profit = pd.read_csv(StringIO(csv_string))
                        df_profit["Round"] = round_number

                        if "Net profit" in df_profit.columns:
                            df_profit["Net profit"] = df_profit["Net profit"].apply(
                                self._clean_currency
                            )

                        for _, row in df_profit.iterrows():
                            self.round_net_profit.append({
                                "Round": row["Round"],
                                "Company": row["Company"],
                                "Net profit": row["Net profit"]
                            })

            else:
                print("Unsupported JSON structure")

        except Exception as e:
            print("Load error:", e)


    # ---------------------------
    # Export JSON
    # ---------------------------
    def export_json(self):
        df = self.get_all_rounds_df()
        return df.to_json(orient="records", indent=2)


    # ---------------------------
    # Convert to stored markets format
    # ---------------------------
    def to_stored_markets_format(self):
        df = self.get_all_rounds_df()

        results = []

        for _, row in df.iterrows():
            results.append({
                "round": int(row["Round"]),
                "market_id": row.get("market_id"),
                "raw_text": row.to_json()
            })

        return results


    # ---------------------------
    # company name Handler
    # ---------------------------
    
    def get_company_name(self):
        return self.company_name
    
    def set_company_name(self, name):
        self.company_name = name

    # ---------------------------
    # Round number Handler
    # ---------------------------

    def get_round_number(self):
        return self.round_number
    
    def set_round_number(self, number):
        self.round_number = number

    def add_round_number(self, number):
        self.round_number += number   