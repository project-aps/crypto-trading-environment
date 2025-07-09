import numpy as np
import pandas as pd


def sma(df, period=14):
    """Simple Moving Average"""
    df[f"sma_{period}"] = df["close"].rolling(window=period).mean()
    return [f"sma_{period}"], df


def ema(df, period=14):
    """Exponential Moving Average"""
    df[f"ema_{period}"] = df["close"].ewm(span=period, adjust=False).mean()
    return [f"ema_{period}"], df


def rsi(df, period=14):
    """Relative Strength Index"""
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    df[f"rsi_{period}"] = 100 - (100 / (1 + rs))
    return [f"rsi_{period}"], df


def macd(df, short_period=12, long_period=26, signal_period=9):
    """Moving Average Convergence Divergence"""
    short_ema = df["close"].ewm(span=short_period, adjust=False).mean()
    long_ema = df["close"].ewm(span=long_period, adjust=False).mean()
    df["macd"] = short_ema - long_ema
    df["macd_signal"] = df["macd"].ewm(span=signal_period, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]
    return ["macd", "macd_signal", "macd_hist"], df


def bollinger_bands(df, period=20, num_std=2):
    """Bollinger Bands"""
    sma = df["close"].rolling(window=period).mean()
    std = df["close"].rolling(window=period).std()
    df["bb_upper"] = sma + (num_std * std)
    df["bb_lower"] = sma - (num_std * std)
    return ["bb_upper", "bb_lower"], df


def atr(df, period=14):
    """Average True Range"""
    high_low = df["high"] - df["low"]
    high_close = np.abs(df["high"] - df["close"].shift())
    low_close = np.abs(df["low"] - df["close"].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["atr"] = tr.rolling(window=period).mean()
    return ["atr"], df


def stochastic_oscillator(df, k_period=14, d_period=3):
    """Stochastic Oscillator"""
    low_min = df["low"].rolling(window=k_period).min()
    high_max = df["high"].rolling(window=k_period).max()
    df["%K"] = 100 * (df["close"] - low_min) / (high_max - low_min)
    df["%D"] = df["%K"].rolling(window=d_period).mean()
    return ["%K", "%D"], df


def williams_r(df, period=14):
    """Williams %R"""
    high_max = df["high"].rolling(window=period).max()
    low_min = df["low"].rolling(window=period).min()
    df["williams_r"] = -100 * (high_max - df["close"]) / (high_max - low_min)
    return ["williams_r"], df


def cci(df, period=20):
    """Commodity Channel Index"""
    tp = (df["high"] + df["low"] + df["close"]) / 3
    sma_tp = tp.rolling(window=period).mean()
    mad = (tp - sma_tp).abs().rolling(window=period).mean()
    df["cci"] = (tp - sma_tp) / (0.015 * mad)
    return ["cci"], df


def adx_old(df, period=14):
    """Average Directional Index"""
    high_diff = df["high"].diff()
    low_diff = df["low"].diff()
    tr = pd.concat([high_diff, low_diff, df["close"].diff()], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    plus_dm = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0)
    minus_dm = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0)
    plus_di = 100 * (plus_dm.rolling(window=period).sum() / atr)
    minus_di = 100 * (minus_dm.rolling(window=period).sum() / atr)
    df["adx"] = (
        100
        * (np.abs(plus_di - minus_di) / (plus_di + minus_di))
        .rolling(window=period)
        .mean()
    )
    return ["adx"], df


