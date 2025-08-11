# Example usage
from environment import MultiUserSingleAssetTradingDiscreteActionEnv
from stable_baselines3 import PPO

# from stable_baselines3.common.env_checker import check_env


base_user_config = {
    "account": "spot",  # "spot", "margin", or "futures"
    "initial_cash": 10000,
    "leverage": 1,
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

    # model = PPO.load(
    #     "C:/Users/hp/Downloads/model_btcusdt_ppo_stepwise_return_2/model_step_2500000.zip"
    # )

    # Initialize environment
    env = MultiUserSingleAssetTradingDiscreteActionEnv(
        engine_data_path="./data/final_data/btcusdt/btcusdt_test_engine_data.csv",  # raw OHLCV data for trading engine
        env_data_path="./data/final_data/btcusdt/btcusdt_test_env_data.csv",  # observation data with indicators
        users_config={},  # {}
        base_user_config=base_user_config,
        asset="BTCUSDT",
        window_size=50,
        reward_type="stepwise_portfolio_return",
        store_daywise_portfolio_values=True,
        daywise_logs_path="logs/users_portfolio_values_random_test.json",
        engine_logs_path="logs/users_details_random_test.json",
        verbose=True,  # Set to True for verbose logging
        bankrupt_threshold=0.001,  # Threshold for bankruptcy check
    )
    # check_env(env)

    # Reset environment
    obs, _ = env.reset()
    # print(f"Observation shape: {obs.shape}, Observation: {obs}")

    terminated = False
    truncated = False
    while not (terminated or truncated):
        action = env.action_space.sample()
        # action, _ = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env.step(action)
        # env.render()
