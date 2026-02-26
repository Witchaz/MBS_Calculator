import pandas as pd
import numpy as np
from firebase_admin import firestore


class InventoryPlanningService:

    def __init__(self, repository):
        self.repo = repository

    # =====================================================
    # LOAD FULL DATASET (เหมือน performance)
    # =====================================================
    def get_full_dataset(self, game_id: str) -> pd.DataFrame:
        rows = []

        rounds_ref = (
        self.repo.db.collection("mbs_games")
        .document(game_id)
        .collection("rounds")
        .order_by("round_number", direction=firestore.Query.DESCENDING)
        .limit(1)
        .stream()
    )

        doc = next(rounds_ref, None)
        data = doc.to_dict()

        production_list = data.get("production", [])
        for i in production_list:
            market_sales = i.get("market_sales", {})
            rows.append({
                "round": i.get("round_number",0),
                "production_volume": i.get("production_volume", 0),
                "capacity": i.get("next_production_capacity", 0),
                "raw_material_inventory": i.get("raw_material_inventory", 0),
                "finished_goods_inventory_total": i.get(
                    "finished_goods_inventory_total", 0),
                "market_1_finished_good":market_sales.get("1", 0),
                "market_2_finished_good":market_sales.get("2", 0),
                "market_3_finished_good":market_sales.get("3", 0),
                "market_4_finished_good":market_sales.get("4", 0)
            })

        df = pd.DataFrame(rows).sort_values("round")

        return df

    # =====================================================
    # SNAPSHOT (เหมือน performance style)
    # =====================================================
    def get_snapshot(self, df_round: pd.DataFrame):

        if df_round.empty:
            return None

        row = df_round.iloc[0]
        return {
            "fg_inventory": float(row["finished_goods_inventory_total"]),
            "rm_inventory": float(row["raw_material_inventory"]),
            "production": float(row["production_volume"]),
            "capacity": float(row["capacity"]),
        }

    # =====================================================
    # PRODUCTION CALCULATION
    # =====================================================
    def compute_production_plan(
        self,
        snapshot: dict,
        forecast_demand: float,
        target_ratio: float
    ):

        fg_inventory = snapshot["fg_inventory"]
        capacity = snapshot["capacity"]

        target_inventory = forecast_demand * target_ratio

        required_production = (
            forecast_demand + target_inventory - fg_inventory
        )

        if required_production < 0:
            required_production = 0

        utilization = (
            required_production / capacity * 100
            if capacity > 0 else 0
        )

        capacity_gap = capacity - required_production

        if capacity == 0:
            risk = "NO_CAPACITY"
        elif required_production > capacity:
            risk = "CAPACITY_SHORTAGE"
        elif required_production == 0:
            risk = "NO_PRODUCTION_NEEDED"
        else:
            risk = "FEASIBLE"

        return {
            "required_production": required_production,
            "target_inventory": target_inventory,
            "utilization_pct": utilization,
            "capacity_gap": capacity_gap,
            "risk": risk,
        }

    # =====================================================
    # UTILITY (เหมือน performance)
    # =====================================================
    def to_scalar(self, value):
        if isinstance(value, pd.Series):
            value = value.iloc[0]
        return float(value)