import yfinance as yf
import os

def fetch_and_save_stock_data(ticker: str, period="1y", interval="1d"):
    print(f"Fetching data for {ticker}...")
    stock = yf.Ticker(ticker)
    df = stock.history(period=period, interval=interval)

    if df.empty:
        print("No data found.")
        return

    os.makedirs("../data", exist_ok=True)
    path = f"data/{ticker}_history.csv" 
    os.makedirs("data", exist_ok=True)
    df.to_csv(path)
    print(f"Saved {ticker} data to {path}")

# Example usage
if __name__ == "__main__":
    fetch_and_save_stock_data("AAPL")
