import os, re, sys, logging, argparse
import numpy as np
import pandas as pd
from datetime import datetime

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(open(sys.stdout.fileno(), mode='w', encoding='utf-8', closefd=False)),
        logging.FileHandler("cleaning_pipeline.log", mode="w", encoding="utf-8"),
    ],
)

# Date Standardisation

def clean_dates(series: pd.Series) -> pd.Series:
    def parse_one(val):
        if pd.isna(val):
            return pd.NaT
        val = str(val).strip()

        # Already ISO
        if re.match(r'^\d{4}-\d{2}-\d{2}$', val):
            try:
                dt = datetime.strptime(val, "%Y-%m-%d")
                if 1 <= dt.month <= 12 and 1 <= dt.day <= 31:
                    return dt
            except ValueError:
                return pd.NaT

        # DD/MM/YYYY or MM/DD/YYYY
        if re.match(r'^\d{2}/\d{2}/\d{4}$', val):
            d, m, y = int(val[:2]), int(val[3:5]), int(val[6:])
            # Detect MM/DD/YYYY when first part > 12
            if d > 12:
                try:
                    return datetime.strptime(val, "%d/%m/%Y")
                except ValueError:
                    return pd.NaT
            else:
                # Try MM/DD/YYYY first (common in messy data)
                try:
                    return datetime.strptime(val, "%m/%d/%Y")
                except ValueError:
                    try:
                        return datetime.strptime(val, "%d/%m/%Y")
                    except ValueError:
                        return pd.NaT

        # DD-MM-YY  or  DD-MM-YYYY
        if re.match(r'^\d{2}-\d{2}-\d{2}$', val):
            try:
                return datetime.strptime(val, "%d-%m-%y")
            except ValueError:
                return pd.NaT
        if re.match(r'^\d{2}-\d{2}-\d{4}$', val):
            try:
                return datetime.strptime(val, "%d-%m-%Y")
            except ValueError:
                return pd.NaT

        # Fallback: pandas smart parser
        try:
            return pd.to_datetime(val, dayfirst=True)
        except Exception:
            return pd.NaT

    parsed = series.map(parse_one)
    n_invalid = parsed.isna().sum()
    if n_invalid:
        log.warning(f"  [Date] {n_invalid} unparseable dates → forward-filled.")
        parsed = parsed.fillna(method="ffill").fillna(method="bfill")
    return parsed.dt.strftime("%Y-%m-%d")


# Price Cleaning (INR)

def clean_price(series: pd.Series, col_name: str = "price") -> pd.Series:
    def parse_price(val):
        if pd.isna(val):
            return np.nan
        val = str(val).strip()
        if val.lower() in ("price on request", "por", "n/a", "na", "", "nan"):
            return np.nan
        # Strip currency symbols and separators
        val = re.sub(r'[₹$€£Rs\s]', '', val, flags=re.IGNORECASE)
        val = val.replace(",", "")
        try:
            return float(val)
        except ValueError:
            return np.nan

    cleaned = series.map(parse_price)
    median_price = cleaned.median()
    n_missing = cleaned.isna().sum()
    if n_missing:
        log.warning(f"  [Price/{col_name}] {n_missing} missing/POR → filled with median ₹{median_price:,.2f}")
        cleaned = cleaned.fillna(median_price)
    return cleaned.round(2)


# Rating Standardisation (1.0 – 5.0)

def clean_ratings(series: pd.Series) -> pd.Series:
    def parse_rating(val):
        if pd.isna(val):
            return np.nan
        val = str(val).strip().lower()
        val = val.replace("stars", "").replace("star", "").strip()

        # Fraction like 3/5 or 2.5/5.0
        frac = re.match(r'^([\d.]+)\s*/\s*([\d.]+)$', val)
        if frac:
            num, denom = float(frac.group(1)), float(frac.group(2))
            if denom == 0:
                return np.nan
            scaled = (num / denom) * 5.0
            return round(min(max(scaled, 1.0), 5.0), 1)

        try:
            r = float(val)
            # If on a 10-point scale, rescale
            if r > 5:
                r = r / 2.0
            return round(min(max(r, 1.0), 5.0), 1)
        except ValueError:
            return np.nan

    cleaned = series.map(parse_rating)
    median_r = round(cleaned.median(), 1)
    n_missing = cleaned.isna().sum()
    if n_missing:
        log.warning(f"  [Rating] {n_missing} missing → filled with median {median_r}")
        cleaned = cleaned.fillna(median_r)
    return cleaned


