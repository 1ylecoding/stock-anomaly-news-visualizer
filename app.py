# app.py
import streamlit as st
import pandas as pd
import json
import os

from scripts.data_fetcher import fetch_and_save_stock_data
from scripts.analyzer import detect_all_anomalies
from scripts.main import fetch_news_for_anomalies
from scripts.visualize import generate_visualization

st.set_page_config(page_title="Stock Anomaly Detector", layout="wide")

# --- HEADER ---
st.markdown("""
    <style>
        .main { background-color: #111; }
        h1, h2, h3, .stButton>button {
            color: white !important;
        }
        .stButton>button {
            background-color: #008CBA;
            border-radius: 10px;
            font-size: 16px;
            padding: 0.5em 1.5em;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center;'>📈 Stock Anomaly Detector + News Enrichment</h1>", unsafe_allow_html=True)
st.markdown("This tool flags unusual price movements using volatility-adjusted models and fetches real news headlines to explain them.", unsafe_allow_html=True)

# --- INPUTS ---
st.sidebar.title("Configuration")

ticker = st.sidebar.text_input("Stock Ticker", value="AAPL").upper()
st.sidebar.markdown("### Thresholds")
mad_threshold = st.sidebar.slider("1-Day Z Score (MAD)", 1.0, 5.0, 2.5)
rolling_threshold = st.sidebar.slider("5-Day Trend Z", 1.0, 5.0, 2.0)
extreme_threshold = st.sidebar.slider("3-Day Return Z", 1.0, 5.0, 2.5)
persistent_threshold = st.sidebar.slider("7-Day Run Z", 0.1, 5.0, 0.5)

# TIME SLIDER

st.sidebar.markdown("### 📆 Time Period")
period_map = {
    "3M": "3mo",
    "6M": "6mo",
    "9M": "9mo",
    "12M": "1y",
    "15M": "15mo",
    "18M": "18mo",
    "21M": "21mo",
    "24M": "2y"
}
selected_period_label = st.sidebar.select_slider(
    "Select data window",
    options=list(period_map.keys()),
    value="12M"
)
selected_period = period_map[selected_period_label]


# API BUTTON
st.sidebar.markdown("### 🔑 News API Key")
api_key = st.sidebar.text_input("Paste your API Key", type="password")
st.sidebar.markdown("[Get a free one](https://www.thenewsapi.com/)")

if not api_key:
    st.sidebar.warning("🔐 Please enter your News API key to fetch headlines.")


# --- RUN BUTTON ---
if st.sidebar.button("🚀 Run Anomaly Detection"):
    st.success(f"Running analysis for **{ticker}**...")

    config = {
        "mad_threshold": mad_threshold,
        "rolling_window": 5,
        "rolling_threshold": rolling_threshold,
        "extreme_window": 3,
        "extreme_threshold": extreme_threshold,
        "persistent_min_days": 7,
        "persistent_threshold": persistent_threshold,
    }

    # Fetch data
    fetch_and_save_stock_data(ticker, period=selected_period)
    df = pd.read_csv(f"data/{ticker}_history.csv", parse_dates=["Date"])
    df.set_index("Date", inplace=True)

    # --- Detect anomalies ---
    anomalies = detect_all_anomalies(df, config=config)

    # 1-day MAD anomalies
    anomaly_dates = pd.to_datetime(anomalies["mad"].index, errors="coerce", utc=True).strftime("%Y-%m-%d").tolist()

    # 5-day rolling trend anomalies
    trend_df = anomalies["rolling"].copy()
    trend_df["AnomalyDate"] = pd.to_datetime(trend_df["AnomalyDate"], errors="coerce", utc=True)
    trend_dates = trend_df["AnomalyDate"].dt.strftime("%Y-%m-%d").tolist()

    # 3-day extreme return anomalies
    extreme_df = anomalies["extreme"].copy()
    extreme_df["AnomalyDate"] = pd.to_datetime(extreme_df["AnomalyDate"], errors="coerce", utc=True)
    extreme_dates = extreme_df["AnomalyDate"].dt.strftime("%Y-%m-%d").tolist()

    # 7-day persistent run anomalies
    persistent_df = anomalies["persistent"].copy()
    if not persistent_df.empty:
        persistent_df["start_date"] = pd.to_datetime(persistent_df["start_date"], errors="coerce", utc=True)
        persistent_dates = persistent_df["start_date"].dt.strftime("%Y-%m-%d").tolist()
    else:
        persistent_dates = []


    all_dates = sorted(set(anomaly_dates + trend_dates + extreme_dates + persistent_dates))

    with st.spinner("📰 Fetching news for anomaly dates..."):
        news = fetch_news_for_anomalies(ticker, all_dates, api_key=api_key)
        news_path = f"data/{ticker}_news.json"
        with open(news_path, "w") as f:
            json.dump(news, f, indent=2)

    # Visualize
    st.info("📊 Generating interactive chart...")
    generate_visualization(
        price_csv=f"data/{ticker}_history.csv",
        news_json=news_path,
        ticker=ticker,
        z_anomalies=anomaly_dates,
        trend_anomalies=trend_dates,
        extreme_anomalies=extreme_dates,
        run_anomalies=persistent_dates
    )

    chart_path = f"plots/{ticker.lower()}_anomaly_chart.html"
    st.markdown(f"✅ [Open Interactive Chart]({chart_path})", unsafe_allow_html=True)

    # Optional: embed inside the app
    with open(chart_path, "r", encoding="utf-8") as f:
        html = f.read()
    st.components.v1.html(html, height=600, scrolling=True)

