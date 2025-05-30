from newsapi_fetcher import get_newsapi_news

# Test date - replace with one of your anomaly dates
date = "2024-01-25"
query = "Apple Inc"

news = get_newsapi_news(query, date)

if not news:
    print("⚠️ No news found.")
else:
    print(f"\n🗞️ News for {query} on {date}:")
    for i, article in enumerate(news, 1):
        print(f"{i}. {article['title']} ({article['source']})")
        print(f"   → {article['url']}\n")
