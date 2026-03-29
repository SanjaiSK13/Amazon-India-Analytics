import os, warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
import seaborn as sns
from matplotlib.gridspec import GridSpec

warnings.filterwarnings("ignore")

# Paths
BASE     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA     = os.path.join(BASE, "data", "cleaned", "amazon_india_master_cleaned.csv")
OUT_DIR  = os.path.join(BASE, "reports", "eda_charts")
os.makedirs(OUT_DIR, exist_ok=True)

# Global Style
PALETTE   = ["#FF9900","#232F3E","#146EB4","#F3A847","#1A73E8","#34A853","#EA4335","#9C27B0"]
CAT_PAL   = sns.color_palette("Set2", 12)
BG        = "#FAFAFA"
ACCENT    = "#FF9900"
DARK      = "#232F3E"

plt.rcParams.update({
    "figure.facecolor":  BG,
    "axes.facecolor":    BG,
    "axes.edgecolor":    "#CCCCCC",
    "axes.labelcolor":   DARK,
    "axes.titlesize":    14,
    "axes.titleweight":  "bold",
    "axes.titlecolor":   DARK,
    "xtick.color":       "#555555",
    "ytick.color":       "#555555",
    "text.color":        DARK,
    "font.family":       "DejaVu Sans",
    "grid.color":        "#EEEEEE",
    "grid.linewidth":    0.8,
    "legend.framealpha": 0.9,
    "legend.edgecolor":  "#DDDDDD",
})

def save(fig, name):
    path = os.path.join(OUT_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"  Saved: {name}")

def fmt_inr(x, _=None):
    if x >= 1e7:  return f"₹{x/1e7:.1f}Cr"
    if x >= 1e5:  return f"₹{x/1e5:.1f}L"
    if x >= 1e3:  return f"₹{x/1e3:.0f}K"
    return f"₹{x:.0f}"

def add_watermark(fig):
    fig.text(0.99, 0.01, "Amazon India Analytics | 2015–2025",
             ha="right", va="bottom", fontsize=7, color="#AAAAAA")

# Load Data
print("\nLoading cleaned master dataset...")
df = pd.read_csv(DATA, low_memory=False)
df["order_date"]      = pd.to_datetime(df["order_date"], errors="coerce")
df["final_amount_inr"] = pd.to_numeric(df["final_amount_inr"], errors="coerce")
df["original_price_inr"] = pd.to_numeric(df["original_price_inr"], errors="coerce")
df["discount_percent"] = pd.to_numeric(df["discount_percent"], errors="coerce")
df["customer_rating"]  = pd.to_numeric(df["customer_rating"], errors="coerce")
df["delivery_days"]    = pd.to_numeric(df["delivery_days"], errors="coerce")
df = df[df["final_amount_inr"] > 0].copy()

print(f"  Rows: {len(df):,} | Years: {sorted(df['order_year'].unique())}")
print(f"  Starting 20 EDA visualizations...\n")

# Q1 — Revenue Trend Analysis (Yearly)
print("Q1: Revenue trend analysis...")
yearly = (df.groupby("order_year")["final_amount_inr"]
            .sum().reset_index(name="revenue"))
yearly["growth_pct"] = yearly["revenue"].pct_change() * 100

fig, ax1 = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor(BG)

bars = ax1.bar(yearly["order_year"], yearly["revenue"],
               color=ACCENT, alpha=0.85, width=0.6, zorder=3)
ax1.set_xlabel("Year", fontsize=12)
ax1.set_ylabel("Total Revenue", fontsize=12)
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_inr))
ax1.set_title("Yearly Revenue Trend — Amazon India", fontsize=15, pad=15)
ax1.grid(axis="y", zorder=0)

ax2 = ax1.twinx()
ax2.plot(yearly["order_year"], yearly["growth_pct"],
         color=DARK, marker="o", linewidth=2.5, markersize=7, zorder=4)
ax2.set_ylabel("YoY Growth %", fontsize=12, color=DARK)
ax2.axhline(0, color="#AAAAAA", linewidth=0.8, linestyle="--")

for _, row in yearly.iterrows():
    ax1.text(row["order_year"], row["revenue"] * 1.02,
             fmt_inr(row["revenue"]), ha="center", fontsize=9, fontweight="bold", color=DARK)
    if pd.notna(row["growth_pct"]):
        clr = "#34A853" if row["growth_pct"] > 0 else "#EA4335"
        ax2.text(row["order_year"], row["growth_pct"] + 1.5,
                 f"{row['growth_pct']:+.1f}%", ha="center", fontsize=8, color=clr, fontweight="bold")

p1 = mpatches.Patch(color=ACCENT, label="Revenue")
p2 = plt.Line2D([0],[0], color=DARK, marker="o", label="YoY Growth %")
ax1.legend(handles=[p1, p2], loc="upper left", fontsize=10)
add_watermark(fig)
save(fig, "Q1_yearly_revenue_trend.png")

# Q2 — Seasonal Patterns (Monthly Heatmap)
print("Q2: Seasonal patterns...")
df["month_name"] = df["order_date"].dt.strftime("%b")
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
pivot = (df.groupby(["order_year","order_month"])["final_amount_inr"]
           .sum().unstack(fill_value=0))
pivot.columns = [MONTHS[c-1] for c in pivot.columns]
pivot = pivot.reindex(columns=MONTHS, fill_value=0)

fig, axes = plt.subplots(1, 2, figsize=(16, 6))
fig.patch.set_facecolor(BG)
fig.suptitle("Seasonal Sales Patterns — Monthly Analysis", fontsize=15, fontweight="bold", color=DARK)

sns.heatmap(pivot / 1e6, annot=True, fmt=".1f", cmap="YlOrRd",
            ax=axes[0], linewidths=0.5, cbar_kws={"label": "Revenue (₹M)"})
axes[0].set_title("Monthly Revenue Heatmap (₹ Millions)", fontsize=12)
axes[0].set_xlabel("Month"); axes[0].set_ylabel("Year")

monthly_avg = pivot.mean()
colors = [ACCENT if v == monthly_avg.max() else "#146EB4" for v in monthly_avg]
axes[1].bar(monthly_avg.index, monthly_avg.values, color=colors, alpha=0.85)
axes[1].set_title("Average Monthly Revenue (All Years)", fontsize=12)
axes[1].set_xlabel("Month"); axes[1].set_ylabel("Avg Revenue (₹)")
axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(fmt_inr))
axes[1].grid(axis="y")
peak_month = monthly_avg.idxmax()
axes[1].annotate(f"Peak: {peak_month}", xy=(peak_month, monthly_avg.max()),
                 xytext=(peak_month, monthly_avg.max()*1.08),
                 ha="center", fontsize=9, color=ACCENT, fontweight="bold",
                 arrowprops=dict(arrowstyle="->", color=ACCENT))

plt.tight_layout()
add_watermark(fig)
save(fig, "Q2_seasonal_patterns.png")

# Q3 — RFM Customer Segmentation
print("Q3: RFM customer segmentation...")
snapshot = df["order_date"].max() + pd.Timedelta(days=1)
rfm = df.groupby("customer_id").agg(
    Recency   = ("order_date", lambda x: (snapshot - x.max()).days),
    Frequency = ("transaction_id", "count"),
    Monetary  = ("final_amount_inr", "sum")
).reset_index()

