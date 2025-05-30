import pandas as pd
import plotly.graph_objects as go
import json
import os

def generate_visualization(price_csv, news_json, ticker, z_anomalies=None, trend_anomalies=None, run_anomalies=None):

    # === Load and normalize column names ===
    df = pd.read_csv(price_csv)
    df["Date"] = pd.to_datetime(df["Date"], utc=True, errors="coerce")
    df = df.rename(columns={"Date": "date", "Close": "close"})
    df["return"] = df["close"].pct_change()
    df["direction"] = df["return"].apply(lambda x: "up" if x > 0 else "down")

    # === Load anomaly news ===
    with open(news_json, "r") as f:
        news_by_date = json.load(f)

    df["date_str"] = df["date"].dt.strftime("%Y-%m-%d")

    df["z_dot"] = df["date_str"].isin(z_anomalies)
    df["trend_dot"] = df["date_str"].isin(trend_anomalies)
    df["run_dot"] = df["date_str"].isin(run_anomalies)
    
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


    # === Add anomaly dots by type ===
    dots_z = go.Scatter(
        x=df[df["z_dot"]]["date"],
        y=df[df["z_dot"]]["close"],
        mode="markers",
        marker=dict(size=10, color="yellow", line=dict(width=1, color="black")),
        name="1-Day Spikes (Z-Score)",
        text=df[df["z_dot"]]["news"],
        hovertemplate="<b>📌 Z-Score Anomaly</b><br>%{text}<extra></extra>"
    )

    dots_trend = go.Scatter(
        x=df[df["trend_dot"]]["date"],
        y=df[df["trend_dot"]]["close"],
        mode="markers",
        marker=dict(size=10, color="dodgerblue", line=dict(width=1, color="black")),
        name="5-Day Trend Anomaly",
        text=df[df["trend_dot"]]["news"],
        hovertemplate="<b>📈 Trend Anomaly</b><br>%{text}<extra></extra>"
    )

    dots_run = go.Scatter(
        x=df[df["run_dot"]]["date"],
        y=df[df["run_dot"]]["close"],
        mode="markers",
        marker=dict(size=10, color="mediumorchid", line=dict(width=1, color="black")),
        name="Persistent Run Anomaly",
        text=df[df["run_dot"]]["news"],
        hovertemplate="<b>🔥 Run Anomaly</b><br>%{text}<extra></extra>"
    )


    # === Build chart ===
    fig = go.Figure(segments + [dots_z, dots_trend, dots_run])
    fig.update_layout(
        title=f"📈 {ticker.upper()} Stock Price with Anomalies and News Headlines",
        xaxis_title="Date",
        yaxis_title="Close Price (USD)",
        hovermode="closest",
        template="plotly_dark",
        font=dict(family="Arial", size=14),
        margin=dict(l=40, r=40, t=80, b=40),
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
    )

    # === Show and export ===
    fig.show()

    os.makedirs("plots", exist_ok=True)
    output_path = f"plots/{ticker.lower()}_anomaly_chart.html"
    
    # == custom html
    custom_html = '''
    <style>
    #news-box a {
        color: white;
        text-decoration: none;
    }
    #news-box a:hover {
        text-decoration: underline;
    }
    </style>

    <div id="news-box" style="...">
        ...
    </div>

    <script>
    document.addEventListener("DOMContentLoaded", function () {
        ...
    });
    </script>
    '''

    fig.write_html(output_path, include_plotlyjs="cdn", full_html=True, post_script=custom_html)

    # === Save chart first
    fig.write_html(output_path)

# === Inject persistent floating news box with close button ===
    with open(output_path, "r", encoding="utf-8") as f:
        html = f.read()

    injected = '''
    <!-- Floating persistent news box -->
    <div id="news-box" style="
        position: fixed;
        top: 100px;
        right: 50px;
        width: 350px;
        padding: 12px;
        background: #222;
        color: white;
        font-family: sans-serif;
        font-size: 14px;
        border: 1px solid #444;
        border-radius: 6px;
        z-index: 1000;
        display: none;
        box-shadow: 0 0 10px rgba(0,0,0,0.5);
    ">
        <div style="text-align: right;">
            <button onclick="document.getElementById('news-box').style.display='none'" style="
                background: none;
                border: none;
                color: white;
                font-size: 16px;
                cursor: pointer;
            ">✖</button>
        </div>
        <div id="news-content" style="margin-top: 10px;"></div>
    </div>

    <script>
    document.addEventListener("DOMContentLoaded", function () {
        let chart = document.querySelector(".plotly-graph-div");
        if (chart) {
            chart.on("plotly_click", function(data) {
                let newsHTML = data.points[0].text;
                let box = document.getElementById("news-box");
                let content = document.getElementById("news-content");
                if (box && content) {
                    content.innerHTML = newsHTML;
                    box.style.display = "block";
                }
            });
        }
    });
    </script>
    '''

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html.replace("</body>", injected + "\n</body>"))



    print(f"✅ Chart saved to {output_path}")
