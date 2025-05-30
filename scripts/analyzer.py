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
    path = f"../data/{ticker}_history.csv"
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
    print(f"Saved {len(anomalies)} anomalies to ../data/{ticker}_anomalies.csv")

    return anomalies

def detect_rolling_trend_anomalies(df, window=5, threshold=0.12):
    df["RollingReturn"] = df["Close"].pct_change(periods=window)
    df["RollingAnomaly"] = df["RollingReturn"].abs() > threshold

    # Shift index forward so anomaly is assigned to the *end* of the window
    df["AnomalyDate"] = df.index
    df["AnomalyDate"] = df["AnomalyDate"].shift(-window)

    trend_anomalies = df[df["RollingAnomaly"]].copy()
    trend_anomalies = trend_anomalies.dropna(subset=["AnomalyDate"])
    trend_anomalies["AnomalyDate"] = pd.to_datetime(trend_anomalies["AnomalyDate"], utc=True)

    return trend_anomalies

def detect_persistent_run_anomalies(df, min_days=7, min_total_return=0.10):
    """
    Detects long uninterrupted up or down runs and flags end of run as anomaly.
    E.g., 7+ consecutive up days, total gain > 10%
    """
    df = df.copy()
    df["Return"] = df["Close"].pct_change()

    results = []
    start_idx = None
    direction = None
    total_return = 0

    for i in range(1, len(df)):
        daily_return = df.iloc[i]["Return"]

        if daily_return > 0:
            curr_dir = "up"
        elif daily_return < 0:
            curr_dir = "down"
        else:
            curr_dir = None

        if curr_dir == direction:
            total_return *= (1 + daily_return)
        else:
            # Check if previous run qualifies
            if start_idx is not None:
                run_length = i - start_idx
                cumulative_return = total_return - 1.0
                if run_length >= min_days and abs(cumulative_return) > min_total_return:
                    results.append(df.index[i - 1])

            # Start new run
            start_idx = i - 1
            total_return = 1.0 * (1 + daily_return)  # initialize to 1 + first return
            direction = curr_dir


    # Final run check
    if start_idx is not None:
        run_length = len(df) - start_idx
        cumulative_return = total_return - 1.0
        if run_length >= min_days and abs(cumulative_return) > min_total_return:

            results.append(df.index[-1])

    return pd.DataFrame({"PersistentAnomalyDate": pd.to_datetime(results)})


# Example usage
if __name__ == "__main__":
    detect_anomalies_mad("AAPL")