for col in ["Recency","Frequency","Monetary"]:
    labels_asc = [4,3,2,1] if col == "Recency" else [1,2,3,4]
    try:
        scores = pd.qcut(rfm[col], 4, labels=labels_asc, duplicates="drop")
        # qcut may return fewer bins due to duplicates; remap to 1-4
        rfm[f"{col}_score"] = pd.to_numeric(scores, errors="coerce").fillna(2).astype(int)
    except Exception:
        # Fallback: rank-based scoring
        if col == "Recency":
            rfm[f"{col}_score"] = pd.cut(rfm[col].rank(pct=True),
                bins=[0,.25,.5,.75,1.01], labels=[4,3,2,1]).astype(int)
        else:
            rfm[f"{col}_score"] = pd.cut(rfm[col].rank(pct=True),
                bins=[0,.25,.5,.75,1.01], labels=[1,2,3,4]).astype(int)

rfm["RFM_Score"] = (rfm["Recency_score"].astype(int) +
                    rfm["Frequency_score"].astype(int) +
                    rfm["Monetary_score"].astype(int))

def segment(score):
    if score >= 10: return "Champions"
    if score >= 8:  return "Loyal"
    if score >= 6:  return "Potential"
    if score >= 4:  return "At Risk"
    return "Lost"

rfm["Segment"] = rfm["RFM_Score"].apply(segment)

fig = plt.figure(figsize=(16, 6))
fig.patch.set_facecolor(BG)
fig.suptitle("RFM Customer Segmentation", fontsize=15, fontweight="bold", color=DARK)
gs = GridSpec(1, 3, figure=fig, wspace=0.35)

seg_colors = {"Champions":"#34A853","Loyal":"#146EB4","Potential":"#FF9900",
              "At Risk":"#F4B400","Lost":"#EA4335"}

ax1 = fig.add_subplot(gs[0])
seg_counts = rfm["Segment"].value_counts()
wedge_colors = [seg_colors[s] for s in seg_counts.index]
ax1.pie(seg_counts, labels=seg_counts.index, colors=wedge_colors,
        autopct="%1.1f%%", startangle=90, pctdistance=0.8,
        textprops={"fontsize":9})
ax1.set_title("Customer Segment Distribution", fontsize=11)

ax2 = fig.add_subplot(gs[1])
seg_rev = rfm.groupby("Segment")["Monetary"].mean().sort_values(ascending=True)
bars = ax2.barh(seg_rev.index, seg_rev.values,
                color=[seg_colors[s] for s in seg_rev.index], alpha=0.85)
ax2.set_title("Avg Revenue per Segment", fontsize=11)
ax2.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_inr))
ax2.grid(axis="x")
for bar, val in zip(bars, seg_rev.values):
    ax2.text(val * 1.01, bar.get_y() + bar.get_height()/2,
             fmt_inr(val), va="center", fontsize=8)

ax3 = fig.add_subplot(gs[2])
sample = rfm.sample(min(2000, len(rfm)), random_state=42)
scatter_colors = [seg_colors[s] for s in sample["Segment"]]
ax3.scatter(sample["Frequency"], sample["Monetary"] / 1000,
            c=scatter_colors, alpha=0.5, s=15)
ax3.set_xlabel("Frequency (orders)"); ax3.set_ylabel("Monetary (₹K)")
ax3.set_title("Frequency vs Monetary Value", fontsize=11)
handles = [mpatches.Patch(color=v, label=k) for k,v in seg_colors.items()]
ax3.legend(handles=handles, fontsize=7, loc="upper right")

add_watermark(fig)
save(fig, "Q3_rfm_segmentation.png")

# Q4 — Payment Method Evolution
print("Q4: Payment method evolution...")
pay_yr = (df.groupby(["order_year","payment_method"])["transaction_id"]
            .count().unstack(fill_value=0))
pay_pct = pay_yr.div(pay_yr.sum(axis=1), axis=0) * 100

fig, axes = plt.subplots(1, 2, figsize=(16, 6))
fig.patch.set_facecolor(BG)
fig.suptitle("Payment Method Evolution — Amazon India", fontsize=15, fontweight="bold", color=DARK)

pay_colors = {"UPI":"#34A853","Cash on Delivery":"#EA4335","Credit Card":"#146EB4",
              "Debit Card":"#4285F4","Net Banking":"#9C27B0",
              "Wallet":"#FF9900","BNPL":"#00BCD4"}
cols_order = [c for c in ["UPI","Cash on Delivery","Credit Card","Debit Card",
                           "Net Banking","Wallet","BNPL"] if c in pay_pct.columns]

pay_pct[cols_order].plot(kind="area", stacked=True, ax=axes[0],
    color=[pay_colors.get(c,"#AAAAAA") for c in cols_order], alpha=0.8)
axes[0].set_title("Payment Share Over Time (Stacked Area)", fontsize=12)
axes[0].set_ylabel("Share (%)"); axes[0].set_xlabel("Year")
axes[0].legend(fontsize=8, loc="upper right")
axes[0].set_ylim(0, 100)

latest_yr = pay_yr.index.max()
latest_counts = pay_yr.loc[latest_yr].sort_values(ascending=True)
bar_colors = [pay_colors.get(c,"#AAAAAA") for c in latest_counts.index]
axes[1].barh(latest_counts.index, latest_counts.values, color=bar_colors, alpha=0.85)
axes[1].set_title(f"Payment Methods — {latest_yr}", fontsize=12)
axes[1].set_xlabel("Number of Transactions")
axes[1].grid(axis="x")
total = latest_counts.sum()
for i, (idx, val) in enumerate(latest_counts.items()):
    axes[1].text(val * 1.01, i, f"{val:,} ({val/total*100:.1f}%)", va="center", fontsize=9)

plt.tight_layout()
add_watermark(fig)
save(fig, "Q4_payment_evolution.png")

# Q5 — Category Performance (Subcategory level since only Electronics)
print("Q5: Category/subcategory performance...")
subcat = (df.groupby("subcategory")["final_amount_inr"]
            .agg(["sum","count","mean"]).reset_index()
            .rename(columns={"sum":"revenue","count":"orders","mean":"avg_order"}))
subcat = subcat.sort_values("revenue", ascending=False).head(12)

fig, axes = plt.subplots(1, 3, figsize=(18, 6))
fig.patch.set_facecolor(BG)
fig.suptitle("Subcategory Performance Analysis", fontsize=15, fontweight="bold", color=DARK)

colors_sub = sns.color_palette("tab10", len(subcat))
axes[0].barh(subcat["subcategory"], subcat["revenue"],
             color=colors_sub, alpha=0.85)
axes[0].set_title("Revenue by Subcategory", fontsize=12)
axes[0].xaxis.set_major_formatter(mticker.FuncFormatter(fmt_inr))
axes[0].invert_yaxis(); axes[0].grid(axis="x")

axes[1].barh(subcat["subcategory"], subcat["orders"],
             color=colors_sub, alpha=0.85)
axes[1].set_title("Orders by Subcategory", fontsize=12)
axes[1].xaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"{x/1e3:.0f}K"))
axes[1].invert_yaxis(); axes[1].grid(axis="x")

