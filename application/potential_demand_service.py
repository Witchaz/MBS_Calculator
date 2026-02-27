import pandas as pd

class DemandService:

    def __init__(self, repository):
        self.repo = repository

    # =====================================================
    # LOAD MARKET RESULTS (actual + potential)
    # =====================================================
    def load_round_demand(self, game_id: str, round_number: int) -> pd.DataFrame:

        round_data = self.repo.load_round_raw(game_id, round_number)

        if not round_data:
            return pd.DataFrame()

        df = pd.DataFrame(round_data.get("potential_demand", []))

        if df.empty:
            return df

        # Derived metric: unmet demand
        df["unsatisfied_demand"] = (
            df["potential_demand"] - df["actual_sales_volume"]
        )

        df["lost_sales_pct"] = (
            df["unsatisfied_demand"] / df["potential_demand"]
        ).fillna(0)

        return df

    # =====================================================
    # CALCULATE POTENTIAL DEMAND (if needed)
    # =====================================================
    def calculate_potential_demand(
        self,
        game_id: str,
        round_number: int,
        base_demand: float
    ) -> float:

        game_data = self.repo.get_game(game_id)

        seasonal = game_data.get("seasonal_indicator", {})

        season_key = self._map_round_to_season(round_number)

        multiplier = seasonal.get(season_key, 100) / 100

        return base_demand * multiplier

    # =====================================================
    # ROUND → SEASON
    # =====================================================
    def _map_round_to_season(self, round_number: int) -> str:

        season_index = (round_number - 1) % 4

        mapping = {
            0: "spring",
            1: "summer",
            2: "autumn",
            3: "winter"
        }

        return mapping[season_index]