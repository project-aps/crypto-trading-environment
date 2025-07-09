# Multi-User Trading Engine Environment for Reinforcement Learning

This project is a modular **multi-user single asset trading engine environment** built using `gymnasium`, tailored for **Reinforcement Learning (RL)** training. It simulates realistic spot, margin, and futures trading for multiple users using OHLCV market data, along with support for funding, borrowing, liquidation, and trading fee calculations.

---

### Project Summary

This project implements a **Multi-User Single-Asset Trading Environment** designed for reinforcement learning (RL) applications in algorithmic trading.

-   **Trading Engine**: Supports spot, margin, and futures accounts with flexible leverage settings for multiple users.
-   **Market Data Handling**: Loads OHLCV data and additional normalized indicator features for realistic market simulation.
-   **Gym-Compatible Environment**: Custom OpenAI Gym environment that simulates trading multiple users simultaneously on a single asset.
-   **User Configuration**: Each user can have multiple accounts with distinct initial cash balances and leverage, while the base user has exactly one account type that defines the reward calculation.
-   **Data Splitting & Windowing**: Supports train-test split based on timestamps and configurable observation window size to simulate realistic trading scenarios.
-   **Reward Calculation**: Rewards are calculated based on the base user’s account performance, facilitating focused RL training.
-   **Use Case**: Ideal for developing and testing reinforcement learning agents that operate in a multi-user, multi-account trading scenario.

This environment allows you to train sophisticated RL trading strategies while considering realistic trading constraints and multi-user market impact.

## Project Setup

Follow these steps to set up the project for the first time:

### 1. Clone the Repository

```bash
git clone https://github.com/project-aps/crypto-trading-environment.git
cd crypto-trading-environment
```

### 2. Create and Activate Virtual Environment

#### Using `venv` (recommended):

On **Linux/macOS**:

```bash
python3 -m venv trading_env
source trading_env/bin/activate
```

On **Windows**:

```bash
python -m venv trading_env
trading_env\Scripts\activate
```

### 3. Install Required Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Trading Environment

Once everything is set up and dependencies are installed, you can run the trading environment using:

Make sure the virtual environment is activated before running.

```bash
trading_env\Scripts\activate
```

```bash
python main.py
```

### 5. Example Usage

```python
from environment import MultiUserSingleAssetTradingDiscreteActionEnv

# Define the users configuration
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

# Initialize the environment
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
    )


# Reset environment
obs = env.reset()
done = False
total_reward = 0

# Run one episode
while not done:
    action = env.action_space.sample()  # Random action, replace with your RL model action or model.predict(obs)
    obs, reward, done, truncated, info = env.step(action)
    total_reward += reward
    step_count += 1

    # Optional rendering
    # env.render(mode="human")

print(f"Finished in {step_count} steps, Final Reward (equity): {reward}")
```

### Contact

For any questions, suggestions, or contributions,
Feel free to open issues or pull requests on the GitHub repository. Your feedback and contributions are highly appreciated!

### License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

---

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy  
of this software and associated documentation files (the "Software"), to deal  
in the Software without restriction, including without limitation the rights  
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell  
copies of the Software, and to permit persons to whom the Software is  
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all  
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR  
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,  
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE  
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER  
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,  
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE  
SOFTWARE.
