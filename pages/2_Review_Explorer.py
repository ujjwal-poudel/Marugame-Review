import sys
import os
import html
import streamlit as st
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.styles import inject_global_styles
from src.data_loader import load_raw_reviews

# ── Page Config ───────────────────────────────────────────
st.set_page_config(page_title="Review Explorer | Marugame", layout="wide")
inject_global_styles()

# ── Load Data ─────────────────────────────────────────────
raw = load_raw_reviews()

# ── Page Header ───────────────────────────────────────────
st.markdown("""
<div class="page-title">
    <span class="material-symbols-rounded" style="font-size:28px; color:#818cf8;">rate_review</span>
    Review Explorer
</div>
<div class="page-subtitle">Browse, search, and filter all scraped Google reviews</div>
""", unsafe_allow_html=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ── Filters ───────────────────────────────────────────────
col_search, col_rating, col_sort = st.columns([3, 1, 1])

with col_search:
    search_query = st.text_input(
        "Search reviews:",
        placeholder="Type a keyword (e.g. udon, tempura, wait)...",
    )

with col_rating:
    rating_filter = st.selectbox(
        "Rating:",
        options=["All", "5", "4", "3", "2", "1"],
    )

with col_sort:
    sort_order = st.selectbox(
        "Sort by:",
        options=["Newest first", "Oldest first", "Highest rating", "Lowest rating"],
    )

# ── Apply Filters ─────────────────────────────────────────
filtered = raw.copy()

if search_query:
    mask = filtered["text"].fillna("").str.contains(search_query, case=False)
    filtered = filtered[mask]

if rating_filter != "All":
    filtered = filtered[filtered["rating"] == int(rating_filter)]

# Sort
sort_map = {
    "Newest first": ("date", False),
    "Oldest first": ("date", True),
    "Highest rating": ("rating", False),
    "Lowest rating": ("rating", True),
}
sort_col, sort_asc = sort_map[sort_order]
filtered = filtered.sort_values(by=sort_col, ascending=sort_asc)

# ── Results Count ─────────────────────────────────────────
st.caption(f"Showing {len(filtered)} of {len(raw)} reviews")

# ── Review Cards ──────────────────────────────────────────
for _, row in filtered.iterrows():
    rating = row.get("rating", 0)
    if rating <= 2:
        card_class = "negative"
    elif rating >= 4:
        card_class = "positive"
    else:
        card_class = "neutral"

    try:
        date_str = row["date"].strftime("%-d %B %Y · %-I:%M %p")
    except Exception:
        date_str = str(row["date"])

    review_text = html.escape(str(row.get("text", ""))).replace("\n", "<br>")
    if not review_text.strip():
        review_text = "No review text available."

    author = html.escape(str(row.get("author", "Anonymous")))
    owner_resp = row.get("owner_response", "")
    has_response = pd.notna(owner_resp) and str(owner_resp).strip() != ""

    response_html = ""
    if has_response:
        response_html = f"""
        <div style="margin-top:10px; padding:10px 14px; background:rgba(79,70,229,0.1); border-radius:6px; font-size:0.85rem;">
            <span style="font-weight:600; color:#818cf8;">Owner Response:</span>
            <span style="color:#d1d5db;">{owner_resp}</span>
        </div>
        """

    st.markdown(f"""
    <div class="review-card {card_class}">
        <div class="review-meta">
            <span class="material-symbols-rounded">calendar_today</span>
            {date_str}
            <span class="rating-badge">{int(rating)}/5</span>
        </div>
        <div class="review-text">"{review_text}"</div>
        <div class="review-author">-- {author}</div>
        {response_html}
    </div>
    """, unsafe_allow_html=True)