wedges, texts, autotexts = axes[2].pie(
    subcat["revenue"], labels=subcat["subcategory"],
    autopct="%1.1f%%", colors=colors_sub, startangle=90,
    pctdistance=0.8, textprops={"fontsize": 7})
axes[2].set_title("Revenue Share (Subcategory)", fontsize=12)

plt.tight_layout()
add_watermark(fig)
save(fig, "Q5_category_performance.png")

# Q6 — Prime vs Non-Prime Analysis
print("Q6: Prime membership analysis...")
prime = df.copy()
prime["Prime"] = prime["is_prime_member"].map({True:"Prime", False:"Non-Prime"})

fig, axes = plt.subplots(2, 3, figsize=(18, 10))
fig.patch.set_facecolor(BG)
fig.suptitle("Prime vs Non-Prime Customer Behaviour", fontsize=15, fontweight="bold", color=DARK)

prime_colors = {"Prime":"#FF9900","Non-Prime":"#146EB4"}
pcolors = [prime_colors["Prime"], prime_colors["Non-Prime"]]

# Avg order value
avg_ov = prime.groupby("Prime")["final_amount_inr"].mean()
axes[0,0].bar(avg_ov.index, avg_ov.values, color=pcolors, alpha=0.85, width=0.5)
axes[0,0].set_title("Avg Order Value", fontsize=11)
axes[0,0].yaxis.set_major_formatter(mticker.FuncFormatter(fmt_inr))
axes[0,0].grid(axis="y")
for i,(k,v) in enumerate(avg_ov.items()):
    axes[0,0].text(i, v*1.02, fmt_inr(v), ha="center", fontsize=10, fontweight="bold")

# Order frequency per customer
freq = prime.groupby(["customer_id","Prime"])["transaction_id"].count().reset_index()
freq_avg = freq.groupby("Prime")["transaction_id"].mean()
axes[0,1].bar(freq_avg.index, freq_avg.values, color=pcolors, alpha=0.85, width=0.5)
axes[0,1].set_title("Avg Orders per Customer", fontsize=11)
axes[0,1].grid(axis="y")
for i,(k,v) in enumerate(freq_avg.items()):
    axes[0,1].text(i, v*1.02, f"{v:.1f}", ha="center", fontsize=10, fontweight="bold")

# Delivery days
dd = prime.groupby("Prime")["delivery_days"].mean()
axes[0,2].bar(dd.index, dd.values, color=pcolors, alpha=0.85, width=0.5)
axes[0,2].set_title("Avg Delivery Days", fontsize=11)
axes[0,2].grid(axis="y")
for i,(k,v) in enumerate(dd.items()):
    axes[0,2].text(i, v*1.02, f"{v:.1f} days", ha="center", fontsize=10, fontweight="bold")

# Return rate
ret = prime.groupby("Prime")["return_status"].apply(
    lambda x: (x=="Returned").sum()/len(x)*100)
axes[1,0].bar(ret.index, ret.values, color=pcolors, alpha=0.85, width=0.5)
axes[1,0].set_title("Return Rate (%)", fontsize=11)
axes[1,0].set_ylabel("%"); axes[1,0].grid(axis="y")
for i,(k,v) in enumerate(ret.items()):
    axes[1,0].text(i, v*1.02, f"{v:.1f}%", ha="center", fontsize=10, fontweight="bold")

# Revenue distribution
for lbl, grp in prime.groupby("Prime"):
    grp["final_amount_inr"].clip(0, grp["final_amount_inr"].quantile(0.99)).plot(
        kind="hist", bins=40, alpha=0.6, ax=axes[1,1],
        color=prime_colors[lbl], label=lbl)
axes[1,1].set_title("Order Value Distribution", fontsize=11)
axes[1,1].set_xlabel("Order Value (₹)")
axes[1,1].xaxis.set_major_formatter(mticker.FuncFormatter(fmt_inr))
axes[1,1].legend(); axes[1,1].grid(axis="y")

# Prime growth over years
prime_yr = prime.groupby(["order_year","Prime"])["customer_id"].nunique().unstack(fill_value=0)
prime_yr.plot(kind="bar", ax=axes[1,2], color=pcolors, alpha=0.85)
axes[1,2].set_title("Unique Customers by Year", fontsize=11)
axes[1,2].set_xlabel("Year"); axes[1,2].set_ylabel("Customers")
axes[1,2].legend(fontsize=9); axes[1,2].grid(axis="y")
axes[1,2].tick_params(axis="x", rotation=0)

plt.tight_layout()
add_watermark(fig)
save(fig, "Q6_prime_analysis.png")

# Q7 — Geographic Analysis
print("Q7: Geographic analysis...")
city_rev = (df.groupby(["customer_city","customer_tier"])["final_amount_inr"]
              .agg(["sum","count"]).reset_index()
              .rename(columns={"sum":"revenue","count":"orders"}))
city_top = city_rev.sort_values("revenue", ascending=False).head(15)

tier_rev = (df.groupby("customer_tier")["final_amount_inr"]
              .agg(["sum","count","mean"]).reset_index()
              .rename(columns={"sum":"revenue","count":"orders","mean":"avg_order"}))
tier_order = ["Metro","Tier1","Tier2","Rural"]
tier_rev["customer_tier"] = pd.Categorical(tier_rev["customer_tier"],
                                            categories=tier_order, ordered=True)
tier_rev = tier_rev.sort_values("customer_tier")

tier_colors = {"Metro":"#FF9900","Tier1":"#146EB4","Tier2":"#34A853","Rural":"#9C27B0"}

fig, axes = plt.subplots(1, 3, figsize=(18, 7))
fig.patch.set_facecolor(BG)
fig.suptitle("Geographic Revenue Analysis", fontsize=15, fontweight="bold", color=DARK)

city_colors = [tier_colors.get(t,"#AAAAAA") for t in city_top["customer_tier"]]
axes[0].barh(city_top["customer_city"], city_top["revenue"],
             color=city_colors, alpha=0.85)
axes[0].set_title("Top 15 Cities by Revenue", fontsize=12)
axes[0].xaxis.set_major_formatter(mticker.FuncFormatter(fmt_inr))
axes[0].invert_yaxis(); axes[0].grid(axis="x")
handles = [mpatches.Patch(color=v, label=k) for k,v in tier_colors.items()]
axes[0].legend(handles=handles, fontsize=8, title="Tier")

t_colors = [tier_colors.get(t,"#AAAAAA") for t in tier_rev["customer_tier"]]
axes[1].bar(tier_rev["customer_tier"], tier_rev["revenue"],
            color=t_colors, alpha=0.85, width=0.5)
axes[1].set_title("Revenue by City Tier", fontsize=12)
axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(fmt_inr))
axes[1].grid(axis="y")
for i, row in tier_rev.iterrows():
    axes[1].text(list(tier_rev["customer_tier"]).index(row["customer_tier"]),
                 row["revenue"]*1.02, fmt_inr(row["revenue"]),
                 ha="center", fontsize=9, fontweight="bold")

axes[2].bar(tier_rev["customer_tier"], tier_rev["avg_order"],
            color=t_colors, alpha=0.85, width=0.5)
