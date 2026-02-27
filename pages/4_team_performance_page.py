import streamlit as st
import pandas as pd

from infrastructure.firebase_client import init_firebase
from infrastructure.firestore_repository import FirestoreRepository
from application.performance_service import PerformanceService
from application.round_service import RoundService


# =====================================================
# INIT SERVICE (Singleton per session)
# =====================================================
@st.cache_resource
def get_service():
    db = init_firebase()
    repo = FirestoreRepository(db)
    return PerformanceService(repo)


performance_service = get_service()

@st.cache_resource
def get_service():
    db = init_firebase()
    repo = FirestoreRepository(db)
    return RoundService(repo)

round_service = get_service()


# =====================================================
# REQUIRE GAME
# =====================================================
if "game_id" not in st.session_state:
    st.error("Please select a game first.")
    st.stop()

game_id = st.session_state["game_id"]
company_name = st.session_state.get("company_name", "")


# =====================================================
# LOAD ALL ROUNDS (ONCE PER GAME)
# =====================================================
if "rounds_data" not in st.session_state or not st.session_state["rounds_data"]:

    raw_rounds = round_service.get_all_rounds(game_id)

    st.session_state["rounds_data"] = {
        r["round_number"]: r
        for r in raw_rounds
    }

rounds_data = st.session_state["rounds_data"]

if not rounds_data:
    st.warning("No data found in this game.")
    st.stop()

# =====================================================
# UI CONFIG
# =====================================================
round_numbers = sorted(rounds_data.keys())
round_tabs = st.tabs([f"Round {r}" for r in round_numbers])

metrics_summary = ["Net profit", "revenue", "sales_volume"]

columns_to_show = [
    "company",
    "product_quality",
    "product_image",
    "sales_volume",
    "price",
    "revenue"
]

metrics = [
    "price",
    "product_quality",
    "product_image",
    "revenue",
    "sales_volume",
    "market_share"
]



# =====================================================
# MAIN LOOP
# =====================================================
for tab, rnd in zip(round_tabs, round_numbers):

    with tab:

        round_doc = rounds_data[rnd]

        if "market_data" not in round_doc:
            st.warning("No market data.")
            continue

        df_round = pd.DataFrame(round_doc["market_data"])

        # ---- inject net profit ----
        if "net_profit" in round_doc:

            df_profit = pd.DataFrame(round_doc["net_profit"])

            if not df_profit.empty:
                df_round = df_round.merge(
                    df_profit,
                    on="company",
                    how="left"
                )
        if "price" in df_round.columns and "sales_volume" in df_round.columns:
            df_round["revenue"] = (
                df_round["price"] * df_round["sales_volume"]
            )
        if df_round.empty:
            st.warning("Empty dataset.")
            continue

        # ================= ROUND SUMMARY =================
        df_summary = performance_service.get_round_summary(df_round)

        if df_summary.empty:
            st.warning("No summary available.")
            continue

        st.subheader("📊 Round Summary")

        st.dataframe(
            df_summary.style.format({
                "Net profit": "{:,.2f}",
                "revenue": "{:,.2f}",
                "sales_volume": "{:,.0f}"
            }),
            width="stretch"
        )

        # ================= SUMMARY METRICS =================
        for metric in metrics_summary:

            if metric not in df_summary.columns:
                continue

            with st.expander(metric):

                df_metric = performance_service.compute_metric_table(
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

                our_row = our_row.iloc[0]
                our_value = our_row[metric]
                our_rank = int(our_row["rank"])
                market_total = df_metric[metric].sum()

                pct_vs_leader = (
                    (our_value - leader[metric]) /
                    abs(leader[metric]) * 100
                ) if leader[metric] != 0 else 0

                pct_vs_avg = (
                    (our_value - market_avg) /
                    abs(market_avg) * 100
                ) if market_avg != 0 else 0

                # KPI ROW 1
                k1, k2, k3, k4 = st.columns(4)
                k1.metric("Leader", leader["company"])
                k2.metric("Round Avg", f"{market_avg:,.2f}")
                k3.metric("Our Rank", f"{our_rank}/{len(df_metric)}")
                k4.metric("Our Value", f"{our_value:,.2f}")

                # KPI ROW 2
                c1, c2 = st.columns(2)
                c1.metric("Vs Leader", f"{pct_vs_leader:+.2f}%")
                c2.metric("Vs Avg", f"{pct_vs_avg:+.2f}%")

                if metric in ["revenue", "sales_volume"]:
                    st.divider()
                    st.metric("🌍 Market Total", f"{market_total:,.2f}")


        # ================= MARKET LEVEL =================
        markets = sorted(df_round["market_id"].unique())
        market_tabs = st.tabs([f"Market {m}" for m in markets])

        for market_tab, market in zip(market_tabs, markets):

            with market_tab:

                df_market = df_round[
                    df_round["market_id"] == market
                ]

                if df_market.empty:
                    st.warning("No market data.")
                    continue

                df_show = df_market[columns_to_show]

                st.dataframe(
                    df_show.style.format({
                        "product_quality": "{:.2f}",
                        "product_image": "{:.2f}",
                        "price": "{:.2f}",
                        "sales_volume": "{:,.0f}",
                        "revenue": "{:,.2f}"
                    }),
                    width="stretch"
                )

                # ================= MARKET METRICS =================
                for metric in metrics:

                    if metric not in df_market.columns:
                        continue

                    with st.expander(metric):

                        df_metric = performance_service.compute_metric_table(
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

                        our_row = our_row.iloc[0]
                        our_value = our_row[metric]
                        our_rank = int(our_row["rank"])

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