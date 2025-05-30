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

def detect_extreme_multi_day_anomalies(df, window=3, threshold=0.10):
    """
    Detects extreme price moves over a 2-3 day window exceeding the threshold.
    """
    df = df.copy()
    df["Return"] = df["Close"].pct_change()
    
    # Calculate rolling compounded return over the window
    df["RollingReturn"] = (1 + df["Return"]).rolling(window=window).apply(lambda x: x.prod() - 1, raw=True)
    
    # Flag anomalies exceeding threshold
    df["ExtremeAnomaly"] = df["RollingReturn"].abs() > threshold
    
    # Extract dates where anomalies occur (end of rolling window)
    anomalies = df[df["ExtremeAnomaly"]].copy()
    anomalies["AnomalyDate"] = anomalies.index
    
    return anomalies[["AnomalyDate", "RollingReturn"]]


def detect_persistent_run_anomalies(df, min_days=7, min_total_return=0.05):
    df = df.copy()
    df["Return"] = df["Close"].pct_change()

    runs = []
    start_idx = 0
    direction = 0  # 1=up, -1=down, 0=undefined

    for i in range(1, len(df)):
        ret = df["Return"].iloc[i]
        curr_dir = 1 if ret > 0 else (-1 if ret < 0 else 0)

        if direction == 0:
            direction = curr_dir
            start_idx = i - 1

        if curr_dir == direction or curr_dir == 0:
            continue  # continue the run
        else:
            end_idx = i - 1
            run_length = end_idx - start_idx + 1

            if run_length >= min_days:
                run_returns = df["Return"].iloc[start_idx:end_idx + 1]
                cumulative_return = (1 + run_returns).prod() - 1
                print(f"Run from {df.index[start_idx]} to {df.index[end_idx]}: return {cumulative_return:.4f}")

                if abs(cumulative_return) >= min_total_return:
                    runs.append({
                        "start_date": df.index[start_idx],
                        "end_date": df.index[end_idx],
                        "cumulative_return": cumulative_return,
                        "direction": "up" if cumulative_return > 0 else "down"
                    })

            direction = curr_dir
            start_idx = i - 1

    # Check last run at the end of data
    end_idx = len(df) - 1
    run_length = end_idx - start_idx + 1

    if run_length >= min_days:
        run_returns = df["Return"].iloc[start_idx:end_idx + 1]
        cumulative_return = (1 + run_returns).prod() - 1
        print(f"Run from {df.index[start_idx]} to {df.index[end_idx]}: return {cumulative_return:.4f}")

        if abs(cumulative_return) >= min_total_return:
            runs.append({
                "start_date": df.index[start_idx],
                "end_date": df.index[end_idx],
                "cumulative_return": cumulative_return,
                "direction": "up" if cumulative_return > 0 else "down"
            })

    runs_df = pd.DataFrame(runs)
    print(f"Total runs detected: {len(runs_df)}")
    return runs_df






# Example usage
if __name__ == "__main__":
    detect_anomalies_mad("AAPL")