axes[2].set_title("Avg Order Value by Tier", fontsize=12)
axes[2].yaxis.set_major_formatter(mticker.FuncFormatter(fmt_inr))
axes[2].grid(axis="y")
for i, row in tier_rev.iterrows():
    axes[2].text(list(tier_rev["customer_tier"]).index(row["customer_tier"]),
                 row["avg_order"]*1.02, fmt_inr(row["avg_order"]),
                 ha="center", fontsize=9, fontweight="bold")

plt.tight_layout()
add_watermark(fig)
save(fig, "Q7_geographic_analysis.png")

# Q8 — Festival Sales Impact
print("Q8: Festival sales impact...")
df["is_fest"] = df["is_festival_sale"].astype(str).str.lower().isin(["true","1","yes"])
fest_comp = df.groupby("is_fest").agg(
    revenue=("final_amount_inr","sum"),
    orders=("transaction_id","count"),
    avg_order=("final_amount_inr","mean"),
    avg_discount=("discount_percent","mean")
).reset_index()
fest_comp["label"] = fest_comp["is_fest"].map({True:"Festival", False:"Regular"})

festival_rev = (df[df["is_fest"] & df["festival_name"].notna() & (df["festival_name"]!="None")]
                .groupby("festival_name")["final_amount_inr"].sum()
                .sort_values(ascending=False).head(10))

fig, axes = plt.subplots(2, 2, figsize=(16, 10))
fig.patch.set_facecolor(BG)
fig.suptitle("Festival Sales Impact Analysis", fontsize=15, fontweight="bold", color=DARK)

metrics = ["revenue","orders","avg_order","avg_discount"]
titles  = ["Total Revenue","Number of Orders","Avg Order Value","Avg Discount %"]
fmt_fns = [fmt_inr, lambda x,_: f"{x/1e3:.0f}K", fmt_inr, lambda x,_: f"{x:.1f}%"]
f_colors = ["#FF9900","#146EB4"]

for ax, metric, title, fmtf in zip(axes.flat, metrics, titles, fmt_fns):
    bars = ax.bar(fest_comp["label"], fest_comp[metric], color=f_colors, alpha=0.85, width=0.45)
    ax.set_title(title, fontsize=12)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmtf))
    ax.grid(axis="y")
    for bar, val in zip(bars, fest_comp[metric]):
        ax.text(bar.get_x()+bar.get_width()/2, val*1.02,
                fmtf(val, None), ha="center", fontsize=10, fontweight="bold")

plt.tight_layout()
add_watermark(fig)
save(fig, "Q8_festival_sales.png")

fig2, ax = plt.subplots(figsize=(12, 5))
fig2.patch.set_facecolor(BG)
colors_f = sns.color_palette("tab10", len(festival_rev))
bars = ax.bar(festival_rev.index, festival_rev.values, color=colors_f, alpha=0.85)
ax.set_title("Revenue by Festival Event (Top 10)", fontsize=14, fontweight="bold")
ax.set_ylabel("Revenue"); ax.set_xlabel("")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_inr))
ax.grid(axis="y"); ax.tick_params(axis="x", rotation=25)
for bar, val in zip(bars, festival_rev.values):
    ax.text(bar.get_x()+bar.get_width()/2, val*1.02,
            fmt_inr(val), ha="center", fontsize=9, fontweight="bold")
add_watermark(fig2)
save(fig2, "Q8b_festival_by_event.png")

# Q9 — Age Group Behaviour
print("Q9: Age group analysis...")
age = df.groupby("customer_age_group").agg(
    revenue=("final_amount_inr","sum"),
    orders=("transaction_id","count"),
    avg_order=("final_amount_inr","mean"),
    avg_rating=("customer_rating","mean"),
).reset_index()
age_order = ["18-25","26-35","36-45","46-55","55+"]
age["customer_age_group"] = pd.Categorical(age["customer_age_group"],
                                            categories=age_order, ordered=True)
age = age.sort_values("customer_age_group")

age_subcat = (df.groupby(["customer_age_group","subcategory"])["final_amount_inr"]
                .sum().unstack(fill_value=0))
age_subcat = age_subcat.reindex(age_order).fillna(0)

fig, axes = plt.subplots(1, 3, figsize=(18, 6))
fig.patch.set_facecolor(BG)
fig.suptitle("Customer Age Group Behaviour", fontsize=15, fontweight="bold", color=DARK)

age_colors = sns.color_palette("viridis", len(age))
axes[0].bar(age["customer_age_group"], age["revenue"], color=age_colors, alpha=0.85)
axes[0].set_title("Revenue by Age Group", fontsize=12)
axes[0].yaxis.set_major_formatter(mticker.FuncFormatter(fmt_inr))
axes[0].grid(axis="y")
for i, row in age.iterrows():
    axes[0].text(age_order.index(row["customer_age_group"]), row["revenue"]*1.01,
                 fmt_inr(row["revenue"]), ha="center", fontsize=8, fontweight="bold")

axes[1].bar(age["customer_age_group"], age["avg_order"], color=age_colors, alpha=0.85)
axes[1].set_title("Avg Order Value by Age Group", fontsize=12)
axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(fmt_inr))
axes[1].grid(axis="y")

top5_sub = age_subcat[age_subcat.sum().nlargest(5).index]
top5_sub.plot(kind="bar", stacked=True, ax=axes[2],
              colormap="tab10", alpha=0.85)
axes[2].set_title("Subcategory Preference by Age", fontsize=12)
axes[2].set_xlabel("Age Group"); axes[2].set_ylabel("Revenue")
axes[2].yaxis.set_major_formatter(mticker.FuncFormatter(fmt_inr))
axes[2].legend(fontsize=7, loc="upper right"); axes[2].grid(axis="y")
axes[2].tick_params(axis="x", rotation=0)

plt.tight_layout()
add_watermark(fig)
save(fig, "Q9_age_group_analysis.png")

# Q10 — Price vs Demand Analysis
print("Q10: Price vs demand analysis...")
price_bins = pd.cut(df["original_price_inr"],
                    bins=[0,1000,5000,15000,50000,200000],
                    labels=["<1K","1K-5K","5K-15K","15K-50K","50K+"])
df["price_bucket"] = price_bins

price_demand = df.groupby("price_bucket").agg(
    orders=("transaction_id","count"),
    revenue=("final_amount_inr","sum"),
    avg_discount=("discount_percent","mean"),
    avg_rating=("customer_rating","mean"),
).reset_index()

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.patch.set_facecolor(BG)
fig.suptitle("Price vs Demand Analysis", fontsize=15, fontweight="bold", color=DARK)

pb_colors = sns.color_palette("Blues_r", len(price_demand))
axes[0,0].bar(price_demand["price_bucket"].astype(str), price_demand["orders"],
              color=pb_colors, alpha=0.9)
axes[0,0].set_title("Order Volume by Price Range", fontsize=12)
axes[0,0].set_ylabel("Orders"); axes[0,0].grid(axis="y")
axes[0,0].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"{x/1e3:.0f}K"))

axes[0,1].bar(price_demand["price_bucket"].astype(str), price_demand["revenue"],
              color=pb_colors, alpha=0.9)
