import pandas as pd
import io
import numpy as np
import statsmodels.formula.api as smf
from linearmodels.panel import PanelOLS
import statsmodels.api as sm

# ===== raw string =====
raw_data = """
Company	Product quality	Product image	Price	Sales volume	Market share
Test224	0.48	0.52	$7.29	199,015	3%
Test223	0.94	0.66	$8.19	200,000	3%
Test222	0.65	0.46	$7.50	200,000	3%
Test221	0.75	0.54	$7.50	217,509	4%
Test220	0.17	0.23	$7.50	70,011	1%
Test219	0.21	0.30	$6.70	107,863	2%
Test218	0.22	0.19	$6.50	102,637	2%
Test217	0.61	0.41	$6.00	101,253	2%
Test216	1.07	0.55	$6.80	186,524	3%
Test215	0.27	0.38	$6.50	124,590	2%
Test214	0.27	0.30	$7.50	99,918	2%
Test213	0.23	0.18	$7.00	82,925	1%
Test212	0.52	0.47	$7.25	130,000	2%
Test211	0.22	0.50	$5.60	160,000	3%
Test210	0.70	0.49	$8.00	140,000	2%
Test209	0.19	0.40	$7.00	120,310	2%
Test208	0.47	0.65	$7.99	167,780	3%
Test207	0.47	0.25	$8.79	69,577	1%
Test206	0.27	0.49	$6.20	173,679	3%
Test205	0.84	0.75	$7.00	250,000	4%
Test204	0.30	0.40	$8.00	111,473	2%
Test203	0.76	0.60	$7.50	226,345	4%
Test202	0.50	1.34	$6.50	160,589	3%
Test201	0.22	0.51	$7.60	123,029	2%
Test200	0.71	0.82	$7.20	227,261	4%
Test199	1.09	0.60	$7.50	230,254	4%
Test198	0.75	0.60	$7.80	150,070	3%
Test197	0.30	0.41	$9.00	75,448	1%
Test196	0.92	1.14	$7.30	250,000	4%
Test195	0.24	0.35	$9.00	76,766	1%
Test194	0.40	0.41	$7.50	125,856	2%
Test193	0.75	0.47	$8.50	150,000	3%
Test192	0.58	0.46	$7.70	130,839	2%
Test191	0.27	0.22	$7.70	83,605	1%
Test190	0.29	0.30	$7.10	114,617	2%
Test189	0.25	0.62	$7.30	79,276	1%
Test188	0.17	0.26	$7.50	78,167	1%
Test187	0.59	0.60	$7.00	221,599	4%
Test186	0.71	0.46	$6.89	230,000	4%
Test185	0.82	1.09	$7.50	235,050	4%

"""

# ===== parse string -> DataFrame =====
df = pd.read_csv(io.StringIO(raw_data), sep="\t")

# ===== clean numeric columns =====
df["Price"] = (
    df["Price"]
    .str.replace("$", "", regex=False)
    .astype(float)
)

df["Sales volume"] = (
    df["Sales volume"]
    .str.replace(",", "", regex=False)
    .astype(int)
)

df["Market share"] = (
    df["Market share"]
    .str.replace("%", "", regex=False)
    .astype(float) / 100
)

print(df)
print("\nData types:")
print(df.dtypes)


my_company = "Test200"

# ถ้ายังไม่มี Period ให้สร้างก่อน
df["Period"] = 1

# เรียงข้อมูล
df = df.sort_values(["Period", "Company"])

# เลือก baseline = บริษัทแรกในแต่ละ Period
baseline = df[df["Company"] == my_company]

baseline = baseline.rename(columns={
    "Market share": "share_base",
    "Price": "price_base",
    "Product quality": "quality_base",
    "Product image": "image_base"
})

# merge baseline กลับเข้า df
df = df.merge(
    baseline[["Period", "share_base", "price_base", "quality_base", "image_base"]],
    on="Period"
)

print(df)

# สร้าง log share ratio
df["log_share_ratio"] = np.log(df["Market share"] / df["share_base"])


# สร้าง difference variables
df["d_price"] = df["Price"] - df["price_base"]
df["d_quality"] = df["Product quality"] - df["quality_base"]
df["d_image"] = df["Product image"] - df["image_base"]

model = smf.ols(
    formula="log_share_ratio ~ d_quality + d_image + d_price",
    data=df
).fit()

print(model.summary())

df = df.set_index(['Company', 'Period'])

print(df)
# ตัวแปรอิสระ
X = df[['Product quality', 'Product image', 'Price']]
X = sm.add_constant(X)

# ตัวแปรตาม
y = df['log_share_ratio']

# Fixed Effects (firm FE + time FE)
model = PanelOLS(
    y,
    X,
    entity_effects=True,   # firm fixed effect
    time_effects=True      # Period fixed effect
)

results = model.fit(cov_type='clustered', cluster_entity=True)

print(results.summary)