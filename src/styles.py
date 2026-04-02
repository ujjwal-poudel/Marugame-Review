"""
Shared CSS styles and icon imports for all Streamlit pages.
Centralised here so every page has a consistent look and feel.
"""

import streamlit as st


def inject_global_styles():
    """Inject the shared CSS + Material Icons into the current Streamlit page."""
    st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,1,0" rel="stylesheet">
    <style>
        /* -------------------------------------------------- */
        /*  GLOBAL                                            */
        /* -------------------------------------------------- */
        .stApp {
            font-family: 'Inter', sans-serif;
        }

        /* -------------------------------------------------- */
        /*  PAGE HEADER                                       */
        /* -------------------------------------------------- */
        .page-title {
            font-size: 1.8rem;
            font-weight: 700;
            color: #ffffff;
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 4px;
        }
        .page-subtitle {
            font-size: 0.95rem;
            color: #ffffffcc;
            margin-bottom: 24px;
        }

        /* -------------------------------------------------- */
        /*  SECTION HEADERS                                   */
        /* -------------------------------------------------- */
        .section-header {
            font-size: 1.15rem;
            font-weight: 600;
            color: #ffffff;
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: 12px;
            margin-bottom: 16px;
        }
        .section-icon {
            font-size: 22px;
            color: #ffffff;
        }

        /* -------------------------------------------------- */
        /*  STATION CARDS                                     */
        /* -------------------------------------------------- */
        .station-card {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            transition: box-shadow 0.2s ease;
        }
        .station-card:hover {
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }
        .station-name {
            font-size: 0.85rem;
            font-weight: 600;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }
        .station-total {
            font-size: 1.6rem;
            font-weight: 700;
            color: #1a1a2e;
            margin-bottom: 12px;
        }
        .station-breakdown {
            display: flex;
            justify-content: center;
            gap: 16px;
            font-size: 0.85rem;
            font-weight: 500;
        }
        .neg-count {
            color: #dc2626;
            display: flex;
            align-items: center;
            gap: 4px;
        }
        .pos-count {
            color: #16a34a;
            display: flex;
            align-items: center;
            gap: 4px;
        }
        .bar-track {
            height: 6px;
            background: #16a34a;
            border-radius: 3px;
            margin-top: 12px;
            overflow: hidden;
        }
        .bar-fill-neg {
            height: 100%;
            background: #dc2626;
            border-radius: 3px 0 0 3px;
        }

        /* -------------------------------------------------- */
        /*  REVIEW CARDS                                      */
        /* -------------------------------------------------- */
        .review-card {
            border-left: 4px solid;
            border-radius: 8px;
            padding: 18px 20px;
            margin-bottom: 12px;
            background: #ffffff;
            border-color: #e5e7eb;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }
        .review-card.negative {
            border-left-color: #dc2626;
            background: #fef2f2;
        }
        .review-card.positive {
            border-left-color: #16a34a;
            background: #f0fdf4;
        }
        .review-card.neutral {
            border-left-color: #9ca3af;
            background: #f9fafb;
        }
        .review-meta {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 0.85rem;
            font-weight: 500;
            color: #374151;
            margin-bottom: 6px;
        }
        .review-meta .material-symbols-rounded {
            font-size: 16px;
            color: #6b7280;
        }
        .review-title {
            font-size: 1.05rem;
            font-weight: 600;
            color: #1a1a2e;
            margin-bottom: 8px;
        }
        .review-text {
            font-size: 0.9rem;
            color: #4b5563;
            line-height: 1.6;
            font-style: italic;
            margin-bottom: 8px;
        }
        .review-author {
            font-size: 0.8rem;
            font-weight: 500;
            color: #6b7280;
        }
        .rating-badge {
            display: inline-block;
            background: #f3f4f6;
            color: #1a1a2e;
            font-size: 0.78rem;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 6px;
            margin-left: 4px;
        }

        /* -------------------------------------------------- */
        /*  KPI / METRIC CARDS                                */
        /* -------------------------------------------------- */
        .kpi-card {
            background: #1e1f36;
            border: 1px solid #2d2e4a;
            border-radius: 12px;
            padding: 20px 24px;
            text-align: center;
        }
        .kpi-label {
            font-size: 0.78rem;
            font-weight: 600;
            color: #9ca3af;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
        }
        .kpi-value {
            font-size: 1.8rem;
            font-weight: 700;
            color: #ffffff;
        }
        .kpi-sub {
            font-size: 0.8rem;
            color: #6b7280;
            margin-top: 4px;
        }

        /* -------------------------------------------------- */
        /*  UTILITY                                           */
        /* -------------------------------------------------- */
        .divider {
            border: none;
            border-top: 1px solid rgba(255,255,255,0.1);
            margin: 28px 0;
        }
        .sentiment-tag {
            display: inline-block;
            font-size: 0.72rem;
            font-weight: 600;
            padding: 2px 10px;
            border-radius: 20px;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }
        .sentiment-tag.pos {
            background: #dcfce7;
            color: #166534;
        }
        .sentiment-tag.neg {
            background: #fee2e2;
            color: #991b1b;
        }
        .sentiment-tag.neu {
            background: #f3f4f6;
            color: #4b5563;
        }
    </style>
    """, unsafe_allow_html=True)
