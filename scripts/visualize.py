import pandas as pd
import plotly.graph_objects as go
import json
import os

def generate_visualization(price_csv, news_json):
    # === Load and normalize column names ===
    df = pd.read_csv(price_csv)
    df["Date"] = pd.to_datetime(df["Date"], utc=True, errors="coerce")
    df = df.rename(columns={"Date": "date", "Close": "close"})
    df["return"] = df["close"].pct_change()
    df["direction"] = df["return"].apply(lambda x: "up" if x > 0 else "down")

    # === Load anomaly news ===
    with open(news_json, "r") as f:
        news_by_date = json.load(f)

    df["is_anomaly"] = df["date"].dt.strftime("%Y-%m-%d").isin(news_by_date.keys())
    df["news"] = df["date"].dt.strftime("%Y-%m-%d").map(
        lambda d: "<br>".join(news_by_date.get(d, [])) if news_by_date.get(d) else ""
    )

    # === Segment line by gain/loss ===
    colors = {"up": "limegreen", "down": "crimson"}
    segments = []

    for i in range(1, len(df)):
        curr = df.iloc[i]
        prev = df.iloc[i - 1]
        segments.append(go.Scatter(
            x=[prev["date"], curr["date"]],
            y=[prev["close"], curr["close"]],
            mode="lines",
            line=dict(color=colors[curr["direction"]], width=2),
            hoverinfo="skip",
            showlegend=False
        ))

    # === Add anomaly dots ===
    anomalies = df[df["is_anomaly"]]
    dots = go.Scatter(
        x=anomalies["date"],
        y=anomalies["close"],
        mode="markers",
        marker=dict(
            size=12,
            color="gold",
            line=dict(width=2, color="black"),
            symbol="circle"
        ),
        name="Anomalies",
        text=anomalies["news"],
        hovertemplate="<b>📌 Anomaly Day</b><br>%{text}<extra></extra>"
    )

    # === Build chart ===
    fig = go.Figure(segments + [dots])
    fig.update_layout(
        title="📈 AAPL Stock Price with Anomalies and News Headlines",
        xaxis_title="Date",
        yaxis_title="Close Price (USD)",
        hovermode="closest",
        template="plotly_dark",
        font=dict(family="Arial", size=14),
        margin=dict(l=40, r=40, t=80, b=40),
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )

    # === Show and export ===
    fig.show()

    os.makedirs("plots", exist_ok=True)
    output_path = "plots/aapl_anomaly_chart.html"
    fig.write_html(output_path)
    print(f"✅ Chart saved to {output_path}")
