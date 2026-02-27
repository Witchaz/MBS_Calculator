import pandas as pd
from domain.parsers import parse_market_text, parse_net_profit_text, parse_round_production_dataframe, parse_round_potential_demand
from domain.feature_engineering import prepare_features

class RoundService:

    def __init__(self, repository):
        self.repo = repository

    def save_round(
        self,
        game_id,
        round_number,
        market_blocks: dict,
        net_profit_text: str,
        production_text: str,
        potential_demand_text : str
    ):
        round_dfs = []

        for market_id, market_text in market_blocks.items():
            df = parse_market_text(
                market_text,
                round_number=round_number
            )
            df = prepare_features(
                df
            )
            df["market_id"] = market_id
            round_dfs.append(df)

        if not round_dfs:
            raise ValueError("No valid market data")

        df_market = pd.concat(round_dfs, ignore_index=True)

        df_profit = pd.DataFrame()
        if net_profit_text:
            df_profit = parse_net_profit_text(
                net_profit_text,
                round_number
            )

        df_production = pd.DataFrame()
        if production_text:
            df_production = parse_round_production_dataframe(
                production_text
            )

        df_potential_demand = pd.DataFrame()
        if potential_demand_text:
            df_potential_demand = parse_round_potential_demand(potential_demand_text)
        
        self.repo.save_round(
            game_id,
            round_number,
            df_market,
            df_profit,
            df_production,
            df_potential_demand
        )