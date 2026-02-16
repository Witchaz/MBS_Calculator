import pandas as pd
import numpy as np
import statsmodels.api as sm
from linearmodels.panel import PanelOLS
from io import StringIO
import streamlit as st

@st.cache_data(show_spinner=False)
def parse_game_text(raw_text):
    """
    Convert copied table text into DataFrame.
    Assumes tab or multiple-space separated columns.
    Adjust delimiter if needed.
    """
    df = pd.read_csv(StringIO(raw_text), sep="\t")
    df["Price"] = df["Price"].str.replace("$", "", regex=False).astype(float)
    df["Sales volume"] = df["Sales volume"].str.replace(",", "", regex=False).astype(int)
    df["Market share"] = df["Market share"].str.replace("%", "", regex=False).astype(float) / 100
    return df

# @st.cache_data(show_spinner=False)
def prepare_features(df, round_number):
    df = df.copy()
    df["Round"] = round_number

    epsilon = 1e-6

    # Fill & clip ทุกตัว
    df["Price"] = df["Price"].fillna(epsilon).clip(lower=epsilon)
    df["Product quality"] = df["Product quality"].fillna(epsilon).clip(lower=epsilon)
    df["Market share"] = df["Market share"].fillna(epsilon).clip(lower=epsilon)
    df["Product image"] = df["Product image"].fillna(0).clip(lower=0)

    # Logs
    df["log_price"] = np.log(df["Price"])
    df["log_quality"] = np.log(df["Product quality"])
    df["log_marketing"] = np.log1p(df["Product image"])
    df["log_share"] = np.log(df["Market share"])

    # Hard clean
    df = df.replace([np.inf, -np.inf], np.nan)

    return df

def interpret_results(params, pvalues):
    results = []
    for var in params.index:
        if var == "const":
            continue
        coef = params[var]
        pval = pvalues[var]
        direction = "increase" if coef > 0 else "decrease"
        significance = (
            "Highly significant" if pval < 0.01 else
            "Significant" if pval < 0.05 else
            "Weak evidence" if pval < 0.1 else
            "Not statistically significant"
        )
        elasticity = round(coef, 3)
        results.append({
            "variable": var,
            "direction": direction,
            "elasticity": elasticity,
            "significance": significance,
            "pval": round(pval, 4)
        })
    return results

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

    df_panel = df_all.set_index(["Company", "Round"])

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
    if df_all["Round"].nunique() >= 2:
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

    df["Round"] = int(round_number)

    return df
