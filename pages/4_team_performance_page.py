import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from core.datastore import DataStore


# ---------- INIT SESSION ----------

if "datastore" not in st.session_state:
    st.session_state["datastore"] = DataStore()
ds = st.session_state["datastore"]

if "game_id" not in st.session_state:
    st.error("Please select a game first.")
    st.stop()


# -------------------------
# REQUIRE GAME
# -------------------------
ds.game_id = st.session_state["game_id"]

if ds.get_company_name(ds.game_id) != "":
    st.session_state["company_name"] = \
        ds.get_company_name(ds.game_id)

# -------------------------
# LOAD FROM FIREBASE
# -------------------------
df = ds.load_all_rounds_from_firebase()

if df.empty:
    st.warning("No data found in this game.")
    st.stop()

df = df.drop(
    columns=["log_price","log_quality","log_marketing","log_share"],
    errors="ignore"
)


# ---------- COMPARISON ----------
if st.session_state["company_name"] != "" and not df.empty:

    company_name = st.session_state["company_name"]
    rounds = sorted(df["round"].unique())

    # ---------- ROUND TABS ----------
    round_tabs = st.tabs([f"Round {r}" for r in rounds])

    for round_tab, Round in zip(round_tabs, rounds):

        with round_tab:

            df_round = df[df["round"] == Round]
            markets = sorted(df_round["market_id"].unique())

            # ---------- MARKET TABS ----------
            market_tabs = st.tabs([f"Market {m}" for m in markets])

            for market_tab, market in zip(market_tabs, markets):

                with market_tab:

                    df_market = df_round[
                        df_round["market_id"] == market
                    ].copy()

                    if df_market.empty:
                        st.info("No data available.")
                        continue

                    my_row = df_market[
                        df_market["company"] == company_name
                    ]

                    if my_row.empty:
                        st.info(f"{company_name} not found in this market.")
                        continue

                    my_profit = my_row["Net profit"].iloc[0]

                    df_market["Diff from Us"] = (
                        df_market["Net profit"] - my_profit
                    )

                    df_market["% Diff from Us"] = (
                        df_market["Diff from Us"] / abs(my_profit) * 100
                    ).round(2)
                    df_market = df_market.dropna(subset=["Net profit"])

                    df_market["rank"] = (
                    df_market["Net profit"]
                    .rank(ascending=False, method="min")
                    .astype(int)
                )


                    df_market = df_market.sort_values(
                        "Net profit", ascending=False
                    )

                    df_market["revenue"] = df_market["price"] * df_market["sales_volume"]
                    st.dataframe(df_market, use_container_width=True)
                    
                    
                    # ================= DASHBOARD SUMMARY =================

                    metrics = ["Net profit", "product_image", "product_quality", "revenue", "price", "market_share"]

                    for metric in metrics:

                        if metric not in df_market.columns:
                            continue
                        with st.expander(f"{metric.replace('_',' ')}"):
                            st.markdown(f"## 📊 {metric.replace('_',' ')}")

                            df_metric = df_market.dropna(subset=[metric]).copy()

                            if df_metric.empty:
                                st.info("No data available.")
                                continue

                            # ---------------- SORT + RANK ----------------
                            df_metric = df_metric.sort_values(metric, ascending=False)

                            df_metric["rank"] = (
                                df_metric[metric]
                                .rank(ascending=False, method="min")
                                .astype(int)
                            )

                            leader = df_metric.iloc[0]
                            market_avg = df_metric[metric].mean()

                            our_row = df_metric[df_metric["company"] == company_name]

                            if our_row.empty:
                                continue

                            our_value = our_row[metric].iloc[0]
                            our_rank = int(our_row["rank"].iloc[0])

                            pct_vs_leader = ((our_value - leader[metric]) / abs(leader[metric]) * 100) if leader[metric] != 0 else 0
                            pct_vs_avg = ((our_value - market_avg) / abs(market_avg) * 100) if market_avg != 0 else 0

                            # ================= KPI SECTION =================
                            st.markdown("### 🏆 Market Overview")

                            k1, k2, k3, k4 = st.columns(4)

                            k1.metric("🏆 Market Leader", leader["company"])
                            k2.metric("📈 Market Avg", f"{market_avg:,.2f}")
                            k3.metric("🎯 Our Rank", f"{our_rank}/{len(df_metric)}")
                            k4.metric("📊 Our Value", f"{our_value:,.2f}")

                            c1, c2 = st.columns(2)
                            c1.metric("Vs Leader", f"{pct_vs_leader:+.2f}%")
                            c2.metric("Vs Market Avg", f"{pct_vs_avg:+.2f}%")

                            st.divider()

                            # ================= CLOSEST TO AVERAGE =================
                            st.markdown("### 🎯 Closest to Market Average")

                            df_metric["Diff_from_Avg"] = abs(df_metric[metric] - market_avg)

                            closest_teams = df_metric.sort_values("Diff_from_Avg").head(3)

                            for _, row in closest_teams.iterrows():
                                st.write(
                                    f"{row['company']} — {row[metric]:,.2f} "
                                    f"(Δ {row['Diff_from_Avg']:,.2f})"
                                )

                            st.divider()

                            # ================= TOP / BOTTOM =================
                            left, right = st.columns(2)

                            with left:
                                st.markdown("### 🔥 Top 3")
                                for _, row in df_metric.head(3).iterrows():
                                    st.write(f"{row['rank']}. {row['company']} — {row[metric]:,.2f}")

                            with right:
                                st.markdown("### 🔻 Bottom 3")
                                for _, row in df_metric.tail(3).iterrows():
                                    st.write(f"{row['rank']}. {row['company']} — {row[metric]:,.2f}")

                            st.divider()

                            # ================= FULL TABLE =================
                            st.markdown("### 📋 Full Ranking")
                            with st.expander("See full ranking table", expanded=False):
                                st.dataframe(
                                    df_metric.sort_values("rank"),
                                    use_container_width=True
                                )

                            st.divider()
