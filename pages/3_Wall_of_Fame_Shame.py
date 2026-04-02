import sys
import os
import html
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.styles import inject_global_styles
from src.data_loader import load_intel

# ── Page Config ───────────────────────────────────────────
st.set_page_config(page_title="Wall of Fame & Shame | Marugame", layout="wide")
inject_global_styles()

# ── Load Data ─────────────────────────────────────────────
df = load_intel()

# ── Page Header ───────────────────────────────────────────
st.markdown("""
<div class="page-title">
    <span class="material-symbols-rounded" style="font-size:28px; color:#818cf8;">trophy</span>
    Wall of Fame &amp; Shame
</div>
<div class="page-subtitle">Items ranked by unique review mentions — minimum 3 mentions to qualify</div>
""", unsafe_allow_html=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ── Aggregate: unique reviewers per item per sentiment ────
MIN_MENTIONS = 3

# Positive mentions: unique reviewers who said something positive about this item
pos_mentions = (
    df[df["derived_sentiment"] == "Positive"]
    .groupby("item")["review_id"]
    .nunique()
    .reset_index(name="unique_mentions")
    .query(f"unique_mentions >= {MIN_MENTIONS}")
    .nlargest(10, "unique_mentions")
    .sort_values("unique_mentions", ascending=True)
)

# Negative mentions: unique reviewers who said something negative about this item
neg_mentions = (
    df[df["derived_sentiment"] == "Negative"]
    .groupby("item")["review_id"]
    .nunique()
    .reset_index(name="unique_mentions")
    .query(f"unique_mentions >= {MIN_MENTIONS}")
    .nlargest(10, "unique_mentions")
    .sort_values("unique_mentions", ascending=True)
)

# ── Charts ────────────────────────────────────────────────
col_hero, col_killer = st.columns(2)

# ── THE HEROES ────────────────────────────────────────────
with col_hero:
    st.markdown("""
    <div class="section-header">
        <span class="material-symbols-rounded section-icon" style="color:#16a34a;">military_tech</span>
        The Heroes
    </div>
    """, unsafe_allow_html=True)

    if len(pos_mentions) > 0:
        fig_hero = go.Figure()
        fig_hero.add_trace(go.Bar(
            y=pos_mentions["item"],
            x=pos_mentions["unique_mentions"],
            orientation="h",
            marker=dict(color="#16a34a", cornerradius=4),
            text=pos_mentions["unique_mentions"],
            textposition="outside",
            textfont=dict(size=12, color="#16a34a", family="Inter"),
            hovertemplate="<b>%{y}</b><br>Unique Positive Mentions: %{x}<extra></extra>",
        ))

        fig_hero.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color="#e5e7eb"),
            xaxis=dict(
                title=dict(text="Unique Positive Mentions", font=dict(color="#9ca3af", size=12)),
                gridcolor="rgba(255,255,255,0.05)",
                tickfont=dict(color="#9ca3af"),
            ),
            yaxis=dict(
                tickfont=dict(size=13, color="#e5e7eb"),
                automargin=True,
            ),
            height=420,
            margin=dict(l=10, r=50, t=10, b=40),
            bargap=0.25,
        )

        st.plotly_chart(fig_hero, width="stretch")
    else:
        st.info("No items with 3+ unique positive mentions.")


# ── THE SERVICE KILLERS ───────────────────────────────────
with col_killer:
    st.markdown("""
    <div class="section-header">
        <span class="material-symbols-rounded section-icon" style="color:#dc2626;">dangerous</span>
        The Service Killers
    </div>
    """, unsafe_allow_html=True)

    if len(neg_mentions) > 0:
        fig_killer = go.Figure()
        fig_killer.add_trace(go.Bar(
            y=neg_mentions["item"],
            x=neg_mentions["unique_mentions"],
            orientation="h",
            marker=dict(color="#dc2626", cornerradius=4),
            text=neg_mentions["unique_mentions"],
            textposition="outside",
            textfont=dict(size=12, color="#dc2626", family="Inter"),
            hovertemplate="<b>%{y}</b><br>Unique Negative Mentions: %{x}<extra></extra>",
        ))

        fig_killer.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color="#e5e7eb"),
            xaxis=dict(
                title=dict(text="Unique Negative Mentions", font=dict(color="#9ca3af", size=12)),
                gridcolor="rgba(255,255,255,0.05)",
                tickfont=dict(color="#9ca3af"),
            ),
            yaxis=dict(
                tickfont=dict(size=13, color="#e5e7eb"),
                automargin=True,
            ),
            height=420,
            margin=dict(l=10, r=50, t=10, b=40),
            bargap=0.25,
        )

        st.plotly_chart(fig_killer, width="stretch")
    else:
        st.info("No items with 3+ unique negative mentions.")


