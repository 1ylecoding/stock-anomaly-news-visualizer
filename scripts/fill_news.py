import json
from newsapi_fetcher import get_newsapi_news  # Make sure this works
from tqdm import tqdm

# Load existing file
with open("data/AAPL_news.json", "r") as f:
    news_by_date = json.load(f)

ticker = "Apple Inc"

# Only fetch for dates that are still empty
for date, articles in tqdm(news_by_date.items()):
    if not articles:
        results = get_newsapi_news(ticker, date)
        if results:
            news_by_date[date] = [article["title"] for article in results]
        else:
            news_by_date[date] = ["No major headlines found."]

# Save updated file
with open("data/AAPL_news.json", "w") as f:
    json.dump(news_by_date, f, indent=2)

print("✅ News headlines added to AAPL_news.json")
