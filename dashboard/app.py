import os, sqlite3
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page Config
st.set_page_config(
    page_title="Amazon India Analytics",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Theme Colors
AMAZON_ORANGE = "#FF9900"
AMAZON_DARK   = "#232F3E"
AMAZON_BLUE   = "#146EB4"
COLORS = [AMAZON_ORANGE, AMAZON_BLUE, "#34A853", "#EA4335",
          "#9C27B0", "#00BCD4", "#F4B400", "#FF5722"]

#CSS
st.markdown("""
<style>
    /* Sidebar Background */
    [data-testid="stSidebar"] {background: #232F3E;}
    
    /* Global Sidebar Text (Labels) */
    [data-testid="stSidebar"] .stMarkdown, 
    [data-testid="stSidebar"] .stMultiSelect label,
    [data-testid="stSidebar"] .stRadio label,
    [data-testid="stSidebar"] .stSelectbox label {
        color: white !important;
    }
    
    /* FIX: Force Radio Button Text (All, Prime Only, etc.) to be visible */
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
    [data-testid="stSidebar"] label[data-baseweb="radio"] div p {
        color: #FF9900 !important;
        font-weight: 500 !important;
    }

    /* FIX: Force Selectbox Input Text and Dropdown Options to be dark */
    div[data-baseweb="select"] * {
        color: #232F3E !important;
    }
    
    /* KPI cards */
    .kpi-card {
        background: linear-gradient(135deg, #232F3E 0%, #37475A 100%);
        border-left: 4px solid #FF9900;
        border-radius: 8px;
        padding: 16px 20px;
        margin: 4px 0;
    }
    .kpi-value {font-size: 28px; font-weight: 700; color: #FF9900;}
    .kpi-label {font-size: 13px; color: #aaaaaa; margin-top: 4px;}
    .kpi-delta {font-size: 12px; margin-top: 6px;}
    .delta-up   {color: #34A853;}
    .delta-down {color: #EA4335;}

    /* Section headers */
    .section-header {
        background: linear-gradient(90deg, #232F3E, #37475A);
        color: #FF9900 !important;
        padding: 10px 16px;
        border-radius: 6px;
        font-size: 16px;
        font-weight: 600;
        margin: 12px 0 8px 0;
    }

    /* Page title */
    .page-title {
        font-size: 26px;
        font-weight: 700;
        color: #232F3E;
        border-bottom: 3px solid #FF9900;
        padding-bottom: 8px;
        margin-bottom: 20px;
    }

    /* Hide streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer     {visibility: hidden;}
    header     {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# DATABASE CONNECTION & QUERY HELPERS

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "data", "db", "amazon_india.db")

@st.cache_resource
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

@st.cache_data(ttl=300)
def q(sql: str) -> pd.DataFrame:
    return pd.read_sql_query(sql, get_conn())

def fmt_inr(val):
    if val >= 1e7:  return f"₹{val/1e7:.2f} Cr"
    if val >= 1e5:  return f"₹{val/1e5:.1f} L"
    if val >= 1e3:  return f"₹{val/1e3:.0f} K"
    return f"₹{val:.0f}"

def kpi(label, value, delta=None, delta_label=""):
    delta_html = ""
    if delta is not None:
        cls = "delta-up" if delta >= 0 else "delta-down"
        arrow = "▲" if delta >= 0 else "▼"
        delta_html = f'<div class="kpi-delta {cls}">{arrow} {abs(delta):.1f}% {delta_label}</div>'
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value">{value}</div>
        <div class="kpi-label">{label}</div>
        {delta_html}
    </div>""", unsafe_allow_html=True)

def section(title):
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)

def page_title(title, icon=""):
    st.markdown(f'<div class="page-title">{icon} {title}</div>', unsafe_allow_html=True)

# SIDEBAR NAVIGATION & FILTERS

with st.sidebar:
    st.markdown("## 🛒 Amazon India")
    st.markdown("### Analytics Dashboard")
    st.markdown("---")

    page = st.selectbox("Navigate to", [
        "🏠 Executive Summary",
        "📈 Revenue Analytics",
        "👥 Customer Analytics",
        "📦 Product & Brand",
        "🚚 Operations",
        "🔮 Advanced Analytics",
    ])

    st.markdown("---")
    st.markdown("### Global Filters")

    all_years = q("SELECT DISTINCT order_year FROM transactions ORDER BY order_year")["order_year"].tolist()
    sel_years = st.multiselect("Years", all_years, default=all_years)

    all_tiers = q("SELECT DISTINCT customer_tier FROM customers ORDER BY customer_tier")["customer_tier"].tolist()
    sel_tiers = st.multiselect("City Tier", all_tiers, default=all_tiers)

    prime_filter = st.radio("Prime Membership", ["All", "Prime Only", "Non-Prime Only"])

    st.markdown("---")
    st.markdown("**Data Summary**")
    summary = q("SELECT COUNT(*) AS txn, COUNT(DISTINCT customer_id) AS cust FROM transactions")
    st.markdown(f"- Transactions: **{summary['txn'][0]:,}**")
    st.markdown(f"- Customers: **{summary['cust'][0]:,}**")
    st.markdown(f"- Years: **{len(all_years)}** ({min(all_years)}–{max(all_years)})")

# Build dynamic WHERE clause
yr_clause   = f"order_year IN ({','.join(map(str, sel_years))})" if sel_years else "1=1"
tier_clause = f"customer_tier IN ({','.join([chr(39)+t+chr(39) for t in sel_tiers])})" if sel_tiers else "1=1"
prime_clause = ("t.is_prime_member = 1" if prime_filter == "Prime Only"
                else "t.is_prime_member = 0" if prime_filter == "Non-Prime Only"
                else "1=1")

base_filter = f"t.{yr_clause} AND {prime_clause}".replace("t.order_year", "t.order_year") if "JOIN" in "" else f"{yr_clause} AND {prime_clause}"