axes[0,1].set_title("Revenue by Price Range", fontsize=12)
axes[0,1].yaxis.set_major_formatter(mticker.FuncFormatter(fmt_inr))
axes[0,1].grid(axis="y")

axes[1,0].bar(price_demand["price_bucket"].astype(str), price_demand["avg_discount"],
              color=ACCENT, alpha=0.85)
axes[1,0].set_title("Avg Discount % by Price Range", fontsize=12)
axes[1,0].set_ylabel("Discount %"); axes[1,0].grid(axis="y")
for i, row in price_demand.iterrows():
    axes[1,0].text(i, row["avg_discount"]*1.02,
                   f"{row['avg_discount']:.1f}%", ha="center", fontsize=9)

sample_p = df[["original_price_inr","discount_percent"]].dropna().sample(
    min(3000,len(df)), random_state=42)
axes[1,1].scatter(sample_p["original_price_inr"], sample_p["discount_percent"],
                  alpha=0.3, s=8, color=DARK)
z = np.polyfit(sample_p["original_price_inr"], sample_p["discount_percent"], 1)
xline = np.linspace(sample_p["original_price_inr"].min(),
                    sample_p["original_price_inr"].quantile(0.95), 100)
axes[1,1].plot(xline, np.poly1d(z)(xline), color=ACCENT, linewidth=2, label="Trend")
axes[1,1].set_title("Price vs Discount Scatter", fontsize=12)
axes[1,1].set_xlabel("Price (₹)"); axes[1,1].set_ylabel("Discount %")
axes[1,1].xaxis.set_major_formatter(mticker.FuncFormatter(fmt_inr))
axes[1,1].legend(); axes[1,1].grid()

plt.tight_layout()
add_watermark(fig)
save(fig, "Q10_price_demand.png")

# Q11 — Delivery Performance
print("Q11: Delivery performance...")
df["on_time"] = df["delivery_days"] <= 5

fig, axes = plt.subplots(1, 3, figsize=(18, 6))
fig.patch.set_facecolor(BG)
fig.suptitle("Delivery Performance Analysis", fontsize=15, fontweight="bold", color=DARK)

axes[0].hist(df["delivery_days"].dropna(), bins=range(0,20),
             color=ACCENT, alpha=0.85, edgecolor="white")
axes[0].set_title("Delivery Days Distribution", fontsize=12)
axes[0].set_xlabel("Days"); axes[0].set_ylabel("Orders")
axes[0].axvline(df["delivery_days"].mean(), color=DARK, linestyle="--",
                label=f"Mean: {df['delivery_days'].mean():.1f}d")
axes[0].legend(); axes[0].grid(axis="y")

tier_del = df.groupby("customer_tier")["delivery_days"].mean().reindex(tier_order)
axes[1].bar(tier_del.index, tier_del.values,
            color=[tier_colors.get(t,"#AAA") for t in tier_del.index], alpha=0.85)
axes[1].set_title("Avg Delivery Days by City Tier", fontsize=12)
axes[1].set_ylabel("Days"); axes[1].grid(axis="y")
for i,(k,v) in enumerate(tier_del.items()):
    axes[1].text(i, v*1.02, f"{v:.1f}d", ha="center", fontsize=10, fontweight="bold")

del_type = df.groupby("delivery_type")["final_amount_inr"].agg(["mean","count"])
del_colors = sns.color_palette("Set2", len(del_type))
axes[2].bar(del_type.index, del_type["mean"], color=del_colors, alpha=0.85)
axes[2].set_title("Avg Order Value by Delivery Type", fontsize=12)
axes[2].yaxis.set_major_formatter(mticker.FuncFormatter(fmt_inr))
axes[2].grid(axis="y")
ax2b = axes[2].twinx()
ax2b.plot(del_type.index, del_type["count"], color=DARK,
          marker="o", linewidth=2, label="Order count")
ax2b.set_ylabel("Order Count")
ax2b.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"{x/1e3:.0f}K"))

plt.tight_layout()
add_watermark(fig)
save(fig, "Q11_delivery_performance.png")

# Q12 — Return Rate Analysis
print("Q12: Return analysis...")
ret_cat = df.groupby("subcategory").apply(
    lambda x: pd.Series({
        "return_rate": (x["return_status"]=="Returned").mean()*100,
        "cancel_rate": (x["return_status"]=="Cancelled").mean()*100,
        "orders": len(x)
    })
).reset_index().sort_values("return_rate", ascending=False).head(12)

ret_yr = df.groupby("order_year").apply(
    lambda x: pd.Series({
        "return_rate":  (x["return_status"]=="Returned").mean()*100,
        "cancel_rate":  (x["return_status"]=="Cancelled").mean()*100,
        "delivered_rate":(x["return_status"]=="Delivered").mean()*100,
    })
)

fig, axes = plt.subplots(1, 3, figsize=(18, 6))
fig.patch.set_facecolor(BG)
fig.suptitle("Return & Cancellation Analysis", fontsize=15, fontweight="bold", color=DARK)

axes[0].barh(ret_cat["subcategory"], ret_cat["return_rate"],
             color="#EA4335", alpha=0.8, label="Return")
axes[0].barh(ret_cat["subcategory"], ret_cat["cancel_rate"],
             left=ret_cat["return_rate"], color="#F4B400", alpha=0.8, label="Cancel")
axes[0].set_title("Return & Cancel Rate by Subcategory", fontsize=11)
axes[0].set_xlabel("%"); axes[0].invert_yaxis()
axes[0].legend(fontsize=9); axes[0].grid(axis="x")

axes[1].plot(ret_yr.index, ret_yr["return_rate"], color="#EA4335",
             marker="o", linewidth=2.5, label="Return %")
axes[1].plot(ret_yr.index, ret_yr["cancel_rate"], color="#F4B400",
             marker="s", linewidth=2.5, label="Cancel %")
axes[1].plot(ret_yr.index, ret_yr["delivered_rate"], color="#34A853",
             marker="^", linewidth=2.5, label="Delivered %")
axes[1].set_title("Return Trend by Year", fontsize=12)
axes[1].set_ylabel("%"); axes[1].set_xlabel("Year")
axes[1].legend(fontsize=9); axes[1].grid()

overall = df["return_status"].value_counts()
ret_colors = {"Delivered":"#34A853","Returned":"#EA4335","Cancelled":"#F4B400"}
axes[2].pie(overall, labels=overall.index,
            colors=[ret_colors.get(s,"#AAA") for s in overall.index],
            autopct="%1.1f%%", startangle=90, pctdistance=0.8)
axes[2].set_title("Overall Order Status", fontsize=12)

plt.tight_layout()
add_watermark(fig)
save(fig, "Q12_return_analysis.png")

# Q13 — Brand Performance
print("Q13: Brand performance...")
brand = df.groupby("brand").agg(
    revenue=("final_amount_inr","sum"),
    orders=("transaction_id","count"),
    avg_rating=("product_rating","mean"),
    avg_price=("original_price_inr","mean"),
).reset_index().sort_values("revenue", ascending=False).head(15)

fig, axes = plt.subplots(1, 3, figsize=(18, 7))
fig.patch.set_facecolor(BG)
fig.suptitle("Brand Performance Analysis", fontsize=15, fontweight="bold", color=DARK)

