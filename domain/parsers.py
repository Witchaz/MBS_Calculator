import pandas as pd
import re
from io import StringIO


def parse_market_text(raw_text: str, round_number: int) -> pd.DataFrame:
    markets = re.split(r"Market\s+\d+", raw_text)
    market_numbers = re.findall(r"Market\s+(\d+)", raw_text)

    dfs = []

    for market_num, market_block in zip(market_numbers, markets[1:]):
        market_block = market_block.strip()
        if not market_block:
            continue

        df = pd.read_csv(StringIO(market_block), sep="\t")

        df.columns = (
            df.columns
            .str.strip()
            .str.lower()
            .str.replace(" ", "_")
        )

        df["market_id"] = int(market_num)
        df["round"] = round_number

        if "price" in df.columns:
            df["price"] = (
                df["price"].astype(str)
                .str.replace("$", "", regex=False)
                .str.replace(",", "", regex=False)
                .astype(float)
            )

        if "sales_volume" in df.columns:
            df["sales_volume"] = (
                df["sales_volume"].astype(str)
                .str.replace(",", "", regex=False)
                .astype(float)
            )

        if "market_share" in df.columns:
            df["market_share"] = (
                df["market_share"].astype(str)
                .str.replace("%", "", regex=False)
                .astype(float)
            )

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

    df["round"] = int(round_number)

    return df