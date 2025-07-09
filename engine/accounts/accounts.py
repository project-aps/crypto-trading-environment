from collections import defaultdict
from configs import MINIMUM_QTY_STEP
import math
from decimal import Decimal, getcontext


class Account:
    """A base class representing a trading account.
    It manages the account's cash, holdings, open orders, and trade history.

    parameters:
        acc_name (str): Name of the account. If None, defaults to "Account".
        acc_type (str): Type of the account (e.g., 'spot', 'margin', 'futures').
        cash (float): Initial cash balance in the account.

    Attributes:
        acc_name (str): Name of the account.
        acc_type (str): Type of the account (e.g., 'spot', 'margin', 'futures').
        initial_cash (float): Initial cash balance in the account.
        cash (float): Current cash balance in the account.
        portfolio_value (float): Total value of the portfolio, initially set to cash.
        holdings (defaultdict): A dictionary to track holdings of different assets.
        open_orders (list): A list of currently open orders.
        history (list): A list to store the history of all orders.
    Methods:
        __init__(acc_name, acc_type, cash): Initializes the account with a name, type, and initial cash.
        _apply_slippage(price, side, slippage_rate): Applies slippage to the given price based on the order side and slippage rate.
        _record_close(order, price, close_ts, liquidated=False): Records the closing of an order with its exit price and timestamp.
        get_all_open_orders(): Returns a list of all currently open orders.
        get_all_history(): Returns a list of all order history.
        _get_opposite_side(side): Returns the opposite side of the given order side (e.g., 'buy' -> 'sell', 'long' -> 'short').
        _liquidate_order(order, price, close_ts, liquidated=True): Liquidates an order by closing it at the current price.
        _round_qty(qty, qty_step=MINIMUM_QTY_STEP): Rounds the quantity to the nearest allowed step based on the minimum quantity step.
        return_account_details(): Returns all account data in a JSON-like format.

    Raises:
        ValueError: If the quantity step is not valid (must be greater than zero and less than one).
        ValueError: If the quantity is not an integer or a float.

    """

    def __init__(self, acc_name, acc_type, cash):
        self.acc_name = "Account" if acc_name is None else acc_name
        self.acc_type = acc_type
        self.initial_cash = cash
        self.cash = cash
        self.portfolio_value = cash
        self.holdings = defaultdict(float)
        self.open_orders = []
        self.history = []

    def _apply_slippage(self, price, side, slippage_rate):
        return price * (
            1 + slippage_rate if side in ["buy", "long"] else 1 - slippage_rate
        )

    def _record_close(self, order, price, close_ts, liquidated=False):
        order.exit_price = price
        order.close_ts = close_ts
        order.closed = True
        if liquidated:
            order.order_liquidated = True
        self.history.append(order)
        self.open_orders.remove(order)

    def get_all_open_orders(self):
        return self.open_orders

    def get_all_history(self):
        return self.history

    def _get_opposite_side(self, side):
        if side == "buy":
            return "sell"
        elif side == "sell":
            return "buy"
        elif side == "long":
            return "short"
        elif side == "short":
            return "long"

    def _liquidate_order(self, order, price, close_ts, liquidated=True):
        """
        Liquidate an order by closing it at the current price.
        This is typically called when the order hits its liquidation price.
        """
        if order.closed:
            print(f"Order {order.id} is already closed.")
            return
        if order.mode not in ["margin", "futures"]:
            print(f"Order {order.id} is not a margin or futures order.")
            return

        order.price_change_percentage_100 = (
            (price - order.entry_price) / order.entry_price * 100
            if order.entry_price
            else None
        )
        if order.side in ["buy", "long"]:
            self.holdings[order.asset] -= order.qty
        elif order.side in ["sell", "short"]:
            self.holdings[order.asset] += order.qty
        order.unrealized_pnl = order.open_amount_margin
        order.realized_pnl = order.unrealized_pnl
        order.roi_percentage_100 = -100.0  # Liquidation results in a total loss
        order.realized_roi_percentage_100 = (
            -100.0
        )  # Liquidation results in a total loss

        self._record_close(order, price, close_ts, liquidated=True)
        print(f"Order {order.id} liquidated at price {price} on {close_ts}.")

    def _round_qty(self, qty, qty_step=MINIMUM_QTY_STEP):
        """
        Round the quantity to the nearest allowed step.
        """
        if not isinstance(qty, (int, float)):
            raise ValueError("Quantity must be an integer or a float.")

        if isinstance(qty, int):
            return qty

        if not (0 < qty_step < 1):
            raise ValueError("qty_step must be greater than 0 and less than 1.")

        # Set precision high enough to handle small/big numbers
        getcontext().prec = 30

        # Convert both to Decimal for accuracy and formatting
        qty_dec = Decimal(str(qty))
        step_dec = Decimal(str(qty_step))

        # Get decimal precision from qty_step (number of digits after dot)
        precision = abs(step_dec.as_tuple().exponent)

        # Truncate without rounding
        truncated_qty = qty_dec.quantize(
            Decimal("1." + "0" * precision), rounding="ROUND_DOWN"
        )

        return float(truncated_qty)

    def return_account_details(self):
        """
        Get all account data in a JSON-like format.
        """
        return {
            "acc_name": self.acc_name,
            "acc_type": self.acc_type,
            "initial_cash": self.initial_cash,
            "cash": self.cash,
            "portfolio_value": self.portfolio_value,
            "holdings": dict(self.holdings),
            "open_orders": [order.__dict__ for order in self.open_orders],
            "history": [order.__dict__ for order in self.history],
        }