brand_colors = sns.color_palette("tab20", len(brand))
axes[0].barh(brand["brand"], brand["revenue"], color=brand_colors, alpha=0.85)
axes[0].set_title("Top 15 Brands by Revenue", fontsize=12)
axes[0].xaxis.set_major_formatter(mticker.FuncFormatter(fmt_inr))
axes[0].invert_yaxis(); axes[0].grid(axis="x")

axes[1].barh(brand["brand"], brand["orders"], color=brand_colors, alpha=0.85)
axes[1].set_title("Top 15 Brands by Orders", fontsize=12)
axes[1].xaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"{x/1e3:.0f}K"))
axes[1].invert_yaxis(); axes[1].grid(axis="x")

sc = axes[2].scatter(brand["avg_price"], brand["avg_rating"],
                     s=brand["revenue"]/brand["revenue"].max()*800+50,
                     c=range(len(brand)), cmap="tab20", alpha=0.8)
for _, row in brand.iterrows():
    axes[2].annotate(row["brand"],
                     (row["avg_price"], row["avg_rating"]),
                     fontsize=7, ha="center", va="bottom")
axes[2].set_title("Brand Positioning (size=revenue)", fontsize=12)
axes[2].set_xlabel("Avg Price (₹)"); axes[2].set_ylabel("Avg Rating")
axes[2].xaxis.set_major_formatter(mticker.FuncFormatter(fmt_inr))
axes[2].grid()

plt.tight_layout()
add_watermark(fig)
save(fig, "Q13_brand_performance.png")

# Q14 — Customer Lifetime Value (Cohort)
print("Q14: CLV cohort analysis...")
df["cohort_year"] = df.groupby("customer_id")["order_year"].transform("min")
clv = df.groupby(["cohort_year","customer_id"])["final_amount_inr"].sum().reset_index()
clv_summary = clv.groupby("cohort_year").agg(
    avg_clv=("final_amount_inr","mean"),
    total_customers=("customer_id","count"),
    total_rev=("final_amount_inr","sum"),
).reset_index()

cohort_matrix = (df.groupby(["cohort_year","order_year"])["customer_id"]
                   .nunique().unstack(fill_value=0))

fig, axes = plt.subplots(1, 3, figsize=(18, 6))
fig.patch.set_facecolor(BG)
fig.suptitle("Customer Lifetime Value & Cohort Analysis", fontsize=15, fontweight="bold", color=DARK)

colors_c = sns.color_palette("viridis", len(clv_summary))
axes[0].bar(clv_summary["cohort_year"].astype(str), clv_summary["avg_clv"],
            color=colors_c, alpha=0.85)
axes[0].set_title("Avg CLV by Acquisition Year", fontsize=12)
axes[0].yaxis.set_major_formatter(mticker.FuncFormatter(fmt_inr))
axes[0].set_xlabel("Cohort Year"); axes[0].grid(axis="y")
axes[0].tick_params(axis="x", rotation=0)

axes[1].bar(clv_summary["cohort_year"].astype(str), clv_summary["total_customers"],
            color=colors_c, alpha=0.85)
axes[1].set_title("New Customers Acquired by Year", fontsize=12)
axes[1].set_ylabel("Customers"); axes[1].grid(axis="y")
axes[1].tick_params(axis="x", rotation=0)

if len(cohort_matrix) > 1:
    cohort_pct = cohort_matrix.div(cohort_matrix.iloc[:,0], axis=0) * 100
    sns.heatmap(cohort_pct, annot=True, fmt=".0f", cmap="YlGn",
                ax=axes[2], linewidths=0.5,
                cbar_kws={"label":"Retention %"})
    axes[2].set_title("Cohort Retention Heatmap (%)", fontsize=12)
    axes[2].set_xlabel("Active Year"); axes[2].set_ylabel("Cohort Year")
else:
    clv_dist = clv["final_amount_inr"].clip(0, clv["final_amount_inr"].quantile(0.95))
    axes[2].hist(clv_dist, bins=40, color=ACCENT, alpha=0.85, edgecolor="white")
    axes[2].set_title("CLV Distribution", fontsize=12)
    axes[2].set_xlabel("Lifetime Value (₹)")
    axes[2].xaxis.set_major_formatter(mticker.FuncFormatter(fmt_inr))
    axes[2].grid(axis="y")

plt.tight_layout()
add_watermark(fig)
save(fig, "Q14_clv_cohort.png")

# Q15 — Discount Effectiveness
print("Q15: Discount effectiveness...")
df["disc_bucket"] = pd.cut(df["discount_percent"],
    bins=[-1,0,10,20,30,50,100],
    labels=["0%","1-10%","11-20%","21-30%","31-50%","50%+"])

disc = df.groupby("disc_bucket").agg(
    orders=("transaction_id","count"),
    revenue=("final_amount_inr","sum"),
    avg_order=("final_amount_inr","mean"),
    return_rate=("return_status", lambda x: (x=="Returned").mean()*100),
).reset_index()

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.patch.set_facecolor(BG)
fig.suptitle("Discount Effectiveness Analysis", fontsize=15, fontweight="bold", color=DARK)

d_colors = sns.color_palette("RdYlGn_r", len(disc))
axes[0,0].bar(disc["disc_bucket"].astype(str), disc["orders"],
              color=d_colors, alpha=0.85)
axes[0,0].set_title("Order Volume by Discount Band", fontsize=12)
axes[0,0].set_ylabel("Orders"); axes[0,0].grid(axis="y")

axes[0,1].bar(disc["disc_bucket"].astype(str), disc["revenue"],
              color=d_colors, alpha=0.85)
axes[0,1].set_title("Revenue by Discount Band", fontsize=12)
axes[0,1].yaxis.set_major_formatter(mticker.FuncFormatter(fmt_inr))
axes[0,1].grid(axis="y")

axes[1,0].bar(disc["disc_bucket"].astype(str), disc["avg_order"],
              color=d_colors, alpha=0.85)
axes[1,0].set_title("Avg Order Value by Discount Band", fontsize=12)
axes[1,0].yaxis.set_major_formatter(mticker.FuncFormatter(fmt_inr))
axes[1,0].grid(axis="y")

axes[1,1].bar(disc["disc_bucket"].astype(str), disc["return_rate"],
              color="#EA4335", alpha=0.8)
axes[1,1].set_title("Return Rate by Discount Band", fontsize=12)
axes[1,1].set_ylabel("%"); axes[1,1].grid(axis="y")
for i, row in disc.iterrows():
    axes[1,1].text(i, row["return_rate"]*1.02,
                   f"{row['return_rate']:.1f}%", ha="center", fontsize=9)

for ax in axes.flat:
    ax.tick_params(axis="x", rotation=15)

plt.tight_layout()
add_watermark(fig)
save(fig, "Q15_discount_effectiveness.png")

# Q16 — Product Rating Analysis
print("Q16: Product rating analysis...")
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.patch.set_facecolor(BG)
fig.suptitle("Product Rating & Customer Satisfaction", fontsize=15, fontweight="bold", color=DARK)

