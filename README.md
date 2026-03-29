# 🛒 Amazon India: A Decade of Sales Analytics (2015–2025)

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red?logo=streamlit)
![Pandas](https://img.shields.io/badge/Pandas-2.0+-green?logo=pandas)
![SQLite](https://img.shields.io/badge/SQLite-3-blue?logo=sqlite)
![Plotly](https://img.shields.io/badge/Plotly-5.18+-purple?logo=plotly)
![License](https://img.shields.io/badge/License-MIT-yellow)

> An end-to-end e-commerce analytics platform built on Amazon India's 10-year transactional data (2015–2025). From raw messy CSVs to a professional interactive business intelligence dashboard — covering data cleaning, EDA, SQL database design, and Streamlit deployment.

---

## 📋 Table of Contents

- [Project Overview](#-project-overview)
- [Live Demo](#-live-demo)
- [Project Structure](#-project-structure)
- [Dataset Overview](#-dataset-overview)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Setup & Installation](#-setup--installation)
- [Running the Pipeline](#-running-the-pipeline)
- [Dashboard Pages](#-dashboard-pages)
- [Database Schema](#-database-schema)
- [Key Insights](#-key-insights)
- [Deploy to Streamlit Cloud](#-deploy-to-streamlit-cloud)
- [Contributors](#-contributors)

---

## 🎯 Project Overview

This project builds a **comprehensive e-commerce analytics platform** that demonstrates a complete data science workflow:

| Stage | Description | Output |
|-------|-------------|--------|
| **1. Data Ingestion** | Load 11 year-wise CSVs + product catalog | Raw DataFrames |
| **2. Data Cleaning** | Fix 10 categories of data quality issues | `master_cleaned.csv` |
| **3. EDA** | 20 professional visualizations with business insights | 21 PNG charts |
| **4. SQL Database** | Normalised SQLite DB with 5 tables + 15 analytics views | `amazon_india.db` |
| **5. Dashboard** | 30-chart interactive Streamlit BI dashboard | Live web app |

---

## 📁 Project Structure

```
amazon_india_project/
│
├── 📂 data/
│   ├── raw/                          ← Place all raw CSVs here
│   │   ├── amazon_india_2015.csv
│   │   ├── amazon_india_2016.csv
│   │   ├── ...
│   │   ├── amazon_india_2025.csv
│   │   └── amazon_india_products_catalog.csv
│   ├── cleaned/                      ← Auto-generated cleaned files
│   │   ├── amazon_india_master_cleaned.csv
│   │   └── data_quality_report.csv
│   └── db/
│       ├── amazon_india.db           ← SQLite database
│       └── schema_documentation.md
│
├── 📂 src/
│   ├── data_cleaning.py              ← Step 2: All 10 cleaning challenges
│   ├── eda_analysis.py               ← Step 3: 20 EDA visualizations
│   └── database_setup.py            ← Step 4: DB creation + 15 views
│
├── 📂 dashboard/
│   └── app.py                        ← Step 5: Streamlit dashboard (30 charts)
│
├── 📂 reports/
│   ├── eda_charts/                   ← 21 saved EDA PNG charts
│   └── data_quality_report.html      ← HTML quality report
│
├── requirements.txt                  ← Python dependencies
├── run_dashboard.bat                 ← Windows one-click launcher
├── .gitignore
└── README.md
```

---

## 📊 Dataset Overview

| Property | Details |
|----------|---------|
| **Source** | Amazon India transactional data (simulated, realistic) |
| **Time Period** | 2015 – 2025 (11 years) |
| **Total Records** | ~1,000,000+ transactions |
| **Files** | 11 year-wise CSVs + 1 product catalog |
| **Columns** | 34 transaction columns + 11 catalog columns |
| **Data Quality Issues** | ~25% intentional quality issues for cleaning practice |

### Key Columns

| Column | Type | Description |
|--------|------|-------------|
| `transaction_id` | str | Unique transaction identifier |
| `order_date` | str (mixed) | Date in multiple messy formats |
| `customer_id` | str | Customer identifier |
| `product_id` | str | Product identifier |
| `original_price_inr` | str/float | Price (mixed formats, symbols) |
| `discount_percent` | float | Discount applied |
| `final_amount_inr` | float | Final transaction amount |
| `payment_method` | str | UPI, COD, CC, etc. (inconsistent) |
| `customer_city` | str | City (with variants/misspellings) |
| `is_prime_member` | str | True/False/1/0/Yes/No mixed |
| `customer_rating` | str | Rating in multiple formats |
| `delivery_days` | str | Numeric + text mixed |
| `return_status` | str | Delivered / Returned / Cancelled |

---

## ✨ Features

### 🧹 Data Cleaning (10 Challenges)
- **Date standardisation** — 4 formats → `YYYY-MM-DD`
- **Price cleaning** — ₹ symbols, commas, "Price on Request" → float
- **Rating standardisation** — `4 stars`, `3/5`, `5.0/5.0` → float 1–5
- **City normalisation** — Bangalore/Bengaluru, spelling errors → canonical
- **Boolean cleaning** — Yes/No/1/0/TRUE/FALSE → Python bool
- **Category standardisation** — ELECTRONICS, Electronicss → Electronics
- **Delivery days** — "Same Day", negative, text → int 0–30
- **Duplicate handling** — Distinguish data errors from bulk orders
- **Outlier correction** — 100× inflated prices fixed via IQR
- **Payment standardisation** — COD/C.O.D/CashOnDelivery → canonical

### 📈 EDA (20 Visualizations)
Revenue trends, seasonal heatmaps, RFM segmentation, payment evolution, category performance, Prime analysis, geographic analysis, festival impact, age group behaviour, price-demand analysis, delivery performance, return analysis, brand performance, CLV cohort, discount effectiveness, rating analysis, purchase frequency, spending tiers, competitive pricing, and a business health dashboard.

### 🗄️ SQL Database
- **5 tables**: `transactions`, `customers`, `products`, `time_dimension`, `festivals`
- **16 indexes** on all frequently queried columns
- **15 analytics views** pre-built for dashboard connectivity
- Optimised WAL journal mode for fast reads

### 📊 Streamlit Dashboard (30 Charts)
6 pages of interactive Plotly charts with global sidebar filters (year, city tier, Prime membership), KPI cards, drill-down capabilities, and Amazon-branded theme.

---

## 🛠 Tech Stack

| Tool | Purpose |
|------|---------|
| **Python 3.10+** | Core language |
| **Pandas** | Data manipulation & cleaning |
| **NumPy** | Numerical operations |
| **Matplotlib / Seaborn** | EDA static charts |
| **Plotly** | Interactive dashboard charts |
| **Streamlit** | Dashboard web framework |
| **SQLite** | Lightweight analytical database |
| **SQLAlchemy** | Database ORM |
| **SciPy** | Statistical analysis |

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.10 or higher
- pip

### 1. Clone the repository

```bash
git clone https://github.com/SanjaiSK13/amazon-india-analytics.git
cd amazon-india-analytics
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Add your dataset

Place all raw CSV files inside `data/raw/`:

```
data/raw/amazon_india_2015.csv
data/raw/amazon_india_2016.csv
...
data/raw/amazon_india_2025.csv
data/raw/amazon_india_products_catalog.csv
```

---

## 🚀 Running the Pipeline

Run each step from the **project root directory** (`amazon_india_project/`):

### Step 2 — Data Cleaning
```bash
python src/data_cleaning.py \
  --input_dir data/raw \
  --output_dir data/cleaned \
  --catalog data/raw/amazon_india_products_catalog.csv \
  --years 2015 2016 2017 2018 2019 2020 2021 2022 2023 2024 2025
```
Output: `data/cleaned/amazon_india_master_cleaned.csv`

### Step 3 — EDA Visualizations
```bash
python src/eda_analysis.py
```
Output: `reports/eda_charts/` — 21 PNG charts

### Step 4 — Database Setup
```bash
python src/database_setup.py
```
Output: `data/db/amazon_india.db` — 172MB SQLite database

### Step 5 — Launch Dashboard
```bash
streamlit run dashboard/app.py
```
Open `http://localhost:8501` in your browser.

**Windows users** — just double-click `run_dashboard.bat`

---

## 📊 Dashboard Pages

| Page | Charts | Key Visuals |
|------|--------|-------------|
| 🏠 **Executive Summary** | 1–5 | 8 KPI cards, revenue trend, payment mix, order status |
| 📈 **Revenue Analytics** | 6–10 | Monthly heatmap, quarterly breakdown, festival vs regular |
| 👥 **Customer Analytics** | 11–15 | RFM segments, acquisition, age group, spending tiers, Prime growth |
| 📦 **Product & Brand** | 16–20 | Brand ranking, treemap, price range, rating impact, positioning matrix |
| 🚚 **Operations** | 21–25 | Delivery distribution, payment evolution, return rates, festival impact |
| 🔮 **Advanced Analytics** | 26–30 | CLV cohort, geographic heatmap, age-subcategory mix, revenue forecast, BI command center |

### Global Sidebar Filters
- **Year selector** — filter any combination of years
- **City tier** — Metro / Tier1 / Tier2 / Rural
- **Prime membership** — All / Prime Only / Non-Prime Only

---

## 🗄️ Database Schema

```
transactions (342,705+ rows)
    ├── transaction_id PK
    ├── customer_id FK → customers
    ├── product_id  FK → products
    ├── date_id     FK → time_dimension
    └── ... 25 more columns

customers (121,207+ rows)
    ├── customer_id PK
    ├── customer_city, customer_tier
    ├── total_orders, total_spent, avg_order_value
    └── rfm_segment (via vw_customer_segments)

products (2,004 rows)
    ├── product_id PK
    ├── category, subcategory, brand
    └── base_price_2015, rating, is_prime_eligible

time_dimension (1,825 rows — one per calendar date)
    └── date_id, year, quarter, month, week, day_name, is_weekend

festivals (aggregated festival performance)
    └── festival_name, year, total_orders, total_revenue, avg_discount
```

### Analytics Views (15)
`vw_executive_kpis` · `vw_yearly_revenue` · `vw_monthly_revenue` · `vw_category_performance` · `vw_payment_trends` · `vw_customer_segments` · `vw_prime_analysis` · `vw_geographic_revenue` · `vw_festival_impact` · `vw_brand_performance` · `vw_delivery_performance` · `vw_return_analysis` · `vw_price_analysis` · `vw_age_group_analysis` · `vw_top_products`

---

## 💡 Key Insights

- **UPI dominance**: UPI grew from ~5% in 2016 to 70%+ by 2025, while Cash on Delivery fell from 55% to under 8%
- **Prime impact**: Prime members spend 49% more per order and have 1.2 days faster delivery
- **Festival effect**: Festival periods drive 2.8× higher average discounts and concentrated revenue spikes
- **Metro concentration**: Mumbai, Delhi, and Bengaluru alone contribute 40%+ of total revenue
- **Sweet spot pricing**: ₹5K–₹15K price band generates the highest revenue despite not having the most orders
- **Rating-return link**: Products rated below 3.0 have 2.4× higher return rates than those rated 4.5+

---

## ☁️ Deploy to Streamlit Cloud

See [DEPLOYMENT.md](DEPLOYMENT.md) for full step-by-step instructions.

**Quick version:**
1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo → set `dashboard/app.py` as the main file
4. Add your database file or configure cloud storage

---

## 👤 Contributors

**Sanjai** — Data Analyst  
Built as a portfolio project demonstrating end-to-end data engineering and business intelligence skills.

---

## 📄 License

MIT License — free to use for educational and portfolio purposes.

---

*Built with Python, Streamlit, Plotly, Pandas & SQLite*
