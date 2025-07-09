import pandas as pd
import pandas_ta as ta
from sklearn.preprocessing import StandardScaler
import joblib

"""
aberration, above, above_value, accbands, ad, adosc, adx, alma, amat, ao, aobv, apo, aroon, atr, bbands, below, below_value, bias, bop, brar, cci, cdl_pattern, cdl_z, cfo, cg, chop, cksp, cmf, cmo, coppock, cross, cross_value, cti, decay, decreasing, dema, dm, donchian, dpo, ebsw, efi, ema, entropy, eom, er, eri, fisher, fwma, ha, hilo, hl2, hlc3, hma, hwc, hwma, ichimoku, increasing, inertia, jma, kama, kc, kdj, kst, kurtosis, kvo, linreg, log_return, long_run, macd, mad, massi, mcgd, median, mfi, midpoint, midprice, mom, natr, nvi, obv, ohlc4, pdist, percent_return, pgo, ppo, psar, psl, pvi, pvo, pvol, pvr, pvt, pwma, qqe, qstick, quantile, rma, roc, rsi, rsx, rvgi, rvi, short_run, sinwma, skew, slope, sma, smi, squeeze, squeeze_pro, ssf, stc, stdev, stoch, stochrsi, supertrend, swma, t3, td_seq, tema, thermo, tos_stdevall, trima, trix, true_range, tsi, tsignals, ttm_trend, ui, uo, variance, vhf, vidya, vortex, vp, vwap, vwma, wcp, willr, wma, xsignals, zlma, zscore
"""


def add_indicators(df):
    indicator_columns = []

    # EMA
    df["EMA_20"] = ta.ema(df["close"], length=20)
    indicator_columns.append("EMA_20")

    # SMA
    df["SMA_20"] = ta.sma(df["close"], length=20)
    indicator_columns.append("SMA_20")

    # RSI
    df["RSI_14"] = ta.rsi(df["close"], length=14)
    indicator_columns.append("RSI_14")

    # MACD
    macd = ta.macd(df["close"], fast=12, slow=26, signal=9)
    df = pd.concat([df, macd], axis=1)
    indicator_columns += macd.columns.tolist()

    # OBV
    df["OBV"] = ta.obv(close=df["close"], volume=df["volume"])
    indicator_columns.append("OBV")

    # ATR
    df["ATR_14"] = ta.atr(high=df["high"], low=df["low"], close=df["close"], length=14)
    indicator_columns.append("ATR_14")

    # Bollinger Bands
    bb = ta.bbands(df["close"], length=20, std=2)
    df = pd.concat([df, bb], axis=1)
    indicator_columns += bb.columns.tolist()

    # drop NaN values
    df.dropna(inplace=True)

    return df, indicator_columns


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
        "C:/Users/hp/Desktop/trading_project/workings/crypto_trading_environment/crypto_trading_environment/data/BTCUSDT_1h_2017-08-01_2025-06-01.csv",
        parse_dates=True,
        index_col=0,
    )
    df.sort_index(inplace=True)
    df = df[["open", "high", "low", "close", "volume"]]

    # take only 500 rows
    # df = df.tail(500)

    df_with_indicators, indicators_columns = add_indicators(df)
    print(df_with_indicators)

    # Save the DataFrame with indicators to a new CSV file
    # df_with_indicators.to_csv("ta_btcusdt_indicators.csv", index=True)
