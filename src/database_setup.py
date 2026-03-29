import os, sqlite3, time, logging, sys
import pandas as pd
import numpy as np

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(open(sys.stdout.fileno(), mode='w',
                                   encoding='utf-8', closefd=False)),
        logging.FileHandler("database_setup.log", mode="w", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

# Paths
BASE        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTER_CSV  = os.path.join(BASE, "data", "cleaned", "amazon_india_master_cleaned.csv")
CATALOG_CSV = os.path.join(BASE, "data", "cleaned", "amazon_india_products_catalog_cleaned.csv")
DB_PATH     = os.path.join(BASE, "data", "db", "amazon_india.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# TABLE DDL

DDL = {

"time_dimension": """
CREATE TABLE IF NOT EXISTS time_dimension (
    date_id       TEXT PRIMARY KEY,   -- YYYY-MM-DD
    year          INTEGER NOT NULL,
    quarter       INTEGER NOT NULL,
    month         INTEGER NOT NULL,
    month_name    TEXT    NOT NULL,
    week          INTEGER NOT NULL,
    day_of_week   INTEGER NOT NULL,
    day_name      TEXT    NOT NULL,
    is_weekend    INTEGER NOT NULL,
    is_festival_period INTEGER NOT NULL DEFAULT 0
)""",

"products": """
CREATE TABLE IF NOT EXISTS products (
    product_id        TEXT PRIMARY KEY,
    product_name      TEXT,
    category          TEXT,
    subcategory       TEXT,
    brand             TEXT,
    base_price_2015   REAL,
    weight_kg         REAL,
    rating            REAL,
    is_prime_eligible INTEGER,
    launch_year       INTEGER,
    model             TEXT
)""",

"customers": """
CREATE TABLE IF NOT EXISTS customers (
    customer_id          TEXT PRIMARY KEY,
    customer_city        TEXT,
    customer_state       TEXT,
    customer_tier        TEXT,
    customer_spending_tier TEXT,
    customer_age_group   TEXT,
    is_prime_member      INTEGER,
    first_order_year     INTEGER,
    total_orders         INTEGER DEFAULT 0,
    total_spent          REAL    DEFAULT 0.0,
    avg_order_value      REAL    DEFAULT 0.0
)""",

"festivals": """
CREATE TABLE IF NOT EXISTS festivals (
    festival_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    festival_name TEXT NOT NULL,
    year          INTEGER,
    total_orders  INTEGER,
    total_revenue REAL,
    avg_discount  REAL
)""",

"transactions": """
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id        TEXT PRIMARY KEY,
    order_date            TEXT,
    date_id               TEXT,
    customer_id           TEXT,
    product_id            TEXT,
    product_name          TEXT,
    category              TEXT,
    subcategory           TEXT,
    brand                 TEXT,
    original_price_inr    REAL,
    discount_percent      REAL,
    discounted_price_inr  REAL,
    quantity              INTEGER,
    subtotal_inr          REAL,
    delivery_charges      REAL,
    final_amount_inr      REAL,
    payment_method        TEXT,
    delivery_days         INTEGER,
    delivery_type         TEXT,
    is_prime_member       INTEGER,
    is_festival_sale      INTEGER,
    festival_name         TEXT,
    customer_rating       REAL,
    product_rating        REAL,
    return_status         TEXT,
    order_month           INTEGER,
    order_year            INTEGER,
    order_quarter         INTEGER,
    product_weight_kg     REAL,
    is_prime_eligible     INTEGER,
    FOREIGN KEY (date_id)     REFERENCES time_dimension(date_id),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (product_id)  REFERENCES products(product_id)
)""",
}

# INDEXES

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_txn_date        ON transactions(order_date)",
    "CREATE INDEX IF NOT EXISTS idx_txn_year        ON transactions(order_year)",
    "CREATE INDEX IF NOT EXISTS idx_txn_customer    ON transactions(customer_id)",
    "CREATE INDEX IF NOT EXISTS idx_txn_product     ON transactions(product_id)",
    "CREATE INDEX IF NOT EXISTS idx_txn_category    ON transactions(category)",
    "CREATE INDEX IF NOT EXISTS idx_txn_payment     ON transactions(payment_method)",
    "CREATE INDEX IF NOT EXISTS idx_txn_return      ON transactions(return_status)",
    "CREATE INDEX IF NOT EXISTS idx_txn_festival    ON transactions(is_festival_sale)",
    "CREATE INDEX IF NOT EXISTS idx_txn_prime       ON transactions(is_prime_member)",
    "CREATE INDEX IF NOT EXISTS idx_txn_yr_cat      ON transactions(order_year, category)",
    "CREATE INDEX IF NOT EXISTS idx_cust_city       ON customers(customer_city)",
    "CREATE INDEX IF NOT EXISTS idx_cust_tier       ON customers(customer_tier)",
    "CREATE INDEX IF NOT EXISTS idx_prod_cat        ON products(category)",
    "CREATE INDEX IF NOT EXISTS idx_prod_brand      ON products(brand)",
    "CREATE INDEX IF NOT EXISTS idx_time_year       ON time_dimension(year)",
    "CREATE INDEX IF NOT EXISTS idx_time_month      ON time_dimension(month)",
]

# ANALYTICS VIEWS

VIEWS = {

"vw_yearly_revenue": """
CREATE VIEW IF NOT EXISTS vw_yearly_revenue AS
SELECT
    order_year,
    COUNT(*)                        AS total_orders,
    COUNT(DISTINCT customer_id)     AS unique_customers,
    ROUND(SUM(final_amount_inr),2)  AS total_revenue,
    ROUND(AVG(final_amount_inr),2)  AS avg_order_value,
    ROUND(SUM(delivery_charges),2)  AS total_delivery_charges,
    ROUND(AVG(discount_percent),2)  AS avg_discount_pct
FROM transactions
GROUP BY order_year
ORDER BY order_year""",

"vw_monthly_revenue": """
CREATE VIEW IF NOT EXISTS vw_monthly_revenue AS
SELECT
    order_year,
    order_month,
    COUNT(*)                        AS total_orders,
    ROUND(SUM(final_amount_inr),2)  AS total_revenue,
    ROUND(AVG(final_amount_inr),2)  AS avg_order_value
FROM transactions
GROUP BY order_year, order_month
ORDER BY order_year, order_month""",

"vw_category_performance": """
CREATE VIEW IF NOT EXISTS vw_category_performance AS
SELECT
    category,
    subcategory,
    order_year,
    COUNT(*)                        AS total_orders,
    ROUND(SUM(final_amount_inr),2)  AS total_revenue,
    ROUND(AVG(final_amount_inr),2)  AS avg_order_value,
    ROUND(AVG(discount_percent),2)  AS avg_discount,
    ROUND(AVG(product_rating),2)    AS avg_product_rating,
    ROUND(
      100.0 * SUM(CASE WHEN return_status='Returned' THEN 1 ELSE 0 END)
      / COUNT(*), 2)                AS return_rate_pct
FROM transactions
GROUP BY category, subcategory, order_year""",

"vw_payment_trends": """
CREATE VIEW IF NOT EXISTS vw_payment_trends AS
SELECT
    order_year,
    payment_method,
    COUNT(*)                        AS total_transactions,
    ROUND(SUM(final_amount_inr),2)  AS total_revenue,
    ROUND(
      100.0 * COUNT(*) /
      SUM(COUNT(*)) OVER (PARTITION BY order_year), 2) AS market_share_pct
FROM transactions
GROUP BY order_year, payment_method
ORDER BY order_year, total_transactions DESC""",

"vw_customer_segments": """
CREATE VIEW IF NOT EXISTS vw_customer_segments AS
SELECT
    c.customer_id,
    c.customer_city,
    c.customer_tier,
    c.customer_spending_tier,
    c.customer_age_group,
    c.is_prime_member,
    c.total_orders,
    ROUND(c.total_spent, 2)         AS total_spent,
    ROUND(c.avg_order_value, 2)     AS avg_order_value,
    CASE
        WHEN c.total_orders >= 10 AND c.total_spent >= 500000 THEN 'Champions'
        WHEN c.total_orders >= 6  AND c.total_spent >= 200000 THEN 'Loyal'
        WHEN c.total_orders >= 3  AND c.total_spent >= 50000  THEN 'Potential'
        WHEN c.total_orders >= 2                              THEN 'At Risk'
        ELSE 'Lost'
    END AS rfm_segment
FROM customers c""",

"vw_prime_analysis": """
CREATE VIEW IF NOT EXISTS vw_prime_analysis AS
SELECT
    order_year,
    CASE WHEN is_prime_member=1 THEN 'Prime' ELSE 'Non-Prime' END AS membership,
    COUNT(*)                        AS total_orders,
    COUNT(DISTINCT customer_id)     AS unique_customers,
    ROUND(SUM(final_amount_inr),2)  AS total_revenue,
    ROUND(AVG(final_amount_inr),2)  AS avg_order_value,
    ROUND(AVG(delivery_days),2)     AS avg_delivery_days,
    ROUND(AVG(discount_percent),2)  AS avg_discount,
    ROUND(
      100.0 * SUM(CASE WHEN return_status='Returned' THEN 1 ELSE 0 END)
      / COUNT(*), 2)                AS return_rate_pct
FROM transactions
GROUP BY order_year, is_prime_member""",

"vw_geographic_revenue": """
CREATE VIEW IF NOT EXISTS vw_geographic_revenue AS
SELECT
    c.customer_city,
    c.customer_state,
    c.customer_tier,
    COUNT(t.transaction_id)         AS total_orders,
    COUNT(DISTINCT t.customer_id)   AS unique_customers,
    ROUND(SUM(t.final_amount_inr),2) AS total_revenue,
    ROUND(AVG(t.final_amount_inr),2) AS avg_order_value
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
GROUP BY c.customer_city, c.customer_state, c.customer_tier
ORDER BY total_revenue DESC""",

"vw_festival_impact": """
CREATE VIEW IF NOT EXISTS vw_festival_impact AS
SELECT
    CASE WHEN is_festival_sale=1 THEN 'Festival' ELSE 'Regular' END AS sale_type,
    festival_name,
    order_year,
    COUNT(*)                        AS total_orders,
    ROUND(SUM(final_amount_inr),2)  AS total_revenue,
    ROUND(AVG(final_amount_inr),2)  AS avg_order_value,
    ROUND(AVG(discount_percent),2)  AS avg_discount
FROM transactions
GROUP BY is_festival_sale, festival_name, order_year""",

"vw_brand_performance": """
CREATE VIEW IF NOT EXISTS vw_brand_performance AS
SELECT
    brand,
    category,
    subcategory,
    order_year,
    COUNT(*)                        AS total_orders,
    ROUND(SUM(final_amount_inr),2)  AS total_revenue,
    ROUND(AVG(original_price_inr),2) AS avg_price,
    ROUND(AVG(discount_percent),2)  AS avg_discount,
    ROUND(AVG(product_rating),2)    AS avg_product_rating,
    ROUND(AVG(customer_rating),2)   AS avg_customer_rating
FROM transactions
GROUP BY brand, category, subcategory, order_year
ORDER BY total_revenue DESC""",

"vw_delivery_performance": """
CREATE VIEW IF NOT EXISTS vw_delivery_performance AS
SELECT
    c.customer_tier,
    t.delivery_type,
    t.order_year,
    COUNT(*)                        AS total_orders,
    ROUND(AVG(t.delivery_days),2)   AS avg_delivery_days,
    ROUND(MIN(t.delivery_days),2)   AS min_delivery_days,
    ROUND(MAX(t.delivery_days),2)   AS max_delivery_days,
    ROUND(
      100.0 * SUM(CASE WHEN t.delivery_days <= 5 THEN 1 ELSE 0 END)
      / COUNT(*), 2)                AS on_time_pct
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
GROUP BY c.customer_tier, t.delivery_type, t.order_year""",

"vw_return_analysis": """
CREATE VIEW IF NOT EXISTS vw_return_analysis AS
SELECT
    order_year,
    category,
    subcategory,
    return_status,
    COUNT(*)                        AS total_orders,
    ROUND(SUM(final_amount_inr),2)  AS total_revenue,
    ROUND(AVG(customer_rating),2)   AS avg_rating,
    ROUND(AVG(discount_percent),2)  AS avg_discount
FROM transactions
GROUP BY order_year, category, subcategory, return_status""",

"vw_price_analysis": """
CREATE VIEW IF NOT EXISTS vw_price_analysis AS
SELECT
    CASE
        WHEN original_price_inr < 1000  THEN 'Under 1K'
        WHEN original_price_inr < 5000  THEN '1K-5K'
        WHEN original_price_inr < 15000 THEN '5K-15K'
        WHEN original_price_inr < 50000 THEN '15K-50K'
        ELSE 'Above 50K'
    END AS price_band,
    order_year,
    COUNT(*)                        AS total_orders,
    ROUND(SUM(final_amount_inr),2)  AS total_revenue,
    ROUND(AVG(discount_percent),2)  AS avg_discount,
    ROUND(AVG(customer_rating),2)   AS avg_rating,
    ROUND(
      100.0 * SUM(CASE WHEN return_status='Returned' THEN 1 ELSE 0 END)
      / COUNT(*), 2)                AS return_rate_pct
FROM transactions
GROUP BY price_band, order_year""",

"vw_age_group_analysis": """
CREATE VIEW IF NOT EXISTS vw_age_group_analysis AS
SELECT
    c.customer_age_group,
    t.order_year,
    t.subcategory,
    COUNT(*)                        AS total_orders,
    ROUND(SUM(t.final_amount_inr),2) AS total_revenue,
    ROUND(AVG(t.final_amount_inr),2) AS avg_order_value,
    ROUND(AVG(t.discount_percent),2) AS avg_discount
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
GROUP BY c.customer_age_group, t.order_year, t.subcategory""",

"vw_executive_kpis": """
CREATE VIEW IF NOT EXISTS vw_executive_kpis AS
SELECT
    order_year,
    COUNT(*)                            AS total_orders,
    COUNT(DISTINCT customer_id)         AS unique_customers,
    ROUND(SUM(final_amount_inr), 2)     AS total_revenue,
    ROUND(AVG(final_amount_inr), 2)     AS avg_order_value,
    ROUND(SUM(delivery_charges), 2)     AS total_delivery_revenue,
    ROUND(AVG(discount_percent), 2)     AS avg_discount_pct,
    ROUND(AVG(delivery_days), 2)        AS avg_delivery_days,
    ROUND(AVG(customer_rating), 2)      AS avg_customer_rating,
    SUM(CASE WHEN is_prime_member=1 THEN 1 ELSE 0 END) AS prime_orders,
    SUM(CASE WHEN is_festival_sale=1 THEN 1 ELSE 0 END) AS festival_orders,
    SUM(CASE WHEN return_status='Returned'  THEN 1 ELSE 0 END) AS returned_orders,
    SUM(CASE WHEN return_status='Cancelled' THEN 1 ELSE 0 END) AS cancelled_orders,
    ROUND(
      100.0 * SUM(CASE WHEN return_status='Returned' THEN 1 ELSE 0 END)
      / COUNT(*), 2)                    AS return_rate_pct,
    ROUND(
      100.0 * SUM(CASE WHEN is_prime_member=1 THEN 1 ELSE 0 END)
      / COUNT(*), 2)                    AS prime_order_pct
FROM transactions
GROUP BY order_year
ORDER BY order_year""",

"vw_top_products": """
CREATE VIEW IF NOT EXISTS vw_top_products AS
SELECT
    product_id,
    product_name,
    brand,
    subcategory,
    COUNT(*)                        AS total_orders,
    ROUND(SUM(final_amount_inr),2)  AS total_revenue,
    ROUND(AVG(original_price_inr),2) AS avg_price,
    ROUND(AVG(customer_rating),2)   AS avg_customer_rating,
    ROUND(AVG(product_rating),2)    AS avg_product_rating,
    ROUND(
      100.0 * SUM(CASE WHEN return_status='Returned' THEN 1 ELSE 0 END)
      / COUNT(*), 2)                AS return_rate_pct
FROM transactions
GROUP BY product_id, product_name, brand, subcategory
ORDER BY total_revenue DESC""",
}

# DATA PREPARATION

def prepare_data():
    log.info("Loading master cleaned CSV...")
    df = pd.read_csv(MASTER_CSV, low_memory=False)
    log.info(f"  Rows: {len(df):,} | Columns: {len(df.columns)}")

    # Fix types
    df["order_date"]       = pd.to_datetime(df["order_date"], errors="coerce")
    df["final_amount_inr"] = pd.to_numeric(df["final_amount_inr"], errors="coerce").fillna(0)
    df["is_prime_member"]  = df["is_prime_member"].astype(bool).astype(int)
    df["is_festival_sale"] = df["is_festival_sale"].astype(bool).astype(int)
    df["is_prime_eligible"]= df["is_prime_eligible"].astype(bool).astype(int)
    df["festival_name"]    = df["festival_name"].fillna("None")

    # time_dimension
    log.info("  Building time_dimension...")
    dates = df["order_date"].dropna().unique()
    dates = pd.to_datetime(dates)
    time_df = pd.DataFrame({
        "date_id":     dates.strftime("%Y-%m-%d"),
        "year":        dates.year,
        "quarter":     dates.quarter,
        "month":       dates.month,
        "month_name":  dates.strftime("%B"),
        "week":        dates.isocalendar().week.values,
        "day_of_week": dates.dayofweek,
        "day_name":    dates.strftime("%A"),
        "is_weekend":  (dates.dayofweek >= 5).astype(int),
        "is_festival_period": 0,
    }).drop_duplicates("date_id")

    # products
    log.info("  Building products table...")
    if os.path.exists(CATALOG_CSV):
        prod_df = pd.read_csv(CATALOG_CSV)
        prod_df["is_prime_eligible"] = prod_df["is_prime_eligible"].astype(bool).astype(int)
    else:
        prod_df = (df[["product_id","product_name","category","subcategory",
                       "brand","product_rating","product_weight_kg","is_prime_eligible"]]
                     .drop_duplicates("product_id")
                     .rename(columns={"product_rating":"rating","product_weight_kg":"weight_kg"}))
        prod_df["base_price_2015"] = None
        prod_df["launch_year"]     = None
        prod_df["model"]           = None

    # customers
    log.info("  Building customers table...")
    cust_stats = df.groupby("customer_id").agg(
        total_orders   = ("transaction_id","count"),
        total_spent    = ("final_amount_inr","sum"),
        avg_order_value= ("final_amount_inr","mean"),
        first_order_year=("order_year","min"),
    ).reset_index()

    cust_info = df.drop_duplicates("customer_id")[
        ["customer_id","customer_city","customer_state","customer_tier",
         "customer_spending_tier","customer_age_group","is_prime_member"]
    ]
    cust_df = cust_info.merge(cust_stats, on="customer_id", how="left")

    # festivals
    log.info("  Building festivals table...")
    fest_df = (df[df["is_festival_sale"]==1]
               .groupby(["festival_name","order_year"])
               .agg(total_orders=("transaction_id","count"),
                    total_revenue=("final_amount_inr","sum"),
                    avg_discount=("discount_percent","mean"))
               .reset_index()
               .rename(columns={"order_year":"year"}))

    # transactions
    log.info("  Building transactions table...")
    txn_df = df[[
        "transaction_id","order_date","customer_id","product_id",
        "product_name","category","subcategory","brand",
        "original_price_inr","discount_percent","discounted_price_inr",
        "quantity","subtotal_inr","delivery_charges","final_amount_inr",
        "payment_method","delivery_days","delivery_type",
        "is_prime_member","is_festival_sale","festival_name",
        "customer_rating","product_rating","return_status",
        "order_month","order_year","order_quarter",
        "product_weight_kg","is_prime_eligible"
    ]].copy()

    txn_df["order_date"] = txn_df["order_date"].dt.strftime("%Y-%m-%d")
    txn_df["date_id"]    = txn_df["order_date"]

    return time_df, prod_df, cust_df, fest_df, txn_df

# DATABASE BUILDER

def build_database():
    t0 = time.time()
    log.info(f"\n{'='*60}")
    log.info("  BUILDING AMAZON INDIA ANALYTICS DATABASE")
    log.info(f"  Output: {DB_PATH}")
    log.info(f"{'='*60}\n")

    # Remove old DB
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        log.info("  Removed existing database.")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous  = NORMAL")
    conn.execute("PRAGMA cache_size   = -64000")
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    # Create tables
    log.info("Creating tables...")
    for name, ddl in DDL.items():
        cur.execute(ddl)
        log.info(f"  Created: {name}")
    conn.commit()

    # Load data
    time_df, prod_df, cust_df, fest_df, txn_df = prepare_data()

    def load(df, table, chunksize=500):
        total = len(df)
        loaded = 0
        for i in range(0, total, chunksize):
            chunk = df.iloc[i:i+chunksize]
            chunk.to_sql(table, conn, if_exists="append", index=False,
                     method=None)
            loaded += len(chunk)
            log.info(f"    {table}: {loaded:,}/{total:,} rows loaded")
        conn.commit()
        log.info(f"  ✓ {table}: {total:,} rows")

    log.info("\nLoading data into tables...")
    load(time_df, "time_dimension")
    load(prod_df, "products")
    load(cust_df, "customers")
    load(fest_df, "festivals")
    load(txn_df,  "transactions")

    # Create indexes
    log.info("\nCreating indexes...")
    for idx in INDEXES:
        cur.execute(idx)
        log.info(f"  Created: {idx.split('idx_')[1].split(' ')[0]}")
    conn.commit()

    # Create views
    log.info("\nCreating analytics views...")
    for name, view_sql in VIEWS.items():
        cur.execute(view_sql)
        log.info(f"  Created view: {name}")
    conn.commit()

    # Validation
    log.info("\nValidating database...")
    tables = ["time_dimension","products","customers","festivals","transactions"]
    for tbl in tables:
        count = cur.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        log.info(f"  {tbl:<25} {count:>10,} rows")

    log.info("\nValidating views...")
    for view_name in VIEWS.keys():
        try:
            count = cur.execute(f"SELECT COUNT(*) FROM {view_name}").fetchone()[0]
            log.info(f"  {view_name:<35} {count:>8,} rows")
        except Exception as e:
            log.error(f"  {view_name}: ERROR — {e}")

    conn.close()
    elapsed = time.time() - t0
    db_size  = os.path.getsize(DB_PATH) / 1024 / 1024

    log.info(f"\n{'='*60}")
    log.info(f"  DATABASE READY in {elapsed:.1f}s")
    log.info(f"  File size  : {db_size:.1f} MB")
    log.info(f"  Tables     : {len(DDL)}")
    log.info(f"  Indexes    : {len(INDEXES)}")
    log.info(f"  Views      : {len(VIEWS)}")
    log.info(f"  Path       : {DB_PATH}")
    log.info(f"{'='*60}\n")
    return DB_PATH

# SAMPLE QUERIES

SAMPLE_QUERIES = {
    "Top 5 years by revenue": """
        SELECT order_year,
               total_orders,
               unique_customers,
               total_revenue,
               avg_order_value,
               avg_discount_pct
        FROM vw_executive_kpis
        ORDER BY total_revenue DESC LIMIT 5""",

    "Payment market share (latest year)": """
        SELECT payment_method,
               total_transactions,
               total_revenue,
               market_share_pct
        FROM vw_payment_trends
        WHERE order_year = (SELECT MAX(order_year) FROM transactions)
        ORDER BY market_share_pct DESC""",

    "Prime vs Non-Prime (latest year)": """
        SELECT membership,
               total_orders,
               unique_customers,
               total_revenue,
               avg_order_value,
               avg_delivery_days,
               return_rate_pct
        FROM vw_prime_analysis
        WHERE order_year = (SELECT MAX(order_year) FROM transactions)""",

    "Top 10 cities by revenue": """
        SELECT customer_city,
               customer_tier,
               total_orders,
               unique_customers,
               total_revenue,
               avg_order_value
        FROM vw_geographic_revenue
        LIMIT 10""",

    "Festival vs Regular comparison": """
        SELECT sale_type,
               COUNT(*) as periods,
               SUM(total_orders) AS total_orders,
               SUM(total_revenue) AS total_revenue,
               AVG(avg_discount) AS avg_discount
        FROM vw_festival_impact
        GROUP BY sale_type""",

    "Top 10 brands by revenue": """
        SELECT brand,
               SUM(total_orders)  AS orders,
               SUM(total_revenue) AS revenue,
               AVG(avg_price)     AS avg_price,
               AVG(avg_product_rating) AS rating
        FROM vw_brand_performance
        GROUP BY brand
        ORDER BY revenue DESC
        LIMIT 10""",

    "Customer segment distribution": """
        SELECT rfm_segment,
               COUNT(*) AS customers,
               ROUND(AVG(total_spent),2) AS avg_lifetime_value,
               ROUND(AVG(total_orders),1) AS avg_orders
        FROM vw_customer_segments
        GROUP BY rfm_segment
        ORDER BY avg_lifetime_value DESC""",

    "Delivery performance by tier": """
        SELECT customer_tier,
               SUM(total_orders) AS orders,
               ROUND(AVG(avg_delivery_days),2) AS avg_days,
               ROUND(AVG(on_time_pct),1) AS on_time_pct
        FROM vw_delivery_performance
        GROUP BY customer_tier
        ORDER BY avg_days""",
}


def run_sample_queries(db_path):
    conn = sqlite3.connect(db_path)
    print("\n" + "="*65)
    print("  SAMPLE QUERY RESULTS")
    print("="*65)
    for title, sql in SAMPLE_QUERIES.items():
        try:
            result = pd.read_sql_query(sql, conn)
            print(f"\n--- {title} ---")
            print(result.to_string(index=False))
        except Exception as e:
            print(f"\n--- {title} --- ERROR: {e}")
    conn.close()

# SCHEMA DOCUMENTATION

def export_schema_doc(db_path):
    doc_path = os.path.join(os.path.dirname(db_path), "schema_documentation.md")
    lines = [
        "# Amazon India Analytics — Database Schema\n",
        f"**Database:** `amazon_india.db` (SQLite)\n",
        f"**Tables:** {len(DDL)} | **Views:** {len(VIEWS)} | **Indexes:** {len(INDEXES)}\n\n",
        "---\n\n## Tables\n\n",
    ]
    for name in DDL:
        lines.append(f"### `{name}`\n")
        conn = sqlite3.connect(db_path)
        info = pd.read_sql_query(f"PRAGMA table_info({name})", conn)
        conn.close()
        lines.append("| Column | Type | Not Null | PK |\n")
        lines.append("|--------|------|----------|----|\n")
        for _, row in info.iterrows():
            lines.append(f"| {row['name']} | {row['type']} | "
                         f"{'Yes' if row['notnull'] else 'No'} | "
                         f"{'Yes' if row['pk'] else 'No'} |\n")
        lines.append("\n")

    lines.append("---\n\n## Analytics Views\n\n")
    for name in VIEWS:
        lines.append(f"- **`{name}`**\n")

    lines.append("\n---\n\n## Connection (Python)\n\n")
    lines.append("```python\nimport sqlite3, pandas as pd\n"
                 "conn = sqlite3.connect('data/db/amazon_india.db')\n"
                 "df = pd.read_sql_query('SELECT * FROM vw_executive_kpis', conn)\n"
                 "```\n\n")
    lines.append("## Connection (Streamlit)\n\n")
    lines.append("```python\nimport streamlit as st, sqlite3, pandas as pd\n\n"
                 "@st.cache_resource\n"
                 "def get_connection():\n"
                 "    return sqlite3.connect('data/db/amazon_india.db', check_same_thread=False)\n\n"
                 "@st.cache_data\n"
                 "def run_query(sql):\n"
                 "    conn = get_connection()\n"
                 "    return pd.read_sql_query(sql, conn)\n"
                 "```\n")

    with open(doc_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    log.info(f"  Schema doc: {doc_path}")
    return doc_path

# ENTRY POINT

if __name__ == "__main__":
    db_path = build_database()
    run_sample_queries(db_path)
    export_schema_doc(db_path)
    print(f"\nDone! Database at: {db_path}")
    print(f"Connect in Python:  sqlite3.connect('{db_path}')")
    print(f"Connect in Streamlit: use get_connection() helper in dashboard/app.py")
