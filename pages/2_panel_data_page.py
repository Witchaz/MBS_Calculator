import streamlit as st
import pandas as pd
import numpy as np
from mbs_utils import parse_game_text, prepare_features, run_fixed_effects, run_pooled_ols

data_store = st.session_state["data_store"]

st.title("Multiple Rounds Analysis (Panel Data)")
st.info("For each round, paste all 4 markets below, then add the full round.")



# -------------------------
# Funcitons for Managing Panel Data State
# -------------------------

def rebuild_panel_data():
    grouped = {}
    for m in st.session_state.stored_markets:
        grouped.setdefault(m["round"], []).append(m["df"])

    data_store.round_dfs = [
        pd.concat(grouped[r], ignore_index=True)
        for r in grouped
    ]


def load_market_data(market_index, raw_text):
    st.session_state[f"panel_market_{market_index}"] = raw_text

def clear_market(market_index):
    st.session_state[f"panel_market_{market_index}"] = ""

def has_within_variation(df, group_col, vars_list):
    for var in vars_list:
        # ดูว่าภายในแต่ละ company มีค่ามากกว่า 1 ค่าไหม
        if df.groupby(group_col)[var].nunique().max() <= 1:
            return False
    return True

# -------------------------
# Initialize Persistent State
# -------------------------
if "round_number" not in st.session_state:
    st.session_state.round_number = 1

if "panel_result" not in st.session_state:
    st.session_state.panel_result = None

if "panel_df_all" not in st.session_state:
    st.session_state.panel_df_all = None

if "panel_round" not in st.session_state:
    st.session_state.panel_round = 1

# ถ้ามี flag ให้เพิ่มค่า
if st.session_state.get("increment_round", False):
    st.session_state.panel_round += 1
    st.session_state.increment_round = False


# เก็บ raw text ของแต่ละตลาดที่เคย add แล้ว
if "stored_markets" not in st.session_state:
    st.session_state.stored_markets = []  
    # จะเก็บ dict:
    # {round: x, market: y, raw_text: "...", df: dataframe}

# -------------------------
# Round Number
# -------------------------
data_store.round_number = st.number_input(
    "Round number",
    min_value=1,
    key="panel_round"
)


# -------------------------
# 4 Markets Input
# -------------------------

market_inputs = {}
tabs = st.tabs([f"Market {i}" for i in range(1, 5)])

add_clicked = False  # flag ตรวจว่ากดปุ่มจาก tab ไหน

for idx, tab in enumerate(tabs, start=1):
    with tab:
        market_inputs[idx] = st.text_area(
            f"Paste data for Market {idx}",
            key=f"panel_market_{idx}",
            height=200
        )

        col1, col2 = st.columns(2)

        # -------------------------
        # Add Full Round (อยู่ใน col1)
        # -------------------------
        with col1:
            current_round = getattr(data_store, "round_number", 1)

            if st.button(
                f"Add Round {current_round} (4 Markets)",
                key=f"add_panel_tab_{idx}",
            ):
                add_clicked = True
                st.session_state.round_number += 1
                st.session_state.increment_round = True

                

        # -------------------------
        # Clear Market
        # -------------------------
        with col2:
            st.button(
                f"Clear Market {idx}",
                key=f"clear_market_{idx}",
                on_click=clear_market,
                args=(idx,)
            )

# =====================================================
# ทำ logic Add ข้างล่าง loop (รันแค่ครั้งเดียว)
# =====================================================

if add_clicked:

    try:
        round_id = data_store.round_number

        # ลบ round เดิมถ้ามี
        st.session_state.stored_markets = [
            m for m in st.session_state.stored_markets
            if m["round"] != round_id
        ]

        # Build ใหม่
        for market_id in range(1, 5):

            raw_text = st.session_state[f"panel_market_{market_id}"].strip()

            if not raw_text:
                st.error(f"Market {market_id} is empty.")
                st.stop()

            df = parse_game_text(raw_text)
            df = prepare_features(df, round_number=round_id)
            df["market_id"] = market_id

            st.session_state.stored_markets.append({
                "round": round_id,
                "market": market_id,
                "raw_text": raw_text,
                "df": df
            })

        rebuild_panel_data()

        st.session_state.panel_result = None
        st.session_state.panel_df_all = None

        st.success(f"Round {round_id} saved successfully.")

        data_store.round_number += 1
        st.rerun()

    except Exception as e:
        st.error(str(e))


