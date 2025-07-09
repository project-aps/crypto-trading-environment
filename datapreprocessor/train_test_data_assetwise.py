import pandas as pd
import pandas_ta as ta
from sklearn.preprocessing import StandardScaler
import os
import joblib
import json


# --- STEP 1: Load and add indicators ---
def load_and_add_indicators(csv_path):
    df = pd.read_csv(csv_path, parse_dates=[DATE_COL])
    # df[DATE_COL] = pd.to_datetime(df[DATE_COL])
    # df.sort_values(DATE_COL, inplace=True)

    # Add technical indicators
    # Core indicators
    df.ta.ema(length=9, append=True)  # 9-period Exponential Moving Average Short Term
    df.ta.ema(length=21, append=True)  # 21-period Exponential Moving Average Mid Term
    df.ta.ema(length=50, append=True)  # 50-period Exponential Moving  Long Term
    df.ta.rsi(length=14, append=True)  # Relative Strength Index
    df.ta.macd(append=True)  # Moving Average Convergence Divergence
    df.ta.obv(append=True)  # On-Balance Volume
    df.ta.atr(length=14, append=True)  # Average True Range

    # Volatility and momentum indicators
    df.ta.mfi(length=14, append=True)  # Money Flow Index
    df.ta.adx(length=14, append=True)  # Average Directional Index
    df.ta.bbands(length=20, append=True)  # Bollinger Bands
    df.ta.stoch(append=True)  # Stochastic Oscillator
    df.ta.willr(length=14, append=True)  # Williams %R
    df.ta.cci(length=20, append=True)  # Commodity Channel Index

    # psar = ta.psar(df["high"], df["low"], df["close"])
    # print(psar.shape)
    # print(psar)

    # df.ta.psar(append=True)  # Parabolic SAR

    df.dropna(inplace=True)  # Drop rows with NaNs due to indicator lag
    # get the first date and last date
    start_date = df[DATE_COL].iloc[0]
    end_date = df[DATE_COL].iloc[-1]

    return df.reset_index(drop=True), start_date, end_date


# --- STEP 2: Split into train/test using date ---
def split_train_test(df, train_start, train_end, test_start, test_end):
    train = df[(df[DATE_COL] >= train_start) & (df[DATE_COL] <= train_end)].copy()
    test = df[(df[DATE_COL] >= test_start) & (df[DATE_COL] <= test_end)].copy()
    return train, test


# --- STEP 3: Create engine_data (OHLCV + date only) ---
def get_engine_data(df):
    return df[[DATE_COL, "open", "high", "low", "close", "volume"]].copy()


# --- STEP 4: Create env_data (OHLCV + indicators), normalized ---
def get_env_data(df, scaler=None, fit_scaler=False):
    # Include ohlcv + indicators (drop date column)
    features = df.drop(columns=[DATE_COL])
    if fit_scaler:
        scaler = StandardScaler()
        scaled = scaler.fit_transform(features)
        joblib.dump(scaler, SCALER_FILE)
    else:
        if scaler is None:
            if not os.path.exists(SCALER_FILE):
                raise FileNotFoundError("Scaler not found. Fit on training data first.")
            scaler = joblib.load(SCALER_FILE)
        scaled = scaler.transform(features)

    scaled_df = pd.DataFrame(scaled, columns=features.columns)
    scaled_df[DATE_COL] = df[DATE_COL]
    return scaled_df[[DATE_COL] + list(features.columns)]


# --- STEP 5: Master pipeline ---
def preprocess_pipeline(csv_path, train_start, train_end, test_start, test_end):
    df, _, _ = load_and_add_indicators(csv_path)

    train_df, test_df = split_train_test(
        df, train_start, train_end, test_start, test_end
    )

    # Train sets
    train_engine = get_engine_data(train_df)
    train_env = get_env_data(train_df, fit_scaler=True)

    # Test sets
    test_engine = get_engine_data(test_df)
    test_env = get_env_data(test_df)

    # Ensure lengths and order
    assert len(train_engine) == len(train_env), "Train lengths do not match"
    assert len(test_engine) == len(test_env), "Test lengths do not match"

    # assert all(train_engine[DATE_COL] == train_env[DATE_COL]), "Train datetime mismatch"
    # assert all(test_engine[DATE_COL] == test_env[DATE_COL]), "Test datetime mismatch"

    return train_engine, train_env, test_engine, test_env


# --- Example Execution ---
if __name__ == "__main__":
    # --- CONFIG ---
    TRAIN_START = "2017-08-19 05:00:00+00:00"
    TRAIN_END = "2023-12-31 23:00:00+00:00"
    TEST_START = "2024-01-01 00:00:00+00:00"
    TEST_END = "2025-05-31 23:00:00+00:00"

    # --- CONFIG ---
    CSV_FILE = "data/BTCUSDT_1h_2017-08-01_2025-06-01.csv"
    SCALER_FILE = "data/final_data/btcusdt/env_data_scaler_2017_08_19_2023_12_31.pkl"
    DATE_COL = "date"

    train_engine, train_env, test_engine, test_env = preprocess_pipeline(
        CSV_FILE, TRAIN_START, TRAIN_END, TEST_START, TEST_END
    )

    # save the processed dataframes
    train_engine.to_csv(
        "data/final_data/btcusdt/btcusdt_train_engine_data.csv", index=False
    )
    train_env.to_csv("data/final_data/btcusdt/btcusdt_train_env_data.csv", index=False)
    test_engine.to_csv(
        "data/final_data/btcusdt/btcusdt_test_engine_data.csv", index=False
    )
    test_env.to_csv("data/final_data/btcusdt/btcusdt_test_env_data.csv", index=False)

    # Also save configurations
    config = {
        "train_start": TRAIN_START,
        "train_end": TRAIN_END,
        "test_start": TEST_START,
        "test_end": TEST_END,
        "csv_file": CSV_FILE,
        "scaler_file": SCALER_FILE,
        "train_engine_shape": train_engine.shape,
        "train_env_shape": train_env.shape,
        "test_engine_shape": test_engine.shape,
        "test_env_shape": test_env.shape,
    }
    config_file = "data/final_data/btcusdt/preprocess_config.json"
    with open(config_file, "w") as f:
        json.dump(config, f, indent=4)

    # # Example of output
    print("Train engine shape:", train_engine.shape)
    print("Train env shape:", train_env.shape)
    print("Test engine shape:", test_engine.shape)
    print("Test env shape:", test_env.shape)

    ####################################################################
    # df, start_date, end_date = load_and_add_indicators(
    #     "data/BTCUSDT_1h_2017-08-01_2025-06-01.csv"
    # )
    # df.to_csv("data/final_data/BTCUSDT_indicators.csv", index=False)
    # print(df.head())
    # print(df.columns)

    # print(start_date)
    # print(end_date)
