import pandas as pd

from engine import TradingEngine
from engine.orders import TradeOrder
from utils.order_pipeline import place_all_orders_in_pipeline
from configs.constants import (
    ALL_CASH,
    ALL_HOLDINGS,
    SPOT_ACCOUNT,
    MARGIN_ACCOUNT,
    FUTURES_ACCOUNT,
    LONG_POSITION_SPOT,
    SHORT_POSITION_SPOT,
    LONG_POSITION_MARGIN,
    SHORT_POSITION_MARGIN,
    LONG_POSITION_FUTURES,
    SHORT_POSITION_FUTURES,
)


##########################################################################
# utils functions


def print_user_summary(user):
    print("\n" + "=" * 50)
    print(f"\nUser ID: {user.user_id}")
    print("Total Portfolio Value:", user.get_total_portfolio_value())

    for mode, account in user.accounts.items():
        print(f"\n------ {mode.upper()} ACCOUNT ------")
        print(f"Initial Cash: {account.initial_cash}")
        print(f"Cash: {account.cash}")
        print(f"Holdings: {account.holdings}")
        print(f"Open Orders: {len(account.open_orders)}")
        print(f"Order History: {len(account.history)}")
        print(f"Portfolio Value: {account.portfolio_value:.2f}")

        print("\nOpen Orders Summary:")
        for i, o in enumerate(account.open_orders):
            print("\n" + "-" * 20)
            print(f"{i+1}. Open Order ({o.asset}):")
            for key, val in o.__dict__.items():
                print(f"  {key}: {val if val is not None else 'N/A'}")

        print("\nOrder History Summary:")
        for i, o in enumerate(account.history):
            print("\n" + "-" * 20)
            print(f"{i+1}. Order History ({o.asset}):")
            for key, val in o.__dict__.items():
                print(f"  {key}: {val if val is not None else 'N/A'}")


def run_simulation(engine, orders):
    print("Starting Backtest Simulation...")
    done = False

    while not done:
        current_ts = engine.get_current_timestamp()
        engine.step_simulation()
        place_all_orders_in_pipeline(engine, orders, current_ts)
        done = engine.update_current_timestamp()

    print("Simulation completed.")


##########################################################################
BTCUSDT = "BTCUSDT"
ETHUSDT = "ETHUSDT"

asset_paths = {
    BTCUSDT: "data/BTCUSDT_1h_2017-08-01_2025-06-01.csv",
    ETHUSDT: "data/ETHUSDT_1h_2017-08-01_2025-06-01.csv",
}

# Load engine with price data
engine = TradingEngine(asset_paths=asset_paths, update_daywise_portfolio_values=False)

# Register Users
engine.register_user(
    user_id="u1",
    # spot_account=True,
    # spot_initial_cash=10000,
    # margin_account=False,
    # margin_initial_cash=0,
    futures_account=True,
    futures_initial_cash=10000,
)
engine.register_user(
    user_id="u2",
    spot_account=True,
    spot_initial_cash=10000,
    # margin_account=False,
    # margin_initial_cash=0,
    # futures_account=True,
    # futures_initial_cash=10000,
)
engine.register_user(
    user_id="u3",
    # spot_account=True,
    # spot_initial_cash=10000,
    margin_account=True,
    margin_initial_cash=10000,
    # futures_account=True,
    # futures_initial_cash=10000,
)

# get user1 from engine
user1 = engine.get_user("u1")
user2 = engine.get_user("u2")
user3 = engine.get_user("u3")

order1 = TradeOrder(
    asset=BTCUSDT,
    qty=0.010000023,
    side=LONG_POSITION_FUTURES,
    mode=FUTURES_ACCOUNT,
    leverage=100,
)
order2 = TradeOrder(
    asset=BTCUSDT,
    qty=ALL_CASH,
    side=LONG_POSITION_FUTURES,
    mode=FUTURES_ACCOUNT,
    leverage=10,
)
order3 = TradeOrder(
    asset=ETHUSDT,
    qty=0.010000023,
    side=LONG_POSITION_FUTURES,
    mode=FUTURES_ACCOUNT,
    leverage=2,
)
order4 = TradeOrder(
    asset=BTCUSDT,
    qty=ALL_CASH,
    side=LONG_POSITION_SPOT,
    mode=SPOT_ACCOUNT,
)
order5 = TradeOrder(
    asset=BTCUSDT,
    qty=ALL_HOLDINGS,
    side=SHORT_POSITION_SPOT,
    mode=SPOT_ACCOUNT,
)
order6 = TradeOrder(
    asset=ETHUSDT,
    qty=ALL_CASH,
    side=LONG_POSITION_MARGIN,
    mode=MARGIN_ACCOUNT,
    leverage=2,
)

orders = [
    {
        "type": "open",
        "account_mode": order4.mode,
        "order_object": order4,
        "order_id": order4.id,
        "user": user2,
        "asset": order4.asset,
        "order_execute_ts": pd.to_datetime("2023-12-01 00:00:00+00:00"),
    },
    {
        "type": "open",
        "account_mode": order5.mode,
        "order_object": order5,
        "order_id": order5.id,
        "user": user2,
        "asset": order5.asset,
        "order_execute_ts": pd.to_datetime("2023-12-05 00:00:00+00:00"),
    },
    {
        "type": "open",
        "account_mode": order6.mode,
        "order_object": order6,
        "order_id": order6.id,
        "user": user3,
        "asset": order6.asset,
        "order_execute_ts": pd.to_datetime("2023-12-10 00:00:00+00:00"),
    },
    {
        "type": "close",
        "account_mode": order6.mode,
        "order_object": order6,
        "order_id": order6.id,
        "user": user3,
        "asset": order6.asset,
        "order_execute_ts": pd.to_datetime("2023-12-15 01:00:00+00:00"),
    },
    {
        "type": "open",
        "account_mode": order1.mode,
        "order_object": order1,
        "order_id": order1.id,
        "user": user1,
        "asset": order1.asset,
        "order_execute_ts": pd.to_datetime("2024-01-01 00:00:00+00:00"),
    },
    {
        "type": "open",
        "account_mode": order3.mode,
        "order_object": order3,
        "order_id": order3.id,
        "user": user1,
        "asset": order3.asset,
        "order_execute_ts": pd.to_datetime("2024-01-02 00:00:00+00:00"),
    },
    {
        "type": "close",
        "account_mode": order1.mode,
        "order_object": order1,
        "order_id": order1.id,
        "user": user1,
        "asset": order1.asset,
        "order_execute_ts": pd.to_datetime("2024-02-01 01:00:00+00:00"),
    },
    {
        "type": "open",
        "account_mode": order2.mode,
        "order_object": order2,
        "order_id": order2.id,
        "user": user1,
        "asset": order2.asset,
        "order_execute_ts": pd.to_datetime("2025-01-01 00:00:00+00:00"),
    },
    {
        "type": "close",
        "account_mode": order2.mode,
        "order_object": order2,
        "order_id": order2.id,
        "user": user1,
        "asset": order2.asset,
        "order_execute_ts": pd.to_datetime("2025-02-01 01:00:00+00:00"),
    },
    {
        "type": "close_all",
        "account_mode": "futures",
        "user": user1,
        "order_execute_ts": pd.to_datetime("2025-01-02 01:00:00+00:00"),
    },
]


########################################################################
run_simulation(engine, orders)
engine.save_all_users_details(file_path="logs/users_details_3.json")
# engine.save_all_users_portfolio_values_daywise(
#     file_path="logs/users_portfolio_values_daywise_2.json"
# )

print_user_summary(user1)
print_user_summary(user2)
print_user_summary(user3)

########################################################################
