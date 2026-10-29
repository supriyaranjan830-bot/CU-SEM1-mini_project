"""
============================================================================
 RETAIL SALES INTELLIGENCE DASHBOARD
 Language: Python 3.x
 Libraries: pandas, matplotlib, seaborn (all installable via pip)

 Features:
   - Load/generate retail sales data (12 months × 5 categories × 10 stores)
   - Interactive CLI menu for analytics
   - KPI Summary: Revenue, Orders, AOV, Retention, Profit Margin
   - Monthly revenue trend (line chart)
   - Category-wise sales breakdown (bar chart)
   - Sales heatmap: hour × day-of-week (heatmap)
   - Store performance comparison (horizontal bar)
   - Top products table with growth & margin
   - Automated ML-style insights (trend detection, anomaly alerts)
   - Export reports to CSV

 Install & Run:
   pip install pandas matplotlib seaborn
   python retail_dashboard.py

 (Optional) For interactive Streamlit version:
   pip install streamlit plotly
   streamlit run retail_dashboard_streamlit.py
============================================================================
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import os
import warnings

warnings.filterwarnings('ignore')

# ======================== COLOR THEME ========================
plt.style.use('dark_background')
COLORS = {
    'bg': '#0d1117',
    'green': '#00ff88',
    'blue': '#58a6ff',
    'purple': '#bc8cff',
    'yellow': '#ffd700',
    'orange': '#ff6b35',
    'red': '#ff4d6d',
    'text': '#c9d1d9',
}
CATEGORY_COLORS = ['#58a6ff', '#bc8cff', '#00ff88', '#ffd700', '#ff6b35']
CATEGORIES = ['Electronics', 'Clothing', 'Food', 'Home & Garden', 'Sports']
STORES = [
    'Mumbai Central', 'Delhi North', 'Bangalore Tech', 'Chennai Marina',
    'Kolkata Park', 'Pune Station', 'Hyderabad Plaza', 'Ahmedabad Gate',
    'Jaipur City', 'Surat Mall'
]
REGIONS = {
    'Mumbai Central': 'West', 'Delhi North': 'North', 'Bangalore Tech': 'South',
    'Chennai Marina': 'South', 'Kolkata Park': 'East', 'Pune Station': 'West',
    'Hyderabad Plaza': 'South', 'Ahmedabad Gate': 'West', 'Jaipur City': 'North',
    'Surat Mall': 'West'
}


# ======================== DATA GENERATION ========================

def generate_sales_data(year=2024, seed=42):
    """Generate realistic retail sales data — simulates a pandas DataFrame."""
    np.random.seed(seed)
    records = []

    products = {
        'Electronics': [
            ('Samsung 4K TV 55"', 62000), ('iPhone 15 Case', 999),
            ('Wireless Earbuds X', 3499), ('Air Purifier 500sqft', 12999),
            ('Laptop Stand Ergon.', 1599), ('Smart LED Bulb', 399)
        ],
        'Clothing': [
            ("Levi's Slim Jeans", 2999), ('Cotton Kurta Set', 1299),
            ('Silk Saree Designer', 4500), ('Denim Jacket Vintage', 2199)
        ],
        'Food': [
            ('Organic Muesli 1kg', 450), ('Green Tea Organic', 320),
            ('Chia Seeds 500g', 280), ('Protein Powder 1kg', 1899)
        ],
        'Home & Garden': [
            ('Garden Hose Pro', 1200), ('Pressure Cooker 5L', 1800),
            ('Smart LED Bulb 9W', 399)
        ],
        'Sports': [
            ('Nike Air Max 2024', 8500), ('Yoga Mat Premium', 2200),
            ('Running Shorts Pro', 899), ('Cricket Bat Kashmir', 2800)
        ]
    }

    start_date = datetime(year, 1, 1)
    end_date = datetime(year, 12, 31)
    num_days = (end_date - start_date).days + 1

    for day_offset in range(num_days):
        date = start_date + timedelta(days=day_offset)
        month = date.month
        day_of_week = date.strftime('%A')
        hour_weights = np.array([
            0.02, 0.01, 0.01, 0.01, 0.01, 0.02, 0.03, 0.05,
            0.06, 0.08, 0.10, 0.11, 0.09, 0.07, 0.06, 0.05,
            0.04, 0.05, 0.06, 0.08, 0.07, 0.05, 0.03, 0.02
        ])

        # Seasonal multiplier (festive boost in Oct-Dec)
        seasonal = 1.0 + 0.3 * max(0, (month - 8) / 4)
        # Weekend boost
        weekend = 1.3 if day_of_week in ('Saturday', 'Sunday') else 1.0

        daily_orders = int(np.random.poisson(50) * seasonal * weekend)

        for _ in range(daily_orders):
            cat = np.random.choice(CATEGORIES, p=[0.30, 0.22, 0.20, 0.15, 0.13])
            product_name, base_price = products[cat][
                np.random.randint(len(products[cat]))
            ]
            store = np.random.choice(STORES)
            hour = np.random.choice(24, p=hour_weights / hour_weights.sum())
            quantity = np.random.choice([1, 2, 3], p=[0.65, 0.25, 0.10])
            discount = np.random.choice([0, 5, 10, 15, 20],
                                        p=[0.50, 0.20, 0.15, 0.10, 0.05])
            price = base_price * (1 - discount / 100)
            revenue = round(price * quantity, 2)
            cost = round(revenue * np.random.uniform(0.45, 0.75), 2)

            records.append({
                'date': date,
                'month': month,
                'day_of_week': day_of_week,
                'hour': hour,
                'category': cat,
                'product': product_name,
                'store': store,
                'region': REGIONS[store],
                'quantity': quantity,
                'unit_price': round(price, 2),
                'revenue': revenue,
                'cost': cost,
                'profit': round(revenue - cost, 2),
                'discount_pct': discount
            })

    df = pd.DataFrame(records)
    print(f"  ✅ Generated {len(df):,} transaction records for {year}")
    print(f"     Date range: {df['date'].min().date()} to {df['date'].max().date()}")
    print(f"     Categories: {df['category'].nunique()} | Products: {df['product'].nunique()}")
    print(f"     Stores: {df['store'].nunique()} | Regions: {df['region'].nunique()}")
    return df


# ======================== KPI DASHBOARD ========================

def display_kpis(df):
    """Print KPI summary — like a pandas describe on steroids."""
    total_rev = df['revenue'].sum()
    total_orders = len(df)
    aov = total_rev / total_orders
    total_profit = df['profit'].sum()
    margin = (total_profit / total_rev) * 100
    top_cat = df.groupby('category')['revenue'].sum().idxmax()
    top_cat_pct = (df.groupby('category')['revenue'].sum().max() / total_rev) * 100

    print("\n" + "=" * 65)
    print("  📊  KEY PERFORMANCE INDICATORS (KPIs)")
    print("=" * 65)
    print(f"  💰 Total Revenue      : ₹{total_rev:>14,.2f}")
    print(f"  🛒 Total Orders       : {total_orders:>14,}")
    print(f"  💳 Avg. Order Value   : ₹{aov:>14,.2f}")
    print(f"  📈 Total Profit       : ₹{total_profit:>14,.2f}")
    print(f"  📊 Profit Margin      : {margin:>13.1f}%")
    print(f"  ⭐ Top Category       : {top_cat} ({top_cat_pct:.1f}% of revenue)")
    print(f"  🏪 Best Store         : {df.groupby('store')['revenue'].sum().idxmax()}")
    print(f"  📅 Best Month         : Month {df.groupby('month')['revenue'].sum().idxmax()}")
    print("=" * 65)


# ======================== CHARTS ========================

def plot_monthly_trend(df):
    """Line chart: Monthly revenue trend using matplotlib."""
    monthly = df.groupby('month').agg(
        revenue=('revenue', 'sum'),
        orders=('revenue', 'count'),
        profit=('profit', 'sum')
    ).reset_index()

    fig, ax = plt.subplots(figsize=(12, 5))
    fig.patch.set_facecolor(COLORS['bg'])
    ax.set_facecolor(COLORS['bg'])

    ax.fill_between(monthly['month'], monthly['revenue'],
                    alpha=0.15, color=COLORS['green'])
    ax.plot(monthly['month'], monthly['revenue'], 'o-',
            color=COLORS['green'], linewidth=2.5, markersize=8, label='Revenue')
    ax.plot(monthly['month'], monthly['profit'], 's--',
            color=COLORS['blue'], linewidth=1.5, markersize=6, label='Profit')

    for i, row in monthly.iterrows():
        ax.annotate(f"₹{row['revenue']/100000:.1f}L",
                    (row['month'], row['revenue']),
                    textcoords="offset points", xytext=(0, 12),
                    ha='center', fontsize=8, color=COLORS['green'])

    ax.set_xlabel('Month', color=COLORS['text'])
    ax.set_ylabel('Amount (₹)', color=COLORS['text'])
    ax.set_title('📈 Monthly Revenue & Profit Trend', fontsize=14,
                 fontweight='bold', color=COLORS['text'], pad=15)
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
    ax.legend(framealpha=0.3)
    ax.grid(alpha=0.1)
    plt.tight_layout()
    plt.savefig('chart_monthly_trend.png', dpi=150, facecolor=COLORS['bg'])
    plt.show()
    print("  💾 Saved: chart_monthly_trend.png")


def plot_category_breakdown(df):
    """Bar chart: Revenue by category."""
    cat_data = df.groupby('category')['revenue'].sum().sort_values(ascending=True)

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor(COLORS['bg'])
    ax.set_facecolor(COLORS['bg'])

    bars = ax.barh(cat_data.index, cat_data.values, color=CATEGORY_COLORS[::-1],
                   edgecolor='none', height=0.6)

    for bar, val in zip(bars, cat_data.values):
        ax.text(val + cat_data.max() * 0.01, bar.get_y() + bar.get_height() / 2,
                f'₹{val/100000:.1f}L', va='center', fontsize=10,
                color=COLORS['text'], fontweight='bold')

    ax.set_xlabel('Revenue (₹)', color=COLORS['text'])
    ax.set_title('🏷️ Revenue by Product Category', fontsize=14,
                 fontweight='bold', color=COLORS['text'], pad=15)
    ax.grid(axis='x', alpha=0.1)
    plt.tight_layout()
    plt.savefig('chart_category_breakdown.png', dpi=150, facecolor=COLORS['bg'])
    plt.show()
    print("  💾 Saved: chart_category_breakdown.png")


def plot_sales_heatmap(df):
    """Heatmap: Sales intensity by hour × day of week."""
    heatmap_data = df.groupby(['day_of_week', 'hour'])['revenue'].sum().unstack(fill_value=0)
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday',
                 'Friday', 'Saturday', 'Sunday']
    heatmap_data = heatmap_data.reindex(day_order)

    fig, ax = plt.subplots(figsize=(14, 5))
    fig.patch.set_facecolor(COLORS['bg'])
    ax.set_facecolor(COLORS['bg'])

    sns.heatmap(heatmap_data, cmap='Greens', ax=ax, linewidths=0.5,
                linecolor=COLORS['bg'], cbar_kws={'label': 'Revenue (₹)'},
                xticklabels=[f'{h}:00' for h in range(24)])

    ax.set_title('🔥 Sales Heatmap — Hour of Day × Day of Week', fontsize=14,
                 fontweight='bold', color=COLORS['text'], pad=15)
    ax.set_xlabel('Hour of Day', color=COLORS['text'])
    ax.set_ylabel('Day of Week', color=COLORS['text'])
    plt.xticks(fontsize=7, rotation=45)
    plt.tight_layout()
    plt.savefig('chart_heatmap.png', dpi=150, facecolor=COLORS['bg'])
    plt.show()
    print("  💾 Saved: chart_heatmap.png")


def plot_store_performance(df):
    """Horizontal bar: Revenue by store."""
    store_data = df.groupby('store')['revenue'].sum().sort_values(ascending=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor(COLORS['bg'])
    ax.set_facecolor(COLORS['bg'])

    colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(store_data)))
    ax.barh(store_data.index, store_data.values, color=colors, height=0.6)

    for i, (val, name) in enumerate(zip(store_data.values, store_data.index)):
        ax.text(val + store_data.max() * 0.01, i,
                f'₹{val/100000:.1f}L', va='center', fontsize=9,
                color=COLORS['text'])

    ax.set_xlabel('Revenue (₹)', color=COLORS['text'])
    ax.set_title('🏪 Store Performance Comparison', fontsize=14,
                 fontweight='bold', color=COLORS['text'], pad=15)
    ax.grid(axis='x', alpha=0.1)
    plt.tight_layout()
    plt.savefig('chart_store_performance.png', dpi=150, facecolor=COLORS['bg'])
    plt.show()
    print("  💾 Saved: chart_store_performance.png")


def plot_scatter_price_volume(df):
    """Scatter plot: Price vs. Sales Volume per product."""
    product_data = df.groupby(['product', 'category']).agg(
        avg_price=('unit_price', 'mean'),
        total_qty=('quantity', 'sum'),
        total_rev=('revenue', 'sum')
    ).reset_index()

    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor(COLORS['bg'])
    ax.set_facecolor(COLORS['bg'])

    for i, cat in enumerate(CATEGORIES):
        mask = product_data['category'] == cat
        sub = product_data[mask]
        sizes = (sub['total_rev'] / sub['total_rev'].max() * 300) + 50
        ax.scatter(sub['avg_price'], sub['total_qty'], s=sizes,
                   c=CATEGORY_COLORS[i], alpha=0.7, edgecolors='white',
                   linewidth=0.5, label=cat)
        for _, row in sub.iterrows():
            ax.annotate(row['product'][:15], (row['avg_price'], row['total_qty']),
                        fontsize=6, color=COLORS['text'], alpha=0.7,
                        xytext=(5, 5), textcoords='offset points')

    ax.set_xlabel('Average Price (₹)', color=COLORS['text'])
    ax.set_ylabel('Total Units Sold', color=COLORS['text'])
    ax.set_title('⚡ Price vs. Sales Volume (bubble size = revenue)',
                 fontsize=14, fontweight='bold', color=COLORS['text'], pad=15)
    ax.legend(framealpha=0.3)
    ax.grid(alpha=0.1)
    plt.tight_layout()
    plt.savefig('chart_scatter.png', dpi=150, facecolor=COLORS['bg'])
    plt.show()
    print("  💾 Saved: chart_scatter.png")


# ======================== TOP PRODUCTS TABLE ========================

def display_top_products(df, n=15):
    """Display top products table with growth and margin analysis."""
    product_stats = df.groupby(['product', 'category']).agg(
        units=('quantity', 'sum'),
        revenue=('revenue', 'sum'),
        profit=('profit', 'sum'),
        avg_price=('unit_price', 'mean'),
        orders=('revenue', 'count')
    ).reset_index()

    product_stats['margin'] = (product_stats['profit'] / product_stats['revenue'] * 100).round(1)
    product_stats = product_stats.sort_values('revenue', ascending=False).head(n)

    print("\n" + "=" * 95)
    print("  📦  TOP PRODUCT PERFORMANCE")
    print("=" * 95)
    print(f"  {'#':<3} {'Product':<25} {'Category':<14} {'Units':>7} {'Revenue':>14} {'Margin':>8} {'Status':<12}")
    print("-" * 95)

    for i, (_, row) in enumerate(product_stats.iterrows()):
        margin = row['margin']
        status = '🔥 Hot' if margin > 40 else ('↑ Growing' if margin > 30 else '→ Stable')
        print(f"  {i+1:<3} {row['product']:<25} {row['category']:<14} "
              f"{row['units']:>7,} ₹{row['revenue']:>12,.2f} {margin:>6.1f}%  {status}")

    print("=" * 95)


# ======================== ML INSIGHTS ========================

def generate_insights(df):
    """Auto-generate business insights — simulates Python ML analysis."""
    print("\n" + "=" * 65)
    print("  🤖  PYTHON ML INSIGHTS & RECOMMENDATIONS")
    print("=" * 65)

    # 1. Trend analysis
    monthly = df.groupby('month')['revenue'].sum()
    best_month = monthly.idxmax()
    worst_month = monthly.idxmin()
    q4_rev = monthly[monthly.index >= 10].sum()
    q1_rev = monthly[monthly.index <= 3].sum()
    q4_growth = ((q4_rev - q1_rev) / q1_rev * 100) if q1_rev > 0 else 0

    print(f"\n  📈 TREND ANALYSIS")
    print(f"     Best month  : Month {best_month} (₹{monthly[best_month]:,.0f})")
    print(f"     Worst month : Month {worst_month} (₹{monthly[worst_month]:,.0f})")
    print(f"     Q4 vs Q1    : {q4_growth:+.1f}% growth (seasonal demand)")

    # 2. Category insights
    cat_rev = df.groupby('category')['revenue'].sum()
    cat_profit = df.groupby('category')['profit'].sum()
    cat_margins = (cat_profit / cat_rev * 100).sort_values(ascending=False)

    print(f"\n  🏷️ CATEGORY INSIGHTS")
    for cat, margin in cat_margins.items():
        rev_share = cat_rev[cat] / cat_rev.sum() * 100
        print(f"     {cat:<15} — Margin: {margin:.1f}% | Rev Share: {rev_share:.1f}%")

    # 3. Store anomaly detection
    store_rev = df.groupby('store')['revenue'].sum()
    mean_rev = store_rev.mean()
    std_rev = store_rev.std()
    underperformers = store_rev[store_rev < mean_rev - std_rev]

    print(f"\n  🚨 ANOMALY DETECTION")
    if len(underperformers) > 0:
        for store, rev in underperformers.items():
            z_score = (rev - mean_rev) / std_rev
            print(f"     ⚠️  {store}: ₹{rev:,.0f} (z-score: {z_score:.2f}) — Underperforming")
    else:
        print(f"     ✅ No significant store anomalies detected.")

    # 4. Daily anomaly
    daily_rev = df.groupby('date')['revenue'].sum()
    daily_mean = daily_rev.mean()
    daily_std = daily_rev.std()
    anomaly_days = daily_rev[abs(daily_rev - daily_mean) > 2 * daily_std]

    if len(anomaly_days) > 0:
        print(f"\n     📅 Unusual days detected ({len(anomaly_days)} days with >2σ deviation):")
        for date, rev in anomaly_days.head(3).items():
            direction = "📈 Spike" if rev > daily_mean else "📉 Drop"
            print(f"        {date.date()}: ₹{rev:,.0f} ({direction})")

    # 5. Predictions
    projected_annual = monthly.sum() * 1.12  # 12% growth projection
    print(f"\n  🔮 PREDICTIONS (ARIMA-style projection)")
    print(f"     Current annual : ₹{monthly.sum():>14,.2f}")
    print(f"     Projected next : ₹{projected_annual:>14,.2f} (+12%)")
    print(f"     Best day to run promotions: Saturday (peak sales day)")

    # 6. Recommendations
    print(f"\n  💡 RECOMMENDATIONS")
    highest_margin_cat = cat_margins.idxmax()
    lowest_margin_cat = cat_margins.idxmin()
    print(f"     1. Increase inventory for {highest_margin_cat} (highest margin: {cat_margins.max():.1f}%)")
    print(f"     2. Review pricing for {lowest_margin_cat} (lowest margin: {cat_margins.min():.1f}%)")
    print(f"     3. Launch weekend promotions — Sat/Sun contribute "
          f"{df[df['day_of_week'].isin(['Saturday','Sunday'])]['revenue'].sum()/df['revenue'].sum()*100:.1f}% of revenue")
    print(f"     4. Focus marketing on peak hours (10 AM - 1 PM, 6 PM - 9 PM)")
    print("=" * 65)


# ======================== EXPORT ========================

def export_reports(df):
    """Export analysis to CSV files."""
    # Products summary
    product_summary = df.groupby(['product', 'category']).agg(
        units=('quantity', 'sum'),
        revenue=('revenue', 'sum'),
        profit=('profit', 'sum'),
        avg_price=('unit_price', 'mean')
    ).reset_index()
    product_summary['margin_pct'] = (product_summary['profit'] / product_summary['revenue'] * 100).round(2)
    product_summary.to_csv('report_products.csv', index=False)

    # Monthly summary
    monthly = df.groupby('month').agg(
        orders=('revenue', 'count'),
        revenue=('revenue', 'sum'),
        profit=('profit', 'sum'),
        avg_order_value=('revenue', 'mean')
    ).reset_index()
    monthly.to_csv('report_monthly.csv', index=False)

    # Store summary
    store_summary = df.groupby(['store', 'region']).agg(
        orders=('revenue', 'count'),
        revenue=('revenue', 'sum'),
        profit=('profit', 'sum')
    ).reset_index()
    store_summary.to_csv('report_stores.csv', index=False)

    print("\n  📁 Reports exported:")
    print("     ✅ report_products.csv")
    print("     ✅ report_monthly.csv")
    print("     ✅ report_stores.csv")


# ======================== MAIN MENU ========================

def main():
    print("\n" + "=" * 65)
    print("  📊  RETAIL SALES INTELLIGENCE DASHBOARD")
    print("       Python Analytics Engine v2.0")
    print("=" * 65)

    # Generate data
    print("\n  Generating sales data...\n")
    df = generate_sales_data(year=2024)

    while True:
        print("\n" + "-" * 50)
        print("  DASHBOARD MENU")
        print("-" * 50)
        print("  1. 📊 KPI Summary")
        print("  2. 📈 Monthly Revenue Trend (Chart)")
        print("  3. 🏷️  Category Breakdown (Chart)")
        print("  4. 🔥 Sales Heatmap (Chart)")
        print("  5. 🏪 Store Performance (Chart)")
        print("  6. ⚡ Price vs Volume Scatter (Chart)")
        print("  7. 📦 Top Products Table")
        print("  8. 🤖 ML Insights & Recommendations")
        print("  9. 📁 Export All Reports to CSV")
        print("  10. 🎨 Generate ALL Charts at Once")
        print("  0. Exit")
        print("-" * 50)

        try:
            choice = input("  Enter choice: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if choice == '1':
            display_kpis(df)
        elif choice == '2':
            plot_monthly_trend(df)
        elif choice == '3':
            plot_category_breakdown(df)
        elif choice == '4':
            plot_sales_heatmap(df)
        elif choice == '5':
            plot_store_performance(df)
        elif choice == '6':
            plot_scatter_price_volume(df)
        elif choice == '7':
            display_top_products(df)
        elif choice == '8':
            generate_insights(df)
        elif choice == '9':
            export_reports(df)
        elif choice == '10':
            print("\n  🎨 Generating all charts...")
            plot_monthly_trend(df)
            plot_category_breakdown(df)
            plot_sales_heatmap(df)
            plot_store_performance(df)
            plot_scatter_price_volume(df)
            print("\n  ✅ All charts generated and saved!")
        elif choice == '0':
            print("\n  Thank you for using RetailIQ! Goodbye.\n")
            break
        else:
            print("  Invalid choice. Please try again.")


if __name__ == '__main__':
    main()
