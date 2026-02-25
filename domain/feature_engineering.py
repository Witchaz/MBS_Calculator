import numpy as np
import pandas as pd


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:

    df = df.copy()
    epsilon = 1e-6

    df["price"] = df["price"].fillna(epsilon).clip(lower=epsilon)
    df["product_quality"] = df["product_quality"].fillna(epsilon).clip(lower=epsilon)
    df["market_share"] = df["market_share"].fillna(epsilon).clip(lower=epsilon)
    df["product_image"] = df["product_image"].fillna(0).clip(lower=0)

    df["log_price"] = np.log(df["price"])
    df["log_quality"] = np.log(df["product_quality"])
    df["log_marketing"] = np.log1p(df["product_image"])
    df["log_share"] = np.log(df["market_share"])

    df = df.replace([np.inf, -np.inf], np.nan)

    return df