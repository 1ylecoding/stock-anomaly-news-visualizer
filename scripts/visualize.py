import pandas as pd
import plotly.graph_objects as go
import json
import os
import webbrowser

def generate_visualization(price_csv, news_json, ticker,
                           z_anomalies=None, trend_anomalies=None,
                           run_anomalies=None, extreme_anomalies=None):
    # Load and normalize data
    df = pd.read_csv(price_csv)
    df = df.rename(columns={"Date": "date", "Close": "close"})
    df["date"] = pd.to_datetime(df["date"], utc=True, errors="coerce")
    df["return"] = df["close"].pct_change()
    df["direction"] = df["return"].apply(lambda x: "up" if x > 0 else "down")

    # Load news
    with open(news_json, "r") as f:
        news_by_date = json.load(f)
    df["date_str"] = df["date"].dt.strftime("%Y-%m-%d")
    df["news"] = df["date_str"].map(lambda d: "<br>".join(news_by_date.get(d, [])))

    # Flag anomalies
    df["z_dot"] = df["date_str"].isin(z_anomalies or [])
    df["trend_dot"] = df["date_str"].isin(trend_anomalies or [])
    df["run_dot"] = df["date_str"].isin(run_anomalies or [])
    df["extreme_dot"] = df["date_str"].isin(extreme_anomalies or [])

    # Plot line segments colored by direction
    colors = {"up": "limegreen", "down": "crimson"}
    segments = []
    for i in range(1, len(df)):
        prev, curr = df.iloc[i - 1], df.iloc[i]
        segments.append(go.Scatter(
            x=[prev["date"], curr["date"]],
            y=[prev["close"], curr["close"]],
            mode="lines",
            line=dict(color=colors[curr["direction"]], width=2),
            hoverinfo="skip", showlegend=False
        ))

    # Helper for anomaly dots
    def make_dot(col, color, name, icon):
        sel = df[df[col]]
        return go.Scatter(
            x=sel["date"], y=sel["close"], mode="markers",
            marker=dict(size=12, color=color, line=dict(width=1, color="black")),
            name=name, text=sel["news"],
            hovertemplate=f"<b>{icon} {name}</b><br>%{{text}}<extra></extra>"
        )

    # Create dots, revert to goldenrod
    dots = [
        make_dot("z_dot", "goldenrod", "1-Day Spikes", "📌"),
        make_dot("trend_dot", "dodgerblue", "5-Day Trend", "📈"),
        make_dot("run_dot", "mediumorchid", "Run Anomaly", "🔥"),
        make_dot("extreme_dot", "red", "Extreme Anomaly", "⚡")
    ]

    # Build figure
    fig = go.Figure(segments + dots)
    fig.update_layout(
        title=f"📈 {ticker.upper()} Price with Anomalies & News",
        xaxis_title="Date", yaxis_title="Close Price",
        hovermode="closest", template="plotly_dark",
        font=dict(family="Arial", size=14), margin=dict(l=40, r=40, t=80, b=40),
        # Force all hover labels to white text on dark background
        hoverlabel=dict(
            bgcolor="rgba(0,0,0,0.7)",
            font_color="white"
        )
    )

    # Prepare HTML export
    os.makedirs("plots", exist_ok=True)
    output_path = f"plots/{ticker.lower()}_anomaly_chart.html"

    # JavaScript to append news box and handle clicks
    post_script = '''
    (function() {
      var style = document.createElement('style');
      style.innerHTML = '#news-box a { color: white !important; }';
      document.head.appendChild(style);

      var box = document.createElement('div'); box.id = 'news-box';
      Object.assign(box.style, {
        position: 'fixed', top: '100px', right: '50px', width: '350px', padding: '12px',
        background: '#222', color: 'white', fontFamily: 'sans-serif', fontSize: '14px',
        border: '1px solid #444', borderRadius: '6px', zIndex: 1000, display: 'none',
        boxShadow: '0 0 10px rgba(0,0,0,0.5)'
      });

      var btn = document.createElement('button'); btn.textContent = '✖';
      Object.assign(btn.style, {
        background: 'none', border: 'none', color: 'white', fontSize: '16px', cursor: 'pointer', float: 'right'
      });
      btn.onclick = function() { box.style.display = 'none'; };
      box.appendChild(btn);

      var content = document.createElement('div'); content.id = 'news-content';
      content.style.marginTop = '10px'; content.style.color = 'white';
      box.appendChild(content);
      document.body.appendChild(box);

      var gd = document.querySelector('.plotly-graph-div');
      if (gd && gd.on) {
        gd.on('plotly_click', function(evt) {
          var txt = evt.points[0].text || '';
          content.innerHTML = txt;
          box.style.display = 'block';
        });
      }
    })();
    '''

    # Write HTML with embedded JS, auto-open
    fig.write_html(
        output_path,
        include_plotlyjs=True,
        full_html=True,
        auto_open=True,
        post_script=post_script
    )

    print(f"✅ Chart saved & opened: {output_path}")
