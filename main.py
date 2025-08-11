# Example usage
from environment import MultiUserSingleAssetTradingDiscreteActionEnv

# from stable_baselines3.common.env_checker import check_env


base_user_config = {
    "account": "futures",  # "spot", "margin", or "futures"
    "initial_cash": 10000,
    "leverage": 30,
}
users_config = {
    "user_1": {
        "spot": {"open_account": True, "inital_cash": 10000, "leverage": 1},
        "margin": {"open_account": True, "inital_cash": 10000, "leverage": 2},
        "futures": {"open_account": True, "inital_cash": 10000, "leverage": 5},
    },
    "user_2": {
        "spot": {"open_account": True, "inital_cash": 10000, "leverage": 1},
        "margin": {"open_account": True, "inital_cash": 10000, "leverage": 5},
        "futures": {"open_account": True, "inital_cash": 10000, "leverage": 10},
    },
}


def show_use_summary(engine_logs_path):
    import json

    with open(engine_logs_path, "r") as f:
        logs = json.load(f)

    for user in logs["users"]:
        print(f"User ID: {user['user_id']}")
        print("-" * 50)
        for acc_type, account in user["accounts"].items():
            print("-" * 50)
            print(f"  Account Type: {acc_type}")
            print(f"    Initial Cash: {account['initial_cash']}")
            print(f"    Current Cash: {account['cash']}")
            print(f"    Portfolio Value: {account['portfolio_value']}")
            print(f"    Holdings: {account['holdings']}")
            print(f"    Open Orders: {len(account['open_orders'])}")
            print(f"    Trade History Count: {len(account['history'])}")

            # show all open orders
            if account["open_orders"]:
                print("    Open Orders Details:")
                for order in account["open_orders"]:
                    print("       --------------------------------------")
                    print(f"      Order ID: {order['id']}")
                    for key, value in order.items():
                        print(f"      {key}: {value}")
            else:
                print("    No Open Orders")

            # show all trade history
            if account["history"]:
                print("    Trade History Details:")
                for trade in account["history"]:
                    print("       --------------------------------------")
                    print(f"      Order ID: {trade['id']}")
                    for key, value in trade.items():
                        print(f"      {key}: {value}")
            else:
                print("    No Trade History")


if __name__ == "__main__":
    print("Starting Multi-User Single Asset Trading Environment...")

    # Initialize environment
    env = MultiUserSingleAssetTradingDiscreteActionEnv(
        engine_data_path="data/testings_small/BTCUSDT_engine_data_1000.csv",  # raw OHLCV data for trading engine
        env_data_path="data/testings_small/BTCUSDT_env_scaled_data_1000.csv",  # observation data with indicators
        users_config={},  # {}
        base_user_config=base_user_config,
        asset="BTCUSDT",
        window_size=50,  # 512 for TCN
        reward_type="stepwise_portfolio_return",
        store_daywise_portfolio_values=False,
        # daywise_logs_path="logs/users_portfolio_values_daywise_5.json",
        engine_logs_path="logs/users_details_6.json",
        verbose=True,  # Set to True for verbose logging
        bankrupt_threshold=0.001,  # Threshold for bankruptcy check
        obs_shape_type="windowed",  # "flat" or "windowed"
    )
    # check_env(env)

    # Reset environment
    obs, _ = env.reset()
    # print(f"Observation shape: {obs.shape}, Observation: {obs}")

    done = False
    total_reward = 0
    step_count = 0

    while not done and step_count < 100:  # Limit to some steps for testing
        action = env.action_space.sample()  # or use model.predict(obs)
        obs, reward, done, truncated, info = env.step(action)
        total_reward += reward
        step_count += 1

        # Optional rendering
        # env.render(mode="human")

    show_use_summary(env.engine_logs_path)
    print(f"Finished in {step_count} steps, Final Reward (equity): {total_reward}")
    print(total_reward / step_count if step_count > 0 else 0)
