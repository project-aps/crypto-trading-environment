# user.py
from engine.accounts.spot import SpotAccount
from engine.accounts.margin import MarginAccount
from engine.accounts.futures import FuturesAccount
from configs.constants import (
    SPOT_ACCOUNT,
    MARGIN_ACCOUNT,
    FUTURES_ACCOUNT,
    REGULAR_ACCOUNT_SUBTYPE,
)


class User:
    """A class representing a user in the trading engine.
    It manages the user's accounts (spot, margin, futures) and their portfolio value.
    Attributes:
        user_id (str): Unique identifier for the user.
        accounts (dict): Dictionary of accounts associated with the user.
        portfolio_value (dict): Dictionary to store the portfolio value for each account type.
    """

    def __init__(
        self,
        user_id,
        spot_account=False,
        margin_account=False,
        futures_account=False,
        spot_initial_cash=100000,
        margin_initial_cash=100000,
        futures_initial_cash=100000,
        verbose=False,
    ):
        self.user_id = user_id
        self.verbose = verbose
        # self.accounts = {
        #     "spot": SpotAccount("spot", "regular", spot_initial_cash),
        #     "margin": MarginAccount("margin", "regular", margin_initial_cash),
        #     "futures": FuturesAccount("futures", "regular", futures_initial_cash),
        # }
        self.accounts = {}
        if spot_account:
            self.accounts[SPOT_ACCOUNT] = SpotAccount(
                SPOT_ACCOUNT, REGULAR_ACCOUNT_SUBTYPE, spot_initial_cash, self.verbose
            )
        if margin_account:
            self.accounts[MARGIN_ACCOUNT] = MarginAccount(
                MARGIN_ACCOUNT,
                REGULAR_ACCOUNT_SUBTYPE,
                margin_initial_cash,
                self.verbose,
            )
        if futures_account:
            self.accounts[FUTURES_ACCOUNT] = FuturesAccount(
                FUTURES_ACCOUNT,
                REGULAR_ACCOUNT_SUBTYPE,
                futures_initial_cash,
                self.verbose,
            )
        self.portfolio_value = {
            mode: account.portfolio_value for mode, account in self.accounts.items()
        }

        # portfolio_values_daywise
        self.portfolio_values_daywise = {mode: [] for mode in self.accounts.keys()}
        self.portfolio_values_daywise["total"] = []

    def get_all_accounts(self):
        return self.accounts.values()

    def get_all_accounts_names(self):
        return self.accounts.keys()

    def get_account(self, mode):
        if mode not in self.accounts:
            raise ValueError(
                f"Account mode '{mode}' does not exist for user {self.user_id}."
            )
        return self.accounts[mode]

    def update_portfolio_value(self):
        for mode, account in self.accounts.items():
            self.portfolio_value[mode] = account.portfolio_value

    def get_total_portfolio_value(self):
        return {
            mode: account.portfolio_value for mode, account in self.accounts.items()
        }

    def get_all_accounts_sum_portfolio_value(self):
        """Returns the sum of portfolio values across all accounts."""
        return sum(account.portfolio_value for account in self.accounts.values())

    def return_user_details(self):
        return {
            "user_id": self.user_id,
            "accounts": {
                mode: account.return_account_details()
                for mode, account in self.accounts.items()
            },
            "portfolio_value": self.portfolio_value,
        }

    def add_portfolio_value_daywise(self, ts):
        """Adds the portfolio value for each account mode daywise."""
        for mode, account in self.accounts.items():

            self.portfolio_values_daywise[mode].append(
                {"timestamp": ts, "portfolio_value": account.portfolio_value}
            )

        self.portfolio_values_daywise["total"].append(
            {
                "timestamp": ts,
                "portfolio_value": self.get_all_accounts_sum_portfolio_value(),
            }
        )

    def get_portfolio_value_daywise(self, mode=None):
        """Returns the portfolio value daywise for a specific account mode or all accounts."""
        if mode:
            if mode not in self.portfolio_values_daywise:
                raise ValueError(f"Mode '{mode}' does not exist.")
            return self.portfolio_values_daywise[mode]
        return self.portfolio_values_daywise
