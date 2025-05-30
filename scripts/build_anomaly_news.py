import json
from newsapi_fetcher import get_newsapi_news  # make sure this works
from tqdm import tqdm

# Your anomaly dates, as strings
anomaly_dates = [
    "2024-01-25",
    "2024-02-12",
    "2024-04-18"
]

# Use this if you want ticker in query
ticker = "Apple Inc"

news_by_date = {}

for date in tqdm(anomaly_dates):
    headlines = get_newsapi_news(ticker, date)
    if headlines:
        news_by_date[date] = [article["title"] for article in headlines]
    else:
        news_by_date[date] = ["No major headlines found."]

# Save to JSON
with open("data/anomaly_news.json", "w") as f:
    json.dump(news_by_date, f, indent=2)

print("✅ anomaly_news.json saved.")
