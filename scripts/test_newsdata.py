import os
import requests
from dotenv import load_dotenv

# Load the API key from .env
load_dotenv()
API_KEY = os.getenv("NEWSDATA_API_KEY")

def get_newsdata_news(ticker, date):
    url = "https://newsdata.io/api/1/archive"
    params = {
        "apikey": API_KEY,
        "q": ticker,               # You can try "Apple Inc" too
        "language": "en",
        "from_date": date,
        "to_date": date,
        "category": "business",
        "country": "us"
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"❌ Error {response.status_code}: {response.text}")
        return []
    
    data = response.json()
    results = data.get("results", [])
    
    top_articles = []
    for article in results[:3]:
        top_articles.append({
            "title": article.get("title"),
            "source": article.get("source_id"),
            "url": article.get("link"),
            "pubDate": article.get("pubDate")
        })
    
    return top_articles

# 🧪 Test with one token and one anomaly date
if __name__ == "__main__":
    ticker = "AAPL"
    date = "2024-01-25"  # replace with any anomaly date you have
    news = get_newsdata_news(ticker, date)
    
    if not news:
        print("⚠️ No news found.")
    else:
        print(f"\n🗞️ News for {ticker} on {date}:")
        for i, n in enumerate(news, 1):
            print(f"{i}. {n['title']} ({n['source']})")
            print(f"   → {n['url']}\n")