st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ── Intelligence Drill-Down ───────────────────────────────
st.markdown("""
<div class="section-header">
    <span class="material-symbols-rounded section-icon">manage_search</span>
    Intelligence Drill-Down (Proof)
</div>
""", unsafe_allow_html=True)

# Build combined item list (all items that appear in either chart)
all_charted = set()
if len(pos_mentions) > 0:
    all_charted.update(pos_mentions["item"].tolist())
if len(neg_mentions) > 0:
    all_charted.update(neg_mentions["item"].tolist())

# Sort by total negative mentions first (worst items at top of dropdown)
all_item_neg = (
    df[df["derived_sentiment"] == "Negative"]
    .groupby("item")["review_id"]
    .nunique()
    .reset_index(name="neg_count")
)
qualified_items = (
    all_item_neg[all_item_neg["item"].isin(all_charted)]
    .sort_values("neg_count", ascending=False)["item"]
    .tolist()
)
# Add any hero-only items that have no negatives
for item in all_charted:
    if item not in qualified_items:
        qualified_items.append(item)

# Controls
ctrl1, ctrl2 = st.columns([3, 1])

with ctrl1:
    selected_item = st.selectbox("Select Item for Detailed Evidence:", qualified_items)

with ctrl2:
    sort_by_date = st.checkbox("Latest Date First", value=True)

if selected_item:
    evidence = df[df["item"] == selected_item].copy()

    # Sort
    if sort_by_date:
        evidence = evidence.sort_values("date", ascending=False)
    else:
        evidence = evidence.sort_values("sentiment_score", ascending=True)

    # Stats row
    avg_score = evidence["sentiment_score"].mean()
    neg = len(evidence[evidence["derived_sentiment"] == "Negative"])
    pos = len(evidence[evidence["derived_sentiment"] == "Positive"])
    neu = len(evidence[evidence["derived_sentiment"] == "Neutral"])

    avg_label = "Positive" if avg_score > 0.1 else "Negative" if avg_score < -0.1 else "Neutral"
    score_color = "#dc2626" if avg_label == "Negative" else "#16a34a" if avg_label == "Positive" else "#9ca3af"

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Total Mentions", len(evidence))
    s2.metric("Unique Reviews", evidence["review_id"].nunique())
    s3.metric("Negative", neg)
    s4.metric("Positive", pos)

    st.markdown(f"""
    <div style="font-size:0.9rem; color:#d1d5db; margin:8px 0 16px;">
        Average Sentiment:
        <span style="font-weight:700; color:{score_color}; font-size:1rem;">{avg_label} ({avg_score:+.2f})</span>
    </div>
    """, unsafe_allow_html=True)

    # Build display table
    display_df = evidence[["date", "visit_time_ai", "opinion", "aspect_detail", "derived_sentiment", "rating", "author"]].copy()
    display_df = display_df.rename(columns={
        "date": "Date",
        "visit_time_ai": "Visit Time",
        "opinion": "Opinion",
        "aspect_detail": "Aspect Detail",
        "derived_sentiment": "Sentiment",
        "rating": "Rating",
        "author": "Author",
    })

    # Format date
    if "Date" in display_df.columns:
        display_df["Date"] = pd.to_datetime(display_df["Date"], errors="coerce").dt.strftime("%-d %B %Y")

    st.dataframe(
        display_df,
        width="stretch",
        hide_index=True,
        height=min(400, 38 + len(display_df) * 35),
    )
