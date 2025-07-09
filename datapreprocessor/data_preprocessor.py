# dataset.py
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from typing import List, Callable, Optional

from datapreprocessor.indicators import apply_all_indicators


class DatasetProcessor:
    def __init__(
        self,
        csv_paths,
        fillna_method="fill_na",
    ):
        self.csv_paths = csv_paths
        self.raw_features = ["open", "high", "low", "close", "volume"]
        self.indicators = None
        self.fillna_method = fillna_method
        self.scaler = StandardScaler()

    def load_and_process(self):
        df_list = []
        for path in self.csv_paths:
            df = pd.read_csv(path, parse_dates=True, index_col=0)
            df.sort_index(inplace=True)
            # Ensure the DataFrame has the required columns
            if not all(col in df.columns for col in self.raw_features):
                raise ValueError(
                    f"CSV file {path} is missing required columns: {self.raw_features}"
                )
            df = df[
                self.raw_features
                + [col for col in df.columns if col not in self.raw_features]
            ]  # only include raw_features
            df = self._add_indicators(df)
            df = self._preprocess(df)
            df_list.append(df)

        # TODO: take proper care of concatenation
        return pd.concat(df_list).dropna()

    def _add_indicators(self, df):
        # for fn in self.indicators:
        #     df = fn(df)

        indicators, df = apply_all_indicators(df)
        if not indicators:
            raise ValueError(
                "No indicators were applied. Check your indicator functions."
            )

        self.indicators = indicators
        return df

    def _preprocess(self, df):
        if self.fillna_method == "ffill":
            df.fillna(method="ffill", inplace=True)
        elif self.fillna_method == "bfill":
            df.fillna(method="bfill", inplace=True)
        else:
            df.fillna(self.fillna_method, inplace=True)
        return df

    def fit_normalizer(self, df, feature_cols):
        self.scaler.fit(df[feature_cols])

    def normalize(self, df, feature_cols):
        return self.scaler.transform(df[feature_cols])

    def get_window(self, df, start, window, feature_cols):
        slice_df = df.iloc[start - window : start]
        norm_features = self.normalize(slice_df, feature_cols)
        ohlcv = slice_df[["open", "high", "low", "close", "volume"]].values
        return np.hstack([ohlcv, norm_features])
