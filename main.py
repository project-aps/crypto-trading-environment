# Example usage
from environment import MultiUserSingleAssetTradingDiscreteActionEnv

# from stable_baselines3.common.env_checker import check_env


base_user_config = {
    "account": "futures",  # "spot", "margin", or "futures"
    "initial_cash": 10000,
    "leverage": 50,
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


if __name__ == "__main__":
    print("Starting Multi-User Single Asset Trading Environment...")

    # Initialize environment
    env = MultiUserSingleAssetTradingDiscreteActionEnv(
        engine_data_path="data/testings_small/BTCUSDT_engine_data_1000.csv",  # raw OHLCV data for trading engine
        env_data_path="data/testings_small/BTCUSDT_env_scaled_data_1000.csv",  # observation data with indicators
        users_config=users_config,  # {}
        base_user_config=base_user_config,
        asset="BTCUSDT",
        window_size=50,
        reward_type="portfolio_return",
        store_daywise_portfolio_values=True,
        daywise_logs_path="logs/users_portfolio_values_daywise_5.json",
        engine_logs_path="logs/users_details_5.json",
        verbose=False,  # Set to True for verbose logging
        bankrupt_threshold=0.001,  # Threshold for bankruptcy check
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

    print(f"Finished in {step_count} steps, Final Reward (equity): {reward}")
