# Amazon India Analytics — Database Schema
**Database:** `amazon_india.db` (SQLite)
**Tables:** 5 | **Views:** 15 | **Indexes:** 16

---

## Tables

### `time_dimension`
| Column | Type | Not Null | PK |
|--------|------|----------|----|
| date_id | TEXT | No | Yes |
| year | INTEGER | Yes | No |
| quarter | INTEGER | Yes | No |
| month | INTEGER | Yes | No |
| month_name | TEXT | Yes | No |
| week | INTEGER | Yes | No |
| day_of_week | INTEGER | Yes | No |
| day_name | TEXT | Yes | No |
| is_weekend | INTEGER | Yes | No |
| is_festival_period | INTEGER | Yes | No |

### `products`
| Column | Type | Not Null | PK |
|--------|------|----------|----|
| product_id | TEXT | No | Yes |
| product_name | TEXT | No | No |
| category | TEXT | No | No |
| subcategory | TEXT | No | No |
| brand | TEXT | No | No |
| base_price_2015 | REAL | No | No |
| weight_kg | REAL | No | No |
| rating | REAL | No | No |
| is_prime_eligible | INTEGER | No | No |
| launch_year | INTEGER | No | No |
| model | TEXT | No | No |

### `customers`
| Column | Type | Not Null | PK |
|--------|------|----------|----|
| customer_id | TEXT | No | Yes |
| customer_city | TEXT | No | No |
| customer_state | TEXT | No | No |
| customer_tier | TEXT | No | No |
| customer_spending_tier | TEXT | No | No |
| customer_age_group | TEXT | No | No |
| is_prime_member | INTEGER | No | No |
| first_order_year | INTEGER | No | No |
| total_orders | INTEGER | No | No |
| total_spent | REAL | No | No |
| avg_order_value | REAL | No | No |

### `festivals`
| Column | Type | Not Null | PK |
|--------|------|----------|----|
| festival_id | INTEGER | No | Yes |
| festival_name | TEXT | Yes | No |
| year | INTEGER | No | No |
| total_orders | INTEGER | No | No |
| total_revenue | REAL | No | No |
| avg_discount | REAL | No | No |

### `transactions`
| Column | Type | Not Null | PK |
|--------|------|----------|----|
| transaction_id | TEXT | No | Yes |
| order_date | TEXT | No | No |
| date_id | TEXT | No | No |
| customer_id | TEXT | No | No |
| product_id | TEXT | No | No |
| product_name | TEXT | No | No |
| category | TEXT | No | No |
| subcategory | TEXT | No | No |
| brand | TEXT | No | No |
| original_price_inr | REAL | No | No |
| discount_percent | REAL | No | No |
| discounted_price_inr | REAL | No | No |
| quantity | INTEGER | No | No |
| subtotal_inr | REAL | No | No |
| delivery_charges | REAL | No | No |
| final_amount_inr | REAL | No | No |
| payment_method | TEXT | No | No |
| delivery_days | INTEGER | No | No |
| delivery_type | TEXT | No | No |
| is_prime_member | INTEGER | No | No |
| is_festival_sale | INTEGER | No | No |
| festival_name | TEXT | No | No |
| customer_rating | REAL | No | No |
| product_rating | REAL | No | No |
| return_status | TEXT | No | No |
| order_month | INTEGER | No | No |
| order_year | INTEGER | No | No |
| order_quarter | INTEGER | No | No |
| product_weight_kg | REAL | No | No |
| is_prime_eligible | INTEGER | No | No |

---

## Analytics Views

- **`vw_yearly_revenue`**
- **`vw_monthly_revenue`**
- **`vw_category_performance`**
- **`vw_payment_trends`**
- **`vw_customer_segments`**
- **`vw_prime_analysis`**
- **`vw_geographic_revenue`**
- **`vw_festival_impact`**
- **`vw_brand_performance`**
- **`vw_delivery_performance`**
- **`vw_return_analysis`**
- **`vw_price_analysis`**
- **`vw_age_group_analysis`**
- **`vw_executive_kpis`**
- **`vw_top_products`**

---

## Connection (Python)

```python
import sqlite3, pandas as pd
conn = sqlite3.connect('data/db/amazon_india.db')
df = pd.read_sql_query('SELECT * FROM vw_executive_kpis', conn)
```

## Connection (Streamlit)

```python
import streamlit as st, sqlite3, pandas as pd

@st.cache_resource
def get_connection():
    return sqlite3.connect('data/db/amazon_india.db', check_same_thread=False)

@st.cache_data
def run_query(sql):
    conn = get_connection()
    return pd.read_sql_query(sql, conn)
```
