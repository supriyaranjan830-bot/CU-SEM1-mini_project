from __future__ import annotations

from io import StringIO
from pathlib import Path
import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

from retail_core import (
    CATEGORIES, DAYS, REGIONS, STORES, build_csv_report, build_dashboard,
    filter_sales_data, get_sales_data,
)

BASE_DIR = Path(__file__).resolve().parent
PUBLIC_DIR = BASE_DIR / "public"
app = FastAPI(title="RetailIQ Analytics", version="1.0.0", docs_url="/api/docs")
# Locally, FastAPI serves assets. On Vercel, files under public/ are served by its CDN.
if not os.getenv("VERCEL"):
    app.mount("/assets", StaticFiles(directory=PUBLIC_DIR / "assets"), name="assets")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def home() -> HTMLResponse:
    index_file = PUBLIC_DIR / "index.html"
    return HTMLResponse(index_file.read_text(encoding="utf-8"))


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "RetailIQ Analytics", "engine": "Python"}


@app.get("/api/filters")
def filters() -> dict:
    return {
        "categories": CATEGORIES,
        "regions": sorted(set(REGIONS.values())),
        "stores": STORES,
        "days": DAYS,
        "years": [2024, 2025, 2026],
    }


def _filtered_data(
    year: int, category: str, region: str, store: str,
    start_month: int, end_month: int,
):
    if year < 2020 or year > 2035:
        raise HTTPException(status_code=400, detail="Choose a year between 2020 and 2035.")
    valid_categories = ["All categories", *CATEGORIES]
    valid_regions = ["All regions", *sorted(set(REGIONS.values()))]
    valid_stores = ["All stores", *STORES]
    if category not in valid_categories:
        raise HTTPException(status_code=400, detail="Invalid category filter.")
    if region not in valid_regions:
        raise HTTPException(status_code=400, detail="Invalid region filter.")
    if store not in valid_stores:
        raise HTTPException(status_code=400, detail="Invalid store filter.")
    if start_month < 1 or start_month > 12 or end_month < 1 or end_month > 12 or start_month > end_month:
        raise HTTPException(status_code=400, detail="Month range must be between 1 and 12, with start no later than end.")
    return filter_sales_data(
        get_sales_data(year), category=category, region=region, store=store,
        start_month=start_month, end_month=end_month,
    )


@app.get("/api/dashboard")
def dashboard(
    year: int = Query(2024, ge=2020, le=2035),
    category: str = "All categories",
    region: str = "All regions",
    store: str = "All stores",
    start_month: int = Query(1, ge=1, le=12),
    end_month: int = Query(12, ge=1, le=12),
) -> dict:
    df = _filtered_data(year, category, region, store, start_month, end_month)
    return build_dashboard(df, year=year)


@app.get("/api/export/{kind}")
def export_report(
    kind: str,
    year: int = Query(2024, ge=2020, le=2035),
    category: str = "All categories",
    region: str = "All regions",
    store: str = "All stores",
    start_month: int = Query(1, ge=1, le=12),
    end_month: int = Query(12, ge=1, le=12),
) -> Response:
    if kind not in {"products", "monthly", "stores"}:
        raise HTTPException(status_code=404, detail="Report type not found.")
    df = _filtered_data(year, category, region, store, start_month, end_month)
    csv_text = build_csv_report(df, kind)
    filename = f"retailiq_{kind}_{year}.csv"
    return Response(
        content=csv_text,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