# PAGE 1 — EXECUTIVE SUMMARY

if page == "🏠 Executive Summary":
    page_title("Executive Summary Dashboard", "🏠")

    # KPI Row
    kpi_data = q(f"""
        SELECT
            SUM(t.final_amount_inr)               AS revenue,
            COUNT(*)                               AS orders,
            COUNT(DISTINCT t.customer_id)          AS customers,
            AVG(t.final_amount_inr)                AS aov,
            AVG(t.customer_rating)                 AS rating,
            100.0*SUM(CASE WHEN t.return_status='Returned' THEN 1 ELSE 0 END)/COUNT(*) AS ret_rate,
            100.0*SUM(CASE WHEN t.is_prime_member=1 THEN 1 ELSE 0 END)/COUNT(*) AS prime_pct,
            AVG(t.discount_percent)                AS avg_disc
        FROM transactions t
        JOIN customers c USING(customer_id)
        WHERE t.{yr_clause} AND {prime_clause} AND c.{tier_clause}
    """)
    r = kpi_data.iloc[0]

    c1,c2,c3,c4 = st.columns(4)
    with c1: kpi("Total Revenue",    fmt_inr(r["revenue"]))
    with c2: kpi("Total Orders",     f"{int(r['orders']):,}")
    with c3: kpi("Unique Customers", f"{int(r['customers']):,}")
    with c4: kpi("Avg Order Value",  fmt_inr(r["aov"]))

    c5,c6,c7,c8 = st.columns(4)
    with c5: kpi("Avg Customer Rating", f"{r['rating']:.2f} / 5.0")
    with c6: kpi("Return Rate",         f"{r['ret_rate']:.1f}%")
    with c7: kpi("Prime Orders %",      f"{r['prime_pct']:.1f}%")
    with c8: kpi("Avg Discount",        f"{r['avg_disc']:.1f}%")

    st.markdown("<br>", unsafe_allow_html=True)

    # Chart 1: Revenue Trend
    section("Chart 1 — Yearly Revenue & Growth")
    yr = q(f"SELECT order_year, SUM(final_amount_inr) AS rev, COUNT(*) AS orders FROM transactions WHERE {yr_clause} GROUP BY order_year ORDER BY order_year")
    yr["growth"] = yr["rev"].pct_change() * 100

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=yr["order_year"], y=yr["rev"], name="Revenue",
                         marker_color=AMAZON_ORANGE, opacity=0.85,
                         text=[fmt_inr(v) for v in yr["rev"]], textposition="outside"), secondary_y=False)
    fig.add_trace(go.Scatter(x=yr["order_year"], y=yr["growth"], name="YoY Growth %",
                             mode="lines+markers+text",
                             line=dict(color=AMAZON_DARK, width=3),
                             marker=dict(size=8),
                             text=[f"{v:+.1f}%" if pd.notna(v) else "" for v in yr["growth"]],
                             textposition="top center"), secondary_y=True)
    fig.update_layout(title="Yearly Revenue & YoY Growth", height=420,
                      plot_bgcolor="white", paper_bgcolor="white",
                      legend=dict(orientation="h", y=1.1))
    fig.update_yaxes(title_text="Revenue (₹)", secondary_y=False)
    fig.update_yaxes(title_text="Growth %", secondary_y=True)
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    # Chart 2: Orders by Category
    with col1:
        section("Chart 2 — Revenue by Subcategory")
        cat = q(f"SELECT subcategory, SUM(final_amount_inr) AS rev FROM transactions WHERE {base_filter} GROUP BY subcategory ORDER BY rev DESC LIMIT 10")
        fig2 = px.bar(cat, x="rev", y="subcategory", orientation="h",
                      color="rev", color_continuous_scale=["#146EB4", AMAZON_ORANGE],
                      labels={"rev":"Revenue","subcategory":""},
                      text=[fmt_inr(v) for v in cat["rev"]])
        fig2.update_layout(height=380, plot_bgcolor="white", paper_bgcolor="white",
                           coloraxis_showscale=False, yaxis=dict(autorange="reversed"))
        fig2.update_traces(textposition="outside")
        st.plotly_chart(fig2, use_container_width=True)

    # Chart 3: Payment Mix
    with col2:
        section("Chart 3 — Payment Method Mix")
        pay = q(f"SELECT payment_method, COUNT(*) AS cnt FROM transactions WHERE {base_filter} GROUP BY payment_method ORDER BY cnt DESC")
        fig3 = px.pie(pay, values="cnt", names="payment_method",
                      color_discrete_sequence=COLORS, hole=0.45)
        fig3.update_layout(height=380, paper_bgcolor="white",
                           legend=dict(orientation="v", x=1, y=0.5))
        fig3.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig3, use_container_width=True)

    col3, col4 = st.columns(2)

    # Chart 4: Return Status
    with col3:
        section("Chart 4 — Order Status Breakdown")
        ret = q(f"SELECT return_status, COUNT(*) AS cnt, ROUND(SUM(final_amount_inr),0) AS rev FROM transactions WHERE {base_filter} GROUP BY return_status")
        fig4 = px.bar(ret, x="return_status", y="cnt",
                      color="return_status",
                      color_discrete_map={"Delivered":"#34A853","Returned":"#EA4335","Cancelled":"#F4B400"},
                      text="cnt", labels={"cnt":"Orders","return_status":""})
        fig4.update_layout(height=350, plot_bgcolor="white", paper_bgcolor="white",
                           showlegend=False)
        fig4.update_traces(texttemplate="%{text:,}", textposition="outside")
        st.plotly_chart(fig4, use_container_width=True)

    # Chart 5: Prime vs Non-Prime
    with col4:
        section("Chart 5 — Prime vs Non-Prime Orders")
        prime = q(f"""SELECT
            CASE WHEN is_prime_member=1 THEN 'Prime' ELSE 'Non-Prime' END AS type,
            order_year, COUNT(*) AS orders,
            ROUND(AVG(final_amount_inr),0) AS aov
            FROM transactions WHERE {yr_clause}
            GROUP BY is_prime_member, order_year ORDER BY order_year""")
        fig5 = px.bar(prime, x="order_year", y="orders", color="type",
                      barmode="group",
                      color_discrete_map={"Prime": AMAZON_ORANGE, "Non-Prime": AMAZON_BLUE},
                      labels={"orders":"Orders","order_year":"Year","type":""})
        fig5.update_layout(height=350, plot_bgcolor="white", paper_bgcolor="white",
                           legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig5, use_container_width=True)

