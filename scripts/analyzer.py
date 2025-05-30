import pandas as pd
import numpy as np
DEFAULT_MIN_GAP_DAYS = 3


def modified_z_score(x: np.ndarray) -> np.ndarray:
    """
    Compute the modified Z-score using median absolute deviation.

    Args:
        x: 1D array of numeric values.
    Returns:
        Array of modified Z-scores.
    """
    median = np.median(x)
    mad = np.median(np.abs(x - median))
    if mad == 0:
        return np.zeros(len(x))
    return 0.6745 * (x - median) / mad


def detect_all_anomalies(df: pd.DataFrame, config: dict = None) -> dict:
    """
    Run all anomaly detectors with configurable thresholds.

    Args:
        df: DataFrame with a DateTime index and 'Close' column.
        config: Dictionary of parameters:
            - mad_threshold
            - rolling_window, rolling_threshold
            - extreme_window, extreme_threshold
            - persistent_min_days, persistent_threshold
    Returns:
        Dict with keys 'mad', 'rolling', 'extreme', 'persistent', each a DataFrame of anomalies.
    """
    if config is None:
        config = {
            "mad_threshold": 3.5,
            "rolling_window": 5,
            "rolling_threshold": 3.5,
            "extreme_window": 3,
            "extreme_threshold": 3.5,
            "persistent_min_days": 7,
            "persistent_threshold": 3.5,
        }
    results = {}

    results["mad"] = detect_anomalies_mad(df, threshold=config["mad_threshold"])
    results["rolling"] = detect_rolling_trend_anomalies(
        df,
        window=config["rolling_window"],
        threshold=config["rolling_threshold"]
    )
    results["extreme"] = detect_extreme_multi_day_anomalies(
        df,
        window=config["extreme_window"],
        threshold=config["extreme_threshold"]
    )
    results["persistent"] = detect_persistent_run_anomalies(
        df,
        min_days=config["persistent_min_days"],
        threshold=config["persistent_threshold"]
    )
    return results


def detect_anomalies_mad(df: pd.DataFrame, threshold: float) -> pd.DataFrame:
    """
    Detect single-day anomalies using Modified Z-Score on daily returns.

    Returns:
        DataFrame of anomalies with ['Close', 'Return', 'ModifiedZ'].
    """
    df = df.copy()
    df["Return"] = df["Close"].pct_change()

    returns = df["Return"].dropna().values
    z_scores = modified_z_score(returns)

    df = df.iloc[1:].copy()
    df["ModifiedZ"] = z_scores
    df["Anomaly"] = df["ModifiedZ"].abs() > threshold

    return df[df["Anomaly"]][["Close", "Return", "ModifiedZ"]]


def detect_rolling_trend_anomalies(df: pd.DataFrame, window: int, threshold: float) -> pd.DataFrame:
    """
    Detect multi-day rolling-window anomalies using localized Modified Z-Score.

    Uses a 60-period lookback for median and MAD to adapt to recent volatility.

    Returns:
        DataFrame with ['AnomalyDate', 'RollingReturn', 'ModifiedZ'].
    """
    df = df.copy()
    df["RollingReturn"] = df["Close"].pct_change(periods=window)
    df = df.dropna(subset=["RollingReturn"]).copy()

    df["Median"] = df["RollingReturn"].rolling(60, min_periods=1).median()
    df["MAD"] = df["RollingReturn"].rolling(60, min_periods=1) \
        .apply(lambda x: np.median(np.abs(x - np.median(x))), raw=True)

    df["ModifiedZ"] = 0.6745 * (df["RollingReturn"] - df["Median"]) / df["MAD"].replace(0, np.nan)
    df["RollingAnomaly"] = df["ModifiedZ"].abs() > threshold

    anomalies = df[df["RollingAnomaly"]].copy()
    anomalies["AnomalyDate"] = pd.to_datetime(anomalies.index, utc=True)

    # Collapse anomalies within 'window' days
    grouped = []
    last_date = None
    for date in anomalies["AnomalyDate"]:
        if last_date is None or (date - last_date).days >= window:
            grouped.append(date)
            last_date = date
    collapsed = anomalies[anomalies["AnomalyDate"].isin(grouped)].copy()

    return collapsed[["AnomalyDate", "RollingReturn", "ModifiedZ"]]

