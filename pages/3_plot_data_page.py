import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from core.datastore import DataStore


if "data_store" not in st.session_state:
    st.session_state["data_store"] = DataStore()

# print(dir(st.session_state["data_store"]))
df = st.session_state["data_store"].round_dfs.copy()
df = pd.concat(df, ignore_index=True)
st.title("3D Strategy Positioning by Market")

print(df)

# ===== เลือกรอบ =====
round_selected = st.selectbox(
    "Select Round",
    sorted(df["Round"].unique())
)


df_round = df[df["Round"] == round_selected].copy()

# =========================
# SIDEBAR FILTER SECTION
# =========================
st.sidebar.header("Filter Controls")

def range_filter(column_name, label):

    col_min = float(df_round[column_name].min())
    col_max = float(df_round[column_name].max())

    enable = st.sidebar.checkbox(
        f"Enable {label}",
        key=f"{column_name}_enable"
    )

    if not enable:
        return False, col_min, col_max

    value = st.sidebar.slider(
        f"{label} Range",
        min_value=col_min,
        max_value=col_max,
        value=(col_min, col_max),
        key=f"{column_name}_slider"
    )

    return True, value[0], value[1]


price_enable, price_min, price_max = range_filter("Price", "Price")
quality_enable, quality_min, quality_max = range_filter("Product quality", "Product Quality")
image_enable, image_min, image_max = range_filter("Product image", "Product Image")
share_enable, share_min, share_max = range_filter("Market share", "Market Share")
sales_enable, sales_min, sales_max = range_filter("Sales volume", "Sales Volume")


# Reset Button (ไม่ล้าง data_store)
if st.sidebar.button("Reset Filters"):
    for key in list(st.session_state.keys()):
        if "_enable" in key or "_slider" in key:
            del st.session_state[key]
    st.rerun()



# -----------------------
# Default values
# -----------------------
DEFAULT_MIN = int(df["Price"].min())
DEFAULT_MAX = int(df["Price"].max())

if "price_range" not in st.session_state:
    st.session_state.price_range = (DEFAULT_MIN, DEFAULT_MAX)

df_filtered = df_round.copy()

if price_enable:
    df_filtered = df_filtered[
        (df_filtered["Price"] >= price_min) &
        (df_filtered["Price"] <= price_max)
    ]

if quality_enable:
    df_filtered = df_filtered[
        (df_filtered["Product quality"] >= quality_min) &
        (df_filtered["Product quality"] <= quality_max)
    ]

if image_enable:
    df_filtered = df_filtered[
        (df_filtered["Product image"] >= image_min) &
        (df_filtered["Product image"] <= image_max)
    ]

if share_enable:
    df_filtered = df_filtered[
        (df_filtered["Market share"] >= share_min) &
        (df_filtered["Market share"] <= share_max)
    ]

if sales_enable:
    df_filtered = df_filtered[
        (df_filtered["Sales volume"] >= sales_min) &
        (df_filtered["Sales volume"] <= sales_max)
    ]



# =========================
# DEBUG INFO
# =========================
st.write(f"Rows after filter: {len(df_filtered)}")

if df_filtered.empty:
    st.warning("No data matches the selected filters.")
    st.stop()


# =========================
# 3D SCATTER PLOT
# =========================
fig = px.scatter_3d(
    df_filtered,
    x="Price",
    y="Product quality",
    z="Product image",
    color="Market share",  # ใช้ market share เป็นสี
    size="Sales volume",   # ใช้ยอดขายเป็นขนาดจุด
    hover_name="Company",     # แสดงชื่อทีมตอน hover
)

fig.update_layout(
    height=700,
    scene=dict(
        xaxis_title="Price",
        yaxis_title="Product Quality",
        zaxis_title="Product Image"
    )
)

st.plotly_chart(fig, use_container_width=True)


# =========================
# TABLE VIEW
# =========================
st.subheader("Filtered Data")
st.dataframe(df_filtered)
