import pandas as pd


class MarketData:
    """MarketData class to manage and retrieve market data for various assets.
    It loads asset data from CSV files and provides methods to access price information, timestamps, and OHLCV data.

    Parameters:
        asset_csv_paths (dict): Dictionary mapping asset names to their respective CSV file paths.
            Example:
            {
                "BTCUSDT": "data/BTCUSDT_1h.csv",
                "ETHUSDT": "data/ETHUSDT_1h.csv"
            }

    Attributes:
        asset_data (dict): Dictionary mapping asset names to their DataFrame containing market data.
        assets (list): List of asset names loaded from the provided CSV files.
    Methods:
        __init__(asset_csv_paths): Initializes the MarketData instance by loading asset data from CSV files.
        _validate_asset(asset): Validates if the given asset exists in the loaded data.
        _get_asset_df(asset): Retrieves the DataFrame for the specified asset.
        get_price(asset, timestamp): Returns the close price of the asset at the specified timestamp.
        get_first_timestamp(asset): Returns the first timestamp of the asset's data.
        get_last_timestamp(asset): Returns the last timestamp of the asset's data.
        get_next_timestamp(asset, timestamp): Returns the next timestamp after the specified timestamp for the asset.
        get_ohlcv(asset, timestamp): Returns the OHLCV data for the asset at
        the specified timestamp.
    Raises:
        ValueError: If the asset is not found in the loaded data or if the timestamp is not available.
        ValueError: If no asset data is loaded during initialization.

    """

    def __init__(self, asset_csv_paths):
        """
        asset_csv_paths: dict mapping asset name to CSV file path
            e.g. {
                "BTCUSDT": "data/BTCUSDT_1h.csv",
                "ETHUSDT": "data/ETHUSDT_1h.csv"
            }
        """
        self.asset_data = {}

        for asset, path in asset_csv_paths.items():
            df = pd.read_csv(path, parse_dates=["date"])
            df.set_index("date", inplace=True)
            df.sort_index(inplace=True)
            self.asset_data[asset] = df

        if not self.asset_data:
            raise ValueError("No asset data loaded. Please check the provided paths.")

        self.assets = list(self.asset_data.keys())

    def _validate_asset(self, asset):
        if asset not in self.asset_data:
            raise ValueError(f"Asset {asset} not found in market data.")

    def _get_asset_df(self, asset):
        self._validate_asset(asset)
        return self.asset_data[asset]

    def get_price(self, asset, timestamp):
        df = self._get_asset_df(asset)
        try:
            return df.loc[pd.to_datetime(timestamp)]["close"]
        except KeyError:
            raise ValueError(f"Close Price for {asset} at {timestamp} not found.")

    def get_first_timestamp(self, asset):
        df = self._get_asset_df(asset)
        if df.empty:
            raise ValueError(f"No data available for {asset}.")
        return df.index[0]

    def get_last_timestamp(self, asset):
        df = self._get_asset_df(asset)
        if df.empty:
            raise ValueError(f"No data available for {asset}.")
        return df.index[-1]

    def get_next_timestamp(self, asset, timestamp):
        df = self._get_asset_df(asset)
        try:
            idx = df.index.get_loc(pd.to_datetime(timestamp))
            if isinstance(idx, slice) or isinstance(idx, list):
                idx = idx.start if isinstance(idx, slice) else idx[0]
            if idx + 1 < len(df):
                return False, df.index[idx + 1]
            else:
                return True, None
        except KeyError:
            raise ValueError(f"Timestamp {timestamp} not found for {asset}.")

    def get_ohlcv(self, asset, timestamp):
        df = self._get_asset_df(asset)
        try:
            row = df.loc[pd.to_datetime(timestamp)]
            return {
                "open": row["open"],
                "high": row["high"],
                "low": row["low"],
                "close": row["close"],
                "volume": row["volume"],
            }
        except KeyError:
            raise ValueError(f"OHLCV data for {asset} at {timestamp} not found.")


if __name__ == "__main__":
    asset_paths = {
        "BTCUSDT": "data/BTCUSDT_1h_2017-08-01_2025-06-01.csv",
        "ETHUSDT": "data/ETHUSDT_1h_2017-08-01_2025-06-01.csv",
    }

    md = MarketData(asset_paths)
    print(md.assets)  # List of assets loaded

    asset = "BTCUSDT"
    timestamp = "2024-01-01 00:00:00+00:00"

    try:
        price = md.get_price(asset, timestamp)
        print(f"Price of {asset} at {timestamp}: {price}")

        first = md.get_first_timestamp(asset)
        print(f"First timestamp for {asset}: {first}")

        last = md.get_last_timestamp(asset)
        print(f"Last timestamp for {asset}: {last}")

        end_of_data, next_ts = md.get_next_timestamp(asset, first)
        print(f"Next timestamp after {first}: {next_ts}, end reached: {end_of_data}")

        ohlcv = md.get_ohlcv(asset, timestamp)
        # print(f"OHLCV at {timestamp}: {ohlcv}")
    except ValueError as e:
        print(e)
