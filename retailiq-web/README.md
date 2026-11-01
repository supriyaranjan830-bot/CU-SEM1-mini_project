# RetailIQ — Retail Sales Intelligence Dashboard

A browser-based version of the original `retail_dashboard.py`. The analytics and synthetic transaction generation run in **Python** using Pandas and NumPy. FastAPI exposes the analytics to the browser, and Chart.js renders the interactive charts.

> **Data notice:** The built-in dataset is synthetic. It is generated with a fixed random seed (42) and is not connected to a live point-of-sale system or real retailer records.

## Included features

- KPI summary: revenue, orders, average order value, profit, and profit margin
- Monthly revenue and profit trend
- Category revenue contribution and category margin ranking
- Hour-of-day × day-of-week sales heatmap
- Store performance comparison
- Product price vs. unit-volume bubble chart
- Top 15 products by revenue, including units, profit, and margin
- Rule-based trend analysis, store/daily anomaly prompts, and recommendations
- Filters for year, category, region, store, and month range
- CSV exports for product, monthly, and store summaries
- Original terminal-based program preserved as `retail_dashboard_cli.py`

## Run locally on macOS / Linux

Python 3.12 is recommended. From this folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app:app --reload
```

Open **http://127.0.0.1:8000**.

Useful endpoints:

- `/api/health` — service health
- `/api/filters` — available dashboard filters
- `/api/dashboard` — JSON analytics payload
- `/api/export/products` — product CSV
- `/api/export/monthly` — monthly CSV
- `/api/export/stores` — store CSV
- `/api/docs` — interactive API documentation

## Deploy to Vercel

This project uses Vercel's Python runtime with FastAPI. `app.py` exports the FastAPI instance, `requirements.txt` declares Python dependencies, `.python-version` selects Python 3.12, and the browser assets live under `public/`.

### Option A — Deploy with GitHub (recommended)

1. Create a GitHub repository, for example `retailiq-dashboard`.
2. From this project folder, run:

   ```bash
   git init
   git add .
   git commit -m "Build RetailIQ Python dashboard"
   git branch -M main
   git remote add origin https://github.com/YOUR-USERNAME/retailiq-dashboard.git
   git push -u origin main
   ```

3. Sign in at [Vercel](https://vercel.com/), choose **Add New → Project**, and import the repository.
4. Keep the detected Python/FastAPI settings. No frontend build command is required.
5. Select **Deploy**. Vercel will provide the public URL.

### Option B — Deploy using the Vercel CLI

Install and sign in to the Vercel CLI, then run these commands from this project folder:

```bash
npm install -g vercel@latest
vercel login
vercel
```

Follow the prompts to create/link a project. For the production deployment, run:

```bash
vercel --prod
```

## Architecture

```text
Browser
  ├── public/index.html + public/assets/styles.css
  ├── public/assets/app.js + Chart.js
  └── calls /api/*
          │
          ▼
       app.py (FastAPI)
          │
          ▼
       retail_core.py
          ├── NumPy: deterministic transaction simulation
          ├── Pandas: filtering, grouping, KPIs and summaries
          └── Python: anomaly rules, insights and CSV exports
```

The browser is responsible for presentation and interaction. The calculations and data aggregation stay in Python. The app is stateless between requests; the synthetic dataset is cached in a function instance for reuse, but Vercel may create or replace instances at any time.

## Calculation notes

The original formulas are retained where applicable. The annual projection is the selected period's revenue multiplied by **1.12**, matching the original script's fixed 12% uplift assumption. It is a scenario estimate, not an ARIMA model or a trained machine-learning forecast. Store alerts use a one-standard-deviation-below-mean threshold, and daily alerts use a two-standard-deviation threshold.

The source script's CG-like `growth` wording in the top-products heading did not correspond to an implemented growth calculation; the website therefore shows the metrics actually calculated by the script (units, revenue, profit, average price, orders, margin, and status) rather than inventing a product growth metric.

## Project structure

```text
retailiq-web/
├── app.py
├── retail_core.py
├── retail_dashboard_cli.py
├── requirements.txt
├── .python-version
├── vercel.json
└── public/
    ├── index.html
    └── assets/
        ├── app.js
        └── styles.css
```