# PAGE 2 — REVENUE ANALYTICS

elif page == "📈 Revenue Analytics":
    page_title("Revenue Analytics", "📈")

    # Chart 6: Monthly Heatmap
    section("Chart 6 — Monthly Revenue Heatmap")
    mon = q(f"SELECT order_year, order_month, SUM(final_amount_inr) AS rev FROM transactions WHERE {yr_clause} GROUP BY order_year, order_month")
    pivot = mon.pivot(index="order_year", columns="order_month", values="rev").fillna(0)
    month_names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    pivot.columns = [month_names[c-1] for c in pivot.columns]
    fig6 = px.imshow(pivot, color_continuous_scale="YlOrRd",
                     labels=dict(color="Revenue"),
                     text_auto=False, aspect="auto")
    fig6.update_layout(height=320, paper_bgcolor="white")
    fig6.update_traces(text=[[fmt_inr(v) for v in row] for row in pivot.values],
                       texttemplate="%{text}")
    st.plotly_chart(fig6, use_container_width=True)

    col1, col2 = st.columns(2)

    # Chart 7: Quarterly Revenue
    with col1:
        section("Chart 7 — Quarterly Revenue Breakdown")
        qtr = q(f"SELECT order_year, order_quarter, SUM(final_amount_inr) AS rev FROM transactions WHERE {yr_clause} GROUP BY order_year, order_quarter")
        qtr["quarter_label"] = "Q" + qtr["order_quarter"].astype(str)
        fig7 = px.bar(qtr, x="order_year", y="rev", color="quarter_label",
                      barmode="stack", color_discrete_sequence=COLORS,
                      labels={"rev":"Revenue","order_year":"Year","quarter_label":"Quarter"})
        fig7.update_layout(height=380, plot_bgcolor="white", paper_bgcolor="white",
                           legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig7, use_container_width=True)

    # Chart 8: Revenue by City Tier
    with col2:
        section("Chart 8 — Revenue by City Tier")
        tier_rev = q(f"""SELECT c.customer_tier, t.order_year,
                    SUM(t.final_amount_inr) AS rev
                    FROM transactions t JOIN customers c USING(customer_id)
                    WHERE {yr_clause}
                    GROUP BY c.customer_tier, t.order_year""")
        fig8 = px.line(tier_rev, x="order_year", y="rev", color="customer_tier",
                       markers=True, color_discrete_sequence=COLORS,
                       labels={"rev":"Revenue","order_year":"Year","customer_tier":"Tier"})
        fig8.update_layout(height=380, plot_bgcolor="white", paper_bgcolor="white",
                           legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig8, use_container_width=True)

    col3, col4 = st.columns(2)

    # Chart 9: Festival vs Regular Revenue
    with col3:
        section("Chart 9 — Festival vs Regular Revenue")
        fest = q(f"""SELECT order_year,
                    SUM(CASE WHEN is_festival_sale=1 THEN final_amount_inr ELSE 0 END) AS festival,
                    SUM(CASE WHEN is_festival_sale=0 THEN final_amount_inr ELSE 0 END) AS regular
                    FROM transactions WHERE {yr_clause} GROUP BY order_year""")
        fig9 = go.Figure()
        fig9.add_trace(go.Bar(x=fest["order_year"], y=fest["festival"], name="Festival",
                              marker_color=AMAZON_ORANGE))
        fig9.add_trace(go.Bar(x=fest["order_year"], y=fest["regular"], name="Regular",
                              marker_color=AMAZON_BLUE))
        fig9.update_layout(barmode="group", height=370, plot_bgcolor="white",
                           paper_bgcolor="white", legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig9, use_container_width=True)

    # Chart 10: Discount Impact on Revenue
    with col4:
        section("Chart 10 — Avg Order Value by Discount Band")
        disc = q(f"""SELECT
                    CASE
                        WHEN discount_percent = 0        THEN '0%'
                        WHEN discount_percent <= 10      THEN '1-10%'
                        WHEN discount_percent <= 20      THEN '11-20%'
                        WHEN discount_percent <= 30      THEN '21-30%'
                        WHEN discount_percent <= 50      THEN '31-50%'
                        ELSE '50%+'
                    END AS disc_band,
                    COUNT(*) AS orders,
                    ROUND(AVG(final_amount_inr),0) AS aov,
                    ROUND(SUM(final_amount_inr),0) AS rev
                    FROM transactions WHERE {base_filter}
                    GROUP BY disc_band""")
        disc_order = ["0%","1-10%","11-20%","21-30%","31-50%","50%+"]
        disc["disc_band"] = pd.Categorical(disc["disc_band"], categories=disc_order, ordered=True)
        disc = disc.sort_values("disc_band")
        fig10 = make_subplots(specs=[[{"secondary_y": True}]])
        fig10.add_trace(go.Bar(x=disc["disc_band"], y=disc["orders"], name="Orders",
                               marker_color=AMAZON_BLUE, opacity=0.7), secondary_y=False)
        fig10.add_trace(go.Scatter(x=disc["disc_band"], y=disc["aov"], name="Avg Order Value",
                                   mode="lines+markers", line=dict(color=AMAZON_ORANGE, width=3),
                                   marker=dict(size=8)), secondary_y=True)
        fig10.update_layout(height=370, plot_bgcolor="white", paper_bgcolor="white",
                            legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig10, use_container_width=True)


