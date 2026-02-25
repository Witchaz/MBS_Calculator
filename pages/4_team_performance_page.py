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
for round_tab, Round in zip(round_tabs, rounds):

    with round_tab:

        df_round = df[df["round"] == Round]

        # ================= ROUND SUMMARY =================
        df_summary = service.get_round_summary(df_round)
        st.subheader("📊 Round Summary")
        st.dataframe(df_summary.style.format({
        "Net profit": "{:,.2f}",
        "revenue": "{:,.2f}",
        "sales_volume": "{:,.0f}"
    }), width="stretch",)

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

                our_row = df_metric.loc[
                    df_metric["company"] == company_name
                ].iloc[0]

                if our_row.empty:
                    continue
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
                df_show = df_market[columns_to_show]
                st.dataframe(df_show.style.format({
                    "product_quality":"{:.2f}",
                    "product_image":"{:.2f}",
                    "price":"{:.2f}",
                    "sales_volume":"{:,.0f}",
                    "revenue" :"{:,.2f}"
                }), width="stretch")

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

                        # ================= TOP / MIDDLE / BOTTOM 3 (WITH TEAM NAMES) =================

                        st.markdown("---")
                        st.markdown("### Distribution Snapshot (Unweighted)")

                        if metric in df_market.columns:

                            df_sorted = (
                                df_market
                                .dropna(subset=[metric])
                                .sort_values(by=metric, ascending=False)
                                .reset_index(drop=True)
                            )

                            n = len(df_sorted)

                            if n >= 3:

                                top3 = df_sorted.head(3)

                                bottom3 = df_sorted.tail(3).sort_values(
                                    by=metric,
                                    ascending=False
                                )

                                # middle 3 logic
                                if n >= 6:
                                    mid_start = (n // 2) - 1
                                    middle3 = df_sorted.iloc[mid_start:mid_start+3]
                                else:
                                    middle3 = df_sorted.iloc[max(0, n//2-1):n//2+2]

                                col_t, col_m, col_b = st.columns(3)

                                # ---- TOP 3 ----
                                with col_t:
                                    st.markdown("#### 🔼 Top 3")
                                    for _, row in top3.iterrows():
                                        st.write(
                                            f"{row['company']} — {row[metric]:,.2f}"
                                        )

                                # ---- MIDDLE 3 ----
                                with col_m:
                                    st.markdown("#### ⚖ Middle 3")
                                    for _, row in middle3.iterrows():
                                        st.write(
                                            f"{row['company']} — {row[metric]:,.2f}"
                                        )

                                # ---- BOTTOM 3 ----
                                with col_b:
                                    st.markdown("#### 🔽 Bottom 3")
                                    for _, row in bottom3.iterrows():
                                        st.write(
                                            f"{row['company']} — {row[metric]:,.2f}"
                                        )
                        # ================= ROW 3 : MARKET WEIGHTED AVG =================

                        weighted_applicable_metrics = [
                            "price",
                            "product_quality",
                            "product_image"
                        ]

                        if metric in weighted_applicable_metrics:

                            weighted_value = service.compute_weighted_average(
                                df_market,
                                value_col=metric,
                                weight_col="sales_volume"
                            )
                            weighted_value = service.to_scalar(weighted_value)
                            our_value = service.to_scalar(our_row[metric])
                            
                            st.markdown("---")
                            col_w1, col_w2 = st.columns([1,1])

                            col_w1.metric(
                                "Market Weighted Avg",
                                f"{weighted_value:,.2f}"
                            )
                            
                            # Optional: gap vs our value
                            if metric in our_row:
                                gap = our_value - weighted_value
                                col_w2.metric(
                                    "Gap vs Market",
                                    f"{gap:+.2f}"
                                )