# City-Name Normalisation

CITY_ALIASES = {
    # Bangalore variants
    "bangalore": "Bengaluru", "bengaluru": "Bengaluru", "banglore": "Bengaluru",
    "bangaluru": "Bengaluru", "bangalor": "Bengaluru",
    # Mumbai variants
    "mumbai": "Mumbai", "bombay": "Mumbai",
    # Delhi variants
    "delhi": "Delhi", "new delhi": "Delhi", "newdelhi": "Delhi",
    # Other common variants
    "hyderabad": "Hyderabad", "hyd": "Hyderabad", "secundarabad": "Hyderabad",
    "chennai": "Chennai", "madras": "Chennai",
    "kolkata": "Kolkata", "calcutta": "Kolkata",
    "pune": "Pune", "poona": "Pune",
    "ahmedabad": "Ahmedabad", "amdavad": "Ahmedabad",
    "jaipur": "Jaipur", "jaipure": "Jaipur",
    "lucknow": "Lucknow", "luckhnow": "Lucknow",
    "chandigarh": "Chandigarh",
    "kochi": "Kochi", "cochin": "Kochi", "ernakulam": "Kochi",
    "nagpur": "Nagpur",
    "indore": "Indore",
    "bhopal": "Bhopal",
    "visakhapatnam": "Visakhapatnam", "vizag": "Visakhapatnam", "vishakhapatnam": "Visakhapatnam",
    "coimbatore": "Coimbatore", "kovai": "Coimbatore",
    "surat": "Surat",
    "vadodara": "Vadodara", "baroda": "Vadodara",
    "rajkot": "Rajkot",
    "jodhpur": "Jodhpur",
    "kanpur": "Kanpur", "cawnpore": "Kanpur",
    "agra": "Agra",
    "nashik": "Nashik", "nasik": "Nashik",
    "aurangabad": "Aurangabad",
    "mysuru": "Mysuru", "mysore": "Mysuru",
    "hubli": "Hubli", "hubballi": "Hubli",
    "madurai": "Madurai",
    "tiruchirappalli": "Tiruchirappalli", "trichy": "Tiruchirappalli", "tiruchi": "Tiruchirappalli",
    "bhubaneswar": "Bhubaneswar", "bhubaneshwar": "Bhubaneswar",
    "ludhiana": "Ludhiana",
    "patna": "Patna",
    "guwahati": "Guwahati",
    "thiruvananthapuram": "Thiruvananthapuram", "trivandrum": "Thiruvananthapuram",
    "kollam": "Kollam",
    "thrissur": "Thrissur",
    "kozhikode": "Kozhikode", "calicut": "Kozhikode",
    "mangaluru": "Mangaluru", "mangalore": "Mangaluru",
    "belgaum": "Belagavi", "belagavi": "Belagavi",
    "guntur": "Guntur",
    "nellore": "Nellore",
    "kurnool": "Kurnool",
    "rajahmundry": "Rajahmundry",
    "tirupati": "Tirupati",
    "amritsar": "Amritsar",
    "jalandhar": "Jalandhar",
    "gurgaon": "Gurugram", "gurugram": "Gurugram",
    "noida": "Noida",
    "faridabad": "Faridabad",
    "ghaziabad": "Ghaziabad",
}

def clean_cities(series: pd.Series) -> pd.Series:
    def normalise(val):
        if pd.isna(val):
            return "Unknown"
        key = str(val).strip().lower()
        key = re.split(r'[/|]', key)[0].strip()
        return CITY_ALIASES.get(key, str(val).strip().title())

    cleaned = series.map(normalise)
    changed = (cleaned != series.str.strip().str.title()).sum()
    log.info(f"  [City] {changed} city names normalised.")
    return cleaned


#Boolean Column Cleaning

BOOL_TRUE  = {"true", "yes", "y", "1", "t", "on"}
BOOL_FALSE = {"false", "no", "n", "0", "f", "off"}

