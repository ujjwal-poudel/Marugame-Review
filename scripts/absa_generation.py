import pandas as pd
import ollama
import json
from tqdm import tqdm

df = pd.read_csv('data/marugame_google_reviews/restaurant_reviews_indexed.csv')
processed_insights = []

MODEL_NAME = 'deepseek-r1:8b'

# Updated prompt — explicitly instruct multi-aspect extraction + wrap in a root key
# (since format='json' forces a single JSON object, we use a wrapper key)
SYSTEM_PROMPT = """
You are a Marugame Udon Restaurant BI Specialist performing Aspect-Based Sentiment Analysis (ABSA).

TASK: Read the review and extract EVERY distinct aspect mention. Each mention is independent — the same review can have:
- Multiple aspect_details (e.g., "shrimp", "kake broth", "wait time")
- Different categories for each (e.g., shrimp → Tempura, kake broth → Seimen)
- Different sentiments for each (e.g., shrimp → Positive, kake broth → Negative)

Top-Level Categories (aspect): [Seimen, Yusen & Prep, Tempura, Service, Value]

For EACH distinct mention, create a separate object with its own independent sentiment:
{
  "aspect_detail": "specific item mentioned (e.g., 'shrimp', 'kake broth', 'wait time')",
  "aspect": "one of the 5 categories — assign based on what the detail relates to",
  "opinion": "2-3 word summary from the text for THIS specific detail",
  "sentiment_score": float from -1.0 to 1.0 for THIS specific detail,
  "aspect_sentiment": "Positive", "Negative", or "Neutral" for THIS specific detail
}

IMPORTANT:
- Do NOT average or share sentiment across details. Each detail gets its own score.
- If the review says "the shrimp was great but the broth was bland", that is TWO separate objects with different sentiments.
- Map each aspect_detail to the most fitting category independently.

Return: {"aspects": [{...}, {...}, ...]}
If no aspects found: {"aspects": []}
Do not add information beyond what is in the review text.
"""

print(f"Generating Hierarchical Insights for {len(df)} reviews...")

for _, row in tqdm(df.iterrows(), total=len(df)):
    if pd.isna(row['text']) or str(row['text']).strip() == "":
        continue

    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': f"Review: {row['text']}"}
            ],
            format='json'
        )

        raw_output = response['message']['content']
        parsed = json.loads(raw_output)

        # Handle both formats: wrapped {"aspects": [...]} or bare list [...]
        if isinstance(parsed, dict):
            extracted_items = parsed.get('aspects', [])
            # fallback: if no 'aspects' key, treat the dict itself as a single item
            if not extracted_items and 'aspect' in parsed:
                extracted_items = [parsed]
        elif isinstance(parsed, list):
            extracted_items = parsed
        else:
            continue

        for item in extracted_items:
            score = item.get('sentiment_score', 0)
            sentiment = "Positive" if score > 0.1 else "Negative" if score < -0.1 else "Neutral"
            is_killer = score <= -0.6

            processed_insights.append({
                'review_id': row['review_id'],
                'date': row['date'],
                'author': row['author'],
                'aspect': item.get('aspect'),
                'aspect_detail': item.get('aspect_detail'),
                'opinion': item.get('opinion'),
                'sentiment_score': score,
                'aspect_sentiment': item.get('aspect_sentiment', sentiment),
                'derived_sentiment': sentiment,
                'is_service_killer': is_killer,
                'original_text': row['text']
            })

    except (json.JSONDecodeError, TypeError) as e:
        print(f"Parse error on {row['review_id']}: {e}")
        continue
    except Exception as e:
        print(f"Error on {row['review_id']}: {e}")
        continue

final_df = pd.DataFrame(processed_insights)
final_df.to_csv('data/marugame_google_reviews/final_intelligence_hierarchy.csv', index=False)
print(f"\nDone! {len(final_df)} insights extracted from {len(df)} reviews.")