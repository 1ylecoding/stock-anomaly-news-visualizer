import os
import json
import pandas as pd
import yfinance as yf

from scripts.data_fetcher import fetch_and_save_stock_data
from scripts.analyzer import detect_all_anomalies
from scripts.newsapi_fetcher import get_newsapi_news
from scripts.visualize import generate_visualization

def get_company_name(ticker):
    try:
        return yf.Ticker(ticker).info.get("longName", ticker)
    except:
        return ticker  # fallback

from scripts.newsapi_fetcher import get_newsapi_news

def fetch_news_for_anomalies(ticker, dates, api_key, anomaly_type="default"):
    import yfinance as yf
    try:
        company_name = yf.Ticker(ticker).info.get("longName", ticker)
    except:
        company_name = ticker  # fallback

    news = {}
    for date in dates:
        results = get_newsapi_news(query=company_name, date=date, api_key=api_key)
        link_color = "white"
        news[date] = [
            f"<a href='{a['url']}' target='_blank' style='color:{link_color}; text-decoration:none;'>{a['title']} ({a['source']})</a>"
            for a in results
        ] if results else ["No major headlines found."]
    return news


def main():
    ticker = input("Enter the stock ticker (e.g., AAPL, MSFT, GOOGL): ").strip().upper()
    print(f"🚀 Starting full pipeline for {ticker}")
# anomaly thresholds
    print("Configure anomaly thresholds (press Enter for default):")
    mad_input        = input(" • 1-day z-score threshold [default 2.5]: ").strip()
    rolling_input    = input(" • 5-day z-score threshold [default 2.0]: ").strip()
    extreme_input    = input(" • 3-day z-score threshold [default 2.5]: ").strip()
    persistent_input = input(" • 7-day z-score threshold [default 0.5]: ").strip()

    mad_threshold        = float(mad_input)        if mad_input else 2.5
    rolling_threshold    = float(rolling_input)    if rolling_input else 2.0
    extreme_threshold    = float(extreme_input)    if extreme_input else 2.5
    persistent_threshold = float(persistent_input) if persistent_input else 0.5

    config = {
        "mad_threshold":        mad_threshold,
        "rolling_window":       5,
        "rolling_threshold":    rolling_threshold,
        "extreme_window":       3,
        "extreme_threshold":    extreme_threshold,
        "persistent_min_days":  7,
        "persistent_threshold": persistent_threshold,
    }

    ##### Step 1: Fetch data
    print("📥 Fetching stock data...")
    fetch_and_save_stock_data(ticker)

    # Load price data once
    df = pd.read_csv(f"data/{ticker}_history.csv", parse_dates=["Date"])
    df.set_index("Date", inplace=True)

    print("Using thresholds:", config)
    anomalies = detect_all_anomalies(df, config=config)


    ##### Step 2: Detect anomalies (unified)
    print("🔍 Detecting anomalies...")
    anomalies = detect_all_anomalies(df, config=config)

    # Extract anomaly date lists
    # 1-day MAD anomalies
    anomalies_df = anomalies["mad"]
    anomaly_dates = pd.to_datetime(anomalies_df.index, utc=True).strftime("%Y-%m-%d").tolist()

    # Rolling trend anomalies
    trend_df = anomalies["rolling"]
    trend_df["AnomalyDate"] = pd.to_datetime(trend_df["AnomalyDate"], utc=True)
    trend_dates = trend_df["AnomalyDate"].dt.strftime("%Y-%m-%d").tolist()

    # Extreme multi-day anomalies
    extreme_df = anomalies["extreme"]
    extreme_df["AnomalyDate"] = pd.to_datetime(extreme_df["AnomalyDate"], utc=True)
    extreme_dates = extreme_df["AnomalyDate"].dt.strftime("%Y-%m-%d").tolist()

    # Persistent run anomalies (use start_date for news)
    persistent_df = anomalies["persistent"]
    print("Persistent run anomaly columns:", persistent_df.columns)
    print(persistent_df.head())
    if not persistent_df.empty:
        persistent_df["start_date"] = pd.to_datetime(persistent_df["start_date"], utc=True)
        persistent_dates = persistent_df["start_date"].dt.strftime("%Y-%m-%d").tolist()
    else:
        persistent_dates = []

    total_anomalies = (
        len(anomalies_df)
        + len(trend_df)
        + len(extreme_df)
        + len(persistent_df)
    )
    print(f"✅ Detected {total_anomalies} total anomalies")

    ###### Step 6: Combine dates & fetch news
    print("📰 Fetching news for anomalies...")
    all_anomaly_dates = sorted(set(anomaly_dates + trend_dates + extreme_dates + persistent_dates))

    news_z       = fetch_news_for_anomalies(ticker, anomaly_dates, anomaly_type="z")
    news_trend   = fetch_news_for_anomalies(ticker, trend_dates,   anomaly_type="trend")
    news_extreme = fetch_news_for_anomalies(ticker, extreme_dates, anomaly_type="extreme")
    news_run     = fetch_news_for_anomalies(ticker, persistent_dates, anomaly_type="run")

    news_by_date = {**news_z, **news_trend, **news_extreme, **news_run}
    news_path = f"data/{ticker}_news.json"
    with open(news_path, "w") as f:
        json.dump(news_by_date, f, indent=2)
    print(f"✅ News saved to {news_path}")

    ##### Step 7: Visualize
    print("📊 Creating interactive chart...")
    generate_visualization(
        price_csv=f"data/{ticker}_history.csv",
        news_json=news_path,
        ticker=ticker,
        z_anomalies=anomaly_dates,
        trend_anomalies=trend_dates,
        extreme_anomalies=extreme_dates,
        run_anomalies=persistent_dates
    )

    print("✅ Done! Chart saved in /plots")

if __name__ == "__main__":
    main()