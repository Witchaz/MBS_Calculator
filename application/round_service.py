import pandas as pd
from typing import List, Dict, Any

from domain.parsers import (
    parse_market_text,
    parse_net_profit_text,
    parse_round_production_dataframe,
    parse_round_potential_demand
)

from domain.feature_engineering import prepare_features


class RoundService:
    """
    Stateless service layer.
    Handles round parsing + persistence.
    """

    def __init__(self, repository):
        self.repo = repository

    # =====================================================
    # SAVE ROUND
    # =====================================================
    def save_round(
        self,
        game_id: str,
        round_number: int,
        market_blocks: Dict[str, str],
        net_profit_text: str = "",
        production_text: str = "",
        potential_demand_text: str = ""
    ) -> None:

        round_dfs = []

        # -----------------------------
        # Parse Market Blocks
        # -----------------------------
        for market_id, market_text in market_blocks.items():

            df = parse_market_text(
                market_text,
                round_number=round_number
            )

            df = prepare_features(df)

            df["market_id"] = market_id

            # 🔥 derive revenue here (schema ใหม่)
            if {"price", "sales_volume"}.issubset(df.columns):
                df["revenue"] = df["price"] * df["sales_volume"]

            round_dfs.append(df)

        if not round_dfs:
            raise ValueError("No valid market data")

        df_market = pd.concat(round_dfs, ignore_index=True)

        # -----------------------------
        # Net Profit (optional)
        # -----------------------------
        df_profit = pd.DataFrame()
        if net_profit_text:
            df_profit = parse_net_profit_text(
                net_profit_text,
                round_number
            )

        # -----------------------------
        # Production (optional)
        # -----------------------------
        df_production = pd.DataFrame()
        if production_text:
            df_production = parse_round_production_dataframe(
                production_text
            )

        # -----------------------------
        # Potential Demand (optional)
        # -----------------------------
        df_potential_demand = pd.DataFrame()
        if potential_demand_text:
            df_potential_demand = parse_round_potential_demand(
                potential_demand_text
            )

        # -----------------------------
        # Persist
        # -----------------------------
        self.repo.save_round(
            game_id=game_id,
            round_number=round_number,
            market_df=df_market,
            profit_df=df_profit,
            production_df=df_production,
            potential_demand_df=df_potential_demand
        )

    # =====================================================
    # READ METHODS
    # =====================================================
    def get_round(self, game_id: str, round_number: int) -> Dict[str, Any]:
        return self.repo.get_full_round(game_id, round_number)

    def get_all_rounds(self, game_id: str) -> List[Dict[str, Any]]:
        return self.repo.get_all_rounds(game_id)

    def get_round_numbers(self, game_id: str) -> List[int]:
        return self.repo.get_round_numbers(game_id)

    def map_rounds_by_number(
        self,
        rounds: List[Dict[str, Any]]
    ) -> Dict[int, Dict[str, Any]]:

        return {
            r["round_number"]: r
            for r in rounds
            if "round_number" in r
        }