axes[0,0].hist(df["customer_rating"].dropna(), bins=20,
               color=ACCENT, alpha=0.85, edgecolor="white")
axes[0,0].set_title("Customer Rating Distribution", fontsize=12)
axes[0,0].set_xlabel("Rating (1-5)"); axes[0,0].set_ylabel("Count")
axes[0,0].grid(axis="y")
axes[0,0].axvline(df["customer_rating"].mean(), color=DARK, linestyle="--",
                  label=f"Mean: {df['customer_rating'].mean():.2f}")
axes[0,0].legend()

rating_ret = df.groupby(pd.cut(df["customer_rating"], bins=[0,2,3,4,5],
    labels=["1-2","2-3","3-4","4-5"]))["return_status"].apply(
    lambda x: (x=="Returned").mean()*100).reset_index()
rating_ret.columns = ["rating_band","return_rate"]
axes[0,1].bar(rating_ret["rating_band"].astype(str), rating_ret["return_rate"],
              color=["#EA4335","#F4B400","#146EB4","#34A853"], alpha=0.85)
axes[0,1].set_title("Return Rate by Rating Band", fontsize=12)
axes[0,1].set_ylabel("%"); axes[0,1].grid(axis="y")

sub_rating = df.groupby("subcategory")["customer_rating"].mean().sort_values(ascending=False).head(10)
axes[1,0].barh(sub_rating.index, sub_rating.values,
               color=sns.color_palette("RdYlGn",len(sub_rating)), alpha=0.85)
axes[1,0].set_title("Avg Customer Rating by Subcategory", fontsize=12)
axes[1,0].set_xlabel("Avg Rating"); axes[1,0].set_xlim(0,5)
axes[1,0].axvline(4, color=DARK, linestyle="--", alpha=0.5)
axes[1,0].invert_yaxis(); axes[1,0].grid(axis="x")

rating_yr = df.groupby("order_year")["customer_rating"].mean()
axes[1,1].plot(rating_yr.index, rating_yr.values, color=ACCENT,
               marker="o", linewidth=2.5, markersize=8)
axes[1,1].set_title("Avg Rating Trend by Year", fontsize=12)
axes[1,1].set_ylabel("Rating"); axes[1,1].set_ylim(1,5)
axes[1,1].grid()
for yr, val in rating_yr.items():
    axes[1,1].text(yr, val+0.05, f"{val:.2f}", ha="center", fontsize=9, fontweight="bold")

plt.tight_layout()
add_watermark(fig)
save(fig, "Q16_rating_analysis.png")

# Q17 — Customer Purchase Frequency & Loyalty
print("Q17: Purchase frequency & loyalty...")
cust_freq = df.groupby("customer_id").agg(
    total_orders=("transaction_id","count"),
    total_spent=("final_amount_inr","sum"),
    years_active=("order_year",lambda x: x.nunique()),
    avg_order=("final_amount_inr","mean"),
).reset_index()

freq_bins = pd.cut(cust_freq["total_orders"],
    bins=[0,1,3,6,10,100],
    labels=["1","2-3","4-6","7-10","10+"])
cust_freq["freq_band"] = freq_bins

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.patch.set_facecolor(BG)
fig.suptitle("Customer Purchase Frequency & Loyalty", fontsize=15, fontweight="bold", color=DARK)

band_counts = cust_freq["freq_band"].value_counts().sort_index()
fb_colors = sns.color_palette("Blues", len(band_counts))
axes[0,0].bar(band_counts.index.astype(str), band_counts.values, color=fb_colors, alpha=0.85)
axes[0,0].set_title("Customers by Order Frequency", fontsize=12)
axes[0,0].set_xlabel("Number of Orders"); axes[0,0].set_ylabel("Customers")
axes[0,0].grid(axis="y")
for i,(k,v) in enumerate(band_counts.items()):
    axes[0,0].text(i, v*1.01, f"{v:,}", ha="center", fontsize=9)

band_rev = cust_freq.groupby("freq_band")["total_spent"].mean().sort_index()
axes[0,1].bar(band_rev.index.astype(str), band_rev.values, color=fb_colors, alpha=0.85)
axes[0,1].set_title("Avg Lifetime Spend by Frequency", fontsize=12)
axes[0,1].yaxis.set_major_formatter(mticker.FuncFormatter(fmt_inr))
axes[0,1].grid(axis="y")

sample_f = cust_freq.sample(min(2000,len(cust_freq)), random_state=42)
axes[1,0].scatter(sample_f["total_orders"],
                  sample_f["total_spent"]/1000,
                  alpha=0.3, s=8, color=DARK)
axes[1,0].set_title("Orders vs Total Spend per Customer", fontsize=12)
axes[1,0].set_xlabel("Total Orders"); axes[1,0].set_ylabel("Total Spend (₹K)")
axes[1,0].grid()

ya = cust_freq["years_active"].value_counts().sort_index()
axes[1,1].bar(ya.index.astype(str), ya.values, color=ACCENT, alpha=0.85)
axes[1,1].set_title("Customers by Years Active", fontsize=12)
axes[1,1].set_xlabel("Years Active"); axes[1,1].set_ylabel("Customers")
axes[1,1].grid(axis="y")

plt.tight_layout()
add_watermark(fig)
save(fig, "Q17_purchase_frequency.png")

# Q18 — Spending Tier Analysis
print("Q18: Spending tier analysis...")
spend = df.groupby("customer_spending_tier").agg(
    revenue=("final_amount_inr","sum"),
    orders=("transaction_id","count"),
    avg_order=("final_amount_inr","mean"),
    customers=("customer_id","nunique"),
    return_rate=("return_status",lambda x:(x=="Returned").mean()*100),
).reset_index()

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.patch.set_facecolor(BG)
fig.suptitle("Customer Spending Tier Analysis", fontsize=15, fontweight="bold", color=DARK)

st_colors = {"Budget":"#34A853","Standard":"#146EB4","Premium":"#FF9900","Luxury":"#9C27B0"}
s_colors = [st_colors.get(t,"#AAA") for t in spend["customer_spending_tier"]]

axes[0,0].bar(spend["customer_spending_tier"], spend["revenue"], color=s_colors, alpha=0.85)
axes[0,0].set_title("Revenue by Spending Tier", fontsize=12)
axes[0,0].yaxis.set_major_formatter(mticker.FuncFormatter(fmt_inr))
axes[0,0].grid(axis="y")

axes[0,1].bar(spend["customer_spending_tier"], spend["avg_order"], color=s_colors, alpha=0.85)
axes[0,1].set_title("Avg Order Value by Tier", fontsize=12)
axes[0,1].yaxis.set_major_formatter(mticker.FuncFormatter(fmt_inr))
axes[0,1].grid(axis="y")

axes[1,0].bar(spend["customer_spending_tier"], spend["customers"], color=s_colors, alpha=0.85)
axes[1,0].set_title("Unique Customers by Tier", fontsize=12)
axes[1,0].set_ylabel("Customers"); axes[1,0].grid(axis="y")
axes[1,0].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"{x/1e3:.0f}K"))

axes[1,1].bar(spend["customer_spending_tier"], spend["return_rate"],
              color="#EA4335", alpha=0.75)
