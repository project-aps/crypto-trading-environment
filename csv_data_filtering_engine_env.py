import pandas as pd


def get_only_top_n_data(df, n):
    """
    Returns a DataFrame with only the first 1000 rows of the input DataFrame.

    Parameters:
    df (pd.DataFrame): The input DataFrame.

    Returns:
    pd.DataFrame: A DataFrame containing only the first 1000 rows.
    """
    return df.head(n)


def get_data_from_start_and_end_date(df, start_date, end_date):
    """
    Returns a DataFrame filtered by the specified start and end dates.

    Parameters:
    df (pd.DataFrame): The input DataFrame with a 'date' column.
    start_date (str): The start date in 'YYYY-MM-DD HH:MM:SS' format.
    end_date (str): The end date in 'YYYY-MM-DD HH:MM:SS' format.

    Returns:
    pd.DataFrame: A DataFrame filtered by the specified date range.
    """
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    if "date" not in df.columns:
        raise ValueError("DataFrame must contain a 'date' column.")

    df["date"] = pd.to_datetime(df["date"])
    return df[(df["date"] >= start_date) & (df["date"] <= end_date)]


def get_first_and_last_timestamp_from_df(df):
    """
    Returns the start and end timestamps from the DataFrame.

    Parameters:
    df (pd.DataFrame): The input DataFrame with a 'date' column.

    Returns:
    tuple: A tuple containing the start and end timestamps.
    """
    if "date" not in df.columns:
        raise ValueError("DataFrame must contain a 'date' column.")

    df["date"] = pd.to_datetime(df["date"])
    if df.empty:
        raise ValueError("DataFrame is empty. Cannot get start and end timestamps.")
    return df["date"].loc[0], df["date"].iloc[-1]


def get_first_n_data_from_both_engine_and_env(engine_data_path, env_data_path, n):
    """
    Returns the first n rows of data from both engine and environment data files.

    Parameters:
    engine_data_path (str): Path to the engine data CSV file.
    env_data_path (str): Path to the environment data CSV file.
    n (int): Number of rows to return.

    Returns:
    tuple: Two DataFrames containing the first n rows from engine and environment data.
    """
    engine_df = pd.read_csv(engine_data_path, parse_dates=["date"])
    env_df = pd.read_csv(env_data_path, parse_dates=["date"])

    # get the first and last timestamps from both DataFrames
    engine_start_time, engine_end_time = get_first_and_last_timestamp_from_df(engine_df)
    env_start_time, env_end_time = get_first_and_last_timestamp_from_df(env_df)

    # get the start_time from where both DataFrames overlap
    start_time = max(engine_start_time, env_start_time)
    # end_time = min(engine_end_time, env_end_time)

    # filter both DataFrames by the start and end timestamps
    engine_df = engine_df[engine_df["date"] >= start_time]
    env_df = env_df[env_df["date"] >= start_time]

    # get only the top n rows from both DataFrames
    engine_df = get_only_top_n_data(engine_df, n)
    env_df = get_only_top_n_data(env_df, n)

    engine_df = engine_df[["date", "open", "high", "low", "close", "volume"]]

    # check the length of both DataFrames
    if len(engine_df) != len(env_df):
        raise ValueError(
            "The number of rows in engine_df and env_df do not match after filtering."
        )

    return engine_df, env_df


if __name__ == "__main__":
    # Define the paths to the engine and environment data files
    engine_data_path = "data/indicators/processed_data_with_indicators_BTCUSDT.csv"
    env_data_path = "data/indicators/scaled_data_with_indicators_BTCUSDT.csv"

    # Get the first 1000 rows from both engine and environment data
    filtered_engine_df, filtered_env_df = get_first_n_data_from_both_engine_and_env(
        engine_data_path, env_data_path, 1000
    )

    # Save the filtered DataFrames to CSV files
    filtered_engine_df.to_csv(
        "data/testings_small/BTCUSDT_engine_data_1000.csv", index=False
    )
    filtered_env_df.to_csv(
        "data/testings_small/BTCUSDT_env_scaled_data_1000.csv", index=False
    )
