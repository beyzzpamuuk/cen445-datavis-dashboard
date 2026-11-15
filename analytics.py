"""Validated data, reproducible aggregation and basket identity for the dashboard."""

from __future__ import annotations

import hashlib
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
import pycountry

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "superstore.csv"
SOURCE_URL = "https://www.kaggle.com/datasets/fatihilhan/global-superstore-dataset"
REPOSITORY_URL = "https://github.com/beyzzpamuuk/cen445-datavis-dashboard"
CATEGORIES = ["Furniture", "Office Supplies", "Technology"]
NUMERIC = ["sales", "profit", "discount", "quantity", "shipping_cost"]
BASKET_COLUMNS = ["country", "order_id", "customer_id", "order_date"]
LABELS = {
    "sales": "Sales (USD)",
    "profit": "Profit (USD)",
    "margin": "Profit margin (%)",
    "discount": "Discount",
    "quantity": "Units",
    "shipping_cost": "Shipping cost (USD)",
    "category": "Category",
    "sub_category": "Sub-category",
    "market": "Market",
    "country": "Country",
    "segment": "Customer segment",
    "ship_mode": "Shipping mode",
    "lines": "Order lines",
    "orders": "Distinct baskets",
    "month": "Month",
}


def load_dataset(path: Path | str = DATA_PATH) -> tuple[pd.DataFrame, dict]:
    """Never impute target profit. Keep valid extreme observations and report each step."""
    path = Path(path)
    try:
        raw = pd.read_csv(path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        raw = pd.read_csv(path, encoding="latin1")
    df = raw.copy()
    df.columns = df.columns.str.strip().str.lower().str.replace(r"[.\s-]+", "_", regex=True)
    required = set(
        NUMERIC + BASKET_COLUMNS + ["category", "sub_category", "segment", "ship_mode", "market", "ship_date"]
    )
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Required columns are missing: {', '.join(missing)}")
    audit = {
        "raw_rows": len(raw),
        "raw_columns": len(raw.columns),
        "missing_cells": int(raw.isna().sum().sum()),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }
    audit["duplicate_rows"] = int(df.duplicated().sum())
    df = df.drop_duplicates().copy()
    for col in df.select_dtypes(include=["object", "str"]).columns:
        df[col] = df[col].astype("string").str.strip().replace("", pd.NA)
    for col in NUMERIC:
        df[col] = pd.to_numeric(df[col], errors="coerce").replace([np.inf, -np.inf], np.nan)
    for col in ["order_date", "ship_date"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    valid = df[NUMERIC + BASKET_COLUMNS + ["category"]].notna().all(axis=1)
    valid &= (df.sales >= 0) & df.discount.between(0, 1) & (df.quantity >= 1)
    valid &= (df.quantity % 1 == 0) & (df.shipping_cost >= 0)
    audit["invalid_rows"] = int((~valid).sum())
    df = df.loc[valid].copy()
    if df.empty:
        raise ValueError("No valid order lines remain after validation.")
    audit["zero_sales_rows"] = int(df.sales.eq(0).sum())
    cat_cols = ["market", "sub_category", "segment", "ship_mode", "region", "city", "state"]
    audit["filled_category_cells"] = 0
    for col in cat_cols:
        if col in df:
            audit["filled_category_cells"] += int(df[col].isna().sum())
            df[col] = df[col].fillna("Unknown")
    old_year = pd.to_numeric(df["year"], errors="coerce") if "year" in df else df.order_date.dt.year
    audit["year_disagreements"] = int((old_year.notna() & old_year.ne(df.order_date.dt.year)).sum())
    df["year"] = df.order_date.dt.year
    df["month"] = df.order_date.dt.to_period("M").dt.to_timestamp()
    df["shipping_days"] = (df.ship_date - df.order_date).dt.days
    audit["invalid_shipping_dates"] = int((df.ship_date.isna() | (df.shipping_days < 0)).sum())
    df.loc[df.shipping_days < 0, "shipping_days"] = np.nan
    # Raw Order.ID is not globally unique. Identity is established BEFORE any filters.
    codes, _ = pd.factorize(pd.MultiIndex.from_frame(df[BASKET_COLUMNS]), sort=True)
    df["basket_id"] = codes
    aliases = {
        "Cote d'Ivoire": "CIV",
        "Democratic Republic of the Congo": "COD",
        "Republic of the Congo": "COG",
        "Macedonia": "MKD",
        "Myanmar (Burma)": "MMR",
        "South Korea": "KOR",
        "Swaziland": "SWZ",
        "Turkey": "TUR",
        "Russia": "RUS",
        "Iran": "IRN",
        "Syria": "SYR",
        "Tanzania": "TZA",
        "Vietnam": "VNM",
    }

    def iso3(name):
        if name in aliases:
            return aliases[name]
        try:
            return pycountry.countries.lookup(name).alpha_3
        except LookupError:
            return None

    df["country_iso3"] = df.country.map({c: iso3(c) for c in df.country.unique()})
    audit["unmapped_countries"] = sorted(df.loc[df.country_iso3.isna(), "country"].unique().tolist())
    conflicts = df.groupby("order_id")[["customer_id", "order_date", "country"]].nunique()
    audit["ambiguous_order_ids"] = int((conflicts.max(axis=1) > 1).sum())
    q1, q3 = df.sales.quantile([0.25, 0.75])
    lower, upper = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
    df["is_outlier"] = ~df.sales.between(lower, upper)
    audit.update(
        clean_rows=len(df),
        removed_rows=len(raw) - len(df),
        outlier_count=int(df.is_outlier.sum()),
        iqr_lower=float(lower),
        iqr_upper=float(upper),
        baskets=int(df.basket_id.nunique()),
        outlier_sales_share=float(df.loc[df.is_outlier, "sales"].sum() / df.sales.sum()),
    )
    return df.reset_index(drop=True), audit


def filter_data(df, markets, categories, years, exclude_outliers=False):
    mask = df.market.isin(markets) & df.category.isin(categories) & df.year.between(*years)
    if exclude_outliers:
        mask &= ~df.is_outlier
    return df.loc[mask].copy()


def summarize(df: pd.DataFrame, by: str | list[str]) -> pd.DataFrame:
    result = (
        df.groupby(by, observed=True, dropna=False)
        .agg(
            sales=("sales", "sum"),
            profit=("profit", "sum"),
            lines=("sales", "size"),
            orders=("basket_id", "nunique"),
            discount=("discount", "mean"),
        )
        .reset_index()
    )
    result["margin"] = np.where(result.sales.ne(0), result.profit / result.sales * 100, np.nan)
    return result


def hierarchy_nodes(df, levels):
    """Explicit totals and ratios at EVERY node; avoid averaging raw profit values."""
    records = []
    for depth in range(len(levels) + 1):
        if depth == 0:
            grouped = [((), df)]
        else:
            grouped = df.groupby(levels[:depth], observed=True, sort=True)
        for key, group in grouped:
            keys = key if isinstance(key, tuple) else (key,)
            if depth == 0:
                keys = ()
            # JSON encodes path components without ambiguous delimiter collisions.
            import json

            node_id = json.dumps(list(keys), ensure_ascii=False)
            parent = json.dumps(list(keys[:-1]), ensure_ascii=False) if depth else ""
            sales, profit = float(group.sales.sum()), float(group.profit.sum())
            records.append(
                {
                    "id": node_id,
                    "parent": parent,
                    "label": str(keys[-1]) if depth else "All selected",
                    "sales": sales,
                    "profit": profit,
                    "margin": profit / sales * 100 if sales else np.nan,
                    "lines": len(group),
                    "depth": depth,
                }
            )
    return pd.DataFrame(records)


def basket_pairs(df):
    baskets = df.groupby("basket_id", observed=True).sub_category.agg(lambda s: sorted(set(s)))
    counts, occurrences = {}, {}
    for items in baskets:
        for item in items:
            occurrences[item] = occurrences.get(item, 0) + 1
        for pair in combinations(items, 2):
            counts[pair] = counts.get(pair, 0) + 1
    total = len(baskets)
    rows = [
        {
            "source": a,
            "target": b,
            "baskets": n,
            "support": n / total,
            "lift": n * total / (occurrences[a] * occurrences[b]),
        }
        for (a, b), n in counts.items()
    ]
    return pd.DataFrame(rows, columns=["source", "target", "baskets", "support", "lift"]).sort_values(
        ["baskets", "source", "target"], ascending=[False, True, True]
    ).reset_index(drop=True), total