axes[1,1].set_title("Return Rate by Spending Tier", fontsize=12)
axes[1,1].set_ylabel("%"); axes[1,1].grid(axis="y")
for i,row in spend.iterrows():
    axes[1,1].text(i, row["return_rate"]*1.02,
                   f"{row['return_rate']:.1f}%", ha="center", fontsize=9, fontweight="bold")

plt.tight_layout()
add_watermark(fig)
save(fig, "Q18_spending_tier.png")

# Q19 — Competitive Pricing & Brand Positioning
print("Q19: Competitive pricing analysis...")
brand_price = df.groupby("brand").agg(
    avg_price=("original_price_inr","mean"),
    median_price=("original_price_inr","median"),
    revenue=("final_amount_inr","sum"),
    orders=("transaction_id","count"),
    avg_discount=("discount_percent","mean"),
).reset_index().sort_values("revenue", ascending=False).head(15)

fig, axes = plt.subplots(1, 2, figsize=(16, 7))
fig.patch.set_facecolor(BG)
fig.suptitle("Competitive Pricing & Brand Positioning", fontsize=15, fontweight="bold", color=DARK)

bp_colors = sns.color_palette("tab20", len(brand_price))
sub_box = df[df["brand"].isin(brand_price["brand"].head(10))]
sub_box.boxplot(column="original_price_inr", by="brand", ax=axes[0],
                patch_artist=True,
                boxprops=dict(facecolor=ACCENT, alpha=0.6),
                medianprops=dict(color=DARK, linewidth=2),
                whiskerprops=dict(color="#888"),
                capprops=dict(color="#888"),
                flierprops=dict(marker=".", markersize=3, alpha=0.3))
axes[0].set_title("Price Distribution — Top 10 Brands", fontsize=12)
axes[0].set_xlabel("Brand"); axes[0].set_ylabel("Price (₹)")
axes[0].yaxis.set_major_formatter(mticker.FuncFormatter(fmt_inr))
axes[0].tick_params(axis="x", rotation=45)
plt.sca(axes[0]); plt.title("Price Distribution — Top 10 Brands", fontsize=12)

sc = axes[1].scatter(brand_price["avg_price"], brand_price["avg_discount"],
                     s=brand_price["revenue"]/brand_price["revenue"].max()*600+50,
                     c=range(len(brand_price)), cmap="tab20", alpha=0.8)
for _, row in brand_price.iterrows():
    axes[1].annotate(row["brand"], (row["avg_price"], row["avg_discount"]),
                     fontsize=7, ha="center", va="bottom", color=DARK)
axes[1].set_title("Avg Price vs Avg Discount (size=revenue)", fontsize=12)
axes[1].set_xlabel("Avg Price (₹)"); axes[1].set_ylabel("Avg Discount %")
axes[1].xaxis.set_major_formatter(mticker.FuncFormatter(fmt_inr))
axes[1].grid()

plt.tight_layout()
add_watermark(fig)
save(fig, "Q19_pricing_analysis.png")

# Q20 — Business Health Dashboard (Multi-KPI Summary)
print("Q20: Business health dashboard...")
fig = plt.figure(figsize=(20, 14))
fig.patch.set_facecolor(BG)
fig.suptitle("Business Health Dashboard — Amazon India Analytics",
             fontsize=18, fontweight="bold", color=DARK, y=0.98)
gs = GridSpec(3, 4, figure=fig, hspace=0.45, wspace=0.4)

total_rev    = df["final_amount_inr"].sum()
total_orders = len(df)
unique_cust  = df["customer_id"].nunique()
avg_order    = df["final_amount_inr"].mean()
overall_ret  = (df["return_status"]=="Returned").mean()*100
avg_del      = df["delivery_days"].mean()
prime_pct    = df["is_prime_member"].mean()*100
avg_disc     = df["discount_percent"].mean()

kpi_data = [
    ("Total Revenue", fmt_inr(total_rev), "#FF9900"),
    ("Total Orders",  f"{total_orders:,}", "#146EB4"),
    ("Unique Customers", f"{unique_cust:,}", "#34A853"),
    ("Avg Order Value",  fmt_inr(avg_order), "#9C27B0"),
    ("Return Rate",  f"{overall_ret:.1f}%", "#EA4335"),
    ("Avg Delivery", f"{avg_del:.1f} days", "#00BCD4"),
    ("Prime Members", f"{prime_pct:.1f}%", "#FF9900"),
    ("Avg Discount", f"{avg_disc:.1f}%", "#F4B400"),
]

for i, (label, value, color) in enumerate(kpi_data):
    r, c = divmod(i, 4)
    ax = fig.add_subplot(gs[r, c]) if r < 2 else None
    if ax is None: break
    ax.set_facecolor(BG)
    ax.add_patch(mpatches.FancyBboxPatch((0.05,0.1), 0.9, 0.8,
        boxstyle="round,pad=0.05", facecolor=color, alpha=0.15,
        edgecolor=color, linewidth=2))
    ax.text(0.5, 0.65, value, ha="center", va="center",
            fontsize=18, fontweight="bold", color=color, transform=ax.transAxes)
    ax.text(0.5, 0.25, label, ha="center", va="center",
            fontsize=10, color=DARK, transform=ax.transAxes)
    ax.axis("off")

ax_rev = fig.add_subplot(gs[2, :2])
yr_rev = df.groupby("order_year")["final_amount_inr"].sum()
ax_rev.fill_between(yr_rev.index, yr_rev.values, alpha=0.3, color=ACCENT)
ax_rev.plot(yr_rev.index, yr_rev.values, color=ACCENT, marker="o", linewidth=2.5)
ax_rev.set_title("Revenue Trend", fontsize=12); ax_rev.grid()
ax_rev.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_inr))
for yr, val in yr_rev.items():
    ax_rev.text(yr, val*1.03, fmt_inr(val), ha="center", fontsize=8, fontweight="bold")

ax_pay = fig.add_subplot(gs[2, 2])
latest_pay = df[df["order_year"]==df["order_year"].max()]["payment_method"].value_counts()
wedge_c = [pay_colors.get(p,"#AAA") for p in latest_pay.index]
ax_pay.pie(latest_pay, labels=latest_pay.index, colors=wedge_c,
           autopct="%1.0f%%", startangle=90, pctdistance=0.8,
           textprops={"fontsize":7})
ax_pay.set_title(f"Payment Mix ({df['order_year'].max()})", fontsize=12)

ax_top = fig.add_subplot(gs[2, 3])
top_sub = df.groupby("subcategory")["final_amount_inr"].sum().nlargest(6)
ax_top.barh(top_sub.index, top_sub.values,
            color=sns.color_palette("tab10",len(top_sub)), alpha=0.85)
ax_top.set_title("Top Subcategories", fontsize=12)
ax_top.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_inr))
ax_top.invert_yaxis(); ax_top.grid(axis="x")

add_watermark(fig)
save(fig, "Q20_business_health_dashboard.png")

# Summary
charts = sorted([f for f in os.listdir(OUT_DIR) if f.endswith(".png")])
print(f"\n{'='*55}")
print(f"  EDA COMPLETE — {len(charts)} charts saved to:")
print(f"  {OUT_DIR}")
print(f"{'='*55}")
for c in charts:
    print(f"  {c}")