def clean_boolean(series: pd.Series) -> pd.Series:
    def parse_bool(val):
        if pd.isna(val):
            return np.nan
        v = str(val).strip().lower()
        if v in BOOL_TRUE:
            return True
        if v in BOOL_FALSE:
            return False
        return np.nan

    cleaned = series.map(parse_bool)
    n_missing = cleaned.isna().sum()
    if n_missing:
        mode_val = cleaned.mode()[0] if not cleaned.dropna().empty else False
        log.warning(f"  [Bool/{series.name}] {n_missing} missing → filled with mode={mode_val}")
        cleaned = cleaned.fillna(mode_val)
    return cleaned.astype(bool)


# Product Category Standardisation

CATEGORY_ALIASES = {
    "electronics": "Electronics",
    "electronicss": "Electronics",
    "electronic": "Electronics",
    "electronics & accessories": "Electronics",
    "electronics and accessories": "Electronics",
    "fashion": "Fashion",
    "clothing": "Fashion",
    "apparel": "Fashion",
    "home & kitchen": "Home & Kitchen",
    "home and kitchen": "Home & Kitchen",
    "home kitchen": "Home & Kitchen",
    "home": "Home & Kitchen",
    "kitchen": "Home & Kitchen",
    "books": "Books",
    "book": "Books",
    "beauty & personal care": "Beauty & Personal Care",
    "beauty and personal care": "Beauty & Personal Care",
    "beauty": "Beauty & Personal Care",
    "personal care": "Beauty & Personal Care",
    "sports & fitness": "Sports & Fitness",
    "sports and fitness": "Sports & Fitness",
    "sports": "Sports & Fitness",
    "fitness": "Sports & Fitness",
    "grocery & food": "Grocery & Food",
    "grocery and food": "Grocery & Food",
    "grocery": "Grocery & Food",
    "food": "Grocery & Food",
    "toys & games": "Toys & Games",
    "toys and games": "Toys & Games",
    "toys": "Toys & Games",
    "games": "Toys & Games",
}

def clean_categories(series: pd.Series) -> pd.Series:
    def normalise(val):
        if pd.isna(val):
            return "Other"
        key = str(val).strip().lower()
        return CATEGORY_ALIASES.get(key, str(val).strip().title())

    cleaned = series.map(normalise)
    changed = (cleaned != series).sum()
    log.info(f"  [Category] {changed} category names standardised.")
    return cleaned


#  Days Cleaning

def clean_delivery_days(series: pd.Series) -> pd.Series:
    def parse_days(val):
        if pd.isna(val):
            return np.nan
        val = str(val).strip().lower()
        if val in ("same day", "sameday", "0 days", "today"):
            return 0
        if val in ("express", "instant"):
            return 1
        # Range like '1-2 days' → take lower bound
        rng = re.match(r'^(\d+)\s*[-–]\s*\d+', val)
        if rng:
            return int(rng.group(1))
        # Strip 'days', 'day'
        val = re.sub(r'\s*(days?|d)\s*$', '', val).strip()
        try:
            v = int(float(val))
            if v < 0 or v > 30:
                return np.nan
            return v
        except ValueError:
            return np.nan

    cleaned = series.map(parse_days)
    median_days = int(cleaned.median())
    n_bad = cleaned.isna().sum()
    if n_bad:
        log.warning(f"  [DeliveryDays] {n_bad} invalid entries → filled with median={median_days}")
        cleaned = cleaned.fillna(median_days)
    return cleaned.astype(int)


# Duplicate Detection & Handling

def handle_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)

    # Step 1: exact duplicates
    exact_dupes = df.duplicated(keep="first")
    df = df[~exact_dupes].copy()
    log.info(f"  [Duplicates] Exact duplicates removed: {exact_dupes.sum()}")

    # Step 2: functional duplicates (same key fields)
    key_cols = ["customer_id", "product_id", "order_date", "final_amount_inr"]
    df["_dup_count"] = df.groupby(key_cols)["transaction_id"].transform("count")

    # Genuine bulk: ≤5 occurrences → keep
    error_mask = df["_dup_count"] > 5
    df_ok    = df[~error_mask].drop(columns=["_dup_count"])
    df_error = df[error_mask].copy()

    # Within error group, keep first 5
    df_error["_rank"] = df_error.groupby(key_cols).cumcount() + 1
    df_error = df_error[df_error["_rank"] <= 5].drop(columns=["_dup_count", "_rank"])

    df = pd.concat([df_ok, df_error], ignore_index=True)
    after = len(df)
    log.info(f"  [Duplicates] Rows before: {before}, after: {after} | removed: {before - after}")
    return df