# -------------------------
# Data management 
# -------------------------
st.subheader("Stored Panel Data")

if st.session_state.stored_markets:

    # ---- Group by Round ----
    grouped = {}
    for item in st.session_state.stored_markets:
        grouped.setdefault(item["round"], []).append(item)

    for round_id in sorted(grouped.keys()):

        st.markdown(f"### Round {round_id}")

        markets = grouped[round_id]

        for m in sorted(markets, key=lambda x: x["market"]):

            col1, col2, col3, col4 = st.columns([3,1,1,1])

            with col1:
                st.write(f"Market {m['market']}")

            # (อนาคต) ปุ่มไปหน้าข้อมูล
            with col2:
                st.button(
                    "Go to Data",
                    key=f"go_{round_id}_{m['market']}"
                )

            # โหลดกลับเข้า parse ช่อง
            with col3:
                st.button(
                    "Load",
                    key=f"load_{round_id}_{m['market']}",
                    on_click=lambda r=m["round"], mk=m["market"], txt=m["raw_text"]:
                        st.session_state.update(
                            {f"panel_market_{mk}": txt}
                        )
                )

            # ลบตลาดเดียว
            with col4:
                if st.button(
                    "Delete",
                    key=f"del_{round_id}_{m['market']}"
                ):
                    st.session_state.stored_markets = [
                        x for x in st.session_state.stored_markets
                        if not (x["round"] == round_id and x["market"] == m["market"])
                    ]
                    st.rerun()

        # ---- Delete Entire Round ----
        if st.button(
            f"Delete Round {round_id}",
            key=f"delete_round_{round_id}"
        ):
            st.session_state.stored_markets = [
                x for x in st.session_state.stored_markets
                if x["round"] != round_id
            ]
            st.rerun()
        st.write("---")
# -------------------------
# Run Panel Analysis
# -------------------------
if st.button("Run Panel Analysis", key="run_panel"):

    if len(data_store.round_dfs) >= 1:   # ✅ เปลี่ยนจาก >=2 เป็น >=1
        try:
            df_all = pd.concat(data_store.round_dfs, ignore_index=True)
            st.session_state.panel_df_all = df_all

            results_by_market = {}
            if "panel_df_all" in st.session_state:

                df_all = st.session_state.panel_df_all

            for market in df_all["market_id"].unique():

                df_m = df_all[df_all["market_id"] == market]

                pooled = None
                fe = None

                # ✅ Pooled OLS ใช้ได้เสมอ
                pooled = run_pooled_ols(df_m)

                vars_to_check = ["log_quality", "log_price", "log_image", "log_marketing"]

                fe = None

                try:
                    # เช็คขั้นต่ำว่ามีมากกว่า 1 รอบ
                    if df_m.groupby("Company")["Round"].nunique().min() >= 2:
                        fe = run_fixed_effects(df_m)
                    else:
                        st.info(
                            f"Market {market}: ต้องมีอย่างน้อย 2 รอบต่อบริษัทสำหรับ Fixed Effects"
                        )

                except Exception as e:
                    st.warning(
                        f"Market {market}: ไม่สามารถประมาณค่า Fixed Effects ได้ "
                        f"(สาเหตุ: {str(e)})"
                    )
                    fe = None


                results_by_market[market] = {
                    "pooled": pooled,
                    "fe": fe
                }

            st.session_state.panel_result = results_by_market

        except Exception as e:
            st.error(str(e))

    else:
        st.warning("Add at least 1 round.")

        
