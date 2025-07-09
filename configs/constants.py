# This file contains constants used throughout the trading engine.


######################################################################
# Accounts
SPOT_ACCOUNT = "spot"
MARGIN_ACCOUNT = "margin"
FUTURES_ACCOUNT = "futures"

REGULAR_ACCOUNT_SUBTYPE = "regular"

ACCOUNT_MODES = [SPOT_ACCOUNT, MARGIN_ACCOUNT, FUTURES_ACCOUNT]
LIQUIDATION_ACCOUNT_MODES = [MARGIN_ACCOUNT, FUTURES_ACCOUNT]


######################################################################
# Positions
BUY_POSITION = "buy"
SELL_POSITION = "sell"
LONG_POSITION = "long"
SHORT_POSITION = "short"

LONG_POSITIONS = [BUY_POSITION, LONG_POSITION]
SHORT_POSITIONS = [SELL_POSITION, SHORT_POSITION]

SPOT_POSITIONS = [BUY_POSITION, SELL_POSITION]
MARGIN_POSITIONS = [LONG_POSITION, SHORT_POSITION]
FUTURES_POSITIONS = [LONG_POSITION, SHORT_POSITION]

LONG_POSITION_SPOT = BUY_POSITION
SHORT_POSITION_SPOT = SELL_POSITION

LONG_POSITION_MARGIN = LONG_POSITION
SHORT_POSITION_MARGIN = SHORT_POSITION

LONG_POSITION_FUTURES = LONG_POSITION
SHORT_POSITION_FUTURES = SHORT_POSITION

######################################################################
# Quantity Types

ALL_CASH = "all_cash"
ALL_HOLDINGS = "all_holdings"

######################################################################
######################################################################
