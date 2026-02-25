import streamlit as st
import pandas as pd

from infrastructure.firebase_client import init_firebase
from infrastructure.firestore_repository import FirestoreRepository
from application.performance_service import PerformanceService


# =====================================================
# INIT SERVICE
# =====================================================
@st.cache_resource
def get_service():
    db = init_firebase()
    repo = FirestoreRepository(db)
    return PerformanceService(repo)


service = get_service()


# =====================================================
# REQUIRE GAME
# =====================================================
if "game_id" not in st.session_state:
    st.error("Please select a game first.")
    st.stop()

game_id = st.session_state["game_id"]
company_name = st.session_state.get("company_name", "")


# =====================================================
# LOAD DATA
# =====================================================
df = service.get_full_dataset(game_id)

if df.empty:
    st.warning("No data found in this game.")
    st.stop()


rounds = sorted(df["round"].unique())
round_tabs = st.tabs([f"Round {r}" for r in rounds])


# =====================================================
# MAIN LOOP
# =====================================================
for round_tab, Round in zip(round_tabs, rounds):

    with round_tab:

        df_round = df[df["round"] == Round]

        # ================= ROUND SUMMARY =================
        df_summary = service.get_round_summary(df_round)

        st.subheader("📊 Round Summary")
        st.dataframe(df_summary, width="stretch")

        metrics_summary = ["Net profit", "revenue", "sales_volume"]

        for metric in metrics_summary:

            with st.expander(metric):
                df_metric = service.compute_metric_table(
                    df_summary,
                    metric
                )

                if df_metric.empty:
                    continue

                leader = df_metric.iloc[0]
                market_avg = df_metric[metric].mean()

                our_row = df_metric[
                    df_metric["company"] == company_name
                ]

                if our_row.empty:
                    continue

                our_value = our_row[metric].iloc[0]
                our_rank = int(our_row["rank"].iloc[0])
                market_total = df_metric[metric].sum()

                pct_vs_leader = (
                    (our_value - leader[metric]) /
                    abs(leader[metric]) * 100
                ) if leader[metric] != 0 else 0

                pct_vs_avg = (
                    (our_value - market_avg) /
                    abs(market_avg) * 100
                ) if market_avg != 0 else 0

                # ================= KPI ROW 1 =================
                k1, k2, k3, k4 = st.columns(4)

                k1.metric("Leader", leader["company"])
                k2.metric("Round Avg", f"{market_avg:,.2f}")
                k3.metric("Our Rank", f"{our_rank}/{len(df_metric)}")
                k4.metric("Our Value", f"{our_value:,.2f}")

                # ================= KPI ROW 2 =================
                c1, c2 = st.columns(2)
                c1.metric("Vs Leader", f"{pct_vs_leader:+.2f}%")
                c2.metric("Vs Avg", f"{pct_vs_avg:+.2f}%")

                if metric in ["revenue", "sales_volume"]:
                    st.divider()
                    st.metric(
                        "🌍 Market Total",
                        f"{market_total:,.2f}"
                    )
        # ================= MARKET LEVEL =================
        markets = sorted(df_round["market_id"].unique())

        market_tabs = st.tabs([f"Market {m}" for m in markets])

        for market_tab, market in zip(market_tabs, markets):

            with market_tab:

                df_market = df_round[
                    df_round["market_id"] == market
                ]

                st.dataframe(df_market, width="stretch")

                metrics = [
                    "price",
                    "product_quality",
                    "product_image",
                    "revenue",
                    "sales_volume",
                    "market_share"
                ]

                for metric in metrics:

                    if metric not in df_market.columns:
                        continue

                    with st.expander(metric):

                        df_metric = service.compute_metric_table(
                            df_market,
                            metric
                        )

                        if df_metric.empty:
                            continue

                        leader = df_metric.iloc[0]
                        market_avg = df_metric[metric].mean()

                        our_row = df_metric[
                            df_metric["company"] == company_name
                        ]

                        if our_row.empty:
                            continue

                        our_value = our_row[metric].iloc[0]
                        our_rank = int(our_row["rank"].iloc[0])

                        pct_vs_leader = (
                            (our_value - leader[metric]) /
                            abs(leader[metric]) * 100
                        ) if leader[metric] != 0 else 0

                        pct_vs_avg = (
                            (our_value - market_avg) /
                            abs(market_avg) * 100
                        ) if market_avg != 0 else 0

                        k1, k2, k3, k4 = st.columns(4)

                        k1.metric("Leader", leader["company"])
                        k2.metric("Market Avg", f"{market_avg:,.2f}")
                        k3.metric("Our Rank", f"{our_rank}/{len(df_metric)}")
                        k4.metric("Our Value", f"{our_value:,.2f}")

                        c1, c2 = st.columns(2)
                        c1.metric("Vs Leader", f"{pct_vs_leader:+.2f}%")
                        c2.metric("Vs Avg", f"{pct_vs_avg:+.2f}%")