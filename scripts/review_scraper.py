import os
import pandas as pd
from dotenv import load_dotenv
from outscraper import OutscraperClient

# ============================================================
# CONFIGURATION - Edit these variables before running
# ============================================================

# Google Maps link or Place ID for the restaurant you want to scrape.
# Option 1: Use the full Google Maps URL (copy from your browser)
# Option 2: Use a Google Place ID (more reliable, doesn't change)
# Option 3: Use the restaurant name + city (least reliable)
RESTAURANT_LINK = "https://www.google.com/maps/place/Marugame+Udon/@43.6627867,-79.3840762,749m/data=!3m2!1e3!4b1!4m6!3m5!1s0x882b3570bf2f8427:0xf9de31299167811d!8m2!3d43.6627867!4d-79.3840762!16s%2Fg%2F11yyh1gcfm?entry=ttu&g_ep=EgoyMDI2MDMyNC4wIKXMDSoASAFQAw%3D%3D"

# Number of reviews to scrape.
# Free tier: 500 total reviews, max 250 per place.
MAX_REVIEWS_PER_PLACE = 30

# Sort order: "most_relevant", "newest", "highest_rating", "lowest_rating"
SORT_ORDER = "newest"

# Minimum reviews a place must have to bother scraping (skip near-empty places).
MIN_REVIEWS_TO_SCRAPE = 1

# Language for the reviews (ISO 639-1 code)
REVIEW_LANGUAGE = "en"

# Output directory and filename
# This file will have the SAME headers as restaurant_reviews_indexed.csv:
#   review_id, author, rating, text, date, owner_response
OUTPUT_DIR = "data/marugame_google_reviews"
OUTPUT_FILENAME = "new_reviews.csv"

# Starting review_id number.
# Check the last review_id in restaurant_reviews_indexed.csv and set this
# to the next number so IDs don't collide when you merge later.
# e.g. if last ID is rev_57, set this to 58.
REVIEW_ID_START = 58

# ============================================================
# SETUP - Load API key and initialize client
# ============================================================
load_dotenv()
API_KEY = os.getenv("OUTSCRAPER_API_KEY")

if not API_KEY:
    raise ValueError(
        "OUTSCRAPER_API_KEY not found! Make sure it's set in your .env file."
    )

client = OutscraperClient(api_key=API_KEY)


# ============================================================
# MAIN SCRAPING FUNCTION
# ============================================================
def get_restaurant_reviews(
    restaurant_link: str,
    max_reviews: int = MAX_REVIEWS_PER_PLACE,
    min_reviews: int = MIN_REVIEWS_TO_SCRAPE,
    sort: str = SORT_ORDER,
    language: str = REVIEW_LANGUAGE,
    id_start: int = REVIEW_ID_START,
) -> pd.DataFrame | None:
    """
    Fetches Google Maps reviews for a specific restaurant.

    Args:
        restaurant_link: Google Maps URL, Place ID, or search query.
        max_reviews:     Max reviews to pull (capped at 250 for free tier).
        min_reviews:     Skip if the place has fewer reviews than this.
        sort:            Sort order — "newest", "most_relevant", etc.
        language:        Language code for reviews (e.g. 'en').
        id_start:        Starting number for review_id (e.g. 58 → rev_58, rev_59, ...).

    Returns:
        DataFrame of reviews, or None if no reviews found.
    """
    # Safety check: never exceed 250 per place on free tier
    if max_reviews > 250:
        print(f"max_reviews was {max_reviews}, capping at 250 (free tier limit).")
        max_reviews = 250

    print(f"Fetching reviews for: {restaurant_link}")
    print(f"   Max reviews: {max_reviews}")
    print(f"   Sort order:  {sort}")
    print(f"   Language:    {language}")
    print()

    # --- Call Outscraper API ---
    results = client.google_maps_reviews(
        [restaurant_link],
        reviews_limit=max_reviews,
        sort=sort,
        language=language,
    )

    # --- Validate response ---
    if not results or not results[0]:
        print("No results returned. Check your restaurant link or Place ID.")
        return None

    place_info = results[0]
    place_name = place_info.get("name", "Unknown Restaurant")
    total_reviews_on_google = place_info.get("reviews", 0)

    print(f"Restaurant found: {place_name}")
    print(f"Total reviews on Google: {total_reviews_on_google}")

    # --- Check minimum review threshold ---
    if total_reviews_on_google < min_reviews:
        print(
            f"Skipping -- only {total_reviews_on_google} reviews found, "
            f"minimum is {min_reviews}. Not worth scraping."
        )
        return None

    # --- Extract review data ---
    reviews_data = place_info.get("reviews_data", [])

    if not reviews_data:
        print("No review data returned despite reviews existing. Try again later.")
        return None

    print(f"   Reviews scraped: {len(reviews_data)}")

    # --- Build clean DataFrame ---
    # Headers match restaurant_reviews_indexed.csv:
    #   review_id, author, rating, text, date, owner_response
    processed_reviews = []
    current_id = id_start

    for r in reviews_data:
        review_text = r.get("review_text")
        # Skip reviews with no text (rating-only reviews aren't useful for analysis)
        if not review_text or review_text.strip() == "":
            continue

        processed_reviews.append(
            {
                "review_id": f"rev_{current_id}",
                "author": r.get("author_title"),
                "rating": r.get("review_rating"),
                "text": review_text,
                "date": r.get("review_datetime_utc"),
                "owner_response": r.get("owner_answer"),
            }
        )
        current_id += 1

    if not processed_reviews:
        print("All scraped reviews were empty (rating-only). Nothing to save.")
        return None

    df = pd.DataFrame(processed_reviews)

    # --- Save to CSV ---
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME)
    df.to_csv(output_path, index=False)

    print()
    print(f"Done! {len(df)} reviews with text saved to: {output_path}")
    print(f"   ({len(reviews_data) - len(df)} empty/rating-only reviews excluded)")
    print(f"   Review IDs: rev_{id_start} through rev_{current_id - 1}")
    print()
    print("Quick stats:")
    print(f"   Average rating: {df['rating'].mean():.2f}")
    print(f"   Rating distribution:\n{df['rating'].value_counts().sort_index().to_string()}")

    return df


# ============================================================
# RUN
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  RESTAURANT REVIEW SCRAPER")
    print(f"  Free tier budget: 500 total reviews")
    print(f"  Fetching:         {MAX_REVIEWS_PER_PLACE} reviews ({SORT_ORDER})")
    print(f"  Review IDs start: rev_{REVIEW_ID_START}")
    print("=" * 60)
    print()

    df = get_restaurant_reviews(
        restaurant_link=RESTAURANT_LINK,
        max_reviews=MAX_REVIEWS_PER_PLACE,
        min_reviews=MIN_REVIEWS_TO_SCRAPE,
        sort=SORT_ORDER,
        language=REVIEW_LANGUAGE,
        id_start=REVIEW_ID_START,
    )

    if df is not None:
        print("\nPreview (first 5 rows):")
        print(df.head().to_string())