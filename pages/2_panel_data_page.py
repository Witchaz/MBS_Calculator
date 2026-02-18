import streamlit as st
import pandas as pd
import numpy as np
from core.datastore import DataStore
from mbs_utils import parse_game_text, prepare_features, run_fixed_effects, run_pooled_ols


if "data_store" not in st.session_state:
    st.session_state["data_store"] = DataStore()

data_store = st.session_state["data_store"]

st.title("Insights Data from Sale Status")


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
# Data management 
# -------------------------
st.subheader("Stored Panel Data")

ds = st.session_state.get("data_store", None)

# เลือก source เดียวเท่านั้น
if ds and ds.round_dfs:
    all_markets = ds.to_stored_markets_format()
elif "stored_markets" in st.session_state:
    all_markets = st.session_state.stored_markets
else:
    all_markets = []

# -------------------------
# DEBUG SECTION
# -------------------------
with st.expander("🔍 Debug Panel Data State", expanded=False):
    st.markdown("## 🔎 Debug Info")

    st.write("Total records in all_markets:", len(all_markets))

    # แสดง source breakdown
    stored_count = len(st.session_state.get("stored_markets", []))
    ds_count = 0
    if ds and ds.round_dfs:
        try:
            ds_count = len(ds.to_stored_markets_format())
        except:
            pass

    st.write("stored_markets count:", stored_count)
    st.write("DataStore count:", ds_count)

    # ---- Count per round ----
    round_count = {}
    for item in all_markets:
        round_count.setdefault(item["round"], 0)
        round_count[item["round"]] += 1

    st.write("Count per round:", round_count)

    # ---- Count per (round, market) ----
    market_count = {}
    for item in all_markets:
        key = (item["round"], item["market_id"])
        market_count.setdefault(key, 0)
        market_count[key] += 1

    st.write("Count per (round, Market):", market_count)

    st.markdown("## 🔎 round Debug")

    # ดู round ทั้งหมดที่มี
    round_values = [item.get("round") for item in all_markets]
    st.write("Unique round Values:", sorted(set(round_values)))

    # นับจำนวนต่อ round
    round_count = {}
    for r in round_values:
        round_count.setdefault(r, 0)
        round_count[r] += 1

    st.write("Count per round:", round_count)

    # ดูตัวอย่าง 10 record แรก
    st.write("Sample Records:")
    st.write(all_markets[:10])


if all_markets:

    # ---- Group by round ----
    grouped = {}
    for item in all_markets:
        grouped.setdefault(item["round"], []).append(item)

    for round_id in sorted(grouped.keys()):

        st.markdown(f"### round {round_id}")

        markets = grouped[round_id]

        # ---- Group by market_id ภายใน round ----
        market_group = {}
        for item in markets:
            market_group.setdefault(item["market_id"], []).append(item)

        for market_id in sorted(market_group.keys()):

            teams_in_market = market_group[market_id]

            col1, col2, col3, col4 = st.columns([3,1,1,1])

            # -------- Display --------
            with col1:
                st.write(f"Market {market_id} ({len(teams_in_market)} teams)")


            # -------- Go to Data --------
            with col2:
                st.button(
                    "Go to Data",
                    key=f"go_{round_id}_{market_id}"
                )

            # -------- LOAD MARKET (โหลดทั้ง market) --------
            with col3:

                def load_market(r=round_id, mk=market_id, teams=teams_in_market):
                    st.session_state[f"panel_market_{mk}"] = teams

                st.button(
                    "Load",
                    key=f"load_{round_id}_{market_id}",
                    on_click=load_market
                )

            # -------- DELETE MARKET --------
            with col4:
                if st.button(
                    "Delete",
                    key=f"del_{round_id}_{market_id}"
                ):
                    if "stored_markets" in st.session_state:
                        st.session_state.stored_markets = [
                            x for x in st.session_state.stored_markets
                            if not (
                                x["round"] == round_id and
                                x["market_id"] == market_id
                            )
                        ]
                    st.rerun()
        # -------- DELETE ROUND --------
        if st.button(
            f"Delete round {round_id}",
            key=f"delete_round_{round_id}"
        ):
            if "stored_markets" in st.session_state:
                st.session_state.stored_markets = [
                    x for x in st.session_state.stored_markets
                    if x["round"] != round_id
                ]
            st.rerun()

        st.write("---")

