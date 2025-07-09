from engine.accounts import Account
from configs import SLIPPAGE, FEE_STRUCTURE
import pandas as pd


class SpotAccount(Account):
    """A class representing a spot trading account.
    It inherits from the Account class and implements methods specific to spot trading.

    parameters:
        acc_name (str): Name of the account. If None, defaults to "SpotAccount
        acc_type (str): Type of the account, should be "spot".
        cash (float): Initial cash balance in the account.
    Attributes:
        acc_name (str): Name of the account.
        acc_type (str): Type of the account, should be "spot".
        initial_cash (float): Initial cash balance in the account.
        cash (float): Current cash balance in the account.
        portfolio_value (float): Total value of the portfolio, initially set to cash.
        holdings (defaultdict): A dictionary to track holdings of different assets.
        open_orders (list): A list of currently open orders.
        history (list): A list to store the history of all orders.
    Methods:
        open(order, ts, md, fee_calc): Opens a new order in the spot account
        max_open_qty(price, side="buy", is_price_slippaged=False): Calculates the maximum quantity that can be opened for a given asset at a specific price.
        max_sell_qty(asset): Calculates the maximum quantity that can be sold for a given asset.
        close_all_open_orders(ts, md, fee_calc): Closes all open orders in the spot account.
    Raises:
        ValueError: If the order mode is not "spot" or if the order is already closed.
        ValueError: If the order quantity is non-positive after calculating maximum open quantity.
        ValueError: If there are insufficient cash or holdings to open or close an order.

    """

    def _calculate_close_final_cash_value(self, px, order, ts, fee_calc):
        """
        Calculate the final cash value after closing an order, including fees.
        Parameters:
            px (float): The price at which the order is closed.
            order (TradeOrder): The order being closed.
            ts (pd.Timestamp): The timestamp of the close.
            fee_calc (FeeCalculator): An instance of FeeCalculator to calculate fees.
        Returns:
            tuple: A tuple containing the total cost, cost, and fee.
        Raises:
            ValueError: If the order quantity is non-positive after calculating maximum open quantity.

        """

        cost = order.qty * px
        fee = fee_calc.trade_fee("spot", self.acc_type, cost)

        return cost + fee, cost, fee

    def open(self, order, ts, md, fee_calc):
        """
        Open a new order in the spot account.
        Parameters:
            order (TradeOrder): The order to be opened.
            ts (pd.Timestamp): The timestamp of the order.
            md (MarketData): An instance of MarketData to get the current price.
            fee_calc (FeeCalculator): An instance of FeeCalculator to calculate fees.
        Returns:
            None
        Raises:
            ValueError: If the order mode is not "spot" or if the order is already
            closed.
            ValueError: If the order quantity is non-positive after calculating maximum open quantity.
        """
        px = self._apply_slippage(
            md.get_price(order.asset, ts), order.side, SLIPPAGE["spot"]
        )
        if order.qty == "all_cash":
            order.qty = self.max_open_qty(px, order.side, True)
            if order.qty == 0:
                if self.verbose:
                    print(f"Order {order.id} has zero quantity after max calculation.")
                return
            if order.qty <= 0:
                if self.verbose:
                    print(
                        f"Order {order.id} has non-positive or zero quantity after max calculation."
                    )
                return
        elif order.qty == "all_holdings":
            order.qty = self.max_sell_qty(order.asset)
            if order.qty == 0:
                if self.verbose:
                    print(f"Order {order.id} has zero quantity after max calculation.")
                return
            if order.qty <= 0:
                if self.verbose:
                    print(
                        f"Order {order.id} has non-positive or zero quantity after max calculation."
                    )
                return
        if order.mode != "spot":
            print(f"Order {order.id} is not a spot order.")
            return
        if order.closed:
            print(f"Order {order.id} is already closed.")
            return
        if order.qty <= 0:
            print(f"Order {order.id} has non-positive quantity.")
            return

        order.qty = self._round_qty(order.qty)
        if order.qty <= 0:
            print(f"Order {order.id} has non-positive quantity after rounding.")
            return

        _, cost, fee = self._calculate_close_final_cash_value(px, order, ts, fee_calc)

        if order.side in ["buy", "long"]:
            # assert self.cash >= cost + fee
            if not (self.cash >= cost + fee):
                print(
                    f"Insufficient cash to open order {order.id}: "
                    f"Required: {cost + fee}, Available: {self.cash}"
                )
                return
            self.cash -= cost + fee
            self.holdings[order.asset] += order.qty
            order.open_amount_user = cost + fee
            order.open_amount_notional = cost
        else:
            # assert self.holdings[order.asset] >= order.qty
            if not (self.holdings[order.asset] >= order.qty):
                print(
                    f"Insufficient holdings to close order {order.id}: "
                    f"Required: {order.qty}, Available: {self.holdings[order.asset]}"
                )
                return
            self.holdings[order.asset] -= order.qty
            self.cash += cost - fee
            order.open_amount_user = cost - fee
            order.open_amount_notional = cost
        order.entry_price = px
        order.trade_fee_spot = fee
        order.open_ts = ts
        order.closed = True
        self.history.append(order)
        if self.verbose:
            self._log_order(order, px, ts, "open")

    def update_portfolio_value(self, current_prices, ts, fee_calc):
        """
        Update the portfolio value based on current holdings and prices.
        Parameters:
            current_prices (dict): A dictionary of current prices for each asset.
            ts (pd.Timestamp): The timestamp for the update.
            fee_calc (FeeCalculator): An instance of FeeCalculator to calculate fees.
        Returns:
            None
        """
        self.portfolio_value = self.cash + sum(
            qty * price - fee_calc.trade_fee("spot", self.acc_type, qty * price)
            for asset, qty in self.holdings.items()
            for price in [current_prices.get(asset, 0)]
        )

    def max_open_qty(self, price, side="buy", is_price_slippaged=False):
        """
        Calculate the maximum quantity that can be opened for a given asset at a specific price.
        Parameters:
            price (float): The price at which the asset is being traded.
            side (str): The side of the order, either "buy" or "sell".
            is_price_slippaged (bool): Whether the price is already slippaged.
        Returns:
            float: The maximum quantity that can be opened.
        Raises:
            ValueError: If the price is non-positive after applying slippage.
        """
        if price <= 0:
            print("Price must be greater than zero.")
            return 0

        if is_price_slippaged:
            price = price
        else:
            price = self._apply_slippage(price, side, SLIPPAGE["spot"])
        px = price

        if px <= 0:
            print("Price after slippage must be greater than zero.")
            return 0

        fee_rate = FEE_STRUCTURE["spot"][self.acc_type]
        total_cash = self.cash * 1
        max_qty = total_cash / (px * (1 + fee_rate))

        return self._round_qty(max_qty) if side in ["buy", "long"] else None

    def max_sell_qty(self, asset):
        """
        Calculate the maximum quantity that can be sold for a given asset.
        This is based on the current holdings of the asset in the account.
        Parameters:
            asset (str): The asset for which the maximum sell quantity is calculated.
        Returns:
            float: The maximum quantity that can be sold for the asset.
        """
        if asset not in self.holdings:
            return 0
        return self.holdings[asset] if self.holdings[asset] > 0 else 0

    def close_all_open_orders(self, ts, md, fee_calc):
        """
        Close all open orders in the spot account.
        This method iterates through all open orders and closes them at the current market price.
        Parameters:
            ts (pd.Timestamp): The timestamp at which the orders are closed.
            md (MarketData): An instance of MarketData to get the current price.
            fee_calc (FeeCalculator): An instance of FeeCalculator to calculate fees.
        Returns:
            None
        """
        # throow error that all orders are closed immediately in spot account
        print("All orders are closed/executed immediately in spot account.")
        return

    def close_all_open_orders_by_asset(self, asset, ts, md, fee_calc):
        """
        Close all open orders for a specific asset in the spot account.
        This method iterates through all open orders for the specified asset and closes them at the current market price.
        Parameters:
            asset (str): The asset for which the open orders are closed.
            ts (pd.Timestamp): The timestamp at which the orders are closed.
            md (MarketData): An instance of MarketData to get the current price.
            fee_calc (FeeCalculator): An instance of FeeCalculator to calculate fees.
        Returns:
            None
        """
        print(
            f"All orders for {asset} are closed/executed immediately in spot account."
        )
        return

    def get_asset_holdings(self, asset):
        """
        Get the current holdings of a specific asset in the spot account.
        Parameters:
            asset (str): The asset for which the holdings are retrieved.
        Returns:
            float: The quantity of the specified asset held in the account.
        """
        return self.holdings.get(asset, 0.0)
