import sys
import os
import html as html_mod
import streamlit as st
import pandas as pd

# ── Ensure project root is on the path ────────────────────
sys.path.insert(0, os.path.dirname(__file__))

from src.styles import inject_global_styles
from src.data_loader import load_intel, load_raw_reviews, STATIONS

# ── Page Config ───────────────────────────────────────────
st.set_page_config(
    page_title="Marugame Review Intelligence",
    page_icon="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 36 36'><text y='32' font-size='32'>M</text></svg>",
    layout="wide",
)
inject_global_styles()

# ── Load Data ─────────────────────────────────────────────
df = load_intel()
raw = load_raw_reviews()

# ── Page Header ───────────────────────────────────────────
st.markdown("""
<div class="page-title">
    <span class="material-symbols-rounded" style="font-size:28px; color:#818cf8;">dashboard</span>
    Marugame Review Intelligence
</div>
<div class="page-subtitle">Overview dashboard -- key metrics across all stations</div>
""", unsafe_allow_html=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ── KPI Row ───────────────────────────────────────────────
total_reviews = df["review_id"].nunique()
total_insights = len(df)
avg_rating = df["rating"].mean() if "rating" in df.columns else 0
neg_count = len(df[df["derived_sentiment"] == "Negative"])
pos_count = len(df[df["derived_sentiment"] == "Positive"])
killers = len(df[df["is_service_killer"] == True])

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Total Reviews</div>
        <div class="kpi-value">{total_reviews}</div>
        <div class="kpi-sub">{total_insights} aspect insights extracted</div>
    </div>
    """, unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Average Rating</div>
        <div class="kpi-value">{avg_rating:.1f}<span style="font-size:0.9rem; color:#9ca3af;">/5</span></div>
        <div class="kpi-sub">across all scraped reviews</div>
    </div>
    """, unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Sentiment Split</div>
        <div class="kpi-value" style="color:#dc2626;">{neg_count} <span style="font-size:0.9rem; color:#9ca3af;">/ {pos_count}</span></div>
        <div class="kpi-sub">negative vs positive mentions</div>
    </div>
    """, unsafe_allow_html=True)

with k4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Service Killers</div>
        <div class="kpi-value" style="color:#f59e0b;">{killers}</div>
        <div class="kpi-sub">critical issues (score &le; -0.6)</div>
    </div>
    """, unsafe_allow_html=True)


st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ── Station Health Overview ───────────────────────────────
st.markdown("""
<div class="section-header">
    <span class="material-symbols-rounded section-icon">analytics</span>
    Station Health Overview
</div>
""", unsafe_allow_html=True)

cols = st.columns(5)

for i, station in enumerate(STATIONS):
    station_data = df[df["aspect"] == station]
    neg = len(station_data[station_data["derived_sentiment"] == "Negative"])
    pos = len(station_data[station_data["derived_sentiment"] == "Positive"])
    total = pos + neg if (pos + neg) > 0 else 1
    neg_pct = (neg / total) * 100

    with cols[i]:
        st.markdown(f"""
        <div class="station-card">
            <div class="station-name">{station}</div>
            <div class="station-total">{pos + neg}</div>
            <div class="station-breakdown">
                <span class="neg-count">
                    <span class="material-symbols-rounded" style="font-size:16px;">cancel</span>
                    {neg}
                </span>
                <span class="pos-count">
                    <span class="material-symbols-rounded" style="font-size:16px;">check_circle</span>
                    {pos}
                </span>
            </div>
            <div class="bar-track">
                <div class="bar-fill-neg" style="width: {neg_pct}%;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)


st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ── Recent Critical Issues ────────────────────────────────
st.markdown("""
<div class="section-header">
    <span class="material-symbols-rounded section-icon">warning</span>
    Recent Negative Mentions
</div>
""", unsafe_allow_html=True)

recent_neg = (
    df[df["derived_sentiment"] == "Negative"]
    .sort_values("date", ascending=False)
    .head(5)
)

for _, row in recent_neg.iterrows():
    item_name = html_mod.escape(str(row.get("item", "")).strip())
    opinion = html_mod.escape(str(row.get("opinion", "")).strip())
    card_title = f"{item_name}: {opinion}" if item_name and opinion else (item_name or opinion or "Unknown")
    station = html_mod.escape(str(row.get("aspect", "")))

    try:
        date_str = row["date"].strftime("%-d %B %Y · %-I:%M %p")
    except Exception:
        date_str = str(row["date"])

    rating_val = row.get("rating", "")
    rating_html = f'<span class="rating-badge">{int(rating_val)}/5</span>' if pd.notna(rating_val) and rating_val != "" else ""

    review_text = html_mod.escape(str(row.get("original_text", ""))).replace("\n", "<br>")
    if not review_text.strip():
        review_text = "No review text available."

    author = html_mod.escape(str(row.get("author", "Anonymous")))

    # Owner response
    owner_resp = html_mod.escape(str(row.get("owner_response", "")).strip()).replace("\n", "<br>")
    response_html = ""
    if owner_resp:
        response_html = f"""
        <div style="margin-top:10px; padding:10px 14px; background:rgba(79,70,229,0.1); border-radius:6px; font-size:0.85rem;">
            <span style="font-weight:600; color:#818cf8;">Owner Response:</span>
            <span style="color:#d1d5db;">{owner_resp}</span>
        </div>
        """

    st.markdown(f"""
    <div class="review-card negative">
        <div class="review-meta">
            <span class="material-symbols-rounded">calendar_today</span>
            {date_str}
            <span class="rating-badge">{station}</span>
            {rating_html}
        </div>
        <div class="review-title">{card_title}</div>
        <div class="review-text">"{review_text}"</div>
        <div class="review-author">-- {author}</div>
        {response_html}
    </div>
    """, unsafe_allow_html=True)

st.markdown("")
st.caption("Use the sidebar to navigate to Station Health or Review Explorer for deeper analysis.")