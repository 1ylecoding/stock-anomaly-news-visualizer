# 📊 Stock Anomaly Detector with News Context

This tool analyzes stock price data to detect:
- 🔶 MAD spikes (single-day outliers)
- 🔷 Rolling window trends (e.g., 5-day price surges)
- 🔴 Persistent directional runs (e.g., 9-day climb +14%)

Each anomaly is visualized on an interactive Plotly chart. Hovering over a dot shows:
- Type of anomaly
- Linked headlines from the date

## 🚀 Features
- Detects and categorizes different types of price anomalies
- Fetches real news from TheNewsAPI
- Fully interactive chart (hover + click headlines)
- One-click script (`main.py`) to run full pipeline