# PAGE 3 — CUSTOMER ANALYTICS

elif page == "👥 Customer Analytics":
    page_title("Customer Analytics", "👥")

    col1, col2 = st.columns(2)

    # Chart 11: RFM Segment Distribution
    with col1:
        section("Chart 11 — RFM Customer Segments")
        seg = q("SELECT rfm_segment, COUNT(*) AS customers, ROUND(AVG(total_spent),0) AS avg_ltv FROM vw_customer_segments GROUP BY rfm_segment ORDER BY avg_ltv DESC")
        fig11 = px.bar(seg, x="rfm_segment", y="customers",
                       color="rfm_segment",
                       color_discrete_map={"Champions":"#34A853","Loyal":AMAZON_BLUE,
                                           "Potential":AMAZON_ORANGE,"At Risk":"#F4B400","Lost":"#EA4335"},
                       text="customers",
                       labels={"customers":"Customers","rfm_segment":"Segment"})
        fig11.update_layout(height=380, plot_bgcolor="white", paper_bgcolor="white", showlegend=False)
        fig11.update_traces(texttemplate="%{text:,}", textposition="outside")
        st.plotly_chart(fig11, use_container_width=True)

    # Chart 12: Customer Acquisition by Year
    with col2:
        section("Chart 12 — New Customer Acquisition")
        acq = q("SELECT first_order_year AS year, COUNT(*) AS new_customers FROM customers GROUP BY first_order_year ORDER BY year")
        fig12 = px.area(acq, x="year", y="new_customers",
                        color_discrete_sequence=[AMAZON_ORANGE],
                        labels={"new_customers":"New Customers","year":"Year"})
        fig12.update_layout(height=380, plot_bgcolor="white", paper_bgcolor="white")
        fig12.update_traces(fill="tozeroy", line_color=AMAZON_ORANGE)
        st.plotly_chart(fig12, use_container_width=True)

    col3, col4 = st.columns(2)

    # Chart 13: Age Group Revenue
    with col3:
        section("Chart 13 — Revenue by Age Group")
        age = q(f"""SELECT c.customer_age_group, SUM(t.final_amount_inr) AS rev,
                    COUNT(*) AS orders, ROUND(AVG(t.final_amount_inr),0) AS aov
                    FROM transactions t JOIN customers c USING(customer_id)
                    WHERE {yr_clause}
                    GROUP BY c.customer_age_group ORDER BY rev DESC""")
        age_order = ["18-25","26-35","36-45","46-55","55+"]
        age["customer_age_group"] = pd.Categorical(age["customer_age_group"],
                                                    categories=age_order, ordered=True)
        age = age.sort_values("customer_age_group")
        fig13 = make_subplots(specs=[[{"secondary_y": True}]])
        fig13.add_trace(go.Bar(x=age["customer_age_group"], y=age["rev"], name="Revenue",
                               marker_color=AMAZON_ORANGE, opacity=0.85), secondary_y=False)
        fig13.add_trace(go.Scatter(x=age["customer_age_group"], y=age["aov"], name="Avg Order Value",
                                   mode="lines+markers", line=dict(color=AMAZON_DARK, width=3),
                                   marker=dict(size=8)), secondary_y=True)
        fig13.update_layout(height=380, plot_bgcolor="white", paper_bgcolor="white",
                            legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig13, use_container_width=True)

    # Chart 14: Spending Tier Analysis
    with col4:
        section("Chart 14 — Customer Spending Tiers")
        spend = q(f"""SELECT c.customer_spending_tier,
                    COUNT(DISTINCT t.customer_id) AS customers,
                    SUM(t.final_amount_inr) AS rev,
                    ROUND(AVG(t.final_amount_inr),0) AS aov
                    FROM transactions t JOIN customers c USING(customer_id)
                    WHERE {yr_clause}
                    GROUP BY c.customer_spending_tier""")
        fig14 = px.scatter(spend, x="customers", y="aov",
                           size="rev", color="customer_spending_tier",
                           color_discrete_sequence=COLORS,
                           text="customer_spending_tier",
                           labels={"customers":"Unique Customers","aov":"Avg Order Value","customer_spending_tier":"Tier"})
        fig14.update_layout(height=380, plot_bgcolor="white", paper_bgcolor="white")
        fig14.update_traces(textposition="top center")
        st.plotly_chart(fig14, use_container_width=True)

    # Chart 15: Prime Membership Growth
    section("Chart 15 — Prime Membership Growth Over Years")
    prime_yr = q(f"""SELECT order_year,
                ROUND(100.0*SUM(CASE WHEN is_prime_member=1 THEN 1 ELSE 0 END)/COUNT(*),2) AS prime_pct,
                SUM(CASE WHEN is_prime_member=1 THEN final_amount_inr ELSE 0 END) AS prime_rev,
                SUM(CASE WHEN is_prime_member=0 THEN final_amount_inr ELSE 0 END) AS nonprime_rev
                FROM transactions WHERE {yr_clause} GROUP BY order_year ORDER BY order_year""")
    fig15 = make_subplots(specs=[[{"secondary_y": True}]])
    fig15.add_trace(go.Bar(x=prime_yr["order_year"], y=prime_yr["prime_rev"],
                           name="Prime Revenue", marker_color=AMAZON_ORANGE, opacity=0.85), secondary_y=False)
    fig15.add_trace(go.Bar(x=prime_yr["order_year"], y=prime_yr["nonprime_rev"],
                           name="Non-Prime Revenue", marker_color=AMAZON_BLUE, opacity=0.85), secondary_y=False)
    fig15.add_trace(go.Scatter(x=prime_yr["order_year"], y=prime_yr["prime_pct"],
                               name="Prime Order %", mode="lines+markers+text",
                               line=dict(color="#34A853", width=3), marker=dict(size=8),
                               text=[f"{v:.1f}%" for v in prime_yr["prime_pct"]],
                               textposition="top center"), secondary_y=True)
    fig15.update_layout(barmode="stack", height=380, plot_bgcolor="white", paper_bgcolor="white",
                        legend=dict(orientation="h", y=1.12))
    fig15.update_yaxes(title_text="Revenue (₹)", secondary_y=False)
    fig15.update_yaxes(title_text="Prime %", secondary_y=True, range=[0, 100])
    st.plotly_chart(fig15, use_container_width=True)

