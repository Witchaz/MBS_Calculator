import numpy as np
import pandas as pd


class DemandEngine:

    def __init__(self, environment_info: dict):
        """
        environment_info ตัวอย่างโครงสร้าง:

        {
            "economy_growth": 97.0,
            "seasonal_index": 102.0,
            "price_elasticity": "High",  # per market จะ override ได้
            "marketing_effect": "Moderate",
            "lifecycle": "High",  # per market จะ override ได้
            "rd_effect": "High"
        }
        """
        self.env = environment_info

    # -----------------------------
    # TEXT → NUMERIC MAPPING
    # -----------------------------

    def _level_to_multiplier(self, level):
        mapping = {
            "Low": 0.8,
            "Moderate": 1.0,
            "Medium": 1.0,
            "High": 1.2
        }
        return mapping.get(level, 1.0)

    def _price_sensitivity(self, level):
        mapping = {
            "Low": -0.5,
            "Moderate": -1.0,
            "High": -1.5
        }
        return mapping.get(level, -1.0)

    # -----------------------------
    # ENVIRONMENT MULTIPLIER
    # -----------------------------

    def environment_multiplier(self, market_lifecycle=None):

        economy = self.env["economy_growth"] / 100.0
        seasonal = self.env["seasonal_index"] / 100.0

        lifecycle_level = market_lifecycle or self.env.get("lifecycle", "Moderate")
        lifecycle = self._level_to_multiplier(lifecycle_level)

        return economy * seasonal * lifecycle

    # -----------------------------
    # DECISION MULTIPLIER
    # -----------------------------

    def decision_multiplier(
        self,
        old_price,
        new_price,
        old_image,
        new_image,
        old_quality,
        new_quality,
        price_elasticity_level,
    ):

        # ----- PRICE EFFECT -----
        price_change = (new_price - old_price) / old_price
        sensitivity = self._price_sensitivity(price_elasticity_level)
        price_effect = 1 + sensitivity * price_change

        # ----- IMAGE EFFECT -----
        image_change = (new_image - old_image) / max(old_image, 1e-6)

        rd_multiplier = self._level_to_multiplier(self.env["rd_effect"])
        image_effect = 1 + rd_multiplier * image_change

        # ----- QUALITY EFFECT -----
        quality_change = (new_quality - old_quality) / max(old_quality, 1e-6)
        quality_effect = 1 + rd_multiplier * quality_change

        return price_effect * image_effect * quality_effect

    # -----------------------------
    # FORECAST FUNCTION
    # -----------------------------

    def forecast_next_round(
        self,
        df_last_round: pd.DataFrame,
        decision_changes: dict = None
    ):
        """
        df_last_round ต้องมี column:

        Market
        Price
        Product_Image
        Product_Quality
        Potential_Demand
        Price_Elasticity (ต่อ market)
        Lifecycle (ต่อ market)

        decision_changes ตัวอย่าง:
        {
            "Market 1": {"Price": 105, "Image": 1.3, "Quality": 1.4},
            "Market 2": {...}
        }

        ถ้า None = baseline mode
        """

        results = []

        for _, row in df_last_round.iterrows():

            market = row["Market"]

            old_price = row["Price"]
            old_image = row["Product_Image"]
            old_quality = row["Product_Quality"]
            old_pd = row["Potential_Demand"]

            price_elasticity = row["Price_Elasticity"]
            lifecycle = row["Lifecycle"]

            # ---- ENV MULTIPLIER ----
            env_mult = self.environment_multiplier(lifecycle)

            # ---- BASELINE CASE ----
            new_price = old_price
            new_image = old_image
            new_quality = old_quality

            if decision_changes and market in decision_changes:
                change = decision_changes[market]
                new_price = change.get("Price", old_price)
                new_image = change.get("Image", old_image)
                new_quality = change.get("Quality", old_quality)

            # ---- DECISION MULTIPLIER ----
            decision_mult = self.decision_multiplier(
                old_price,
                new_price,
                old_image,
                new_image,
                old_quality,
                new_quality,
                price_elasticity
            )

            # ---- FINAL FORECAST ----
            predicted_pd = old_pd * env_mult * decision_mult

            results.append({
                "Market": market,
                "Baseline_PD": old_pd * env_mult,
                "Adjusted_PD": predicted_pd,
                "Delta_%": (predicted_pd / (old_pd * env_mult) - 1) * 100
            })

        return pd.DataFrame(results)
