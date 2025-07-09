def calculate_liquidation_price(
    account_type,
    position_type,
    entry_price,
    margin_balance,
    qty,
    leverage=10,
):
    """Calculate the liquidation price for a given account type and position type.
    This function calculates the liquidation price based on the account type (margin or futures),
    position type (buy/long or sell/short), entry price, margin balance, quantity, and leverage.
    Args:
        account_type (str): The type of account, either 'margin' or 'futures'.
        position_type (str): The type of position, either 'buy', 'long', 'sell', or 'short'.
        entry_price (float): The entry price of the position.
        margin_balance (float): The current margin balance in the account.
        qty (float): The quantity of the asset in the position.
        leverage (int, optional): The leverage used for the position. Defaults to 10.
    Returns:
        float: The calculated liquidation price.
    Raises:
        ValueError: If the account type or position type is invalid, or if the margin balance is insufficient.
    """

    def calculate_liquidation_price_margin(
        account_type, position_type, entry_price, margin_balance, qty, leverage
    ):
        """Calculate the liquidation price for a margin account.
        This function calculates the liquidation price based on the account type (margin),
        position type (buy/long or sell/short), entry price, margin balance, quantity, and leverage.
        Args:
            account_type (str): The type of account, must be 'margin'.
            position_type (str): The type of position, either 'buy', 'long', 'sell', or 'short'.
            entry_price (float): The entry price of the position.
            margin_balance (float): The current margin balance in the account.
            qty (float): The quantity of the asset in the position.
            leverage (int): The leverage used for the position.
        Returns:
            float: The calculated liquidation price.
        Raises:
            ValueError: If the account type is not 'margin', or if the position type is invalid,
                        or if the margin balance is insufficient for the position.
        """

        # BINANCE rates for margin and futures accounts for isolated positions
        rates = {
            "margin": {
                "buy": 0.05,
                "sell": 0.0476190501,
            }
        }

        notional_value = entry_price * qty
        initial_balance = notional_value / leverage

        if account_type == "margin":
            if position_type == "buy" or position_type == "long":
                rate = rates[account_type]["buy"]
                if margin_balance < initial_balance:
                    raise ValueError("Margin balance is insufficient for the position.")

                if margin_balance >= notional_value:
                    raise ValueError(
                        "No liquidation risk, margin balance exceeds notional value."
                    )

                # Calculate price drop from entry
                mamr_drop = (rate * (notional_value - margin_balance)) / qty
                liquidation_price = entry_price - ((margin_balance / qty) - mamr_drop)
                return liquidation_price
            elif position_type == "sell" or position_type == "short":
                rate = rates[account_type]["sell"]
                if margin_balance < initial_balance:
                    raise ValueError("Margin balance is insufficient for the position.")

                if margin_balance >= notional_value:
                    raise ValueError(
                        "No liquidation risk, margin balance exceeds notional value."
                    )
                # Calculate price drop from entry
                mamr_drop = (rate * (notional_value + margin_balance)) / qty
                liquidation_price = entry_price + ((margin_balance / qty) - mamr_drop)
                return liquidation_price
            else:
                raise ValueError("Invalid position type for margin account.")

    def calculate_liquidation_price_futures_old(
        account_type, position_type, entry_price, margin_balance, qty, leverage
    ):
        # BINANCE rates for margin and futures accounts for isolated positions
        rates = {
            "futures": {
                "long": 0.0040155,
                "short": 0.0039845,
            }
        }

        notional_value = entry_price * qty
        initial_balance = notional_value / leverage

        if account_type == "futures":
            if position_type == "long" or position_type == "buy":
                rate = rates[account_type]["long"]

                if margin_balance < initial_balance:
                    raise ValueError("Margin balance is insufficient for the position.")

                if margin_balance >= notional_value:
                    return 0.0

                # Calculate price drop from entry
                mamr_drop = (rate * (notional_value - margin_balance)) / qty
                liquidation_price = entry_price - ((margin_balance / qty) - mamr_drop)
                return liquidation_price

            elif position_type == "short" or position_type == "sell":
                rate = rates[account_type]["short"]

                if margin_balance < initial_balance:
                    raise ValueError("Margin balance is insufficient for the position.")

                # Calculate price drop from entry
                mamr_drop = (rate * (notional_value + margin_balance)) / qty
                liquidation_price = entry_price + ((margin_balance / qty) - mamr_drop)
                return liquidation_price

            else:
                raise ValueError("Invalid position type for futures account.")

    def calculate_liquidation_price_futures_new(
        account_type, position_type, entry_price, margin_balance, qty, leverage
    ):
        """Calculate the liquidation price for a futures account.
        This function calculates the liquidation price based on the account type (futures),
        position type (buy/long or sell/short), entry price, margin balance, quantity, and leverage.
        Args:
            account_type (str): The type of account, must be 'futures'.
            position_type (str): The type of position, either 'buy', 'long', 'sell', or 'short'.
            entry_price (float): The entry price of the position.
            margin_balance (float): The current margin balance in the account.
            qty (float): The quantity of the asset in the position.
            leverage (int): The leverage used for the position.
        Returns:
            float: The calculated liquidation price.
        Raises:
            ValueError: If the account type is not 'futures', or if the position type is invalid,
                        or if the margin balance is insufficient for the position.
        """

        def get_maintenance_data(notional_value: float, leverage: float):
            """Get the maintenance margin rate and maintenance amount based on notional value and leverage from BINANCE.
            Args:
                notional_value (float): The notional value of the position.
                leverage (float): The leverage used for the position.
            Returns:
                tuple: A tuple containing the maintenance margin rate (mmr) and maintenance amount (ma).
            Raises:
                ValueError: If the notional value is out of supported range or if leverage exceeds max allowed for the tier.
            """
            tiers = [
                {"min": 0, "max": 300_000, "max_leverage": 125, "mmr": 0.0040, "ma": 0},
                {
                    "min": 300_000,
                    "max": 800_000,
                    "max_leverage": 100,
                    "mmr": 0.0050,
                    "ma": 300,
                },
                {
                    "min": 800_000,
                    "max": 3_000_000,
                    "max_leverage": 75,
                    "mmr": 0.0065,
                    "ma": 1500,
                },
                {
                    "min": 3_000_000,
                    "max": 12_000_000,
                    "max_leverage": 50,
                    "mmr": 0.0100,
                    "ma": 12_000,
                },
                {
                    "min": 12_000_000,
                    "max": 70_000_000,
                    "max_leverage": 25,
                    "mmr": 0.0200,
                    "ma": 132_000,
                },
                {
                    "min": 70_000_000,
                    "max": 100_000_000,
                    "max_leverage": 20,
                    "mmr": 0.0250,
                    "ma": 482_000,
                },
                {
                    "min": 100_000_000,
                    "max": 230_000_000,
                    "max_leverage": 10,
                    "mmr": 0.0500,
                    "ma": 2_982_000,
                },
                {
                    "min": 230_000_000,
                    "max": 480_000_000,
                    "max_leverage": 5,
                    "mmr": 0.1000,
                    "ma": 14_482_000,
                },
                {
                    "min": 480_000_000,
                    "max": 600_000_000,
                    "max_leverage": 4,
                    "mmr": 0.1250,
                    "ma": 26_482_000,
                },
                {
                    "min": 600_000_000,
                    "max": 800_000_000,
                    "max_leverage": 3,
                    "mmr": 0.1500,
                    "ma": 41_482_000,
                },
                {
                    "min": 800_000_000,
                    "max": 1_200_000_000,
                    "max_leverage": 2,
                    "mmr": 0.2500,
                    "ma": 121_482_000,
                },
                {
                    "min": 1_200_000_000,
                    "max": 1_800_000_000,
                    "max_leverage": 1,
                    "mmr": 0.5000,
                    "ma": 421_482_000,
                },
            ]

            for tier in tiers:
                if tier["min"] <= notional_value < tier["max"]:
                    if leverage <= tier["max_leverage"]:
                        return tier["mmr"], tier["ma"]
                    else:
                        raise ValueError(
                            f"Leverage {leverage}x exceeds max allowed {tier['max_leverage']}x for notional value {notional_value}."
                        )

            raise ValueError(
                f"Notional value {notional_value} is out of supported range."
            )

        notional_value = entry_price * qty
        intial_balance = notional_value / leverage
        mmr, ma = get_maintenance_data(notional_value, leverage)

        if account_type == "futures":

            if margin_balance < intial_balance:
                raise ValueError("Margin balance is insufficient for the position.")

            if position_type == "long" or position_type == "buy":
                if margin_balance >= notional_value:
                    return 0.0
                liquidation_price = (margin_balance + ma - (qty * entry_price)) / (
                    qty * mmr - qty
                )
                return liquidation_price

            elif position_type == "short" or position_type == "sell":
                liquidation_price = (margin_balance + ma + (qty * entry_price)) / (
                    qty * mmr + qty
                )
                return liquidation_price

            else:
                raise ValueError(
                    "Invalid position type. Must be 'long', 'short', 'buy', or 'sell'."
                )

    if account_type == "margin":
        return calculate_liquidation_price_margin(
            account_type, position_type, entry_price, margin_balance, qty, leverage
        )

    elif account_type == "futures":
        return calculate_liquidation_price_futures_new(
            account_type, position_type, entry_price, margin_balance, qty, leverage
        )

    else:
        raise ValueError("Invalid account type. Must be 'margin' or 'futures'.")


if __name__ == "__main__":
    # Example usage
    try:
        liquidation_price = calculate_liquidation_price(
            account_type="futures",
            position_type="short",
            leverage=10,
            entry_price=100_000,
            qty=10,
            margin_balance=100_000,
        )
        print(f"Liquidation Price: {liquidation_price}")
    except ValueError as e:
        print(f"Error: {e}")
