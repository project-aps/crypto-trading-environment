# Updated as per July 2025 market conditions

FEE_STRUCTURE = {
    "spot": {"regular": 0.001},  # 0.1% maker/taker fee for spot trading
    "margin": {"regular": 0.001},  # 0.1% maker/taker fee for margin trading
    "futures": {
        "regular": 0.0004
    },  # 0.0200% maker / 0.0500% taker fee for futures trading
}

BORROW_INTEREST_HOURLY = (
    0.0000065938  # 0.00065938% per hour for margin BTC-> 5.78% annually (July 2025)
)
FUNDING_FEE_EVERY_8H = 0.0001  # 0.01% every 8h for futures
SLIPPAGE = {
    "spot": 0.0005,
    "margin": 0.0007,
    "futures": 0.0007,
}  # 0.05% slippage for all modes

MINIMUM_QTY_STEP = 0.00001  # Minimum quantity step for all assets

MARGIN_MAX_LEVERAGE = 10  # Maximum leverage for margin trading
FUTURES_MAX_LEVERAGE = 125  # Maximum leverage for futures trading