def adx(df, period=14):
    """Calculate the Average Directional Index (ADX)"""
    high = df["high"]
    low = df["low"]
    close = df["close"]

    # True Range
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # ATR
    atr = tr.rolling(window=period).mean()

    # +DM and -DM
    up_move = high.diff()
    down_move = low.diff()

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)

    plus_dm = pd.Series(plus_dm, index=df.index)
    minus_dm = pd.Series(minus_dm, index=df.index)

    plus_di = 100 * (plus_dm.rolling(window=period).sum() / atr)
    minus_di = 100 * (minus_dm.rolling(window=period).sum() / atr)

    dx = (np.abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    adx = dx.rolling(window=period).mean()

    df["adx"] = adx

    return ["adx"], df


def obv(df, period=20):
    """On-Balance Volume"""
    df["obv"] = np.where(
        df["close"] > df["close"].shift(1), df["volume"], -df["volume"]
    ).cumsum()
    return ["obv"], df


def ichimoku(df):
    """Ichimoku Cloud"""
    nine_period_high = df["high"].rolling(window=9).max()
    nine_period_low = df["low"].rolling(window=9).min()
    df["tenkan_sen"] = (nine_period_high + nine_period_low) / 2

    period26_high = df["high"].rolling(window=26).max()
    period26_low = df["low"].rolling(window=26).min()
    df["kijun_sen"] = (period26_high + period26_low) / 2

    df["senkou_span_a"] = ((df["tenkan_sen"] + df["kijun_sen"]) / 2).shift(26)
    df["senkou_span_b"] = (
        (df["high"].rolling(window=52).max() + df["low"].rolling(window=52).min()) / 2
    ).shift(26)

    df["chikou_span"] = df["close"].shift(-26)
    return [
        "tenkan_sen",
        "kijun_sen",
        "senkou_span_a",
        "senkou_span_b",
        "chikou_span",
    ], df


def parabolic_sar(df, acceleration=0.02, maximum=0.2):
    """Parabolic SAR"""
    df["sar"] = 0.0
    df["sar_direction"] = 1  # 1 for uptrend, -1 for downtrend
    df["sar_extreme"] = df["high"].rolling(window=2).max()  # Extreme point
    df["sar_af"] = acceleration  # Acceleration factor

    for i in range(1, len(df)):
        if df["sar_direction"].iloc[i - 1] == 1:  # Uptrend
            df["sar"].iloc[i] = df["sar"].iloc[i - 1] + df["sar_af"].iloc[i - 1] * (
                df["sar_extreme"].iloc[i - 1] - df["sar"].iloc[i - 1]
            )
            if df["low"].iloc[i] < df["sar"].iloc[i]:
                df["sar_direction"].iloc[i] = -1
                df["sar_extreme"].iloc[i] = df["low"].iloc[i]
                df["sar_af"].iloc[i] = acceleration
        else:  # Downtrend
            df["sar"].iloc[i] = df["sar"].iloc[i - 1] + df["sar_af"].iloc[i - 1] * (
                df["sar_extreme"].iloc[i - 1] - df["sar"].iloc[i - 1]
            )
            if df["high"].iloc[i] > df["sar"].iloc[i]:
                df["sar_direction"].iloc[i] = 1
                df["sar_extreme"].iloc[i] = df["high"].iloc[i]
                df["sar_af"].iloc[i] = acceleration

        # Limit the acceleration factor
        if df["sar_af"].iloc[i] < maximum:
            df["sar_af"].iloc[i] += acceleration

    return ["sar", "sar_direction", "sar_extreme", "sar_af"], df


def truncate(x):
    if isinstance(x, float):
        return np.floor(x * 100) / 100
    return x


def apply_all_indicators(df):
    """Apply all indicators to the DataFrame."""
    columns_array_sma, df = sma(df)
    columns_array_ema, df = ema(df)
    columns_array_rsi, df = rsi(df)
    columns_array_macd, df = macd(df)
    columns_array_bb, df = bollinger_bands(df)
    columns_array_atr, df = atr(df)
    columns_array_stoch, df = stochastic_oscillator(df)
    columns_array_williams, df = williams_r(df)
    columns_array_cci, df = cci(df)
    columns_array_adx, df = adx(df)
    columns_array_obv, df = obv(df)
    # columns_array_ichimoku, df = ichimoku(df)
    # columns_array_sar, df = parabolic_sar(df)

    df = df.applymap(truncate)

    # indicators_names_with_columns = {
    indicators_names_with_columns = {
        "sma": columns_array_sma,
        "ema": columns_array_ema,
        "rsi": columns_array_rsi,
        "macd": columns_array_macd,
        "bollinger_bands": columns_array_bb,
        "atr": columns_array_atr,
        "stochastic_oscillator": columns_array_stoch,
        "williams_r": columns_array_williams,
        "cci": columns_array_cci,
        "adx": columns_array_adx,
        "obv": columns_array_obv,
        # "ichimoku": columns_array_ichimoku,
        # "parabolic_sar": columns_array_sar,
    }
    all_indicator_columns = [
        col for cols in indicators_names_with_columns.values() for col in cols
    ]
    all_indicator_columns = list(set(all_indicator_columns))

    # Ensure the DataFrame has the required columns
    if not all(col in df.columns for col in all_indicator_columns):
        raise ValueError(
            f"DataFrame is missing required columns: {all_indicator_columns}"
        )
    # Reorder the DataFrame to have OHLCV first, then all indicators
    if not all(col in df.columns for col in ["open", "high", "low", "close", "volume"]):
        raise ValueError(
            "DataFrame must contain 'open', 'high', 'low', 'close', and 'volume' columns."
        )
    # Reorder the DataFrame to have OHLCV first, then all indicators
    df = df[["open", "high", "low", "close", "volume"] + all_indicator_columns]

    # Drop any rows with NaN values
    df.dropna(inplace=True)
    # Reset the index
    # df.reset_index(inplace=True)

    return all_indicator_columns, df


from sklearn.preprocessing import StandardScaler
import joblib


def apply_standard_scaler(df, scaler_path="scaler.pkl"):
    """Apply StandardScaler to specified columns in the DataFrame."""
    df = df.reset_index()
    columns = df.columns.tolist()
    print(columns)
    scaler = StandardScaler()

    # all columns except 'date'
    if "date" in df.columns:
        columns = [col for col in columns if col != "date"]

    df[columns] = scaler.fit_transform(df[columns])

    # Save the scaler to a file
    joblib.dump(scaler, scaler_path)

    return df


if __name__ == "__main__":
    # Example usage
    df = pd.read_csv(
        "C:/Users/hp/Desktop/trading_project/workings/crypto_trading_environment/trading_engine/data/BTCUSDT_1h_2017-08-01_2025-06-01.csv",
        parse_dates=True,
        index_col=0,
    )
    df.sort_index(inplace=True)
    df = df[["open", "high", "low", "close", "volume"]]

    # take only 500 rows for testing
    # df = df.head(500)
    indicators, processed_df = apply_all_indicators(df)
    print(processed_df)
    print("Indicators applied:", indicators)
    # Save the processed DataFrame to a new CSV file
    # processed_df.to_csv("processed_data_with_indicators_BTCUSDT.csv")

    # get the rows upto date 2023-12-31 23:00:00+00:00
    processed_df = processed_df[processed_df.index <= "2023-12-31 23:00:00+00:00"]

    # Apply standard scaler
    scaled_df = apply_standard_scaler(processed_df)
    # print(scaled_df)
    # Save the scaled DataFrame to a new CSV file
    scaled_df.to_csv("scaled_data_with_indicators_BTCUSDT.csv", index=False)
