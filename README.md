# Marugame Review Intelligence

A multi-page Streamlit dashboard for analyzing Google Maps reviews of Marugame Udon using Aspect-Based Sentiment Analysis (ABSA).

## Project Structure

```
Review_Analysis/
├── .streamlit/
│   └── config.toml              # Streamlit theme config
├── app.py                       # Home page (entry point)
├── pages/
│   ├── 1_Station_Health.py      # Station drill-down dashboard
│   └── 2_Review_Explorer.py     # Browse & search all reviews
├── src/
│   ├── __init__.py
│   ├── data_loader.py           # Shared data loading functions
│   └── styles.py                # Shared CSS styles & icons
├── scripts/
│   ├── review_scraper.py        # Outscraper review collection
│   └── absa_generation.py       # ABSA with DeepSeek via Ollama
├── data/
│   └── marugame_google_reviews/  # CSV data files
├── .env                         # API keys (not committed)
├── requirements.txt
└── README.md
```

## Setup

```bash
# 1. Create virtual environment
python -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your API keys to .env
echo 'OUTSCRAPER_API_KEY=your_key_here' > .env
```

## Data Pipeline

The project has a 3-step pipeline:

### Step 1: Scrape Reviews
```bash
python scripts/review_scraper.py
```
Collects Google Maps reviews via Outscraper API. Configure the restaurant link and review limits at the top of the script.

### Step 2: Generate ABSA Insights
```bash
python scripts/absa_generation.py
```
Uses DeepSeek R1 (via Ollama) to extract aspect-level sentiment from each review, categorizing mentions into 5 stations: Seimen, Yusen & Prep, Tempura, Service, Value.

### Step 3: Launch Dashboard
```bash
streamlit run app.py
```
Opens the multi-page dashboard with:
- **Home**: KPI summary + recent critical issues
- **Station Health**: Per-station sentiment drill-down
- **Review Explorer**: Search and filter all raw reviews

## Pages

| Page | Description |
|------|-------------|
| Home | KPIs, station overview cards, recent negative mentions |
| Station Health | Select a station, see all mentions sorted negative-first |
| Review Explorer | Search, filter by rating, sort all reviews |
