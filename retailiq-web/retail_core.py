"""Python analytics engine adapted from the original Retail Sales Intelligence Dashboard."""
from __future__ import annotations

from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any

import numpy as np
import pandas as pd

CATEGORIES = ["Electronics", "Clothing", "Food", "Home & Garden", "Sports"]
STORES = [
    "Mumbai Central", "Delhi North", "Bangalore Tech", "Chennai Marina",
    "Kolkata Park", "Pune Station", "Hyderabad Plaza", "Ahmedabad Gate",
    "Jaipur City", "Surat Mall",
]
REGIONS = {
    "Mumbai Central": "West", "Delhi North": "North", "Bangalore Tech": "South",
    "Chennai Marina": "South", "Kolkata Park": "East", "Pune Station": "West",
    "Hyderabad Plaza": "South", "Ahmedabad Gate": "West", "Jaipur City": "North",
    "Surat Mall": "West",
}
PRODUCTS = {
    "Electronics": [
        ('Samsung 4K TV 55"', 62000), ("iPhone 15 Case", 999),
        ("Wireless Earbuds X", 3499), ("Air Purifier 500sqft", 12999),
        ("Laptop Stand Ergon.", 1599), ("Smart LED Bulb", 399),
    ],
    "Clothing": [
        ("Levi's Slim Jeans", 2999), ("Cotton Kurta Set", 1299),
        ("Silk Saree Designer", 4500), ("Denim Jacket Vintage", 2199),
    ],
    "Food": [
        ("Organic Muesli 1kg", 450), ("Green Tea Organic", 320),
        ("Chia Seeds 500g", 280), ("Protein Powder 1kg", 1899),
    ],
    "Home & Garden": [
        ("Garden Hose Pro", 1200), ("Pressure Cooker 5L", 1800),
        ("Smart LED Bulb 9W", 399),
    ],
    "Sports": [
        ("Nike Air Max 2024", 8500), ("Yoga Mat Premium", 2200),
        ("Running Shorts Pro", 899), ("Cricket Bat Kashmir", 2800),
    ],
}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def generate_sales_data(year: int = 2024, seed: int = 42) -> pd.DataFrame:
    """Generate the same synthetic retail transaction structure as the CLI program."""
    rng = np.random.RandomState(seed)
    records: list[dict[str, Any]] = []
    start_date = datetime(year, 1, 1)
    end_date = datetime(year, 12, 31)
    num_days = (end_date - start_date).days + 1
    hour_weights = np.array([
        0.02, 0.01, 0.01, 0.01, 0.01, 0.02, 0.03, 0.05,
        0.06, 0.08, 0.10, 0.11, 0.09, 0.07, 0.06, 0.05,
        0.04, 0.05, 0.06, 0.08, 0.07, 0.05, 0.03, 0.02,
    ])
    hour_probabilities = hour_weights / hour_weights.sum()

    for day_offset in range(num_days):
        date = start_date + timedelta(days=day_offset)
        month = date.month
        day_of_week = date.strftime("%A")
        seasonal = 1.0 + 0.3 * max(0, (month - 8) / 4)
        weekend = 1.3 if day_of_week in ("Saturday", "Sunday") else 1.0
        daily_orders = int(rng.poisson(50) * seasonal * weekend)

        for _ in range(daily_orders):
            category = rng.choice(CATEGORIES, p=[0.30, 0.22, 0.20, 0.15, 0.13])
            product_name, base_price = PRODUCTS[category][rng.randint(len(PRODUCTS[category]))]
            store = rng.choice(STORES)
            hour = int(rng.choice(24, p=hour_probabilities))
            quantity = int(rng.choice([1, 2, 3], p=[0.65, 0.25, 0.10]))
            discount = int(rng.choice([0, 5, 10, 15, 20], p=[0.50, 0.20, 0.15, 0.10, 0.05]))
            price = base_price * (1 - discount / 100)
            revenue = round(price * quantity, 2)
            cost = round(revenue * rng.uniform(0.45, 0.75), 2)
            records.append({
                "date": date, "month": month, "day_of_week": day_of_week,
                "hour": hour, "category": category, "product": product_name,
                "store": store, "region": REGIONS[store], "quantity": quantity,
                "unit_price": round(price, 2), "revenue": revenue,
                "cost": cost, "profit": round(revenue - cost, 2),
                "discount_pct": discount,
            })
    return pd.DataFrame.from_records(records)


@lru_cache(maxsize=5)
def get_sales_data(year: int = 2024) -> pd.DataFrame:
    return generate_sales_data(year=year, seed=42)


