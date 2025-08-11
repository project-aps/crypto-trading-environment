import pandas as pd
import numpy as np
import mplfinance as mpf
import matplotlib.pyplot as plt


def load_and_parse_data(file_path):
    """Load CSV and parse datetime index."""
    df = pd.read_csv(file_path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    df = df.set_index("date")
    return df


def is_strictly_increasing_index(df):
    """
    Checks if the DataFrame's index (assumed to be datetime) is strictly increasing.

    Returns:
        bool: True if strictly increasing, False otherwise.
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        raise TypeError("Index must be a DatetimeIndex.")

    flag = df.index.is_monotonic_increasing and not df.index.has_duplicates
    return flag


def check_hourly_continuity(df):
    """
    Checks if each row is exactly one hour after the previous.
    If any hours are missing, prints them.

    Returns:
        bool: True if continuous hourly data, False if gaps are found.
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        raise TypeError("Index must be a DatetimeIndex.")

    # Sort index just to be safe
    df = df.sort_index()

    # Generate full expected hourly range
    full_range = pd.date_range(start=df.index.min(), end=df.index.max(), freq="h")

    # Find missing timestamps
    missing_hours = full_range.difference(df.index)

    if missing_hours.empty:
        print("✅ Data has continuous hourly timestamps with no gaps.")
        return True, []
    else:
        print(f"❌ Missing {len(missing_hours)} hourly timestamps:")

        return False, missing_hours


def enforce_frequency(df, freq="h"):
    """Set frequency and find missing timestamps."""
    df = df[~df.index.duplicated(keep="first")]
    df = df.asfreq(freq)
    missing_timestamps = df[df.isna().any(axis=1)]
    return df, missing_timestamps


def check_missing_values(df):
    """Check and report missing values."""
    print("Missing Values Report:")
    print(df.isna().sum())
    return df.isna().sum()


def check_data_consistency(df):
    """Check low <= open/close <= high and volume >= 0."""
    inconsistent_rows = df[
        (df["low"] > df["open"])
        | (df["low"] > df["close"])
        | (df["high"] < df["open"])
        | (df["high"] < df["close"])
        | (df["volume"] < 0)
    ]
    if not inconsistent_rows.empty:
        print(f"\nInconsistent rows found: {len(inconsistent_rows)}")
        print(inconsistent_rows)
    else:
        print("✅ All data rows are consistent.")
    return inconsistent_rows


def impute_missing_values(df, volume_method="interpolate", ohlc_method="interpolate"):
    """Handle missing values via forward fill or interpolation."""

    if ohlc_method not in ["ffill", "interpolate"]:
        raise ValueError("Method must be 'ffill' or 'interpolate'.")

    if volume_method not in ["0", "ffill", "interpolate"]:
        raise ValueError("Volume method must be '0' or 'ffill' or 'interpolate'.")

    # volume imputation
    if volume_method == "0":
        df["volume"] = df["volume"].fillna(0)
        print("✅ Missing volume values set to 0.")
    elif volume_method == "ffill":
        df["volume"] = df["volume"].fillna(method="ffill")
        print("✅ Forward fill applied to volume column.")
    elif volume_method == "interpolate":
        # Interpolate missing values for volume
        df["volume"] = df["volume"].interpolate(method="time")
        print("✅ Interpolation applied to volume column.")

    # OHLCV imputation
    if ohlc_method == "ffill":
        df["open"] = df["open"].fillna(method="ffill")
        df["high"] = df["high"].fillna(method="ffill")
        df["low"] = df["low"].fillna(method="ffill")
        df["close"] = df["close"].fillna(method="ffill")

        print("✅ Forward fill applied to OHLC columns.")
    elif ohlc_method == "interpolate":
        # Interpolate missing values for OHLCV columns
        df[["open", "high", "low", "close"]] = df[
            ["open", "high", "low", "close"]
        ].interpolate(method="time")
        print("✅ Interpolation applied to OHLC columns.")

    return df


def plot_timeseries(df, column="close"):
    """Plot the time series to visually inspect."""
    df[column].plot(title=f"{column} over Time", figsize=(15, 4))
    plt.xlabel("Time")
    plt.ylabel(column)
    plt.grid(True)
    plt.show()


def plot_ohlcv_candlestick(df, title="Candlestick Chart"):
    """
    Plot OHLCV data using mplfinance with volume.
    Expects df with columns: ['open', 'high', 'low', 'close', 'volume'] and a datetime index.
    """
    # Ensure datetime index
    if not isinstance(df.index, pd.DatetimeIndex):
        df = df.copy()
        df.index = pd.to_datetime(df.index)

    # plot only last 1000 rows for performance
    if len(df) > 1000:
        df = df.iloc[-1000:]

    # Rename to standard format if needed
    df_plot = df[["open", "high", "low", "close", "volume"]].copy()
    df_plot.columns = ["Open", "High", "Low", "Close", "Volume"]

    # Plot using mplfinance
    mpf.plot(
        df_plot,
        type="candle",
        volume=True,
        style="yahoo",  # Options: 'yahoo', 'charles', 'nightclouds', etc.
        title=title + " (Last 1000 Rows)",
        # mav=(5, 10),  # Moving averages
        figsize=(15, 12),
        warn_too_much_data=100000,
    )


def summarize_data(df):
    """Print summary statistics."""
    print("\nData Summary:")
    print(df.describe())


def preprocess_crypto_data(file_path):
    #########################################################################
    print("✅ Loading and parsing data...")
    df = load_and_parse_data(file_path)

    #########################################################################
    print("✅ Checking if index is strictly increasing...")
    if not is_strictly_increasing_index(df):
        print("❌ Index is not strictly increasing or has duplicates.")
        # raise ValueError("Index is not strictly increasing or has duplicates.")
    else:
        print("✅ Index is strictly increasing.")

    #########################################################################
    print("✅ Checking for continuous hourly data...")
    continuous, missing_hours = check_hourly_continuity(df)
    if not continuous:
        # raise ValueError("Data is not continuous hourly. Please check the data.")
        if not missing_hours.empty:
            print(missing_hours)
    else:
        print("✅Data is continuous hourly.")

    #########################################################################
    print("✅ Checking for missing values...")
    missing_values = check_missing_values(df)
    if missing_values.sum().sum() > 0:
        print("❌ Missing values found in the dataset.")
        # raise ValueError("Missing values found in the dataset. Please handle them.")
    else:
        print("✅ No missing values found in the dataset.")

    #########################################################################
    print("✅ Checking for data consistency...")
    inconsistent = check_data_consistency(df)

    #########################################################################
    # print("✅ Imputing missing values...")
    df = impute_missing_values(df)

    #########################################################################
    # print("✅ Plotting data...")
    # plot_timeseries(df, column="close")
    plot_ohlcv_candlestick(df, title="OHLCV Candlestick Chart")

    #########################################################################
    # print("✅ Summary statistics:")
    summarize_data(df)

    return df


# Example usage:
if __name__ == "__main__":
    file_path = (
        "data/final_data/btcusdt/BTCUSDT_ohlcv.csv"  # Replace with your CSV file path
    )
    processed_df = preprocess_crypto_data(file_path)