def detect_extreme_multi_day_anomalies(
    df: pd.DataFrame,
    window: int,
    threshold: float,
    min_gap_days: int = DEFAULT_MIN_GAP_DAYS
) -> pd.DataFrame:
    """
    Detect extreme anomalies over a multi-day window using Modified Z-Score.
    Returns a DataFrame with ['AnomalyDate','RollingReturn','ModifiedZ'].
    Ensures anomalies are at least `min_gap_days` apart, and returns naive datetimes.
    """
    df = df.copy()
    df["Return"] = df["Close"].pct_change()

    # 1) rolling compounded returns
    rolling = (
        (1 + df["Return"])
        .rolling(window=window)
        .apply(lambda x: x.prod() - 1, raw=True)
        .dropna()
    )

    # 2) modified Z-scores
    z = modified_z_score(rolling.values)

    # 3) find all anomaly dates
    all_dates = rolling.index[np.abs(z) > threshold]

    # 4) prune dates so they're at least min_gap_days apart
    pruned = []
    last = None
    for d in sorted(all_dates):
        if last is None or (d - last).days >= min_gap_days:
            pruned.append(d)
            last = d

    # 5) build the output DataFrame
    anomalies = pd.DataFrame({
        "AnomalyDate": pruned,
        "RollingReturn": [rolling.loc[d] for d in pruned],
        "ModifiedZ":       [z[list(all_dates).index(d)] for d in pruned]
    })

    # 6) drop timezone info (so downstream .astype or plotting never blows up)
    #    if these timestamps happen to be tz-aware, this makes them naive.
    try:
        anomalies["AnomalyDate"] = anomalies["AnomalyDate"].dt.tz_localize(None)
    except (AttributeError, ValueError):
        # already naive or can't localize—ignore
        pass

    return anomalies


def detect_persistent_run_anomalies(df: pd.DataFrame, min_days: int, threshold: float) -> pd.DataFrame:
    """
    Detect persistent directional runs of at least min_days, flag runs whose
    cumulative return's Modified Z-Score exceeds threshold.

    Returns DataFrame with ['start_date', 'end_date', 'cumulative_return', 'direction'].
    """
    df = df.copy()
    df["Return"] = df["Close"].pct_change()

    # First pass: collect all run cumulative returns
    cum_returns = []
    direction = 0
    start_idx = 0
    run_returns = []
    for i in range(1, len(df)):
        ret = df["Return"].iat[i]
        curr_dir = 1 if ret > 0 else (-1 if ret < 0 else 0)
        if direction == 0:
            direction = curr_dir
            start_idx = i - 1
            run_returns = [ret] if ret != 0 else []
        elif curr_dir == direction or curr_dir == 0:
            if ret != 0:
                run_returns.append(ret)
        else:
            end_idx = i - 1
            length = end_idx - start_idx + 1
            if length >= min_days:
                cum_returns.append(np.prod([1 + r for r in run_returns]) - 1)
            direction = curr_dir
            start_idx = i - 1
            run_returns = [ret] if ret != 0 else []
    # final run
    end_idx = len(df) - 1
    length = end_idx - start_idx + 1
    if length >= min_days:
        cum_returns.append(np.prod([1 + r for r in run_returns]) - 1)

    if not cum_returns:
        return pd.DataFrame(columns=["start_date","end_date","cumulative_return","direction"])

    # Compute z-scores on run returns
    run_z = modified_z_score(np.array(cum_returns))

    # Second pass: collect flagged runs
    results = []
    run_idx = 0
    direction = 0
    start_idx = 0
    run_returns = []
    for i in range(1, len(df)):
        ret = df["Return"].iat[i]
        curr_dir = 1 if ret > 0 else (-1 if ret < 0 else 0)
        if direction == 0:
            direction = curr_dir
            start_idx = i - 1
            run_returns = [ret] if ret != 0 else []
        elif curr_dir == direction or curr_dir == 0:
            if ret != 0:
                run_returns.append(ret)
        else:
            end_idx = i - 1
            length = end_idx - start_idx + 1
            if length >= min_days:
                cum_ret = np.prod([1 + r for r in run_returns]) - 1
                if abs(run_z[run_idx]) > threshold:
                    results.append({
                        "start_date": df.index[start_idx],
                        "end_date": df.index[end_idx],
                        "cumulative_return": cum_ret,
                        "direction": "up" if cum_ret > 0 else "down"
                    })
                run_idx += 1
            direction = curr_dir
            start_idx = i - 1
            run_returns = [ret] if ret != 0 else []
    # final check
    if length >= min_days:
        cum_ret = np.prod([1 + r for r in run_returns]) - 1
        if abs(run_z[run_idx]) > threshold:
            results.append({
                "start_date": df.index[start_idx],
                "end_date": df.index[end_idx],
                "cumulative_return": cum_ret,
                        "direction": "up" if cum_ret > 0 else "down"
            })

    return pd.DataFrame(results)