def filter_sales_data(
    df: pd.DataFrame,
    category: str = "All categories",
    region: str = "All regions",
    store: str = "All stores",
    start_month: int = 1,
    end_month: int = 12,
) -> pd.DataFrame:
    filtered = df
    if category != "All categories":
        filtered = filtered[filtered["category"] == category]
    if region != "All regions":
        filtered = filtered[filtered["region"] == region]
    if store != "All stores":
        filtered = filtered[filtered["store"] == store]
    start_month = max(1, min(12, int(start_month)))
    end_month = max(start_month, min(12, int(end_month)))
    filtered = filtered[filtered["month"].between(start_month, end_month)]
    return filtered.copy()


def _money(value: float) -> float:
    return round(float(value), 2)


def build_dashboard(df: pd.DataFrame, year: int = 2024) -> dict[str, Any]:
    if df.empty:
        return {"year": year, "empty": True, "message": "No transactions match these filters."}

    total_revenue = float(df["revenue"].sum())
    total_orders = int(len(df))
    total_profit = float(df["profit"].sum())
    average_order_value = total_revenue / total_orders if total_orders else 0.0
    profit_margin = (total_profit / total_revenue * 100) if total_revenue else 0.0

    category_revenue = df.groupby("category")["revenue"].sum().reindex(CATEGORIES, fill_value=0)
    category_profit = df.groupby("category")["profit"].sum().reindex(CATEGORIES, fill_value=0)
    category_margin = (category_profit / category_revenue.replace(0, np.nan) * 100).fillna(0)
    best_category = str(category_revenue.idxmax())
    best_category_share = float(category_revenue.max() / total_revenue * 100) if total_revenue else 0

    store_revenue = df.groupby("store")["revenue"].sum().sort_values(ascending=False)
    best_store = str(store_revenue.index[0])

    monthly = df.groupby("month").agg(
        revenue=("revenue", "sum"),
        orders=("revenue", "count"),
        profit=("profit", "sum"),
    ).reindex(range(1, 13), fill_value=0).reset_index()
    best_month = int(monthly.loc[monthly["revenue"].idxmax(), "month"])
    worst_month = int(monthly.loc[monthly["revenue"].idxmin(), "month"])

    category_rows = []
    for cat in CATEGORIES:
        revenue = float(category_revenue[cat])
        category_rows.append({
            "category": cat,
            "revenue": _money(revenue),
            "profit": _money(category_profit[cat]),
            "margin": round(float(category_margin[cat]), 1),
            "share": round(revenue / total_revenue * 100, 1) if total_revenue else 0,
        })

    stores = df.groupby(["store", "region"]).agg(
        orders=("revenue", "count"), revenue=("revenue", "sum"), profit=("profit", "sum")
    ).reset_index().sort_values("revenue", ascending=False)
    store_rows = []
    for row in stores.itertuples(index=False):
        store_rows.append({
            "store": row.store, "region": row.region, "orders": int(row.orders),
            "revenue": _money(row.revenue), "profit": _money(row.profit),
            "margin": round(float(row.profit / row.revenue * 100), 1) if row.revenue else 0,
        })

    product_stats = df.groupby(["product", "category"]).agg(
        units=("quantity", "sum"), revenue=("revenue", "sum"),
        profit=("profit", "sum"), avg_price=("unit_price", "mean"),
        orders=("revenue", "count"),
    ).reset_index()
    product_stats["margin"] = (
        product_stats["profit"] / product_stats["revenue"].replace(0, np.nan) * 100
    ).fillna(0).round(1)
    product_stats = product_stats.sort_values("revenue", ascending=False).head(15)
    products = []
    for row in product_stats.itertuples(index=False):
        margin = float(row.margin)
        status = "Hot" if margin > 40 else ("Growing" if margin > 30 else "Stable")
        products.append({
            "product": row.product, "category": row.category, "units": int(row.units),
            "revenue": _money(row.revenue), "profit": _money(row.profit),
            "avg_price": _money(row.avg_price), "orders": int(row.orders),
            "margin": margin, "status": status,
        })

    heatmap = df.groupby(["day_of_week", "hour"])["revenue"].sum().unstack(fill_value=0)
    heatmap = heatmap.reindex(index=DAYS, columns=range(24), fill_value=0)
    heatmap_values = [[_money(value) for value in heatmap.loc[day].tolist()] for day in DAYS]

    scatter_df = df.groupby(["product", "category"]).agg(
        avg_price=("unit_price", "mean"), total_qty=("quantity", "sum"),
        total_revenue=("revenue", "sum"),
    ).reset_index()
    scatter = []
    for row in scatter_df.itertuples(index=False):
        scatter.append({
            "product": row.product, "category": row.category,
            "avg_price": _money(row.avg_price), "units": int(row.total_qty),
            "revenue": _money(row.total_revenue),
        })

    q4_revenue = float(monthly.loc[monthly["month"] >= 10, "revenue"].sum())
    q1_revenue = float(monthly.loc[monthly["month"] <= 3, "revenue"].sum())
    q4_growth = ((q4_revenue - q1_revenue) / q1_revenue * 100) if q1_revenue > 0 else 0.0
    category_margin_sorted = category_margin.sort_values(ascending=False)

    store_mean = float(store_revenue.mean())
    store_std = float(store_revenue.std()) if len(store_revenue) > 1 else 0.0
    underperformers = []
    if store_std > 0:
        for store_name, revenue in store_revenue.items():
            if revenue < store_mean - store_std:
                underperformers.append({
                    "store": str(store_name), "revenue": _money(revenue),
                    "z_score": round(float((revenue - store_mean) / store_std), 2),
                })

    daily_revenue = df.groupby("date")["revenue"].sum()
    daily_mean = float(daily_revenue.mean()) if len(daily_revenue) else 0.0
    daily_std = float(daily_revenue.std()) if len(daily_revenue) > 1 else 0.0
    daily_anomalies = []
    if daily_std > 0:
        unusual_days = daily_revenue[(daily_revenue - daily_mean).abs() > 2 * daily_std]
        for date, revenue in unusual_days.head(5).items():
            daily_anomalies.append({
                "date": date.strftime("%b %d"), "revenue": _money(revenue),
                "direction": "Spike" if revenue > daily_mean else "Drop",
            })

    weekend_share = float(
        df[df["day_of_week"].isin(["Saturday", "Sunday"])]["revenue"].sum() / total_revenue * 100
    ) if total_revenue else 0.0
    highest_margin_category = str(category_margin_sorted.index[0])
    lowest_margin_category = str(category_margin_sorted.index[-1])

    return {
        "year": year,
        "empty": False,
        "record_count": total_orders,
        "kpis": {
            "revenue": _money(total_revenue), "orders": total_orders,
            "aov": _money(average_order_value), "profit": _money(total_profit),
            "margin": round(profit_margin, 1), "best_category": best_category,
            "best_category_share": round(best_category_share, 1),
            "best_store": best_store, "best_month": best_month,
        },
        "monthly": [
            {"month": int(row.month), "label": MONTHS[int(row.month) - 1],
             "revenue": _money(row.revenue), "profit": _money(row.profit),
             "orders": int(row.orders)}
            for row in monthly.itertuples(index=False)
        ],
        "categories": category_rows,
        "stores": store_rows,
        "products": products,
        "heatmap": {"days": DAYS, "hours": list(range(24)), "values": heatmap_values},
        "scatter": scatter,
        "insights": {
            "best_month": {"month": best_month, "label": MONTHS[best_month - 1],
                           "revenue": _money(monthly.loc[monthly["month"] == best_month, "revenue"].iloc[0])},
            "worst_month": {"month": worst_month, "label": MONTHS[worst_month - 1],
                            "revenue": _money(monthly.loc[monthly["month"] == worst_month, "revenue"].iloc[0])},
            "q4_growth": round(q4_growth, 1),
            "category_margins": [
                {"category": str(name), "margin": round(float(value), 1),
                 "share": round(float(category_revenue[name] / total_revenue * 100), 1) if total_revenue else 0}
                for name, value in category_margin_sorted.items()
            ],
            "store_anomalies": underperformers,
            "daily_anomalies": daily_anomalies,
            "projected_annual_revenue": _money(total_revenue * 1.12),
            "projection_uplift_pct": 12,
            "weekend_revenue_share": round(weekend_share, 1),
            "highest_margin_category": highest_margin_category,
            "lowest_margin_category": lowest_margin_category,
            "promotion_day": "Saturday",
        },
    }


def build_csv_report(df: pd.DataFrame, kind: str) -> str:
    if kind == "products":
        result = df.groupby(["product", "category"]).agg(
            units=("quantity", "sum"), revenue=("revenue", "sum"),
            profit=("profit", "sum"), avg_price=("unit_price", "mean"),
        ).reset_index()
        result["margin_pct"] = (result["profit"] / result["revenue"].replace(0, np.nan) * 100).fillna(0).round(2)
        result = result.sort_values("revenue", ascending=False)
    elif kind == "monthly":
        result = df.groupby("month").agg(
            orders=("revenue", "count"), revenue=("revenue", "sum"),
            profit=("profit", "sum"), avg_order_value=("revenue", "mean"),
        ).reset_index()
    elif kind == "stores":
        result = df.groupby(["store", "region"]).agg(
            orders=("revenue", "count"), revenue=("revenue", "sum"),
            profit=("profit", "sum"),
        ).reset_index().sort_values("revenue", ascending=False)
    else:
        raise ValueError("Unsupported report type")
    return result.to_csv(index=False)
