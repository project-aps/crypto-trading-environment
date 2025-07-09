import uuid


class TradeOrder:
    """A class representing a trade order in the trading engine.
    It contains all the necessary attributes to track the order's lifecycle, including asset, quantity, side, mode, leverage, and various financial metrics.
    Attributes:
        id (str): Unique identifier for the order.
        asset (str): Asset being traded, e.g., 'BTCUSDT'.
        qty (float or str): Quantity of the asset to be traded, can be a float or 'all_cash'.
        closed (bool): Indicates if the order has been closed.
        side (str): 'buy' / 'sell' / 'long' / 'short'.
        mode (str): 'spot' / 'margin' / 'futures'.
        leverage (int): Leverage for the order, default is 1 (no leverage).
        entry_price (float): Price at which the order was opened.
        exit_price (float): Price at which the order was closed.
        price_change_percentage_100 (float): Percentage change in price from entry to exit.
        open_ts (datetime): Timestamp when the order was opened.
        close_ts (datetime): Timestamp when the order was closed.
        open_amount_notional (float): Total Amount used to open the position.
        open_amount_margin (float): User's margin/cash used to open the position.
        open_amount_user (float): User's Total Cash Amount including fees used to open the position.
        closed_amount_notional (float): Total Closing Amount when closing the position using this amount closing fees are calculated.
        closed_amount (float): Amount to be received excluding fees to user when closing the position.
        closed_amount_user (float): Amount received as cash when closing the position including fees.
        unrealized_pnl (float): Profit and Loss from the trade excluding fees.
        realized_pnl (float): Profit and Loss from the trade including fees.
        roi_percentage_100 (float): Return on Investment percentage from the trade excluding fees.
        realized_roi_percentage_100 (float): Return on Investment percentage from the trade including fees.
        trade_fee_spot (float): Trade fee for spot trades.
        trade_fee_open (float): Trade fee for opening the position in margin or futures trades.
        trade_fee_close (float): Trade fee for closing the position in margin or futures trades.
        borrow_fee_margin (float): Borrow fee for margin trades.
        funding_fee_futures (float): Funding fee for futures trades.
        liquidation_price (float or None): Price at which the order will be liquidated, if applicable.
        order_liquidated (bool): Indicates if the order was liquidated or not, default is False.
    """

    def __init__(self, asset, qty, side, mode, leverage=1):
        self.id = uuid.uuid4().hex  # Unique identifier for the order
        self.asset = asset  # Asset being traded, e.g., 'BTCUSDT'
        self.qty = (
            qty  # Quantity of the asset to be traded, can be a float or 'all_cash'
        )
        self.closed = False  # Indicates if the order has been closed
        self.side = side  # 'buy' / 'sell' / 'long' / 'short'
        self.mode = mode  # 'spot' / 'margin' / 'futures'
        self.leverage = leverage  # Leverage for the order, default is 1 (no leverage)
        self.entry_price = None  # Price at which the order was opened
        self.exit_price = None  # Price at which the order was closed
        self.price_change_percentage_100 = (
            None  # Percentage change in price from entry to exit
        )
        self.open_ts = None  # Timestamp when the order was opened
        self.close_ts = None  # Timestamp when the order was closed
        self.open_amount_notional = None  # Total Amount used to open the position
        self.open_amount_margin = None  # User's margin/cash used to open the position
        self.open_amount_user = (
            None  # User's Total Cash Amount including fees used to open the position
        )
        self.closed_amount_notional = None  # Total Closing Amount when closing the position using this amount closing fees are calculated
        self.closed_amount = None  # Amount to be received excluding fees to user when closing the position
        self.closed_amount_user = (
            None  # Amount received as cash when closing the position including fees
        )
        self.unrealized_pnl = None  # Profit and Loss from the trade excluding fees
        self.realized_pnl = None  # Profit and Loss from the trade including fees
        self.roi_percentage_100 = (
            None  # Return on Investment percentage from the trade excluding fees
        )
        self.realized_roi_percentage_100 = (
            None  # Return on Investment percentage from the trade including fees
        )
        self.trade_fee_spot = 0  # Trade fee for spot trades
        self.trade_fee_open = (
            0  # Trade fee for opening the position in margin or futures trades
        )
        self.trade_fee_close = (
            0  # Trade fee for closing the position in margin or futures trades
        )
        self.borrow_fee_margin = 0  # Borrow fee for margin trades
        self.funding_fee_futures = 0  # Funding fee for futures trades
        self.liquidation_price = None  # Price at which the order will be liquidated
        self.order_liquidated = (
            False  # Indicates if the order was liquidated or not, default is False
        )
