"""
ABSA Generation Script (Groq API)
==================================
Uses DeepSeek-R1-Distill-Llama-70B via Groq to extract hierarchical
aspect-based sentiment from Marugame Udon reviews.

Usage:
    python scripts/absa_generation_groq.py

Outputs:
    data/marugame_google_reviews/new_intelligence_hierarchy.csv
"""

import os
import re
import sys
import json
import time
import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv
from groq import Groq

# ============================================================
# CONFIGURATION
# ============================================================

# Which reviews to process. Change to process different files.
INPUT_CSV = "data/marugame_google_reviews/restaurant_reviews_indexed.csv"

# Only process reviews with IDs >= this value.
# Set to 0 to process ALL reviews, or 58 to only process new ones.
PROCESS_FROM_REVIEW_ID = 0

# Output file for the new insights.
# Set to the main file to overwrite, or a separate file to review first.
OUTPUT_CSV = "data/marugame_google_reviews/new_intelligence_hierarchy.csv"

# Groq model
MODEL_NAME = "llama-3.3-70b-versatile"

# Rate limiting: Groq free tier = 30 requests per minute
REQUESTS_PER_MINUTE = 30
DELAY_BETWEEN_REQUESTS = 60.0 / REQUESTS_PER_MINUTE  # 2 seconds

# Max retries on rate limit or transient errors
MAX_RETRIES = 3

# ============================================================
# PROMPT
# ============================================================

SYSTEM_PROMPT = """You are a Marugame Udon BI Specialist performing Hierarchical Aspect-Based Sentiment Analysis (ABSA).

TASK: Read the customer review and extract EVERY distinct mention into a structured JSON list. Each mention is independent — one review can produce multiple objects with different items, categories, and sentiments.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STRICT ITEM & CONTEXT MAPPING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. "Egg" Distinction (CRITICAL — always check context):
   - Soft-boiled, onsen, poached, raw, marinated, "in the soup/broth" → item: "Onsen Egg", aspect: "Yusen & Prep"
   - Fried, battered, crispy, deep-fried, "tempura egg" → item: "Tempura Egg", aspect: "Tempura"

2. "Gyoza" Aliases:
   - "Gyoza", "dumplings", "potstickers", "fried dumplings", "pan-fried dumplings" → item: "Gyoza", aspect: "Tempura"

3. Tempura Canonical Entities (use logical mapping for unlisted items):
   - Kakiage (vegetable fritter / onion rings), Chikuwa (fish cake stick), Karaage (fried chicken), Katsu (cutlet), Shrimp Tempura, Zucchini Tempura, Squid Tempura, Pumpkin Croquette, Sweet Potato Tempura, Eggplant Tempura

4. Noodle References:
   - "Udon", "noodles", "noodle texture", "koshi", "chewy" (when about noodles) → item: "Udon Noodles", aspect: "Seimen"

5. Soup/Broth References:
   - "Kake", "broth", "soup", "dashi", "tonkotsu", "curry" → aspect: "Yusen & Prep"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STRICT CATEGORY DEFINITIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- "Seimen": ONLY the noodles themselves — texture, chewiness (koshi), freshness, thickness, firmness, appearance of noodle-making.
- "Yusen & Prep": Soups, broths (kake, tonkotsu, dashi), sauces, curry, meat toppings (beef, chicken), onsen eggs, green onion, liquid temperature, seasoning.
- "Tempura": Fried items, tempura eggs, oil quality, batter crispness, gyoza, karaage, katsu, croquettes, fried sides.
- "Service": Staff behavior, wait times, line length, seating, cleanliness, ordering process, ambiance, restaurant layout, tips/tipping policy.
- "Value": Price, value for money, portion size, cost comparisons, affordability.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FIELDS TO EXTRACT (per mention)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{
  "item": "Canonical item name (e.g., 'Onsen Egg', 'Shrimp Tempura', 'Udon Noodles', 'Kake Broth'). Use a clean, standardised name.",
  "aspect_detail": "The raw phrase from the review text that triggered this extraction (e.g., 'the shrimp was crispy')",
  "aspect": "One of: Seimen, Yusen & Prep, Tempura, Service, Value",
  "opinion": "2-3 word sentiment summary (e.g., 'very crispy', 'bland broth', 'too long')",
  "sentiment_score": "float from -1.0 (strongly negative) to 1.0 (strongly positive)",
  "aspect_sentiment": "Positive, Negative, or Neutral",
  "visit_time_ai": "Infer from context clues: 'Opening' (morning, just opened, early), 'Mid-day' (lunch, afternoon, noon), 'Closing' (evening, dinner, late, night), or null if no time clues"
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Each mention gets its OWN independent sentiment. Do NOT average across mentions.
2. "the shrimp was great but the broth was bland" = TWO objects with different scores.
3. Do NOT invent information not present in the review.
4. If a review mentions only general "food" without specifics, use item: "General Food", aspect: best guess.
5. visit_time_ai should be null unless there are clear time/meal indicators in the text.

Return: {"aspects": [{...}, {...}, ...]}
If no aspects found: {"aspects": []}"""


# ============================================================
# SETUP
# ============================================================
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    print("ERROR: GROQ_API_KEY not found in .env file.")
    print("Add this line to your .env file:")
    print('  GROQ_API_KEY=your_key_here')
    sys.exit(1)

