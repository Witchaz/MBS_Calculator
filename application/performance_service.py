import pandas as pd


class PerformanceService:

    def __init__(self, repository):
        self.repo = repository

    def get_full_dataset(self, game_id: str) -> pd.DataFrame:
        df = self.repo.load_all_rounds(game_id)

        if df.empty:
            return df

        df = df.drop(
            columns=[
                "log_price",
                "log_quality",
                "log_marketing",
                "log_share"
            ],
            errors="ignore"
        )

        df["revenue"] = df["price"] * df["sales_volume"]

        return df

    def get_round_summary(self, df_round: pd.DataFrame):

        df_summary = (
            df_round
            .groupby("company", as_index=False)
            .agg({
                "Net profit": "mean",
                "revenue": "sum",
                "sales_volume": "sum"
            })
        )

        df_summary["rank"] = (
            df_summary["Net profit"]
            .rank(ascending=False, method="min")
            .astype(int)
        )

        return df_summary

    def compute_metric_table(self, df: pd.DataFrame, metric: str):

        df_metric = df.dropna(subset=[metric]).copy()

        df_metric = df_metric.sort_values(metric, ascending=False)

        df_metric["rank"] = (
            df_metric[metric]
            .rank(ascending=False, method="min")
            .astype(int)
        )

        return df_metric