# -------------------------
# Display Results
# -------------------------
if st.session_state.panel_result:

    st.subheader("Panel Data Results")

    results_by_market = st.session_state.panel_result
    df_all = st.session_state.panel_df_all

    for market, result in results_by_market.items():

        pooled = result["pooled"]
        fe = result["fe"]

        df_m = df_all[df_all["market_id"] == market]

        st.markdown(f"## Market {market}")

        # --------- MODEL HEADERS ---------
        if pooled is not None:
            st.write("### Pooled OLS")

        if fe is not None:
            st.write("### Product Fixed Effects")
        else:
            st.info("Market นี้ไม่มีข้อมูลเพียงพอสำหรับ FE")

        # =====================================================
        # 📊 Impact Analysis (อยู่ในแต่ละ Market)
        # =====================================================
        st.subheader("📊 การวิเคราะห์ผลกระทบ (เพิ่มขึ้น 5%)")

        for var, label in [
            ("log_quality", "คุณภาพสินค้า"),
            ("log_price", "ราคา"),
            ("log_image", "ภาพลักษณ์สินค้า"),
            ("log_marketing", "งบการตลาด")
        ]:

            if pooled is not None and var in pooled.params:

                beta_pooled = pooled.params[var]
                effect_pooled = beta_pooled * 5
                dir_pooled = "เพิ่มขึ้น" if effect_pooled > 0 else "ลดลง"

                st.markdown(f"### 🔹 {label}")

                st.write(
                    f"**Pooled OLS:** หาก{label}เพิ่มขึ้น 5% "
                    f"สินค้าที่มีระดับ{label}สูงกว่าโดยเฉลี่ย "
                    f"มักมีส่วนแบ่งตลาด{dir_pooled}ประมาณ {abs(effect_pooled):.2f}%"
                )

                # FE
                if fe is not None and var in fe.params:

                    beta_fe = fe.params[var]
                    effect_fe = beta_fe * 5
                    dir_fe = "เพิ่มขึ้น" if effect_fe > 0 else "ลดลง"

                    st.write(
                        f"**Product Fixed Effects:** หากสินค้าตัวเดิมเพิ่ม{label}ขึ้น 5% "
                        f"ส่วนแบ่งตลาดคาดว่าจะ{dir_fe}ประมาณ {abs(effect_fe):.2f}%"
                    )

                    if (effect_pooled > 0 and effect_fe < 0) or (
                        effect_pooled < 0 and effect_fe > 0
                    ):
                        st.warning(
                            "⚠ Pooled และ Fixed Effects ให้ทิศทางต่างกัน "
                            "ควรพิจารณาผลจาก Fixed Effects สำหรับการตัดสินใจ"
                        )
                else:
                    st.info("Fixed Effects ไม่สามารถคำนวณได้สำหรับตัวแปรนี้")

        # =====================================================
        # 🔍 Statistical Details
        # =====================================================

        with st.expander("🔍 รายละเอียดทางสถิติ (Pooled OLS)", expanded=False):

            if pooled is not None:

                st.write("**Coefficients:**")
                st.dataframe(pooled.params)

                st.write("**P-values:**")
                st.dataframe(pooled.pvalues)

                st.write("**R-squared:**")
                st.write(pooled.rsquared)

                st.write("**Correlation matrix:**")
                st.dataframe(
                    df_m[
                        ["Product quality", "Price", "Product image", "Market share"]
                    ].corr()
                )
            else:
                st.write("ไม่สามารถคำนวณ Pooled OLS ได้")

        with st.expander("🔍 รายละเอียดทางสถิติ (Product Fixed Effects)", expanded=False):

            if fe is not None:

                st.write("**Coefficients (within effect):**")
                st.dataframe(fe.params)

                st.write("**P-values:**")
                st.dataframe(fe.pvalues)

                st.write("**R-squared (within):**")
                st.write(getattr(fe, "rsquared_within", "N/A"))

            else:
                st.write(
                    "Fixed Effects ไม่สามารถประมาณค่าได้ "
                    "(ข้อมูลไม่มี within variation เพียงพอ)"
                )

        st.markdown("---")
