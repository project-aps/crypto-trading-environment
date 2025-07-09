import numpy as np


class RewardCalculator:
    def __init__(self, inital_portfolio_value, freq_per_year=252):
        self.freq = freq_per_year
        self.inital_portfolio_value = 0.0
        self.pv_history = [inital_portfolio_value]

    def update(self, portfolio_value):
        self.pv_history.append(portfolio_value)

    def reset(self):
        self.pv_history = []
        self.inital_portfolio_value = 0.0

    def stepwise_portfolio_return(self):
        if len(self.pv_history) < 2:
            return 0.0
        return (self.pv_history[-1] - self.pv_history[-2]) / self.pv_history[-2]

    def portfolio_return(self):
        if len(self.pv_history) < 2:
            return 0.0
        return (self.pv_history[-1] - self.pv_history[0]) / self.pv_history[0]

    def log_portfolio_return(self):
        if len(self.pv_history) < 2:
            return 0.0
        return np.log(self.pv_history[-1] / self.pv_history[-2])

    def sharpe_ratio(self):
        if len(self.pv_history) < 2:
            return 0.0
        returns = np.diff(np.log(self.pv_history))
        if returns.std() == 0:
            return 0.0
        return np.sqrt(self.freq) * np.mean(returns) / np.std(returns)

    def hybrid(self, alpha=0.5, use_log=True):
        pr = self.portfolio_return()
        sr = self.sharpe_ratio()
        lr = self.log_portfolio_return() if use_log else pr
        return alpha * lr + (1 - alpha) * sr

    def get_reward_by_type(self, reward_type="hybrid", alpha=0.5, use_log=True):
        if reward_type == "portfolio_return":
            return self.portfolio_return()
        elif reward_type == "log_portfolio_return":
            return self.log_portfolio_return()
        elif reward_type == "sharpe_ratio":
            return self.sharpe_ratio()
        elif reward_type == "hybrid":
            return self.hybrid(alpha, use_log)
        elif reward_type == "stepwise_portfolio_return":
            return self.stepwise_portfolio_return()
        else:
            raise ValueError(f"Unknown reward type: {reward_type}")


if __name__ == "__main__":
    # Example usage
    rc = RewardCalculator(inital_portfolio_value=1000)

    values = [1000, 1050, 1100, 1200, 1150, 800, 600, 1200]
    for value in values:
        rc.update(value)
        print("\n Updated Portfolio Value:", value)
        print("Portfolio Return:", rc.portfolio_return())
        print("Log Portfolio Return:", rc.log_portfolio_return())
        print("Tickwise Portfolio Return:", rc.tickwise_portfolio_return())
        print("Sharpe Ratio:", rc.sharpe_ratio())
