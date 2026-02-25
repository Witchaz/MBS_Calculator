import pandas as pd
import statsmodels.api as sm
from linearmodels.panel import PanelOLS


def run_cross_section(df_round: pd.DataFrame):
    X = df_round[["log_price", "log_quality", "log_marketing"]]
    X = sm.add_constant(X)
    y = df_round["log_share"]
    return sm.OLS(y, X).fit()


def run_pooled_ols(df_all: pd.DataFrame):

    df_all = df_all.replace([float("inf"), float("-inf")], None)

    vars_used = ["log_share", "log_price", "log_quality", "log_marketing"]
    df_all = df_all.dropna(subset=vars_used)

    X = df_all[["log_price", "log_quality", "log_marketing"]]
    X = sm.add_constant(X)
    y = df_all["log_share"]

    return sm.OLS(y, X).fit()


def run_fixed_effects(df_all: pd.DataFrame):

    vars_used = ["log_share", "log_price", "log_quality", "log_marketing"]
    df_all = df_all.dropna(subset=vars_used)

    df_panel = df_all.set_index(["company", "round"])

    exog = df_panel[["log_price", "log_quality", "log_marketing"]]
    endog = df_panel["log_share"]

    model = PanelOLS(
        endog,
        exog,
        entity_effects=True,
        drop_absorbed=True
    )

    return model.fit()


def reestimate_all(round_dfs: list):

    df_all = pd.concat(round_dfs, ignore_index=True)

    pooled = run_pooled_ols(df_all)

    fe = None
    if df_all["round"].nunique() >= 2:
        fe = run_fixed_effects(df_all)

    return df_all, pooled, fe