# Price Outlier Correction

def fix_price_outliers(df: pd.DataFrame,
                       price_col: str = "original_price_inr") -> pd.DataFrame:
    df = df.copy()
    corrected = 0
    capped = 0

    for cat in df["category"].unique():
        mask = df["category"] == cat
        prices = df.loc[mask, price_col]
        median_p = prices.median()
        p99 = prices.quantile(0.99)

        # Decimal error: price > 10× median → likely 100× inflated
        decimal_err = mask & (df[price_col] > 10 * median_p)
        if decimal_err.any():
            df.loc[decimal_err, price_col] = (df.loc[decimal_err, price_col] / 100).round(2)
            corrected += decimal_err.sum()

        # Re-compute p99 after correction
        prices_fixed = df.loc[mask, price_col]
        p99_new = prices_fixed.quantile(0.99)
        still_extreme = mask & (df[price_col] > p99_new)
        if still_extreme.any():
            df.loc[still_extreme, price_col] = p99_new.round(2)
            capped += still_extreme.sum()

    log.info(f"  [Outliers] {corrected} decimal-error prices corrected; {capped} capped at p99.")
    return df


# Payment Method Standardisation

PAYMENT_ALIASES = {
    # UPI group
    "upi": "UPI", "phonepe": "UPI", "googlepay": "UPI", "google pay": "UPI",
    "paytm": "UPI", "bhim": "UPI", "upi/phonepe": "UPI", "upi/googlepay": "UPI",
    # Credit Card
    "credit card": "Credit Card", "creditcard": "Credit Card",
    "credit_card": "Credit Card", "cc": "Credit Card",
    "visa": "Credit Card", "mastercard": "Credit Card", "amex": "Credit Card",
    # Debit Card
    "debit card": "Debit Card", "debitcard": "Debit Card",
    "debit_card": "Debit Card", "dc": "Debit Card",
    "rupay": "Debit Card",
    # Cash on Delivery
    "cash on delivery": "Cash on Delivery", "cod": "Cash on Delivery",
    "c.o.d": "Cash on Delivery", "c.o.d.": "Cash on Delivery",
    "cash": "Cash on Delivery",
    # Net Banking
    "net banking": "Net Banking", "netbanking": "Net Banking",
    "net_banking": "Net Banking", "neft": "Net Banking", "imps": "Net Banking",
    # Wallet
    "wallet": "Wallet", "mobikwik": "Wallet", "freecharge": "Wallet",
    "amazon pay": "Wallet", "amazonpay": "Wallet",
    # BNPL
    "bnpl": "BNPL", "buy now pay later": "BNPL", "lazypay": "BNPL",
    "simpl": "BNPL", "emi": "BNPL",
}

def clean_payment_methods(series: pd.Series) -> pd.Series:
    def normalise(val):
        if pd.isna(val):
            return "Other"
        key = str(val).strip().lower()
        return PAYMENT_ALIASES.get(key, str(val).strip().title())

    cleaned = series.map(normalise)
    changed = (cleaned != series).sum()
    log.info(f"  [Payment] {changed} payment method values standardised.")
    return cleaned


# MISSING VALUE IMPUTATION (supplementary)

