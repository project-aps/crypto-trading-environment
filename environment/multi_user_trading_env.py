import numpy as np
import pandas as pd

import gymnasium as gym
from gymnasium import spaces

from engine.orders import TradeOrder
from engine import TradingEngine
from environment.rewards import RewardCalculator


class MultiUserSingleAssetTradingDiscreteActionEnv(gym.Env):
    """Multi-user single asset trading environment for reinforcement learning.
    This environment simulates a trading scenario where multiple users can trade a single asset
    (e.g., BTCUSDT) using different account types (spot, margin, futures).
    It has a base user that serves as a reference for calculating rewards.
    Other users can perform actions based on the base user actions. It helps in analyzing the performance of multiple users in different account types using leverages too.
    The environment uses a trading engine to manage user accounts and orders, and it calculates rewards
    based on the portfolio value of a base user.
    The environment supports different account types and allows users to perform actions such as buying, selling, or holding the asset.
    The observation space consists of a window of historical data with indicators, and the action space is discrete with three actions:
    0 = hold, 1 = buy/long, 2 = sell/short.
    Attributes:
        engine_data_path (str): Path to the raw OHLCV data for the trading engine.
        env_data_path (str): Path to the observation data with indicators.
        users_config (dict): Configuration for multiple users, including account types and initial cash.
        base_user_config (dict): Configuration for the base user, including account type and initial cash.
        asset (str): The asset to be traded (e.g., "BTCUSDT").
        window_size (int): The size of the observation window.
        reward_type (str): The type of reward to be calculated ("portfolio_return", "log_portfolio_return", "sharpe_ratio", or "hybrid").
        metadata (dict): Metadata for the environment, including render modes.

    Methods:
        __init__: Initializes the environment with the provided configurations and loads the environment data.
        reset: Resets the environment to an initial state and returns the initial observation.
        step: Takes an action in the environment and returns the next observation, reward, done status, truncated status, and additional info.
        render: Renders the current state of the environment for human observation.

    Sample Usage:
    ```python
        from environment.trading_gym_multi_user_env import MultiUserSingleAssetTradingEnv

        base_user_config = {
            "account": "futures",  # "spot", "margin", or "futures"
            "initial_cash": 10000,
            "leverage": 5,
        }
        users_config = {
            "user_1": {
                "spot": {"open_account": True, "inital_cash": 10000, "leverage": 1},
                "margin": {"open_account": True, "inital_cash": 10000, "leverage": 2},
                "futures": {"open_account": True, "inital_cash": 10000, "leverage": 5},
            },
            "user_2": {
                "spot": {"open_account": True, "inital_cash": 10000, "leverage": 1},
                "margin": {"open_account": True, "inital_cash": 10000, "leverage": 5},
                "futures": {"open_account": True, "inital_cash": 10000, "leverage": 10},
            },
        }
        env = MultiUserSingleAssetTradingEnv(
            engine_data_path="path/to/engine_data.csv",
            env_data_path="path/to/env_data.csv",
            users_config=users_config,
            base_user_config=base_user_config,
            asset="BTCUSDT",
            window_size=50,
            reward_type="portfolio_return"
        )
        obs = env.reset()
        done = False
        while not done:
            action = env.action_space.sample()  # or use a trained model to predict the action
            obs, reward, done, truncated, info = env.step(action)
            env.render()
    """

    metadata = {"render_modes": ["human"]}

    def __init__(
        self,
        engine_data_path,
        env_data_path,
        users_config,
        base_user_config,
        asset="BTCUSDT",
        window_size=50,
        reward_type="portfolio_return",
        store_daywise_portfolio_values=False,
        daywise_logs_path=None,
        engine_logs_path=None,
        verbose=False,
        bankrupt_threshold=0.01,  # Threshold for bankruptcy check
        obs_shape_type="flat",  # windowed or flat
    ):
        super(MultiUserSingleAssetTradingDiscreteActionEnv, self).__init__()
        self.asset = asset
        self.engine_data_path = engine_data_path
        self.env_data_path = env_data_path
        self.base_user_config = base_user_config
        self.users_config = users_config
        self.window_size = window_size
        self.reward_type = reward_type
        self.verbose = verbose
        self.bankrupt_threshold = bankrupt_threshold
        self.bankrupt_portfolio_value = (
            self.bankrupt_threshold * self.base_user_config["initial_cash"]
        )

        self.store_daywise_portfolio_values = store_daywise_portfolio_values
        self.daywise_logs_path = daywise_logs_path
        self.engine_logs_path = engine_logs_path

        self.obs_shape_type = obs_shape_type

        self.current_step = self.window_size - 1
        self.done = False

        self._load_env_data()
        # self._init_engine()
        # self._init_base_user()
        # self._init_users()
        # self._init_rewarder()

        self.action_space = spaces.Discrete(3)  # 0 = hold, 1 = buy/long, 2 = sell/short
        # Observation space is a window of historical data with indicators # -1 to exclude the date column
        if self.obs_shape_type == "flat":
            obs_shape = (self.window_size * (self.env_data.shape[1] - 1),)
        elif self.obs_shape_type == "windowed":
            obs_shape = (self.window_size, self.env_data.shape[1] - 1)

        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=obs_shape,
            dtype=np.float32,
        )

    #######################################################################
    def _load_env_data(self):
        df = pd.read_csv(self.env_data_path, parse_dates=["date"])
        # df = df[(df["date"] >= self.start_date) & (df["date"] <= self.end_date)]
        # self.env_data = df.reset_index(drop=True)
        # self.timestamps = self.env_data["date"].tolist()

        self.env_data = df.reset_index(drop=True)
        self.timestamps = self.env_data["date"].tolist()

    #######################################################################

    def _init_engine(self):
        self.engine = TradingEngine(
            asset_paths={self.asset: self.engine_data_path},
            update_daywise_portfolio_values=self.store_daywise_portfolio_values,
            current_ts=self.start_date,
            verbose=self.verbose,
        )

    def _init_base_user(self):
        """Initializes the base user with the provided configuration."""
        # Base user must have only one account type open

        self.engine.register_user(
            user_id="base_user",
            spot_account=self.base_user_config["account"] == "spot",
            spot_initial_cash=(
                self.base_user_config["initial_cash"]
                if self.base_user_config["account"] == "spot"
                else 0
            ),
            margin_account=self.base_user_config["account"] == "margin",
            margin_initial_cash=(
                self.base_user_config["initial_cash"]
                if self.base_user_config["account"] == "margin"
                else 0
            ),
            futures_account=self.base_user_config["account"] == "futures",
            futures_initial_cash=(
                self.base_user_config["initial_cash"]
                if self.base_user_config["account"] == "futures"
                else 0
            ),
        )

    def _init_users(self):
        for user_name, account_config in self.users_config.items():

            self.engine.register_user(
                user_id=user_name,
                spot_account=account_config["spot"]["open_account"],
                spot_initial_cash=(
                    account_config["spot"]["inital_cash"]
                    if account_config["spot"]["open_account"]
                    else 0
                ),
                margin_account=account_config["margin"]["open_account"],
                margin_initial_cash=(
                    account_config["margin"]["inital_cash"]
                    if account_config["margin"]["open_account"]
                    else 0
                ),
                futures_account=account_config["futures"]["open_account"],
                futures_initial_cash=(
                    account_config["futures"]["inital_cash"]
                    if account_config["futures"]["open_account"]
                    else 0
                ),
            )

    def _init_rewarder(self):
        """Initializes the reward calculator."""
        base_user_account_initial_cash = (
            self.engine.get_user(self._get_base_user_id())
            .get_account(self.base_user_config["account"])
            .initial_cash
        )
        self.rewarder = RewardCalculator(
            inital_portfolio_value=base_user_account_initial_cash
        )

    #######################################################################

    def _get_user(self, user_id):
        """Retrieves a user from the engine by user_id."""
        user = self.engine.get_user(user_id)
        if user is None:
            raise ValueError(f"User {user_id} not found in the engine.")
        return user

    def _get_user_account_leverage(self, user_id, account_type, user_type="user"):
        """Retrieves the leverage for a specific account type of a user."""

        if user_type == "base_user":
            account_config = self.base_user_config
            if account_config["account"] != account_type:
                raise ValueError(
                    f"Base user does not have {account_type} account type."
                )
            return account_config["leverage"]
        else:
            if user_id not in self.users_config:
                raise ValueError(f"User {user_id} not found in the configuration.")
            for user_name, account_config in self.users_config.items():
                if user_name == user_id:
                    if account_config[account_type]["open_account"]:
                        return account_config[account_type]["leverage"]

        raise ValueError(
            f"User {user_id} or account type {account_type} not found in the configuration."
        )

    def _get_base_user_id(self):
        """Returns the user ID of the base user."""
        return "base_user"

    def _get_user_account(self, user_id, account_type):
        """Retrieves a specific account type for a user."""
        user = self._get_user(user_id)
        if account_type == "spot":
            return user.get_account("spot")
        elif account_type == "margin":
            return user.get_account("margin")
        elif account_type == "futures":
            return user.get_account("futures")
        else:
            raise ValueError(f"Unknown account type: {account_type}")

    def _get_base_user_portfolio_value(self):
        """Returns the portfolio value of the base user."""
        base_user_id = self._get_base_user_id()
        base_user_account_type = self.base_user_config["account"]
        base_user_account = self._get_user_account(
            user_id=base_user_id, account_type=base_user_account_type
        )
        return base_user_account.portfolio_value

    #######################################################################

    def _get_action_based_on_mode(self, mode, action):
        if mode == "spot":
            if action == 1:
                return "buy"
            elif action == 2:
                return "sell"
        elif mode == "margin":
            if action == 1:
                return "long"
            elif action == 2:
                return "short"
        elif mode == "futures":
            if action == 1:
                return "long"
            elif action == 2:
                return "short"
        else:
            raise ValueError(f"Unknown mode: {mode} for action: {action}")

    def _get_qty_based_on_mode_side(self, mode, side):
        """Determines the quantity type based on mode and side."""
        if mode == "spot":
            if side == "buy":
                return "all_cash"
            elif side == "sell":
                return "all_holdings"
        elif mode in ["margin", "futures"]:
            return "all_cash"
        else:
            raise ValueError(f"Unknown mode: {mode} for side: {side}")

    #######################################################################

    def _place_all_buy_sell_spot_order(
        self, account_type, user_id, asset, qty, side, ts, user_type="user"
    ):
        """Places a buy or sell order for the spot account."""

        if account_type != "spot":
            raise ValueError(
                f"Account type {account_type} is not supported for spot orders."
            )

        user = self._get_user(user_id)
        spot_account = user.get_account("spot")

        if side == "buy":
            if spot_account.get_asset_holdings(asset) <= 0:
                # Place buy order
                self.engine.place_order(
                    user_id=user_id,
                    order=TradeOrder(
                        asset=asset,
                        qty=qty,
                        side="buy",
                        mode="spot",
                    ),
                    ts=ts,
                )
        elif side == "sell":
            if spot_account.get_asset_holdings(asset) > 0:
                # Place sell order
                self.engine.place_order(
                    user_id=user_id,
                    order=TradeOrder(
                        asset=asset,
                        qty=qty,
                        side="sell",
                        mode="spot",
                    ),
                    ts=ts,
                )

    def _place_all_buy_sell_margin_order(
        self, account_type, user_id, asset, qty, side, ts, user_type="user"
    ):
        """Places a buy or sell order for the margin account."""
        if account_type != "margin":
            raise ValueError(
                f"Account type {account_type} is not supported for margin orders."
            )

        user = self._get_user(user_id)
        margin_account = user.get_account("margin")
        leverage = self._get_user_account_leverage(user_id, "margin", user_type)

        long_postion_counts, short_position_counts = (
            margin_account.get_open_orders_long_short_counts_by_asset(asset)
        )

        if side == "long":
            if short_position_counts > 0:
                # Close all short position before opening long position
                self.engine.close_all_orders_by_mode_asset_side(
                    user_id=user_id,
                    mode="margin",
                    asset=asset,
                    side="short",
                    ts=ts,
                )
            if long_postion_counts == 0:
                # Place long order
                self.engine.place_order(
                    user_id=user_id,
                    order=TradeOrder(
                        asset=asset,
                        qty=qty,
                        side=side,
                        mode="margin",
                        leverage=leverage,
                    ),
                    ts=ts,
                )

        elif side == "short":
            if long_postion_counts > 0:
                # Close all long position before opening short position
                self.engine.close_all_orders_by_mode_asset_side(
                    user_id=user_id,
                    mode="margin",
                    asset=asset,
                    side="long",
                    ts=ts,
                )
            if short_position_counts == 0:
                # Place short order
                self.engine.place_order(
                    user_id=user_id,
                    order=TradeOrder(
                        asset=asset,
                        qty=qty,
                        side=side,
                        mode="margin",
                        leverage=leverage,
                    ),
                    ts=ts,
                )

    def _place_all_buy_sell_futures_order(
        self, account_type, user_id, asset, qty, side, ts, user_type="user"
    ):
        """Places a buy or sell order for the futures account."""
        if account_type != "futures":
            raise ValueError(
                f"Account type {account_type} is not supported for futures orders."
            )

        user = self._get_user(user_id)
        futures_account = user.get_account("futures")
        leverage = self._get_user_account_leverage(user_id, "futures", user_type)

        long_postion_counts, short_position_counts = (
            futures_account.get_open_orders_long_short_counts_by_asset(asset)
        )

        if side == "long":
            if short_position_counts > 0:
                # Close all short position before opening long position
                self.engine.close_all_orders_by_mode_asset_side(
                    user_id=user_id,
                    mode="futures",
                    asset=asset,
                    side="short",
                    ts=ts,
                )
            if long_postion_counts == 0:
                # Place long order
                self.engine.place_order(
                    user_id=user_id,
                    order=TradeOrder(
                        asset=asset,
                        qty=qty,
                        side=side,
                        mode="futures",
                        leverage=leverage,
                    ),
                    ts=ts,
                )

        elif side == "short":
            if long_postion_counts > 0:
                # Close all long position before opening short position
                self.engine.close_all_orders_by_mode_asset_side(
                    user_id=user_id,
                    mode="futures",
                    asset=asset,
                    side="long",
                    ts=ts,
                )
            if short_position_counts == 0:
                # Place short order
                self.engine.place_order(
                    user_id=user_id,
                    order=TradeOrder(
                        asset=asset,
                        qty=qty,
                        side=side,
                        mode="futures",
                        leverage=leverage,
                    ),
                    ts=ts,
                )

    def _place_all_buy_sell_order(
        self, account_type, user_id, asset, qty, side, ts, user_type="user"
    ):
        """Generic method to place buy/sell orders based on account type."""
        if account_type == "spot":
            self._place_all_buy_sell_spot_order(
                account_type, user_id, asset, qty, side, ts, user_type
            )
        elif account_type == "margin":
            self._place_all_buy_sell_margin_order(
                account_type, user_id, asset, qty, side, ts, user_type
            )
        elif account_type == "futures":
            self._place_all_buy_sell_futures_order(
                account_type, user_id, asset, qty, side, ts, user_type
            )
        else:
            raise ValueError(f"Unknown account type: {account_type}")

    def _place_all_buy_sell_order_for_base_user_using_action(
        self,
        action,
        ts,
        asset,
        user_type="base_user",
    ):
        """Places buy/sell orders for the base user based on the action."""

        if action not in [1, 2]:
            raise ValueError(
                f"Action {action} is not valid. Only 1 (buy) and 2 (sell) are allowed."
            )
        base_user_id = self._get_base_user_id()
        base_user_account_type = self.base_user_config["account"]
        position_type_base_user = self._get_action_based_on_mode(
            base_user_account_type, action
        )
        base_user_qty = self._get_qty_based_on_mode_side(
            base_user_account_type, position_type_base_user
        )
        self._place_all_buy_sell_order(
            base_user_account_type,
            base_user_id,
            self.asset,
            base_user_qty,
            position_type_base_user,
            ts,
            user_type="base_user",
        )

        # Base User account type

    def _place_all_buy_sell_order_for_all_normal_users_using_action(
        self,
        action,
        ts,
        asset,
        user_type="user",
    ):
        """Places buy/sell orders for all normal users based on the action."""
        if action not in [1, 2]:
            raise ValueError(
                f"Action {action} is not valid. Only 1 (buy) and 2 (sell) are allowed."
            )

        for user_name, account_config in self.users_config.items():
            user_id = user_name
            for account_type, config in account_config.items():
                if config["open_account"]:
                    position_type = self._get_action_based_on_mode(account_type, action)
                    qty = self._get_qty_based_on_mode_side(account_type, position_type)
                    self._place_all_buy_sell_order(
                        account_type,
                        user_id,
                        asset,
                        qty,
                        position_type,
                        ts,
                        user_type="user",
                    )

    #######################################################################

    def _save_engine_data(self):
        """Saves the engine data to a CSV file."""
        if self.store_daywise_portfolio_values and self.daywise_logs_path:
            self.engine.save_all_users_portfolio_values_daywise(
                file_path=self.daywise_logs_path
            )
        if self.engine_logs_path:
            # Save the engine details in json file
            self.engine.save_all_users_details(file_path=self.engine_logs_path)

    #######################################################################
    def _is_base_user_bankrupt(self):
        """Checks if the base user is bankrupt."""
        base_user_portfolio_value = self._get_base_user_portfolio_value()
        bankrupt = base_user_portfolio_value <= self.bankrupt_portfolio_value
        if bankrupt:
            print(
                f"Base user is bankrupt with portfolio value: {base_user_portfolio_value}, "
                f"minimum required portfolio value: {self.bankrupt_portfolio_value}"
            )
        return bankrupt

    #######################################################################

    def reset(self, seed=None, options=None):
        """Resets the environment to an initial state and returns the initial observation."""
        super().reset(seed=seed)

        self.current_step = self.window_size - 1
        self.start_date = self.env_data["date"].iloc[self.current_step]
        self.done = False
        self._init_engine()
        self._init_base_user()
        self._init_users()
        self._init_rewarder()
        info = {}
        return self._get_observation(), info

    def _get_observation(self):
        """Returns the current observation for the environment."""
        if self.current_step >= len(self.env_data):
            raise ValueError("Current step exceeds the length of the environment data.")

        start_idx = self.current_step - self.window_size + 1

        if self.obs_shape_type == "windowed":
            obs = (
                self.env_data.iloc[start_idx : self.current_step + 1]
                .drop(columns=["date"])
                .values
            )
            # reshape the observation to match the expected shape
            obs = obs.reshape(self.window_size, -1)
        elif self.obs_shape_type == "flat":
            obs = (
                self.env_data.iloc[start_idx : self.current_step + 1]
                .drop(columns=["date"])
                .values
            )
            # flatten the observation to match the expected shape
            # obs = obs.flatten()
            obs = obs.reshape(-1)

        return obs.astype(np.float32)

    def step(self, action):

        timestamp = self.timestamps[self.current_step]
        current_ts_engine = self.engine.get_current_timestamp()

        if timestamp != current_ts_engine:
            raise ValueError(
                f"Timestamp mismatch: {timestamp} != {current_ts_engine}. "
                "Ensure the environment is synchronized with the engine."
            )

        self.engine.step_simulation()  # Step the engine to update the current timestamp

        #######################################################################
        # Place all orders in the pipeline based on the action
        if action == 0:  # Hold action, do nothing
            pass
        if action == 1 or action == 2:  # If action is buy or sell
            ###############################################################
            # Base User Action
            self._place_all_buy_sell_order_for_base_user_using_action(
                action=action, ts=timestamp, asset=self.asset, user_type="base_user"
            )
            ###############################################################
            # Other Users accounts Action
            self._place_all_buy_sell_order_for_all_normal_users_using_action(
                action=action, ts=timestamp, asset=self.asset, user_type="user"
            )
            ###############################################################

        #######################################################################
        # Reward calculation
        current_base_user_portfolio_value = self._get_base_user_portfolio_value()
        self.rewarder.update(current_base_user_portfolio_value)
        reward = self.rewarder.get_reward_by_type(reward_type=self.reward_type)

        #######################################################################
        # updation steps
        self.current_step += 1
        engine_done = self.engine.update_current_timestamp()

        ######################################

        if (
            self.current_step >= len(self.env_data)
            or engine_done
            or self._is_base_user_bankrupt()
        ):
            self.done = True
            # self.current_step -= 1  # Adjust current step to the last valid step
            # if engine_done:
            #     print(f"Engine done !!, current step: {self.current_step}, ")

            # Save the engine data in json file
            self._save_engine_data()
            return None, reward, True, False, {}

        obs = self._get_observation() if not self.done else None
        return obs, reward, self.done, False, {}

    def render(self, mode="human"):
        """Renders the environment."""
        if mode == "human":
            if self.current_step >= len(self.env_data):
                print("No more data to render.")
                return

            print(
                f"Step: {self.current_step}, Timestamp: {self.timestamps[self.current_step]}, Base User Portfolio Value: {self._get_base_user_portfolio_value()}"
            )
            # print(f"Current Observation: {self._get_observation()}")
            # print normal user accounts portfolio values
            for user_name, account_config in self.users_config.items():
                user = self._get_user(user_name)
                for account_type in account_config.keys():
                    account = user.get_account(account_type)
                    print(
                        f"User: {user_name}, Account Type: {account_type}, Portfolio Value: {account.portfolio_value}"
                    )
        else:
            raise ValueError(f"Unknown render mode: {mode}")

    def close(self):
        """Closes the environment."""
        # self.engine.close()
        print("Environment closed.")
