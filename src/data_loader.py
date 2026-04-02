"""
Shared data loading functions used across all Streamlit pages.
Uses st.cache_data so data is loaded once and shared.

The intelligence CSV is self-contained — it has all columns needed:
  review_id, date, author, rating, item, aspect, aspect_detail,
  opinion, sentiment_score, aspect_sentiment, derived_sentiment,
  is_service_killer, visit_time_ai, original_text, owner_response

To switch datasets, just change INTEL_CSV below.
"""

import os
import streamlit as st
import pandas as pd

# ── Paths ──────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
MARUGAME_DIR = os.path.join(DATA_DIR, "marugame_google_reviews")

# Intelligence CSV — change this to swap datasets
INTEL_CSV = os.path.join(MARUGAME_DIR, "new_intelligence_hierarchy.csv")

# Raw reviews (for Review Explorer page)
RAW_CSV = os.path.join(MARUGAME_DIR, "restaurant_reviews_indexed.csv")

# ── Station definitions ───────────────────────────────────
STATIONS = ["Seimen", "Yusen & Prep", "Tempura", "Service", "Value"]


@st.cache_data
def load_intel() -> pd.DataFrame:
    """
    Load the AI-generated intelligence CSV.
    This file is self-contained — no merge needed.
    """
    df = pd.read_csv(INTEL_CSV)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # Fill NaN in text columns to avoid display errors
    for col in ["original_text", "owner_response", "item", "aspect_detail", "opinion", "visit_time_ai"]:
        if col in df.columns:
            df[col] = df[col].fillna("")

    return df


@st.cache_data
def load_raw_reviews() -> pd.DataFrame:
    """Load the original scraped reviews."""
    df = pd.read_csv(RAW_CSV)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for col in ["text", "owner_response"]:
        if col in df.columns:
            df[col] = df[col].fillna("")
    return df