def impute_missing(df: pd.DataFrame) -> pd.DataFrame:
    # delivery_charges: 0 for Prime eligible, else median by tier
    if "delivery_charges" in df.columns:
        tier_medians = df.groupby("customer_tier")["delivery_charges"].transform("median")
        df["delivery_charges"] = df["delivery_charges"].fillna(
            df["is_prime_eligible"].map({True: 0, False: None})
        ).fillna(tier_medians).fillna(0)

    # customer_age_group: mode per customer_tier
    if "customer_age_group" in df.columns:
        mode_map = (
            df[df["customer_age_group"].notna()]
            .groupby("customer_tier")["customer_age_group"]
            .agg(lambda x: x.mode()[0] if len(x) else "26-35")
        )
        df["customer_age_group"] = df.apply(
            lambda r: mode_map.get(r["customer_tier"], "26-35")
            if pd.isna(r["customer_age_group"]) else r["customer_age_group"],
            axis=1,
        )

    # festival_name: blank string where is_festival_sale is False
    if "festival_name" in df.columns:
        df["festival_name"] = df["festival_name"].fillna("None")

    # customer_rating: already handled in clean_ratings; safety fill
    if "customer_rating" in df.columns:
        df["customer_rating"] = df["customer_rating"].fillna(df["customer_rating"].median())

    log.info("  [Impute] Residual missing values filled.")
    return df


def clean_dataframe(df: pd.DataFrame, year: int) -> pd.DataFrame:
    log.info(f"\n{'='*60}")
    log.info(f"  Cleaning year: {year}  |  Rows: {len(df):,}  |  Cols: {len(df.columns)}")
    log.info(f"{'='*60}")

    # ── 1. Dates ──────────────────────────────────────────────────────────────
    log.info("► Challenge 1: Date standardisation")
    df["order_date"] = clean_dates(df["order_date"])

    # ── 2. Prices ─────────────────────────────────────────────────────────────
    log.info("► Challenge 2: Price cleaning")
    df["original_price_inr"] = clean_price(df["original_price_inr"], "original_price_inr")

    # ── 3. Ratings ────────────────────────────────────────────────────────────
    log.info("► Challenge 3: Rating standardisation")
    df["customer_rating"] = clean_ratings(df["customer_rating"])

    # ── 4. Cities ─────────────────────────────────────────────────────────────
    log.info("► Challenge 4: City normalisation")
    df["customer_city"] = clean_cities(df["customer_city"])

    # ── 5. Booleans ───────────────────────────────────────────────────────────
    log.info("► Challenge 5: Boolean cleaning")
    for col in ["is_prime_member", "is_festival_sale", "is_prime_eligible"]:
        if col in df.columns:
            df[col] = clean_boolean(df[col])

    # ── 6. Categories ─────────────────────────────────────────────────────────
    log.info("► Challenge 6: Category standardisation")
    df["category"] = clean_categories(df["category"])

    # ── 7. Delivery days ──────────────────────────────────────────────────────
    log.info("► Challenge 7: Delivery days cleaning")
    df["delivery_days"] = clean_delivery_days(df["delivery_days"])

    # ── 8. Duplicates ─────────────────────────────────────────────────────────
    log.info("► Challenge 8: Duplicate handling")
    df = handle_duplicates(df)

    # ── 9. Outliers ───────────────────────────────────────────────────────────
    log.info("► Challenge 9: Price outlier correction")
    df = fix_price_outliers(df, "original_price_inr")

    # ── 10. Payment methods ───────────────────────────────────────────────────
    log.info("► Challenge 10: Payment method standardisation")
    df["payment_method"] = clean_payment_methods(df["payment_method"])

    # ── Impute remaining missing ───────────────────────────────────────────────
    log.info("► Imputing residual missing values")
    df = impute_missing(df)

    # ── Recalculate derived columns ───────────────────────────────────────────
    log.info("► Recalculating derived columns")
    df["discounted_price_inr"] = (
        df["original_price_inr"] * (1 - df["discount_percent"] / 100)
    ).round(2)
    df["subtotal_inr"] = (df["discounted_price_inr"] * df["quantity"]).round(2)
    df["final_amount_inr"] = (df["subtotal_inr"] + df["delivery_charges"].fillna(0)).round(2)

    # Ensure order_month / order_year / order_quarter are consistent
    dates = pd.to_datetime(df["order_date"], errors="coerce")
    df["order_month"]   = dates.dt.month
    df["order_year"]    = dates.dt.year.fillna(year).astype(int)
    df["order_quarter"] = dates.dt.quarter

    log.info(f"  ✓ Year {year} cleaned → {len(df):,} rows remaining.")
    return df


