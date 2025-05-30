import pandas as pd
import numpy as np
import os

def modified_z_score(x):
    median = np.median(x)
    mad = np.median(np.abs(x - median))
    if mad == 0:
        return np.zeros(len(x))  # Prevent divide-by-zero
    return 0.6745 * (x - median) / mad

def detect_anomalies_mad(ticker: str, threshold: float = 3.5):
    path = f"data/{ticker}_history.csv"
    if not os.path.exists(path):
        raise FileNotFoundError(f"No data file found for {ticker} at {path}")

    df = pd.read_csv(path, parse_dates=["Date"], index_col="Date")
    df["Return"] = df["Close"].pct_change()

    # Drop NaNs
    returns = df["Return"].dropna()
    z_scores = modified_z_score(returns)

    df = df.iloc[1:]  # Align with returns (since first return is NaN)
    df["ModifiedZ"] = z_scores
    df["Anomaly"] = np.abs(z_scores) > threshold

    anomalies = df[df["Anomaly"]].copy()
    anomalies = anomalies[["Close", "Return", "ModifiedZ"]]

    anomalies.to_csv(f"../data/{ticker}_anomalies.csv")

    return anomalies

def detect_rolling_trend_anomalies(df, window=5, threshold=0.12):
    df = df.copy()
    df["RollingReturn"] = df["Close"].pct_change(periods=window)
    df["RollingAnomaly"] = df["RollingReturn"].abs() > threshold

    # Assign anomaly to end of window
    df["AnomalyDate"] = df.index
    df["AnomalyDate"] = df["AnomalyDate"].shift(-window)

    anomalies = df[df["RollingAnomaly"]].dropna(subset=["AnomalyDate"]).copy()

    # ✅ Collapse anomalies within `window` days
    grouped = []
    last_date = None
    for date in anomalies["AnomalyDate"]:
        if last_date is None or (date - last_date).days >= window:
            grouped.append(date)
        last_date = date

    collapsed = anomalies[anomalies["AnomalyDate"].isin(grouped)].copy()

    # ✅ Convert AnomalyDate to datetime explicitly
    collapsed["AnomalyDate"] = pd.to_datetime(collapsed["AnomalyDate"], utc=True)

    return collapsed



def detect_persistent_run_anomalies(df, min_days=7, min_total_return=0.10):
    df = df.copy()
    df["Return"] = df["Close"].pct_change()
    df["CumulativeReturn"] = (1 + df["Return"]).rolling(window=min_days).apply(lambda x: x.prod() - 1, raw=True)
    df["PersistentAnomaly"] = df["CumulativeReturn"].abs() > min_total_return

    # Keep only anomaly dates
    anomalies = df[df["PersistentAnomaly"]].copy()
    anomalies = anomalies.dropna(subset=["CumulativeReturn"])
    anomalies["PersistentAnomalyDate"] = anomalies.index

    # ✅ Collapse anomalies within 7 days into a single one
    grouped = []
    last_date = None
    for date in anomalies["PersistentAnomalyDate"]:
        if last_date is None or (date - last_date).days >= min_days:
            grouped.append(date)
        last_date = date

    result = anomalies[anomalies["PersistentAnomalyDate"].isin(grouped)]
    return result[["PersistentAnomalyDate", "CumulativeReturn"]]



# Example usage
if __name__ == "__main__":
    detect_anomalies_mad("AAPL")
