# trading_engine.py
from engine.accounts.fee_calculator import FeeCalculator
from configs.config import *
from engine.users import User
from engine.market_data import MarketData
from configs.constants import (
    LONG_POSITIONS,
    SHORT_POSITIONS,
)
import json


class TradingEngine:
    """A class to simulate a trading engine that manages users, accounts, and orders.
    It handles market data, fees, and liquidations, allowing users to place and close orders across different account types (spot, margin, futures).

    Parameters:
        asset_paths (Dict): Dictionary mapping asset names to their respective CSV file paths.
            Example:
            {
                "BTCUSDT": "data/BTCUSDT_1h.csv",
                "ETHUSDT": "data/ETHUSDT_1h.csv"
            }
        current_ts (datetime, optional): Initial timestamp for the simulation. If not provided, defaults to the first timestamp of the first asset.

    Attributes:
        md (MarketData): Market data object to fetch asset prices.
        fee_calc (FeeCalculator): Fee calculator object to compute trading fees.
        users (dict): Dictionary of registered users, keyed by user ID.
        assets (list): List of assets available in the market data.
        current_ts (datetime): Current timestamp for the simulation, defaults to the first timestamp of the first asset.
    Methods:
        register_user(user_id, spot_account=False, margin_account=False, futures_account=False, spot_initial_cash=100000, margin_initial_cash=100000, futures_initial_cash=100000):
            Registers a new user with specified account types and initial cash amounts.
        get_user(user_id):
            Retrieves a registered user by user ID.
        place_order(user_id, order, ts):
            Places an order for a user at the current timestamp.
        close_order(user_id, mode, order_id, ts):
            Closes an order for a user in the specified account mode at the current timestamp.
        close_all_orders(user_id, mode, ts):
            Closes all open orders for a user in the specified account mode at the current timestamp.
        step_simulation():
            Advances the simulation by one step, checking for liquidations and updating portfolio values.
        update_current_timestamp():
            Updates the current timestamp to the next available timestamp in the market data.
        check_liquidations():
            Checks all users' open orders for potential liquidations based on current market prices.
        update_portfolio_values():
            Updates the portfolio values for all users based on current market prices and fees.
        get_current_timestamp():
            Returns the current timestamp of the simulation.
        save_all_users_details(file_path="users_details.json"):
            Saves all users' details, including accounts, portfolio values, open orders, and history, to a JSON file.

        Usage:
        engine = TradingEngine(asset_paths=["path/to/asset_data.csv"])
        engine.register_user("user1", spot_account=True, margin_account=True, futures_account=True)
        order = TradeOrder(asset="BTCUSDT", qty=1.0, side="buy", mode="spot")
        done = False
        while not done:
            current_ts = engine.get_current_timestamp()
            engine.step_simulation()
            engine.place_order("user1", order, current_ts)
            done = engine.update_current_timestamp()

        engine.save_all_users_details(file_path="logs/users_details.json")
        print(engine.get_user("user1").get_total_portfolio_value())
    """

    def __init__(
        self,
        asset_paths,
        current_ts=None,
        update_daywise_portfolio_values=False,
        verbose=False,
    ):
        self.md = MarketData(asset_paths)
        self.fee_calc = FeeCalculator(
            FEE_STRUCTURE, BORROW_INTEREST_HOURLY, FUNDING_FEE_EVERY_8H
        )
        self.verbose = verbose  # Set to True for verbose logging
        self.users = {}
        self.assets = self.md.assets
        self.current_ts = (
            current_ts if current_ts else self.md.get_first_timestamp(self.assets[0])
        )
        self.update_daywise_portfolio_values = update_daywise_portfolio_values

    def reset(self):
        """Resets the trading engine to its initial state.
        This method clears all registered users and resets the current timestamp to the first available timestamp in the market data.
        It should be called before starting a new simulation or when reinitializing the engine.
        """
        self.users = {}
        self.current_ts = self.md.get_first_timestamp(self.assets[0])

    def register_user(
        self,
        user_id,
        spot_account=False,
        margin_account=False,
        futures_account=False,
        spot_initial_cash=100000,
        margin_initial_cash=100000,
        futures_initial_cash=100000,
    ):
        """Registers a new user with specified account types and initial cash amounts.
        Parameters:
            user_id (str): Unique identifier for the user.
            spot_account (bool): Whether to create a spot account for the user.
            margin_account (bool): Whether to create a margin account for the user.
            futures_account (bool): Whether to create a futures account for the user.
            spot_initial_cash (float): Initial cash amount for the spot account.
            margin_initial_cash (float): Initial cash amount for the margin account.
            futures_initial_cash (float): Initial cash amount for the futures account.
        Raises:
            ValueError: If the user ID is already registered.
        """
        self.users[user_id] = User(
            user_id=user_id,
            spot_account=spot_account,
            margin_account=margin_account,
            futures_account=futures_account,
            spot_initial_cash=spot_initial_cash,
            margin_initial_cash=margin_initial_cash,
            futures_initial_cash=futures_initial_cash,
            verbose=self.verbose,
        )

    def get_user(self, user_id):
        """Retrieves a registered user by user ID.
        Parameters:
            user_id (str): Unique identifier for the user.
        Returns:
            User: The user object associated with the given user ID.
        Raises:
            ValueError: If the user ID is not registered.
        """
        if user_id not in self.users:
            raise ValueError(f"User {user_id} not registered.")
        return self.users[user_id]

    def place_order(self, user_id, order, ts):
        """Places an order for a user at the current timestamp.
        Parameters:
            user_id (str): Unique identifier for the user.
            order (TradeOrder): The order object containing order details.
            ts (datetime): The timestamp at which the order is placed.
        Raises:
            ValueError: If the user ID is not registered or if the timestamp does not match the current simulation timestamp.
        """
        if user_id not in self.users:
            raise ValueError(f"User {user_id} not registered.")
        if self.current_ts != ts:
            raise ValueError(
                f"Timestamp {ts} does not match the current simulation timestamp {self.current_ts}."
            )
        user = self.users[user_id]
        acc = user.get_account(order.mode)
        acc.open(order, ts, self.md, self.fee_calc)

    def close_order(self, user_id, mode, order_id, ts):
        """Closes an order for a user in the specified account mode at the current timestamp.
        Parameters:
            user_id (str): Unique identifier for the user.
            mode (str): The account mode (e.g., "spot", "margin", "futures").
            order_id (str): Unique identifier for the order to be closed.
            ts (datetime): The timestamp at which the order is closed.
        Raises:
            ValueError: If the user ID is not registered or if the timestamp does not match the current simulation timestamp.
        """
        if user_id not in self.users:
            raise ValueError(f"User {user_id} not registered.")
        if self.current_ts != ts:
            raise ValueError(
                f"Timestamp {ts} does not match the current simulation timestamp {self.current_ts}."
            )
        user = self.users[user_id]
        acc = user.get_account(mode)
        acc.close(order_id, ts, self.md, self.fee_calc)

    def close_all_orders(self, user_id, mode, ts):
        """Closes all open orders for a user in the specified account mode at the current timestamp.
        Parameters:
            user_id (str): Unique identifier for the user.
            mode (str): The account mode (e.g., "spot", "margin", "futures").
            ts (datetime): The timestamp at which the orders are closed.
        Raises:
            ValueError: If the user ID is not registered or if the timestamp does not match the current simulation timestamp.
        """
        if user_id not in self.users:
            raise ValueError(f"User {user_id} not registered.")
        if self.current_ts != ts:
            raise ValueError(
                f"Timestamp {ts} does not match the current simulation timestamp {self.current_ts}."
            )
        user = self.users[user_id]
        acc = user.get_account(mode)
        acc.close_all_open_orders(ts, self.md, self.fee_calc)

    def close_all_orders_by_mode_asset(self, user_id, mode, asset, ts):
        """Closes all open orders for a user in the specified account mode and asset at the current timestamp.
        Parameters:
            user_id (str): Unique identifier for the user.
            mode (str): The account mode (e.g., "spot", "margin", "futures").
            asset (str): The asset for which to close orders.
            ts (datetime): The timestamp at which the orders are closed.
        Raises:
            ValueError: If the user ID is not registered or if the timestamp does not match the current simulation timestamp.
        """
        if user_id not in self.users:
            raise ValueError(f"User {user_id} not registered.")
        if self.current_ts != ts:
            raise ValueError(
                f"Timestamp {ts} does not match the current simulation timestamp {self.current_ts}."
            )
        user = self.users[user_id]
        acc = user.get_account(mode)
        acc.close_all_open_orders_by_asset(asset, ts, self.md, self.fee_calc)

    def close_all_orders_by_mode_asset_side(self, user_id, mode, asset, side, ts):
        """Closes all open orders for a user in the specified account mode, asset, and side at the current timestamp.
        Parameters:
            user_id (str): Unique identifier for the user.
            mode (str): The account mode (e.g., "spot", "margin", "futures").
            asset (str): The asset for which to close orders.
            side (str): The side of the orders to close (e.g., "buy", "sell").
            ts (datetime): The timestamp at which the orders are closed.
        Raises:
            ValueError: If the user ID is not registered or if the timestamp does not match the current simulation timestamp.
        """
        if user_id not in self.users:
            raise ValueError(f"User {user_id} not registered.")
        if self.current_ts != ts:
            raise ValueError(
                f"Timestamp {ts} does not match the current simulation timestamp {self.current_ts}."
            )
        user = self.users[user_id]
        acc = user.get_account(mode)
        acc.close_all_open_orders_by_asset_and_side(
            asset, side, ts, self.md, self.fee_calc
        )

    # at each step of the simulation, we can call this method to update the market data
    def step_simulation(self):
        """Advances the simulation by one step, checking for liquidations and updating portfolio values.
        This method updates the current timestamp, checks for liquidations across all users' accounts,
        and updates the portfolio values for all users based on current market prices and fees.
        It should be called at each step of the simulation to ensure that the market data is up-to-date
        and that all users' accounts are properly managed.
        """
        # check liquidations for all users
        self.check_liquidations()

    def update_current_timestamp(self):
        """Updates the current timestamp to the next available timestamp in the market data.
        This method retrieves the next timestamp for the first asset in the market data.
        It should be called after placing or closing orders to ensure that the simulation progresses
        to the next time step.
        Returns:
            bool: True if the end of the market data is reached, False otherwise.
        Raises:
            ValueError: If no asset data is loaded or if the current timestamp is not available.
        """
        # update all users' portfolio values
        self.update_portfolio_values()

        if self.update_daywise_portfolio_values:
            # update all users' portfolio values daywise
            self.update_all_users_portfolio_values_daywise(self.current_ts)

        # Update the current timestamp to the next available timestamp
        done, next_timestamp = self.md.get_next_timestamp(
            self.assets[0], self.current_ts
        )

        if not done:
            self.current_ts = next_timestamp
        return done

    def check_liquidations(self):
        """Checks all users' open orders for potential liquidations based on current market prices.
        This method iterates through all users and their accounts, checking each open order's liquidation price against the current market price. If an order is found to be liquidated, it is closed at the current price.
        It should be called at each step of the simulation to ensure that any liquidated positions are handled immediately.
        """
        for user in self.users.values():
            for mode in user.get_all_accounts_names():
                account = user.get_account(mode)
                for order in account.open_orders:
                    if order.mode == mode and not order.closed:
                        try:
                            liquidation_price = order.liquidation_price
                            current_price = self.md.get_price(
                                order.asset, self.current_ts
                            )
                            if (
                                order.side in LONG_POSITIONS
                                and current_price <= liquidation_price
                            ) or (
                                order.side in SHORT_POSITIONS
                                and current_price >= liquidation_price
                            ):
                                # account._record_close(
                                #     order, current_price, self.current_ts, True
                                # )
                                account._liquidate_order(
                                    order, current_price, self.current_ts, True
                                )
                        except ValueError as e:
                            print(f"Liquidation check error for order {order.id}: {e}")

    def update_portfolio_values(self):
        """Updates the portfolio values for all users based on current market prices and fees. This method iterates through all users and their accounts, fetching the current prices for each asset and updating the portfolio value for each account type (spot, margin, futures). It should be called at each step of the simulation to ensure that all users' portfolio values are up-to-date with the latest market data."""
        for user in self.users.values():
            for mode in user.get_all_accounts_names():
                account = user.get_account(mode)

                # if mode == "spot":
                #     current_prices = {
                #         asset: self.md.get_price(asset, self.current_ts)
                #         for asset in account.holdings.keys()
                #         if account.holdings[asset] != 0.0
                #     }

                #     account.update_portfolio_value(
                #         current_prices, self.current_ts, self.fee_calc
                #     )

                # elif mode == "margin":
                #     current_prices = {
                #         asset: self.md.get_price(asset, self.current_ts)
                #         for asset in account.holdings.keys()
                #         if account.holdings[asset] != 0.0
                #     }
                #     account.update_portfolio_value(
                #         current_prices, self.current_ts, self.fee_calc
                #     )
                # elif mode == "futures":
                #     current_prices = {
                #         asset: self.md.get_price(asset, self.current_ts)
                #         for asset in account.holdings.keys()
                #         if account.holdings[asset] != 0.0
                #     }
                #     account.update_portfolio_value(
                #         current_prices, self.current_ts, self.fee_calc
                #     )

                # Update portfolio value for all accounts
                current_prices = {
                    asset: self.md.get_price(asset, self.current_ts)
                    for asset in account.holdings.keys()
                    if account.holdings[asset] != 0.0
                }
                account.update_portfolio_value(
                    current_prices, self.current_ts, self.fee_calc
                )

            user.update_portfolio_value()

    def get_current_timestamp(self):
        """Returns the current timestamp of the simulation.
        This method retrieves the current timestamp that the trading engine is simulating.
        Returns:
            datetime: The current timestamp of the simulation.
        """
        return self.current_ts

    def save_all_users_details(self, file_path="users_details.json"):
        """
        Save all users' details to a file.
        This method saves the current state of all registered users, including their accounts, portfolio values,
        open orders, and history, to a JSON file in a structured format.
        Parameters:
            file_path (str): The path to the file where user details will be saved. Defaults to "users_details.json".
        Raises:
            ValueError: If no users are registered to save details.
        Returns:
            None
        """
        # save in proper json format all users' details, accounts, portfolio values, open_orders, history, initial cash, and current cash

        if not self.users:
            raise ValueError("No users registered to save details.")

        # access all users details and write to file
        data = {
            "current_timestamp": self.current_ts,
            "assets": self.assets,
            "config": {
                "trading_fees": FEE_STRUCTURE,
                "extra_fees": {
                    "margin_borrow_interest_hourly": BORROW_INTEREST_HOURLY,
                    "futures_funding_fee_every_8h": FUNDING_FEE_EVERY_8H,
                },
                "slippage": SLIPPAGE,
                "minimum_qty_step": MINIMUM_QTY_STEP,
            },
            "users": [user.return_user_details() for user in self.users.values()],
        }

        # store the data in a json file
        # print(data)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, default=str)

    def update_all_users_portfolio_values_daywise(self, ts):
        """Updates the portfolio values for all users daywise.
        This method iterates through all users and their accounts, updating the portfolio values daywise
        for each account type (spot, margin, futures) at the specified timestamp.
        Parameters:
            ts (datetime): The timestamp at which to update the portfolio values.
        """
        for user in self.users.values():
            user.add_portfolio_value_daywise(ts)

    def save_all_users_portfolio_values_daywise(
        self, file_path="portfolio_values_daywise.json"
    ):
        """Saves the portfolio values daywise for all users to a JSON file.
        This method retrieves the portfolio values daywise for each user and saves them in a structured format.
        Parameters:
            file_path (str): The path to the file where portfolio values will be saved. Defaults to "portfolio_values_daywise.json".
        """
        data = {
            "current_timestamp": self.current_ts,
            "users": {
                user_id: user.get_portfolio_value_daywise()
                for user_id, user in self.users.items()
            },
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, default=str)
