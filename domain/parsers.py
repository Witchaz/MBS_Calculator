import pandas as pd
import re
from io import StringIO

def parse_market_text(raw_text: str, round_number: int) -> pd.DataFrame:
    raw_text = raw_text.strip()

    # 🔥 แก้จุดสำคัญ: แปลง literal "\t" → tab จริง
    raw_text = raw_text.replace("\\t", "\t")

    if re.search(r"Market\s+\d+", raw_text):
        markets = re.split(r"Market\s+\d+", raw_text)
        market_numbers = re.findall(r"Market\s+(\d+)", raw_text)
        blocks = list(zip(market_numbers, markets[1:]))
    else:
        blocks = [("1", raw_text)]

    dfs = []

    for market_num, market_block in blocks:
        market_block = market_block.strip()
        if not market_block:
            continue

        df = pd.read_csv(
            StringIO(market_block),
            sep="\t",              # ตอนนี้ใช้ tab ได้แล้ว
            engine="python"
        )

        df.columns = (
            df.columns
            .str.strip()
            .str.lower()
            .str.replace(r"^\d+\s+", "", regex=True)
            .str.replace(" ", "_")
        )

        df["market_id"] = int(market_num)
        df["round"] = round_number

        # numeric cleaning
        df["price"] = (
            df["price"].astype(str)
            .str.replace("$", "", regex=False)
            .str.replace(",", "", regex=False)
            .astype(float)
        )

        df["sales_volume"] = (
            df["sales_volume"].astype(str)
            .str.replace(",", "", regex=False)
            .astype(float)
        )

        df["market_share"] = (
            df["market_share"].astype(str)
            .str.replace("%", "", regex=False)
            .astype(float)
        )

        df["product_quality"] = df["product_quality"].astype(float)
        df["product_image"] = df["product_image"].astype(float)

        dfs.append(df)

    if not dfs:
        raise ValueError("No valid market data found.")

    return pd.concat(dfs, ignore_index=True)


def parse_net_profit_text(raw_text: str, round_number: int) -> pd.DataFrame:

    if "\t" in raw_text:
        sep = "\t"
    elif "," in raw_text:
        sep = ","
    else:
        sep = r"\s{2,}"

    df = pd.read_csv(StringIO(raw_text), sep=sep, engine="python")

    df.columns = [col.strip() for col in df.columns]

    if "Net profit" in df.columns:
        df["Net profit"] = (
            df["Net profit"]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.replace("$", "", regex=False)
            .str.replace("(", "-", regex=False)
            .str.replace(")", "", regex=False)
            .astype(float)
        )

    df.rename(columns={"Company":"company"},inplace=True)
    df["round"] = int(round_number)
    return df

def parse_multi_round_table(raw_text: str) -> pd.DataFrame:

    df = pd.read_csv(
        StringIO(raw_text),
        sep="\t"
    )

    # ลบ comma
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].str.replace(",", "", regex=False)

    # แปลง numeric
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="ignore")

    return df

def parse_round_production_dataframe(raw_text: str) -> pd.DataFrame:
    """
    Parse production table (1 round or many rounds)
    คืน DataFrame สำหรับส่งเข้า save_round
    """

    raw_text = raw_text.replace(",", "")
    df_raw = pd.read_csv(StringIO(raw_text), sep="\t")

    records = []

    for _, row in df_raw.iterrows():

        record = {
            "round_number": int(row["Round"]),
            "sales_volume": int(row["Sales volume"]),
            "production_volume": int(row["Production volume"]),
            "next_production_capacity": int(row["Next production capacity"]),
            "raw_material_inventory": int(row["Raw material inventory"]),
            "finished_goods_inventory_total": int(
                row["Finished goods inventory(Total)"]
            ),
            "fg_inventory_1": int(row["Market 1"]),
            "fg_inventory_2": int(row["Market 2"]),
            "fg_inventory_3": int(row["Market 3"]),
            "fg_inventory_4": int(row["Market 4"]),
        }

        records.append(record)

    return pd.DataFrame(records)

def parse_round_potential_demand(raw_text: str) -> pd.DataFrame:
    """
    Parse ตาราง Market Demand (1 round)
    คืน DataFrame สำหรับ save_round
    """

    raw_text = raw_text.replace(",", "")
    df_raw = pd.read_csv(StringIO(raw_text), sep="\t")

    records = []

    for _, row in df_raw.iterrows():

        market_label = str(row["Market"]).strip()

        if market_label.lower() == "total":
            continue

        match = re.search(r"\d+", market_label)
        if not match:
            continue

        market_id = match.group()

        records.append({
            "market_id": market_id,
            "potential_demand": int(row["Potential demand"]),
            "actual_sales_volume": int(row["Sales volume"]),
            "market_share_pct": float(row["Market share(%)"]),
            "finished_goods_inventory": int(row["Finished goods inventory"]),
        })

    return pd.DataFrame(records)