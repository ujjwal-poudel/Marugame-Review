import sys
import os
import html
import streamlit as st
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.styles import inject_global_styles
from src.data_loader import load_intel, STATIONS

# ── Page Config ───────────────────────────────────────────
st.set_page_config(page_title="Station Health | Marugame", layout="wide")
inject_global_styles()

# ── Load Data ─────────────────────────────────────────────
df = load_intel()

# ── Page Header ───────────────────────────────────────────
st.markdown("""
<div class="page-title">
    <span class="material-symbols-rounded" style="font-size:28px; color:#818cf8;">monitoring</span>
    Station Health
</div>
<div class="page-subtitle">Deep-dive into each station's review mentions and sentiment</div>
""", unsafe_allow_html=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ── Station Summary Cards ─────────────────────────────────
st.markdown("""
<div class="section-header">
    <span class="material-symbols-rounded section-icon">analytics</span>
    Station Overview
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

# ── Station Intelligence Drill-Down ───────────────────────
st.markdown("""
<div class="section-header">
    <span class="material-symbols-rounded section-icon">search</span>
    Station Intelligence Drill-Down
</div>
""", unsafe_allow_html=True)

# Controls row
ctrl_col1, ctrl_col2 = st.columns([3, 1])

# Default to the station with the most negative mentions
neg_counts = df[df["derived_sentiment"] == "Negative"]["aspect"].value_counts()
worst_station = neg_counts.index[0] if len(neg_counts) > 0 else STATIONS[0]
default_idx = STATIONS.index(worst_station) if worst_station in STATIONS else 0

with ctrl_col1:
    selected_station = st.selectbox("Select Station to Audit:", STATIONS, index=default_idx)

with ctrl_col2:
    sort_by_date = st.checkbox("Latest Date First", value=True)

# ── Sorting logic ──────────────────────────────────────────
# Groups always: Negative (red) → Neutral (gray) → Positive (green)
proof_df = df[df["aspect"] == selected_station].copy()
proof_df["_score"] = pd.to_numeric(proof_df["sentiment_score"], errors="coerce").fillna(0)
proof_df["_group"] = proof_df["_score"].apply(
    lambda s: 0 if s < -0.1 else (2 if s > 0.1 else 1)
)

if sort_by_date:
    # Within each color group: latest date on top
    proof_df = proof_df.sort_values(by=["_group", "date"], ascending=[True, False])
else:
    # Within each color group: most negative score first (default)
    proof_df = proof_df.sort_values(by=["_group", "_score"], ascending=[True, True])

st.caption(f"{len(proof_df)} mentions for {selected_station}")

for _, row in proof_df.iterrows():
    try:
        # Determine card class
        score = float(row.get("sentiment_score", 0) or 0)
        if score < -0.1:
            card_class = "negative"
            border_color = "#dc2626"
            bg_color = "#fef2f2"
        elif score > 0.1:
            card_class = "positive"
            border_color = "#16a34a"
            bg_color = "#f0fdf4"
        else:
            card_class = "neutral"
            border_color = "#9ca3af"
            bg_color = "#f9fafb"

        # Title = item + opinion
        item_name = html.escape(str(row.get("item", "") or "").strip())
        opinion   = html.escape(str(row.get("opinion", "") or "").strip())
        card_title = f"{item_name}: {opinion}" if item_name and opinion else (item_name or opinion or "Unknown")

        # Date
        try:
            date_str = row["date"].strftime("%-d %B %Y · %-I:%M %p")
        except Exception:
            date_str = str(row.get("date", ""))

        # Rating badge
        try:
            rating_val = row.get("rating", "")
            rating_badge = f'<span style="display:inline-block;background:#f3f4f6;color:#1a1a2e;font-size:0.75rem;font-weight:600;padding:2px 8px;border-radius:6px;margin-left:6px;">{int(float(rating_val))}/5</span>' if pd.notna(rating_val) and str(rating_val) not in ("", "nan") else ""
        except Exception:
            rating_badge = ""

        # Visit time badge
        visit_time = str(row.get("visit_time_ai", "") or "").strip()
        visit_badge = f'<span style="display:inline-block;background:#f3f4f6;color:#1a1a2e;font-size:0.75rem;font-weight:600;padding:2px 8px;border-radius:6px;margin-left:6px;">{html.escape(visit_time)}</span>' if visit_time else ""

        # Review text
        review_text = html.escape(str(row.get("original_text", "") or "")).replace("\n", "<br>").strip()
        if not review_text:
            review_text = "No review text available."

        # Author
        author = html.escape(str(row.get("author", "Anonymous") or "Anonymous"))

        # Owner response
        owner_resp = html.escape(str(row.get("owner_response", "") or "").strip()).replace("\n", "<br>")
        response_block = f"""
            <div style="margin-top:10px;padding:10px 14px;background:rgba(79,70,229,0.08);border-radius:6px;font-size:0.85rem;">
                <span style="font-weight:600;color:#4f46e5;">Owner Response: </span>
                <span style="color:#374151;">{owner_resp}</span>
            </div>""" if owner_resp else ""

        card_html = f"""
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
        <div style="
            font-family: 'Inter', sans-serif;
            border-left: 4px solid {border_color};
            border-radius: 8px;
            padding: 16px 20px;
            margin-bottom: 12px;
            background: {bg_color};
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        ">
            <div style="display:flex;align-items:center;font-size:0.78rem;color:#9ca3af;margin-bottom:6px;">
                <span style="margin-right:4px;">&#128197;</span>
                {date_str}
                {rating_badge}
                {visit_badge}
            </div>
            <div style="font-size:1rem;font-weight:600;color:#1a1a2e;margin-bottom:8px;">{card_title}</div>
            <div style="font-size:0.88rem;color:#4b5563;line-height:1.65;font-style:italic;margin-bottom:8px;">"{review_text}"</div>
            <div style="font-size:0.78rem;font-weight:500;color:#6b7280;">&#8212; {author}</div>
            {response_block}
        </div>
        """
        st.html(card_html)

    except Exception as e:
        st.warning(f"Could not render card for {row.get('review_id', '?')}: {e}")