groq_client = Groq(api_key=GROQ_API_KEY)


# ============================================================
# HELPER: Strip <think>...</think> tags (safety net for R1-style models)
# ============================================================
def strip_thinking_tags(text: str) -> str:
    """Remove any <think>...</think> blocks if present (e.g. DeepSeek R1)."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


# ============================================================
# HELPER: Call Groq with retry + rate limiting
# ============================================================
def call_groq(review_text: str, review_id: str) -> list:
    """
    Send a review to Groq and return extracted aspects.
    Handles rate limits with exponential backoff.
    """
    for attempt in range(MAX_RETRIES):
        try:
            response = groq_client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Review: {review_text}"},
                ],
                temperature=0.2,
                max_completion_tokens=2048,
                response_format={"type": "json_object"},
            )

            raw_output = response.choices[0].message.content
            cleaned = strip_thinking_tags(raw_output)
            parsed = json.loads(cleaned)

            # Handle formats: {"aspects": [...]}, bare list, or single object
            if isinstance(parsed, dict):
                items = parsed.get("aspects", [])
                if not items and "aspect" in parsed:
                    items = [parsed]
            elif isinstance(parsed, list):
                items = parsed
            else:
                return []

            return items

        except json.JSONDecodeError as e:
            print(f"  JSON parse error on {review_id} (attempt {attempt + 1}): {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(DELAY_BETWEEN_REQUESTS)
            continue

        except Exception as e:
            error_str = str(e).lower()
            if "rate_limit" in error_str or "429" in error_str:
                wait = (attempt + 1) * 10  # 10s, 20s, 30s
                print(f"  Rate limited on {review_id}, waiting {wait}s...")
                time.sleep(wait)
                continue
            else:
                print(f"  Error on {review_id} (attempt {attempt + 1}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(DELAY_BETWEEN_REQUESTS)
                continue

    return []


# ============================================================
# MAIN
# ============================================================
def main():
    # Load reviews
    df = pd.read_csv(INPUT_CSV)
    print(f"Loaded {len(df)} reviews from {INPUT_CSV}")

    # Filter to only new reviews if configured
    if PROCESS_FROM_REVIEW_ID > 0:
        # Extract numeric ID from "rev_XX"
        df["_id_num"] = df["review_id"].str.extract(r"(\d+)").astype(int)
        df = df[df["_id_num"] >= PROCESS_FROM_REVIEW_ID].drop(columns=["_id_num"])
        print(f"Filtered to {len(df)} reviews (rev_{PROCESS_FROM_REVIEW_ID}+)")

    if len(df) == 0:
        print("No reviews to process. Check PROCESS_FROM_REVIEW_ID.")
        return

    processed_insights = []
    request_count = 0

    print(f"\nProcessing with {MODEL_NAME} via Groq")
    print(f"Rate limit: {REQUESTS_PER_MINUTE} RPM ({DELAY_BETWEEN_REQUESTS:.1f}s between requests)")
    print(f"{'=' * 60}\n")

    for _, row in tqdm(df.iterrows(), total=len(df), desc="Extracting insights"):
        review_text = str(row.get("text", ""))
        if pd.isna(row["text"]) or review_text.strip() == "":
            continue

        # Rate limiting
        if request_count > 0:
            time.sleep(DELAY_BETWEEN_REQUESTS)

        # Call Groq
        items = call_groq(review_text, row["review_id"])
        request_count += 1

        for item in items:
            score = item.get("sentiment_score", 0)
            # Ensure score is a float
            try:
                score = float(score)
            except (ValueError, TypeError):
                score = 0.0

            sentiment = (
                "Positive" if score > 0.1
                else "Negative" if score < -0.1
                else "Neutral"
            )
            is_killer = score <= -0.6

            processed_insights.append({
                "review_id": row["review_id"],
                "date": row["date"],
                "author": row["author"],
                "rating": row.get("rating", ""),
                "item": item.get("item", ""),
                "aspect": item.get("aspect", ""),
                "aspect_detail": item.get("aspect_detail", ""),
                "opinion": item.get("opinion", ""),
                "sentiment_score": score,
                "aspect_sentiment": item.get("aspect_sentiment", sentiment),
                "derived_sentiment": sentiment,
                "is_service_killer": is_killer,
                "visit_time_ai": item.get("visit_time_ai"),
                "original_text": review_text,
                "owner_response": row.get("owner_response", ""),
            })

    # Save results
    if processed_insights:
        final_df = pd.DataFrame(processed_insights)
        os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
        final_df.to_csv(OUTPUT_CSV, index=False)
        print(f"\nDone! {len(final_df)} insights extracted from {len(df)} reviews.")
        print(f"Saved to: {OUTPUT_CSV}")

        # Quick summary
        print(f"\nSummary:")
        print(f"  Aspects found:  {final_df['aspect'].value_counts().to_dict()}")
        print(f"  Sentiment:      {final_df['derived_sentiment'].value_counts().to_dict()}")
        print(f"  Service killers: {final_df['is_service_killer'].sum()}")
        print(f"  Unique items:   {final_df['item'].nunique()}")
    else:
        print("\nNo insights extracted. Check your reviews and API key.")


if __name__ == "__main__":
    main()
