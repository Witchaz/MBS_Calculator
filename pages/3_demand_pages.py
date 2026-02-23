import streamlit as st

# =========================
# DATASTORE (Session State)
# =========================

def init_datastore():
    if "env" not in st.session_state:
        st.session_state.env = {
            "macro": {
                "inflation_rate": "Low",
                "economic_growth": 97.0,
                "seasonal_indicators": {
                    "Spring": 102.0,
                    "Summer": 86.0,
                    "Autumn": 80.0,
                    "Winter": 94.0
                },
                "investment_credit": False,
                "tax_rate_level": "Low",
                "accelerated_depreciation": False,
                "interest_rate": 0.08
            },
            "industry": {
                "marketshare_deferred_effect": "Moderate",
                "price_elasticity": {
                    "Market 1": "Moderate",
                    "Market 2": "Low",
                    "Market 3": "High",
                    "Market 4": "High"
                },
                "marketing_campaign_effect": {
                    "Market 1": "Low",
                    "Market 2": "Moderate",
                    "Market 3": "High",
                    "Market 4": "Moderate"
                },
                "market_growth_rate": {
                    "Market 1": "High",
                    "Market 2": "High",
                    "Market 3": "Low",
                    "Market 4": "Medium"
                }
            },
            "internal": {
                "r_and_d_effect": "High",
                "production_mode": "Single shift, overtime allowed",
                "maintenance_effect": "Moderate"
            }
        }

    if "decision" not in st.session_state:
        st.session_state.decision = {
            "marketing_expense": {
                "Market 1": 0.0,
                "Market 2": 0.0,
                "Market 3": 0.0,
                "Market 4": 0.0
            },
            "r_and_d_expense": 0.0
        }

    if "result" not in st.session_state:
        st.session_state.result = {
            "product_image": 1.0,
            "product_quality": 1.0,
            "potential_demand": {
                "Market 1": 0,
                "Market 2": 0,
                "Market 3": 0,
                "Market 4": 0
            }
        }

# =========================
# GET / SET FUNCTIONS
# =========================

def get_env():
    return st.session_state.env

def set_env(data):
    st.session_state.env = data

def get_decision():
    return st.session_state.decision

def set_decision(data):
    st.session_state.decision = data

def get_result():
    return st.session_state.result

def set_result(data):
    st.session_state.result = data

# =========================
# SCORING ENGINE
# =========================

def calculate_product_image():
    total_marketing = sum(st.session_state.decision["marketing_expense"].values())

    # Scale logic (สามารถปรับสูตรได้)
    image_score = 1.0 + (total_marketing / 1_000_000)

    return min(2.0, round(image_score, 2))


def calculate_product_quality():
    rd = st.session_state.decision["r_and_d_expense"]

    effect_multiplier = 1.0
    if st.session_state.env["internal"]["r_and_d_effect"] == "High":
        effect_multiplier = 1.5

    quality_score = 1.0 + (rd / 1_000_000) * effect_multiplier

    return min(2.0, round(quality_score, 2))


def calculate_potential_demand():
    base_demand = 10000
    image = st.session_state.result["product_image"]
    quality = st.session_state.result["product_quality"]

    demand_result = {}

    for market in ["Market 1", "Market 2", "Market 3", "Market 4"]:

        growth_factor = {
            "High": 1.2,
            "Medium": 1.0,
            "Low": 0.8
        }[st.session_state.env["industry"]["market_growth_rate"][market]]

        seasonal_factor = st.session_state.env["macro"]["seasonal_indicators"]["Spring"] / 100

        demand = base_demand * image * quality * growth_factor * seasonal_factor

        demand_result[market] = int(demand)

    return demand_result


# =========================
# STREAMLIT UI
# =========================

st.set_page_config(page_title="Business Simulation", layout="wide")
init_datastore()

st.title("📊 Business Simulation Engine")

st.header("📌 Marketing Decision")

for market in ["Market 1", "Market 2", "Market 3", "Market 4"]:
    st.session_state.decision["marketing_expense"][market] = st.number_input(
        f"{market} Marketing Expense",
        min_value=0.0,
        step=10000.0
    )

st.header("🔬 Global R&D Decision")
st.session_state.decision["r_and_d_expense"] = st.number_input(
    "R&D Expense (Global)",
    min_value=0.0,
    step=10000.0
)

if st.button("🚀 Calculate Next Period"):
    st.session_state.result["product_image"] = calculate_product_image()
    st.session_state.result["product_quality"] = calculate_product_quality()
    st.session_state.result["potential_demand"] = calculate_potential_demand()

st.header("📈 Results")

st.write("### Product Image:", st.session_state.result["product_image"])
st.write("### Product Quality:", st.session_state.result["product_quality"])

st.write("### Potential Demand (Units)")
st.write(st.session_state.result["potential_demand"])
