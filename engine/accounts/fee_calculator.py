class FeeCalculator:
    """A class to calculate trading fees, borrowing fees, and funding fees for different account types.
    It uses a fee structure dictionary to determine the fees based on the mode and account type.
    Attributes:
        fee_struct (dict): A dictionary containing fee rates for different modes and account types.
        borrow_rate_hr (float): The hourly borrowing rate for leveraged positions.
        funding_rate_8h (float): The 8-hour funding rate for futures positions.
    Methods:
        trade_fee(mode, acc_type, notional): Calculates the trading fee based on the mode, account type, and notional value.
        borrow_fee(borrow_amount, hours): Calculates the borrowing fee based on the borrowed amount and hours.
        funding_fee(notional, total_funding_events): Calculates the funding fee based on the notional value and total funding events.
    Raises:
        ValueError: If the mode or account type is not found in the fee structure.
        ValueError: If the borrow amount or hours is non-positive.
        ValueError: If the notional value or total funding events is non-positive.
    """

    def __init__(self, fee_struct, borrow_rate_hr, funding_rate_8h):
        self.fee_struct = fee_struct
        self.borrow_rate_hr = borrow_rate_hr
        self.funding_rate_8h = funding_rate_8h

    def trade_fee(self, mode, acc_type, notional):
        """Calculate the trading fee based on the mode, account type, and notional value.
        Parameters:
            mode (str): The mode of the account (e.g., "spot", "margin", "futures").
            acc_type (str): The type of the account (e.g., "regular", "leverage").
            notional (float): The notional value of the trade.
        Returns:
            float: The calculated trading fee.
        Raises:
            ValueError: If the mode or account type is not found in the fee structure.
            ValueError: If the notional value is non-positive.
        """
        return notional * self.fee_struct[mode][acc_type]

    def borrow_fee(self, borrow_amount, hours):
        """Calculate the borrowing fee based on the borrowed amount and hours.
        Parameters:
            borrow_amount (float): The amount borrowed.
            hours (int): The number of hours the amount is borrowed for.
        Returns:
            float: The calculated borrowing fee.
        Raises:
            ValueError: If the borrow amount or hours is non-positive.
        """
        return borrow_amount * self.borrow_rate_hr * hours

    def funding_fee(self, notional, total_funding_events):
        """Calculate the funding fee based on the notional value and total funding events.
        Parameters:
            notional (float): The notional value of the futures position.
            total_funding_events (int): The total number of funding events that occurred.
        Returns:
            float: The calculated funding fee.
        Raises:
            ValueError: If the notional value or total funding events is non-positive.
        """
        return notional * self.funding_rate_8h * total_funding_events
