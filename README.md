# Stock Movement Anomaly Detector with News Context

This tool is a Python-based research assistant for capital markets. It analyses one year of daily stock prices, detects statistically significant price anomalies, and links each event to top news headlines. Interactive visualizations help you explore price spikes, dips, trends, and persistent runs alongside their real-world drivers.

## Key Features

* **Dynamic Anomaly Detection**

  * Single‑day outliers via Modified Z‑Score on daily returns
  * Multi‑day trends and extreme windows using rolling and compounded returns
  * Persistent directional runs flagged by length and modified Z‑Score
  * Configurable thresholds and minimum gap between extreme events

* **News Context Integration**

  * Fetches top headlines for each anomaly date via NewsAPI (or alternative)
  * Caches results to avoid redundant requests
  * Renders headlines as clickable links in hover and floating boxes

* **Interactive Visualization**

  * Plotly chart with colored segments for gains and losses
  * Distinct markers for each anomaly type
  * Hover tooltips show headline summaries
  * Clickable chart dots open a persistent news panel
  * Auto‑opens in your default browser after each run

## Getting Started

### Prerequisites

* Python 3.8 or later
* A free NewsAPI key (or configure alternative news fetcher)
* Git

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/your-username/stock-anomaly-detector.git
   cd stock-anomaly-detector
   ```
2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate   # on Mac/Linux
   venv\\Scripts\\activate  # on Windows
   ```
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file with your NewsAPI key:

   ```text
   NEWSAPI_KEY=YOUR_KEY_HERE
   ```

## Usage

Run the main script and follow the prompts:

```bash
python scripts/main.py
```

* **Ticker**: e.g. `AAPL`, `MSFT`, `GOOGL`
* **Thresholds**: Press **Enter** to accept defaults or type custom values.

After fetching data and news, the tool will:

1. Detect anomalies
2. Generate an interactive HTML chart in `plots/`
3. Auto‑open the chart in your default browser

## Configuration

All detection parameters and thresholds live in `scripts/main.py` under the `config` dictionary. You can also pass command‑line flags if you convert `main.py` to accept arguments.

## Project Structure

```
├── data/                  # Raw data and news JSON
├── plots/                 # Output HTML charts
├── scripts/               # Main entry point and helper modules
│   ├── main.py            # CLI and orchestration
│   ├── data_fetcher.py    # Fetches stock history via yfinance
│   ├── analyzer.py        # All anomaly detection functions
│   ├── newsapi_fetcher.py # Wraps NewsAPI calls
│   └── visualize.py       # Plotly chart generation
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (not in version control)
└── README.md              # This document
```

## Examples

![Chart Example](https://i.imgur.com/KlBdRRh.png)

1. **Hover** over a dot to see headlines.
2. **Click** a dot to open the persistent news box.

## Roadmap

* Support multiple ticker input and batch mode
* Implement alternative news sources to handle rate limits
* Add a CLI flag interface (via `argparse` or `click`)
* Package as installable module with entry points

Contributions are welcome. Please open an issue or submit a pull request:

1. Fork the repo
2. Create a feature branch
3. Commit your changes
4. Push to your branch and open a Pull Request
