import os
import json
import pandas as pd
import yfinance as yf

def get_company_name(ticker):
    try:
        return yf.Ticker(ticker).info.get("longName", ticker)
    except:
        return ticker  # fallback

ticker = input("Enter the stock ticker (e.g., AAPL, MSFT, GOOGL): ").strip().upper()


from data_fetcher import fetch_and_save_stock_data
from analyzer import detect_anomalies_mad
from analyzer import detect_persistent_run_anomalies  # put this at the top
from newsapi_fetcher import get_newsapi_news
from visualize import generate_visualization

def fetch_news_for_anomalies(ticker, dates, anomaly_type="default"):
    company_name = get_company_name(ticker)
    news = {}
    for date in dates:
        results = get_newsapi_news(query=company_name, date=date)
        if anomaly_type == "z":  # yellow dot
            link_color = "black"
        else:  # trend or persistent run
            link_color = "white"

        news[date] = [
            f"<a href='{a['url']}' target='_blank' style='color:{link_color}; text-decoration:none;'>{a['title']} ({a['source']})</a>"
            for a in results
        ] if results else ["No major headlines found."]


    return news



def main():
    #ticker = "AAPL"
    print(f"🚀 Starting full pipeline for {ticker}")

    # === Step 1: Fetch data ===
    print("📥 Fetching stock data...")
    fetch_and_save_stock_data(ticker)

    # === Step 2: Detect anomalies ===
    print("🔍 Detecting anomalies...")
    anomalies_df = detect_anomalies_mad(ticker)
    z_anomalies = pd.to_datetime(anomalies_df.index, utc=True).strftime("%Y-%m-%d").tolist()

    # FIXED: Ensure index is datetime before formatting
    anomaly_dates = pd.to_datetime(anomalies_df.index, utc=True).strftime("%Y-%m-%d").tolist()

    from analyzer import detect_rolling_trend_anomalies  # import this at top if you add the function

    # Read the same price data again for trend analysis
    df = pd.read_csv(f"data/{ticker}_history.csv", parse_dates=["Date"])
    df.set_index("Date", inplace=True)

    # Detect rolling trend anomalies (e.g., 5-day > ±12%)
    trend_anomalies = detect_rolling_trend_anomalies(df, window=5, threshold=0.12)
    trend_dates = trend_anomalies["AnomalyDate"].dt.strftime("%Y-%m-%d").tolist()



    persistent_df = detect_persistent_run_anomalies(df, min_days=7, min_total_return=0.10)
    persistent_df["PersistentAnomalyDate"] = pd.to_datetime(persistent_df["PersistentAnomalyDate"], utc=True)
    persistent_dates = persistent_df["PersistentAnomalyDate"].dt.strftime("%Y-%m-%d").tolist()

    all_anomaly_dates = sorted(set(anomaly_dates + trend_dates + persistent_dates))  # new

    print("📊 Detecting persistent up/down runs...")

    total_anomalies = len(anomalies_df) + len(trend_anomalies) + len(persistent_df)
    print(f"✅ Saved {total_anomalies} total anomalies to data/{ticker}_*.csv")

    # === Step 3: Fetch news ===
    print("📰 Fetching news for anomalies...")
    #news_by_date = fetch_news_for_anomalies(ticker, all_anomaly_dates)  
    news_z = fetch_news_for_anomalies(ticker, z_anomalies, anomaly_type="z")
    news_trend = fetch_news_for_anomalies(ticker, trend_dates, anomaly_type="trend")
    news_run = fetch_news_for_anomalies(ticker, persistent_dates, anomaly_type="run")

# ✅ Combine all into one dictionary
    news_by_date = {**news_z, **news_trend, **news_run}

    news_path = f"data/{ticker}_news.json"
    with open(news_path, "w") as f:
        json.dump(news_by_date, f, indent=2)
    print(f"✅ News saved to {news_path}")

    # === Step 4: Visualize ===
    print("📊 Creating interactive chart...")
    generate_visualization(
    price_csv=f"data/{ticker}_history.csv",
    news_json=news_path,
    ticker=ticker,
    z_anomalies = pd.to_datetime(anomalies_df.index, utc=True).strftime("%Y-%m-%d").tolist(),
    trend_anomalies=trend_anomalies["AnomalyDate"].dt.strftime("%Y-%m-%d").tolist(),
    run_anomalies=persistent_df["PersistentAnomalyDate"].dt.strftime("%Y-%m-%d").tolist()
)

    print("✅ Done! Chart saved in /plots")

if __name__ == "__main__":
    main()