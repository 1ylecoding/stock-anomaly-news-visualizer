import requests

def get_newsapi_news(query, date, api_key):
    url = "https://api.thenewsapi.com/v1/news/all"
    params = {
        "api_token": api_key,
        "search": query,
        "language": "en",
        "published_on": date,
        "categories": "business,finance",
        "limit": 5
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"❌ Error {response.status_code}: {response.text}")
        return []

    articles = response.json().get("data", [])
    return [
        {
            "title": a["title"],
            "url": a["url"],
            "source": a["source"],
            "published_at": a["published_at"]
        }
        for a in articles[:3]
    ]
