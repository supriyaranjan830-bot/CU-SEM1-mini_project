# 📊 Retail Sales Dashboard — Native Python Implementation

## Install & Run

```bash
# Install dependencies
pip install pandas matplotlib seaborn

# Run the dashboard
python retail_dashboard.py
```

## Features (Pure Python)
- **pandas DataFrames** — 20,000+ auto-generated sales records
- **matplotlib + seaborn charts** — saved as high-res PNGs:
  - Monthly revenue trend (line chart)
  - Category breakdown (horizontal bar)
  - Sales heatmap (hour × day-of-week)
  - Store performance comparison
  - Price vs. Volume scatter (bubble chart)
- **KPI Summary** — Revenue, Orders, AOV, Margin, Top Category
- **Top Products Table** — Units, Revenue, Margin %, Status
- **ML Insights** — Trend analysis, anomaly detection (z-score), predictions, recommendations
- **CSV Export** — Products, Monthly, Stores reports

## Generated Charts
After running option 10 ("Generate ALL Charts"), you'll get:
- `chart_monthly_trend.png`
- `chart_category_breakdown.png`
- `chart_heatmap.png`
- `chart_store_performance.png`
- `chart_scatter.png`