# PAGE 4 — PRODUCT & BRAND

elif page == "📦 Product & Brand":
    page_title("Product & Brand Analytics", "📦")

    col1, col2 = st.columns(2)

    # Chart 16: Top Brands Revenue
    with col1:
        section("Chart 16 — Top 15 Brands by Revenue")
        brands = q(f"""SELECT brand, SUM(final_amount_inr) AS rev,
                    COUNT(*) AS orders, ROUND(AVG(product_rating),2) AS rating
                    FROM transactions WHERE {base_filter}
                    GROUP BY brand ORDER BY rev DESC LIMIT 15""")
        fig16 = px.bar(brands, x="rev", y="brand", orientation="h",
                       color="rating", color_continuous_scale=["#EA4335", AMAZON_ORANGE, "#34A853"],
                       text=[fmt_inr(v) for v in brands["rev"]],
                       labels={"rev":"Revenue","brand":"","rating":"Avg Rating"})
        fig16.update_layout(height=480, plot_bgcolor="white", paper_bgcolor="white",
                            yaxis=dict(autorange="reversed"))
        fig16.update_traces(textposition="outside")
        st.plotly_chart(fig16, use_container_width=True)

    # Chart 17: Subcategory Treemap
    with col2:
        section("Chart 17 — Subcategory Revenue Treemap")
        tree = q(f"""SELECT category, subcategory, SUM(final_amount_inr) AS rev
                    FROM transactions WHERE {base_filter}
                    GROUP BY category, subcategory""")
        fig17 = px.treemap(tree, path=["category","subcategory"], values="rev",
                           color="rev", color_continuous_scale=["#146EB4", AMAZON_ORANGE],
                           labels={"rev":"Revenue"})
        fig17.update_layout(height=480, paper_bgcolor="white")
        fig17.update_traces(texttemplate="<b>%{label}</b><br>%{value:,.0f}")
        st.plotly_chart(fig17, use_container_width=True)

    col3, col4 = st.columns(2)

    # Chart 18: Price Range Analysis
    with col3:
        section("Chart 18 — Sales Volume by Price Range")
        price = q(f"""SELECT
                    CASE
                        WHEN original_price_inr < 1000  THEN 'Under ₹1K'
                        WHEN original_price_inr < 5000  THEN '₹1K-5K'
                        WHEN original_price_inr < 15000 THEN '₹5K-15K'
                        WHEN original_price_inr < 50000 THEN '₹15K-50K'
                        ELSE 'Above ₹50K'
                    END AS price_range,
                    COUNT(*) AS orders,
                    ROUND(SUM(final_amount_inr),0) AS rev
                    FROM transactions WHERE {base_filter}
                    GROUP BY price_range""")
        price_order = ["Under ₹1K","₹1K-5K","₹5K-15K","₹15K-50K","Above ₹50K"]
        price["price_range"] = pd.Categorical(price["price_range"], categories=price_order, ordered=True)
        price = price.sort_values("price_range")
        fig18 = make_subplots(specs=[[{"secondary_y": True}]])
        fig18.add_trace(go.Bar(x=price["price_range"], y=price["orders"],
                               name="Orders", marker_color=AMAZON_BLUE, opacity=0.85), secondary_y=False)
        fig18.add_trace(go.Scatter(x=price["price_range"], y=price["rev"],
                                   name="Revenue", mode="lines+markers",
                                   line=dict(color=AMAZON_ORANGE, width=3),
                                   marker=dict(size=8)), secondary_y=True)
        fig18.update_layout(height=380, plot_bgcolor="white", paper_bgcolor="white",
                            legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig18, use_container_width=True)

    # Chart 19: Product Rating Distribution
    with col4:
        section("Chart 19 — Product Rating vs Sales Performance")
        rat = q(f"""SELECT ROUND(product_rating,1) AS rating,
                    COUNT(*) AS orders,
                    ROUND(AVG(final_amount_inr),0) AS aov,
                    ROUND(100.0*SUM(CASE WHEN return_status='Returned' THEN 1 ELSE 0 END)/COUNT(*),2) AS ret_rate
                    FROM transactions WHERE {base_filter} AND product_rating IS NOT NULL
                    GROUP BY ROUND(product_rating,1) ORDER BY rating""")
        fig19 = make_subplots(specs=[[{"secondary_y": True}]])
        fig19.add_trace(go.Bar(x=rat["rating"], y=rat["orders"],
                               name="Orders", marker_color=AMAZON_ORANGE, opacity=0.8), secondary_y=False)
        fig19.add_trace(go.Scatter(x=rat["rating"], y=rat["ret_rate"],
                                   name="Return Rate %", mode="lines+markers",
                                   line=dict(color="#EA4335", width=2.5),
                                   marker=dict(size=7)), secondary_y=True)
        fig19.update_layout(height=380, plot_bgcolor="white", paper_bgcolor="white",
                            legend=dict(orientation="h", y=1.1),
                            xaxis_title="Product Rating")
        st.plotly_chart(fig19, use_container_width=True)

    # Chart 20: Brand Positioning Bubble
    section("Chart 20 — Brand Positioning Matrix (Price vs Rating vs Revenue)")
    bubble = q(f"""SELECT brand,
                ROUND(AVG(original_price_inr),0) AS avg_price,
                ROUND(AVG(product_rating),2) AS avg_rating,
                SUM(final_amount_inr) AS rev,
                COUNT(*) AS orders
                FROM transactions WHERE {base_filter}
                GROUP BY brand HAVING orders > 100
                ORDER BY rev DESC LIMIT 20""")
    fig20 = px.scatter(bubble, x="avg_price", y="avg_rating",
                       size="rev", color="brand",
                       text="brand", hover_data={"rev": ":,.0f", "orders": ":,"},
                       color_discrete_sequence=px.colors.qualitative.Alphabet,
                       labels={"avg_price":"Avg Price (₹)","avg_rating":"Avg Rating","brand":"Brand"})
    fig20.update_layout(height=450, plot_bgcolor="white", paper_bgcolor="white",
                        showlegend=False)
    fig20.update_traces(textposition="top center", textfont_size=9)
    st.plotly_chart(fig20, use_container_width=True)