else:
    st.info("No stored panel data available.")


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
                    if df_m.groupby("company")["round"].nunique().min() >= 2:
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

            st.markdown(f"### 🔹 {label}")

            # =========================
            # POOLED
            # =========================
            if pooled is not None and var in pooled.params:

                beta_pooled = pooled.params[var]
                pval_pooled = pooled.pvalues[var]

                effect_pooled = beta_pooled * 5

                direction = "เพิ่มขึ้น" if effect_pooled > 0 else "ลดลง"
                color = "green" if effect_pooled > 0 else "red"

                st.markdown(
                    f"<span style='color:{color}; font-weight:bold'>"
                    f"Pooled OLS: หาก{label}เพิ่มขึ้น 5% "
                    f"สินค้าที่มี{label}สูงกว่าโดยเฉลี่ย "
                    f"มักมีส่วนแบ่งตลาด{direction}ประมาณ {abs(effect_pooled):.2f}%"
                    f"</span>",
                    unsafe_allow_html=True
                )

                # ---- p-value alert ----
                if pval_pooled < 0.05:
                    strength = (0.05 - pval_pooled) / 0.05 * 100
                    st.success(
                        f"✔ มีนัยสำคัญทางสถิติ (p = {pval_pooled:.4f}) "
                        f"ต่ำกว่า 0.05 ประมาณ {strength:.1f}%"
                    )
                else:
                    st.warning(
                        f"✖ ไม่มีนัยสำคัญ (p = {pval_pooled:.4f})"
                    )

            # =========================
            # FIXED EFFECTS
            # =========================
            if fe is not None and var in fe.params:

                beta_fe = fe.params[var]
                pval_fe = fe.pvalues[var]

                effect_fe = beta_fe * 5
                direction = "เพิ่มขึ้น" if effect_fe > 0 else "ลดลง"
                color = "green" if effect_fe > 0 else "red"

                st.markdown(
                    f"<span style='color:{color}; font-weight:bold'>"
                    f"Fixed Effects: หากสินค้าตัวเดิมเพิ่ม{label}ขึ้น 5% "
                    f"ส่วนแบ่งตลาดคาดว่าจะ{direction}ประมาณ {abs(effect_fe):.2f}%"
                    f"</span>",
                    unsafe_allow_html=True
                )

                # ---- p-value alert ----
                if pval_fe < 0.05:
                    strength = (0.05 - pval_fe) / 0.05 * 100
                    st.success(
                        f"✔ มีนัยสำคัญทางสถิติ (p = {pval_fe:.4f}) "
                        f"ต่ำกว่า 0.05 ประมาณ {strength:.1f}%"
                    )
                else:
                    st.warning(
                        f"✖ ไม่มีนัยสำคัญ (p = {pval_fe:.4f})"
                    )

            elif fe is None:
                st.info("Fixed Effects ไม่สามารถคำนวณได้")

        # =====================================================
        # 🔍 Statistical Details
        # =====================================================

        with st.expander("🔍 รายละเอียดทางสถิติ (Pooled OLS)", expanded=False):

            if pooled is not None:

                st.markdown("### 📘 ความหมายของค่าสถิติ (Pooled OLS)")

                st.write("**1️⃣ Coefficients (ค่าสัมประสิทธิ์)**")
                st.write(
                    "แสดงขนาดและทิศทางของผลกระทบของตัวแปรอิสระต่อส่วนแบ่งตลาด "
                    "ค่าเป็นบวกหมายถึงความสัมพันธ์เชิงบวก "
                    "ค่าเป็นลบหมายถึงความสัมพันธ์เชิงลบ "
                    "ในการตีความแบบ log-log: ค่านี้คือ % การเปลี่ยนแปลงของ Market Share "
                    "เมื่อปัจจัยนั้นเพิ่มขึ้น 1%"
                )
                st.dataframe(pooled.params)

                st.write("**2️⃣ P-values (ระดับนัยสำคัญทางสถิติ)**")
                st.write(
                    "ใช้ทดสอบว่าสัมประสิทธิ์แตกต่างจากศูนย์หรือไม่ "
                    "โดยทั่วไปถ้า p-value < 0.05 ถือว่ามีนัยสำคัญทางสถิติ "
                    "หมายถึงเรามีหลักฐานว่าปัจจัยนั้นส่งผลต่อ Market Share จริง"
                )
                st.dataframe(pooled.pvalues)

                st.write("**3️⃣ R-squared (ความสามารถในการอธิบายโมเดล)**")
                st.write(
                    "แสดงสัดส่วนความแปรปรวนของ Market Share "
                    "ที่โมเดลสามารถอธิบายได้ "
                    "เช่น 0.80 หมายถึงโมเดลอธิบายความแปรปรวนได้ 80%"
                )
                st.write(pooled.rsquared)

                st.write("**4️⃣ Correlation Matrix (ความสัมพันธ์เชิงเส้นระหว่างตัวแปร)**")
                st.write(
                    "ใช้ตรวจสอบความสัมพันธ์ระหว่างตัวแปรอิสระ "
                    "หากมีค่าสูงมาก (เช่น > 0.8) อาจเกิดปัญหา Multicollinearity "
                    "ซึ่งทำให้ค่าสัมประสิทธิ์ไม่นิ่ง"
                )
                st.dataframe(
                    df_m[
                        ["product_quality", "price", "product_image", "market_share"]
                    ].corr()
                )

            else:
                st.write("ไม่สามารถคำนวณ Pooled OLS ได้")


        with st.expander("🔍 รายละเอียดทางสถิติ (Product Fixed Effects)", expanded=False):

            if fe is not None:

                st.markdown("### 📘 ความหมายของค่าสถิติ (Fixed Effects)")

                st.write("**1️⃣ Coefficients (Within Effect)**")
                st.write(
                    "แสดงผลกระทบ 'ภายในสินค้าเดียวกัน' เมื่อเวลาผ่านไป "
                    "โมเดลนี้ควบคุมความแตกต่างเฉพาะตัวของแต่ละสินค้า "
                    "ดังนั้นค่าที่ได้สะท้อนผลเชิงสาเหตุได้ดีกว่า Pooled OLS"
                )
                st.dataframe(fe.params)

                st.write("**2️⃣ P-values (ระดับนัยสำคัญทางสถิติ)**")
                st.write(
                    "ตีความเหมือน Pooled OLS "
                    "หาก p-value ต่ำ แสดงว่าการเปลี่ยนแปลงภายในสินค้านั้น "
                    "มีผลต่อ Market Share อย่างมีนัยสำคัญ"
                )
                st.dataframe(fe.pvalues)

                st.write("**3️⃣ R-squared (Within)**")
                st.write(
                    "วัดความสามารถของโมเดลในการอธิบายความแปรปรวน "
                    "ภายในสินค้าเดียวกันข้ามช่วงเวลา "
                    "ไม่รวมความแตกต่างถาวรระหว่างสินค้า"
                )
                st.write(getattr(fe, "rsquared_within", "N/A"))

            else:
                st.write(
                    "Fixed Effects ไม่สามารถประมาณค่าได้ "
                    "(ข้อมูลไม่มี within variation เพียงพอ)"
                )

        st.markdown("---")


