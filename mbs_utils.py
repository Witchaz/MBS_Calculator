import pandas as pd
import numpy as np
import statsmodels.api as sm
from linearmodels.panel import PanelOLS
from io import StringIO
import streamlit as st
@st.cache_data(show_spinner=False)

def parse_game_text(raw_text, round_number: int):

    import pandas as pd
    from io import StringIO
    import re

    # 🔹 แยกแต่ละตลาด
    markets = re.split(r"Market\s+\d+", raw_text)
    market_numbers = re.findall(r"Market\s+(\d+)", raw_text)

    dfs = []

    for market_num, market_block in zip(market_numbers, markets[1:]):
        market_block = market_block.strip()
        if not market_block:
            continue

        df = pd.read_csv(
            StringIO(market_block),
            sep="\t"
        )

        # Standardize column names
        df.columns = (
            df.columns
            .str.strip()
            .str.lower()
            .str.replace(" ", "_")
        )

        df["market_id"] = int(market_num)
        df["round"] = round_number

        # Clean numeric columns
        if "price" in df.columns:
            df["price"] = (
                df["price"]
                .astype(str)
                .str.replace("$", "", regex=False)
                .str.replace(",", "", regex=False)
                .astype(float)
            )

        if "sales_volume" in df.columns:
            df["sales_volume"] = (
                df["sales_volume"]
                .astype(str)
                .str.replace(",", "", regex=False)
                .astype(float)
            )

        if "market_share" in df.columns:
            df["market_share"] = (
                df["market_share"]
                .astype(str)
                .str.replace("%", "", regex=False)
                .astype(float)
            )

        dfs.append(df)

    final_df = pd.concat(dfs, ignore_index=True)
    return final_df


def prepare_features(df, round_number):
    df = df.copy()
    df["round"] = round_number

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

# @st.cache_data(show_spinner=False)
def run_cross_section(df_round):
    X = df_round[["log_price", "log_quality", "log_marketing"]]
    X = sm.add_constant(X)
    y = df_round["log_share"]
    model = sm.OLS(y, X).fit()
    return model

# @st.cache_data(show_spinner=False)
def run_pooled_ols(df_all):
    

    df_all = df_all.replace([np.inf, -np.inf], np.nan)

    vars_used = ["log_share", "log_price", "log_quality", "log_marketing"]
    df_all = df_all.dropna(subset=vars_used)

    X = df_all[["log_price", "log_quality", "log_marketing"]]
    X = sm.add_constant(X)
    y = df_all["log_share"]

    model = sm.OLS(y, X).fit()

    return model

# @st.cache_data(show_spinner=False)
def run_fixed_effects(df_all):

    df_all = df_all.replace([np.inf, -np.inf], np.nan)

    vars_used = ["log_share", "log_price", "log_quality", "log_marketing"]

    df_all = df_all.dropna(subset=vars_used)

    df_panel = df_all.set_index(["company", "round"])

    exog = df_panel[["log_price", "log_quality", "log_marketing"]]
    endog = df_panel["log_share"]

    model = PanelOLS(
    endog,
    exog,
    entity_effects=True,
    drop_absorbed=True   # ใส่ตรงนี้
    )
    result = model.fit()


    return result


# @st.cache_data(show_spinner=False)
def reestimate_all(round_dfs):
    df_all = pd.concat(round_dfs, ignore_index=True)
    pooled = run_pooled_ols(df_all)
    fe = None
    if df_all["round"].nunique() >= 2:
        fe = run_fixed_effects(df_all)
    return df_all, pooled, fe

@st.cache_data(show_spinner=False)
def parse_net_profit_text(raw_text, round_number):
    """
    Parse copied Net Profit table text into clean DataFrame.
    Supports tab, comma, or multi-space separated columns.
    """

    # auto-detect separator
    if "\t" in raw_text:
        sep = "\t"
    elif "," in raw_text:
        sep = ","
    else:
        sep = r"\s{2,}"  # multiple spaces

    df = pd.read_csv(StringIO(raw_text), sep=sep, engine="python")

    # Standardize column names
    df.columns = [col.strip() for col in df.columns]

    # Clean Net profit
    if "Net profit" in df.columns:
        df["Net profit"] = (
            df["Net profit"]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.replace("$", "", regex=False)
            .str.replace("(", "-", regex=False)
            .str.replace(")", "", regex=False)
            .astype(float)
        )

    df["round"] = int(round_number)

    return df