def clean_catalog(catalog_path: str) -> pd.DataFrame:
    log.info("\n► Cleaning product catalog")
    df = pd.read_csv(catalog_path)
    df["category"]         = clean_categories(df["category"])
    df["is_prime_eligible"] = clean_boolean(df["is_prime_eligible"])
    log.info(f"  ✓ Catalog cleaned → {len(df):,} products.")
    return df


# DATA QUALITY REPORT

def generate_quality_report(df_before: pd.DataFrame,
                             df_after:  pd.DataFrame,
                             year: int) -> pd.DataFrame:
    rows = []
    for col in df_before.columns:
        if col not in df_after.columns:
            continue
        before_null = int(df_before[col].isna().sum())
        after_null  = int(df_after[col].isna().sum()) if col in df_after.columns else 0
        rows.append({
            "year": year,
            "column": col,
            "dtype_before": str(df_before[col].dtype),
            "dtype_after":  str(df_after[col].dtype),
            "null_before":  before_null,
            "null_after":   after_null,
            "rows_before":  len(df_before),
            "rows_after":   len(df_after),
        })
    return pd.DataFrame(rows)


# PIPELINE ENTRY POINT

def run_pipeline(input_dir: str,
                 output_dir: str,
                 years: list = None,
                 catalog_file: str = None) -> pd.DataFrame:
    os.makedirs(output_dir, exist_ok=True)
    if years is None:
        years = list(range(2015, 2026))

    all_dfs = []
    quality_reports = []

    for year in years:
        fname = os.path.join(input_dir, f"amazon_india_{year}.csv")
        if not os.path.exists(fname):
            log.warning(f"  File not found, skipping: {fname}")
            continue

        log.info(f"\n{'#'*60}")
        log.info(f"  Loading {fname}")
        df_raw = pd.read_csv(fname, low_memory=False)
        df_before = df_raw.copy()

        df_clean = clean_dataframe(df_raw.copy(), year)

        # Save year-wise cleaned file
        out_path = os.path.join(output_dir, f"amazon_india_{year}_cleaned.csv")
        df_clean.to_csv(out_path, index=False)
        log.info(f"  ✓ Saved: {out_path}")

        # Quality report
        qr = generate_quality_report(df_before, df_clean, year)
        quality_reports.append(qr)

        all_dfs.append(df_clean)

    # Combine all years
    if all_dfs:
        master_df = pd.concat(all_dfs, ignore_index=True)
        master_path = os.path.join(output_dir, "amazon_india_master_cleaned.csv")
        master_df.to_csv(master_path, index=False)
        log.info(f"\n✅ Master cleaned file: {master_path}  |  {len(master_df):,} rows")

        # Quality report master
        if quality_reports:
            qr_master = pd.concat(quality_reports, ignore_index=True)
            qr_path = os.path.join(output_dir, "data_quality_report.csv")
            qr_master.to_csv(qr_path, index=False)
            log.info(f"✅ Quality report: {qr_path}")
    else:
        master_df = pd.DataFrame()
        log.error("No data files were processed.")

    # Clean catalog
    if catalog_file and os.path.exists(catalog_file):
        df_cat = clean_catalog(catalog_file)
        cat_out = os.path.join(output_dir, "amazon_india_products_catalog_cleaned.csv")
        df_cat.to_csv(cat_out, index=False)
        log.info(f"✅ Cleaned catalog: {cat_out}")

    return master_df

# CLI

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Amazon India Data Cleaning Pipeline")
    parser.add_argument("--input_dir",   default="data/raw",     help="Raw CSVs directory")
    parser.add_argument("--output_dir",  default="data/cleaned", help="Output directory")
    parser.add_argument("--catalog",     default="data/raw/amazon_india_products_catalog.csv")
    parser.add_argument("--years", nargs="*", type=int,
                        default=list(range(2015, 2026)), help="Years to process")
    args = parser.parse_args()

    df = run_pipeline(
        input_dir    = args.input_dir,
        output_dir   = args.output_dir,
        years        = args.years,
        catalog_file = args.catalog,
    )
    print(f"\n🎉 Pipeline complete! Total rows in master file: {len(df):,}")
