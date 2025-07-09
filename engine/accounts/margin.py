from engine.accounts import Account
from configs import SLIPPAGE, FEE_STRUCTURE, MARGIN_MAX_LEVERAGE
from configs.constants import LONG_POSITION_MARGIN, SHORT_POSITION_MARGIN
from engine.accounts.liquidation_price import calculate_liquidation_price
import pandas as pd


class MarginAccount(Account):
    """A class representing a margin trading account.
    It inherits from the Account class and implements methods specific to margin trading.
    Parameters:
        acc_name (str): Name of the account. If None, defaults to "MarginAccount".
        acc_type (str): Type of the account, should be "margin".
        cash (float): Initial cash balance in the account.
    Attributes:
        acc_name (str): Name of the account.
        acc_type (str): Type of the account, should be "margin".
        initial_cash (float): Initial cash balance in the account.
        cash (float): Current cash balance in the account.
        portfolio_value (float): Total value of the portfolio, initially set to cash.
        holdings (defaultdict): A dictionary to track holdings of different assets.
        open_orders (list): A list of currently open orders.
        history (list): A list to store the history of all orders.
    Methods:
        open(order, ts, md, fee_calc): Opens a new order in the margin account.
        close(order_id, ts, md, fee_calc): Closes an existing order in the margin account.
        update_portfolio_value(current_prices, ts, fee_calc): Updates the portfolio value based on current holdings and prices.
        max_open_qty(price, leverage, side="long", is_price_slippaged=False): Calculates the maximum quantity that can be opened for a given asset at a specific price.
        close_all_open_orders(ts, md, fee_calc): Closes all open orders in the margin account.
    Raises:
        ValueError: If the order mode is not "margin" or if the order is already closed.
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
            tuple: A tuple containing the total cash value, pnl, fee, borrow fee, and refund margin.
        Raises:
            ValueError: If the order quantity is non-positive after calculating maximum open quantity.
        """

        hours = (ts - order.open_ts).total_seconds() / 3600
        exit_amount_notional = order.qty * px

        pnl = (px - order.entry_price) * order.qty
        if order.side in ["short", "sell"]:
            pnl *= -1

        fee = fee_calc.trade_fee("margin", self.acc_type, exit_amount_notional)
        borrow_amount = order.open_amount_notional - order.open_amount_margin
        borrow = fee_calc.borrow_fee(borrow_amount, hours)

        refund_margin = order.qty * order.entry_price / order.leverage

        closed_amount_user = pnl + refund_margin - fee - borrow
        return closed_amount_user, pnl, fee, borrow, refund_margin

    def open(self, order, ts, md, fee_calc):
        """Open a new order in the margin account.
        Parameters:
            order (TradeOrder): The order to be opened.
            ts (pd.Timestamp): The timestamp of the order.
            md (MarketData): An instance of MarketData to get the current price.
            fee_calc (FeeCalculator): An instance of FeeCalculator to calculate fees.
        Returns:
            None
        Raises:
            ValueError: If the order mode is not "margin" or if the order is already closed.
            ValueError: If the order quantity is non-positive after calculating maximum open quantity.
        """

        # Check Max leverage
        if order.leverage > MARGIN_MAX_LEVERAGE:
            print(
                f"Order {order.id} has leverage greater than {MARGIN_MAX_LEVERAGE} : {order.leverage}."
            )
            return

        px = self._apply_slippage(
            md.get_price(order.asset, ts), order.side, SLIPPAGE["margin"]
        )
        if order.qty == "all_cash":
            order.qty = self.max_open_qty(px, order.leverage, order.side, True)
            if order.qty <= 0:
                print(
                    f"Order {order.id} has non-positive quantity after max calculation."
                )
                return
        order.qty = self._round_qty(order.qty)
        if order.qty <= 0:
            print(f"Order {order.id} has non-positive quantity after rounding.")
            return

        notional = order.qty * px
        margin = notional / order.leverage
        fee = fee_calc.trade_fee("margin", self.acc_type, notional)
        if not (self.cash >= margin + fee):
            print(
                f"Insufficient cash to open order {order.id}: "
                f"Required: {margin + fee}, Available: {self.cash}"
            )
            return

        if order.side in ["buy", "long"]:
            # self.holdings[order.asset] += 1
            self.holdings[order.asset] += order.qty
        elif order.side in ["sell", "short"]:
            # self.holdings[order.asset] += 1
            self.holdings[order.asset] -= order.qty

        # determine liquidation price
        try:
            liquidation_price = calculate_liquidation_price(
                account_type="margin",
                position_type=order.side,
                entry_price=px,
                margin_balance=margin,
                qty=order.qty,
                leverage=order.leverage,
            )
            # print(f"Liquidation Price: {liquidation_price}")
        except ValueError as e:
            print(f"Error: {e}")
            print(
                f"Cannot open order {order.id} due to liquidation price calculation error."
            )
            return

        self.cash -= margin + fee
        order.entry_price = px
        order.trade_fee_open = fee
        order.open_ts = ts
        order.open_amount_notional = notional
        order.open_amount_margin = margin
        order.open_amount_user = margin + fee
        order.liquidation_price = liquidation_price
        self.open_orders.append(order)

        if self.verbose:
            self._log_order(order, px, ts, "open")

    def close(self, order_id, ts, md, fee_calc):
        """Close an existing order in the margin account.
        Parameters:
            order_id (str): The ID of the order to be closed.
            ts (pd.Timestamp): The timestamp of the close.
            md (MarketData): An instance of MarketData to get the current price.
            fee_calc (FeeCalculator): An instance of FeeCalculator to calculate fees.
        Returns:
            None
        Raises:
            ValueError: If the order is not found in open orders or if it is already closed.
            ValueError: If the order mode is not "margin".
        """

        order = next((o for o in self.open_orders if o.id == order_id), None)
        if order is None:
            print(f"Order {order_id} not found in open orders.")
            # check if order is closed in history
            if any(o.id == order_id and o.closed for o in self.history):
                print(f"Order {order_id} is already closed in history.")
                return
            return

        if order.closed:
            print(f"Order {order_id} is already closed.")
            return
        if order.mode != "margin":
            print(f"Order {order_id} is not a futures order.")
            return

        px = self._apply_slippage(
            md.get_price(order.asset, ts),
            self._get_opposite_side(order.side),
            SLIPPAGE["margin"],
        )
        closed_amount_notional = order.qty * px

        closed_amount_user, pnl, fee, borrow, refund_margin = (
            self._calculate_close_final_cash_value(px, order, ts, fee_calc)
        )

        self.cash += pnl + refund_margin - fee - borrow
        pnl_percentage_100 = (
            pnl / order.open_amount_margin * 100 if order.open_amount_margin else None
        )
        pnl_realized_percentage_100 = (
            (closed_amount_user - order.open_amount_user) / order.open_amount_user * 100
            if order.open_amount_user
            else None
        )

        if order.side in ["buy", "long"]:
            self.holdings[order.asset] -= order.qty
        elif order.side in ["sell", "short"]:
            self.holdings[order.asset] += order.qty

        order.exit_price = px
        order.price_change_percentage_100 = (
            (px - order.entry_price) / order.entry_price * 100
            if order.entry_price
            else None
        )
        order.borrow_fee_margin = borrow
        order.trade_fee_close = fee
        order.close_ts = ts
        order.closed_amount_notional = closed_amount_notional
        order.closed_amount = pnl + refund_margin
        order.closed_amount_user = pnl + refund_margin - fee - borrow
        order.unrealized_pnl = pnl
        order.realized_pnl = order.closed_amount_user - order.open_amount_user
        order.roi_percentage_100 = pnl_percentage_100
        order.realized_roi_percentage_100 = pnl_realized_percentage_100
        order.closed = True
        self._record_close(order, px, ts)

        if self.verbose:
            self._log_order(order, px, ts, "close")

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
        # Here there is no holdings but rather open orders and we need to calculate unrealized cash value
        unrealized_cash = sum(
            self._calculate_close_final_cash_value(
                current_prices[order.asset], order, ts, fee_calc
            )[0]
            for order in self.open_orders
            # if order.asset in current_prices
        )
        self.portfolio_value = self.cash + unrealized_cash

    def max_open_qty(self, price, leverage, side="long", is_price_slippaged=False):
        """
        Calculate the maximum quantity that can be opened for a given asset at a specific price.
        This is based on the current cash available in the account.
        Parameters:
            price (float): The price at which the asset is being traded.
            leverage (float): The leverage used for the trade.
            side (str): The side of the order, either "long" or "short".
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
            price = self._apply_slippage(price, side, SLIPPAGE["margin"])
        px = price

        if px <= 0:
            print("Price after slippage must be greater than zero.")
            return 0

        fee_rate = FEE_STRUCTURE["margin"][self.acc_type]
        total_cash = self.cash * 1
        max_qty = total_cash / (px * ((1 / leverage) + fee_rate))

        return self._round_qty(max_qty)

    def close_all_open_orders(self, ts, md, fee_calc):
        """
        Close all open orders in the margin account.
        This method iterates through all open orders and closes them at the current market price.
        Parameters:
            ts (pd.Timestamp): The timestamp at which the orders are closed.
            md (MarketData): An instance of MarketData to get the current price.
            fee_calc (FeeCalculator): An instance of FeeCalculator to calculate fees.
        Returns:
            None
        Raises:
            ValueError: If there is an error closing an order.
        """
        for order in self.open_orders:
            if not order.closed:
                try:
                    self.close(order.id, ts, md, fee_calc)
                except ValueError as e:
                    print(f"Error closing order {order.id}: {e}")

    def close_all_open_orders_by_asset(self, asset, ts, md, fee_calc):
        """
        Close all open orders for a specific asset in the margin account.
        This method iterates through all open orders and closes those that match the specified asset.
        Parameters:
            asset (str): The asset for which to close open orders.
            ts (pd.Timestamp): The timestamp at which the orders are closed.
            md (MarketData): An instance of MarketData to get the current price.
            fee_calc (FeeCalculator): An instance of FeeCalculator to calculate fees.
        Returns:
            None
        """
        for order in self.open_orders:
            if order.asset == asset and not order.closed:
                try:
                    self.close(order.id, ts, md, fee_calc)
                except ValueError as e:
                    print(f"Error closing order {order.id}: {e}")

    def close_all_open_orders_by_asset_and_side(self, asset, side, ts, md, fee_calc):
        """
        Close all open orders for a specific asset and side in the margin account.
        This method iterates through all open orders and closes those that match the specified asset and side.
        Parameters:
            asset (str): The asset for which to close open orders.
            side (str): The side of the order, either "long" or "short".
            ts (pd.Timestamp): The timestamp at which the orders are closed.
            md (MarketData): An instance of MarketData to get the current price.
            fee_calc (FeeCalculator): An instance of FeeCalculator to calculate fees.
        Returns:
            None
        """
        for order in self.open_orders:
            if order.asset == asset and order.side == side and not order.closed:
                try:
                    self.close(order.id, ts, md, fee_calc)
                except ValueError as e:
                    print(f"Error closing order {order.id}: {e}")

    def get_open_orders_long_short_counts_by_asset(self, asset):
        """
        Get the counts of open long and short orders for a specific asset in the margin account.
        Parameters:
            asset (str): The asset for which to count open long and short orders.
        Returns:
            tuple: A tuple containing the count of open long orders and the count of open short orders.
        """
        long_count = sum(
            1
            for o in self.open_orders
            if o.asset == asset and o.side == LONG_POSITION_MARGIN
        )
        short_count = sum(
            1
            for o in self.open_orders
            if o.asset == asset and o.side == SHORT_POSITION_MARGIN
        )

        return long_count, short_count
