import os
import requests
from dotenv import load_dotenv

load_dotenv()

def get_newsdata_news(ticker, date):
    base_url = "https://newsdata.io/api/1/news"
    params = {
        "apikey": os.getenv("NEWSDATA_API_KEY"),
        "q": ticker,
        "language": "en",
        "from_date": date,
        "to_date": date,
        "category": "business",
        "country": "us"
    }

    response = requests.get(base_url, params=params)
    
    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}")
        return []
    
    data = response.json()
    articles = data.get("results", [])
    
    return [
        {
            "title": a.get("title"),
            "url": a.get("link"),
            "source": a.get("source_id"),
            "pubDate": a.get("pubDate")
        }
        for a in articles[:3]  # top 3 headlines
    ]