# PAGE 5 — OPERATIONS

elif page == "🚚 Operations":
    page_title("Operations & Logistics", "🚚")

    col1, col2 = st.columns(2)

    # Chart 21: Delivery Days Distribution
    with col1:
        section("Chart 21 — Delivery Days Distribution")
        del_dist = q(f"""SELECT delivery_days, COUNT(*) AS orders
                        FROM transactions WHERE {base_filter} AND delivery_days BETWEEN 0 AND 15
                        GROUP BY delivery_days ORDER BY delivery_days""")
        fig21 = px.bar(del_dist, x="delivery_days", y="orders",
                       color="delivery_days",
                       color_continuous_scale=["#34A853", AMAZON_ORANGE, "#EA4335"],
                       labels={"delivery_days":"Delivery Days","orders":"Orders"})
        fig21.update_layout(height=370, plot_bgcolor="white", paper_bgcolor="white",
                            coloraxis_showscale=False)
        st.plotly_chart(fig21, use_container_width=True)

    # Chart 22: Delivery by Tier
    with col2:
        section("Chart 22 — Avg Delivery Days by City Tier")
        del_tier = q(f"""SELECT c.customer_tier, t.delivery_type,
                        ROUND(AVG(t.delivery_days),2) AS avg_days,
                        COUNT(*) AS orders
                        FROM transactions t JOIN customers c USING(customer_id)
                        WHERE {yr_clause}
                        GROUP BY c.customer_tier, t.delivery_type""")
        fig22 = px.bar(del_tier, x="customer_tier", y="avg_days",
                       color="delivery_type", barmode="group",
                       color_discrete_sequence=COLORS,
                       labels={"avg_days":"Avg Days","customer_tier":"City Tier","delivery_type":"Type"})
        fig22.update_layout(height=370, plot_bgcolor="white", paper_bgcolor="white",
                            legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig22, use_container_width=True)

    col3, col4 = st.columns(2)

    # Chart 23: Payment Method Trend
    with col3:
        section("Chart 23 — Payment Method Evolution")
        pay_trend = q(f"""SELECT order_year, payment_method,
                        ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER(PARTITION BY order_year),2) AS share
                        FROM transactions WHERE {yr_clause}
                        GROUP BY order_year, payment_method""")
        fig23 = px.area(pay_trend, x="order_year", y="share", color="payment_method",
                        color_discrete_sequence=COLORS,
                        labels={"share":"Market Share %","order_year":"Year","payment_method":"Method"})
        fig23.update_layout(height=370, plot_bgcolor="white", paper_bgcolor="white",
                            legend=dict(orientation="h", y=1.15))
        st.plotly_chart(fig23, use_container_width=True)

    # Chart 24: Return Rate by Subcategory
    with col4:
        section("Chart 24 — Return Rate by Subcategory")
        ret_sub = q(f"""SELECT subcategory,
                        ROUND(100.0*SUM(CASE WHEN return_status='Returned' THEN 1 ELSE 0 END)/COUNT(*),2) AS ret_rate,
                        ROUND(100.0*SUM(CASE WHEN return_status='Cancelled' THEN 1 ELSE 0 END)/COUNT(*),2) AS cancel_rate,
                        COUNT(*) AS orders
                        FROM transactions WHERE {base_filter}
                        GROUP BY subcategory ORDER BY ret_rate DESC LIMIT 12""")
        fig24 = px.bar(ret_sub, x="ret_rate", y="subcategory", orientation="h",
                       color="ret_rate",
                       color_continuous_scale=["#34A853", "#F4B400", "#EA4335"],
                       text=[f"{v:.1f}%" for v in ret_sub["ret_rate"]],
                       labels={"ret_rate":"Return Rate %","subcategory":""})
        fig24.update_layout(height=370, plot_bgcolor="white", paper_bgcolor="white",
                            yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
        fig24.update_traces(textposition="outside")
        st.plotly_chart(fig24, use_container_width=True)

    # Chart 25: Festival Sales Calendar
    section("Chart 25 — Festival Sales Impact")
    fest_detail = q(f"""SELECT festival_name,
                    SUM(CASE WHEN is_festival_sale=1 THEN final_amount_inr ELSE 0 END) AS fest_rev,
                    SUM(CASE WHEN is_festival_sale=1 THEN 1 ELSE 0 END) AS fest_orders,
                    ROUND(AVG(CASE WHEN is_festival_sale=1 THEN discount_percent END),1) AS avg_disc
                    FROM transactions WHERE {yr_clause} AND festival_name != 'None'
                    GROUP BY festival_name ORDER BY fest_rev DESC""")
    if not fest_detail.empty:
        fig25 = make_subplots(specs=[[{"secondary_y": True}]])
        fig25.add_trace(go.Bar(x=fest_detail["festival_name"], y=fest_detail["fest_rev"],
                               name="Revenue", marker_color=AMAZON_ORANGE, opacity=0.85,
                               text=[fmt_inr(v) for v in fest_detail["fest_rev"]],
                               textposition="outside"), secondary_y=False)
        fig25.add_trace(go.Scatter(x=fest_detail["festival_name"], y=fest_detail["avg_disc"],
                                   name="Avg Discount %", mode="lines+markers",
                                   line=dict(color="#EA4335", width=2.5),
                                   marker=dict(size=8)), secondary_y=True)
        fig25.update_layout(height=400, plot_bgcolor="white", paper_bgcolor="white",
                            legend=dict(orientation="h", y=1.1),
                            xaxis_tickangle=-25)
        fig25.update_yaxes(title_text="Revenue (₹)", secondary_y=False)
        fig25.update_yaxes(title_text="Avg Discount %", secondary_y=True)
        st.plotly_chart(fig25, use_container_width=True)

# PAGE 6 — ADVANCED ANALYTICS

elif page == "🔮 Advanced Analytics":
    page_title("Advanced Analytics", "🔮")

    col1, col2 = st.columns(2)

    # Chart 26: CLV Distribution
    with col1:
        section("Chart 26 — Customer Lifetime Value by Cohort")
        clv = q(f"""SELECT first_order_year AS cohort,
                    ROUND(AVG(total_spent),0) AS avg_clv,
                    COUNT(*) AS customers,
                    ROUND(AVG(total_orders),1) AS avg_orders
                    FROM customers WHERE first_order_year IN ({','.join(map(str,sel_years))})
                    GROUP BY first_order_year ORDER BY cohort""")
        fig26 = make_subplots(specs=[[{"secondary_y": True}]])
        fig26.add_trace(go.Bar(x=clv["cohort"], y=clv["avg_clv"],
                               name="Avg CLV", marker_color=AMAZON_ORANGE,
                               text=[fmt_inr(v) for v in clv["avg_clv"]],
                               textposition="outside"), secondary_y=False)
        fig26.add_trace(go.Scatter(x=clv["cohort"], y=clv["avg_orders"],
                                   name="Avg Orders", mode="lines+markers",
                                   line=dict(color=AMAZON_DARK, width=3),
                                   marker=dict(size=8)), secondary_y=True)
        fig26.update_layout(height=380, plot_bgcolor="white", paper_bgcolor="white",
                            legend=dict(orientation="h", y=1.1))
        fig26.update_yaxes(title_text="Avg CLV (₹)", secondary_y=False)
        fig26.update_yaxes(title_text="Avg Orders", secondary_y=True)
        st.plotly_chart(fig26, use_container_width=True)

    # Chart 27: Geographic Revenue Heatmap
    with col2:
        section("Chart 27 — Top Cities Revenue Heatmap")
        geo = q(f"""SELECT c.customer_city, c.customer_state, c.customer_tier,
                    SUM(t.final_amount_inr) AS rev, COUNT(*) AS orders,
                    ROUND(AVG(t.final_amount_inr),0) AS aov
                    FROM transactions t JOIN customers c USING(customer_id)
                    WHERE {yr_clause}
                    GROUP BY c.customer_city ORDER BY rev DESC LIMIT 20""")
        fig27 = px.bar(geo, x="rev", y="customer_city",
                       color="customer_tier", orientation="h",
                       color_discrete_map={"Metro": AMAZON_ORANGE,"Tier1": AMAZON_BLUE,
                                           "Tier2":"#34A853","Rural":"#9C27B0"},
                       text=[fmt_inr(v) for v in geo["rev"]],
                       labels={"rev":"Revenue","customer_city":"","customer_tier":"Tier"})
        fig27.update_layout(height=380, plot_bgcolor="white", paper_bgcolor="white",
                            yaxis=dict(autorange="reversed"),
                            legend=dict(orientation="h", y=1.1))
        fig27.update_traces(textposition="outside")
        st.plotly_chart(fig27, use_container_width=True)

    col3, col4 = st.columns(2)

    # Chart 28: Cross-sell Subcategory Correlation
    with col3:
        section("Chart 28 — Subcategory Revenue Mix by Age Group")
        age_sub = q(f"""SELECT c.customer_age_group, t.subcategory,
                    SUM(t.final_amount_inr) AS rev
                    FROM transactions t JOIN customers c USING(customer_id)
                    WHERE {yr_clause}
                    GROUP BY c.customer_age_group, t.subcategory""")
        pivot_as = age_sub.pivot_table(index="customer_age_group",
                                       columns="subcategory", values="rev", fill_value=0)
        top_subs = pivot_as.sum().nlargest(6).index
        pivot_as = pivot_as[top_subs]
        fig28 = px.imshow(pivot_as, color_continuous_scale=["white", AMAZON_ORANGE],
                          aspect="auto", labels=dict(color="Revenue"))
        fig28.update_layout(height=380, paper_bgcolor="white")
        st.plotly_chart(fig28, use_container_width=True)

    # Chart 29: Revenue Forecast (Trend Line)
    with col4:
        section("Chart 29 — Revenue Trend & Projection")
        mon_rev = q(f"""SELECT order_year, order_month,
                    SUM(final_amount_inr) AS rev
                    FROM transactions WHERE {yr_clause}
                    GROUP BY order_year, order_month ORDER BY order_year, order_month""")
        mon_rev["period"] = mon_rev["order_year"].astype(str) + "-" + mon_rev["order_month"].astype(str).str.zfill(2)
        mon_rev["idx"] = range(len(mon_rev))

        z = np.polyfit(mon_rev["idx"], mon_rev["rev"], 2)
        trend = np.poly1d(z)
        future_idx = np.arange(len(mon_rev), len(mon_rev)+6)
        future_rev = trend(future_idx)

        fig29 = go.Figure()
        fig29.add_trace(go.Scatter(x=mon_rev["period"], y=mon_rev["rev"],
                                   name="Actual", mode="lines",
                                   line=dict(color=AMAZON_BLUE, width=2)))
        fig29.add_trace(go.Scatter(x=mon_rev["period"], y=trend(mon_rev["idx"]),
                                   name="Trend", mode="lines",
                                   line=dict(color=AMAZON_ORANGE, width=2, dash="dash")))
        proj_labels = [f"Proj+{i+1}" for i in range(6)]
        fig29.add_trace(go.Scatter(x=proj_labels, y=future_rev,
                                   name="Projection", mode="lines+markers",
                                   line=dict(color="#34A853", width=2, dash="dot"),
                                   marker=dict(size=7)))
        fig29.update_layout(height=380, plot_bgcolor="white", paper_bgcolor="white",
                            legend=dict(orientation="h", y=1.1),
                            xaxis_tickangle=-45, xaxis=dict(nticks=12))
        st.plotly_chart(fig29, use_container_width=True)

    # Chart 30: Business Intelligence Command Center
    section("Chart 30 — Business Intelligence Command Center")
    st.markdown("**Key performance indicators across all dimensions — interactive drill-down**")

    cmd_data = q(f"""SELECT order_year,
                COUNT(*) AS orders,
                COUNT(DISTINCT customer_id) AS customers,
                ROUND(SUM(final_amount_inr),0) AS revenue,
                ROUND(AVG(final_amount_inr),0) AS aov,
                ROUND(AVG(discount_percent),2) AS avg_disc,
                ROUND(AVG(delivery_days),2) AS avg_del,
                ROUND(AVG(customer_rating),2) AS avg_rating,
                ROUND(100.0*SUM(CASE WHEN is_prime_member=1 THEN 1 ELSE 0 END)/COUNT(*),1) AS prime_pct,
                ROUND(100.0*SUM(CASE WHEN return_status='Returned' THEN 1 ELSE 0 END)/COUNT(*),1) AS ret_rate,
                ROUND(100.0*SUM(CASE WHEN is_festival_sale=1 THEN 1 ELSE 0 END)/COUNT(*),1) AS fest_pct
                FROM transactions WHERE {yr_clause} GROUP BY order_year ORDER BY order_year""")

    fig30 = make_subplots(rows=2, cols=3,
                          subplot_titles=["Revenue","Orders & Customers",
                                          "Avg Order Value","Prime % & Return Rate",
                                          "Avg Delivery Days","Avg Rating & Discount"],
                          vertical_spacing=0.18, horizontal_spacing=0.1)

    fig30.add_trace(go.Bar(x=cmd_data["order_year"], y=cmd_data["revenue"],
                           marker_color=AMAZON_ORANGE, showlegend=False,
                           text=[fmt_inr(v) for v in cmd_data["revenue"]],
                           textposition="outside"), row=1, col=1)

    fig30.add_trace(go.Scatter(x=cmd_data["order_year"], y=cmd_data["orders"],
                               name="Orders", line=dict(color=AMAZON_BLUE, width=2.5),
                               marker=dict(size=7)), row=1, col=2)
    fig30.add_trace(go.Scatter(x=cmd_data["order_year"], y=cmd_data["customers"],
                               name="Customers", line=dict(color=AMAZON_ORANGE, width=2.5),
                               marker=dict(size=7)), row=1, col=2)

    fig30.add_trace(go.Scatter(x=cmd_data["order_year"], y=cmd_data["aov"],
                               mode="lines+markers+text",
                               line=dict(color="#34A853", width=2.5),
                               marker=dict(size=8), showlegend=False,
                               text=[fmt_inr(v) for v in cmd_data["aov"]],
                               textposition="top center"), row=1, col=3)

    fig30.add_trace(go.Scatter(x=cmd_data["order_year"], y=cmd_data["prime_pct"],
                               name="Prime %", line=dict(color=AMAZON_ORANGE, width=2.5),
                               marker=dict(size=7)), row=2, col=1)
    fig30.add_trace(go.Scatter(x=cmd_data["order_year"], y=cmd_data["ret_rate"],
                               name="Return %", line=dict(color="#EA4335", width=2.5),
                               marker=dict(size=7)), row=2, col=1)

    fig30.add_trace(go.Bar(x=cmd_data["order_year"], y=cmd_data["avg_del"],
                           marker_color=AMAZON_BLUE, showlegend=False,
                           text=[f"{v:.1f}d" for v in cmd_data["avg_del"]],
                           textposition="outside"), row=2, col=2)

    fig30.add_trace(go.Scatter(x=cmd_data["order_year"], y=cmd_data["avg_rating"],
                               name="Avg Rating", line=dict(color="#9C27B0", width=2.5),
                               marker=dict(size=7)), row=2, col=3)
    fig30.add_trace(go.Scatter(x=cmd_data["order_year"], y=cmd_data["avg_disc"],
                               name="Avg Disc %", line=dict(color="#F4B400", width=2.5),
                               marker=dict(size=7)), row=2, col=3)

    fig30.update_layout(height=640, plot_bgcolor="white", paper_bgcolor="white",
                        legend=dict(orientation="h", y=-0.12),
                        title_text="Business Performance Command Center")
    st.plotly_chart(fig30, use_container_width=True)

    # Data table
    st.markdown("#### Raw KPI Data Table")
    cmd_display = cmd_data.copy()
    cmd_display["revenue"] = cmd_display["revenue"].apply(fmt_inr)
    cmd_display.columns = ["Year","Orders","Customers","Revenue","Avg Order",
                           "Avg Disc%","Avg Delivery","Avg Rating","Prime%","Return%","Festival%"]
    st.dataframe(cmd_display, use_container_width=True, hide_index=True)
