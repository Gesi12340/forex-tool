import pandas as pd
import numpy as np
from backend.data_processor import DataProcessor
from backend.risk_manager import RiskManager

class BacktestEngine:
    """
    Simulates trading strategies on historical data.
    """
    def __init__(self, initial_balance=10000):
        self.initial_balance = initial_balance
        self.processor = DataProcessor()
        self.risk = RiskManager()

    def run(self, df):
        """
        Simple vectorized backtest simulation.
        Assumes signal is generated at close of candle.
        """
        # 1. Generate Signals (Simplified Indicator-based for example)
        # Signal: 1 (Buy), -1 (Sell), 0 (Hold)
        df['signal'] = 0
        df.loc[df['rsi'] < 30, 'signal'] = 1
        df.loc[df['rsi'] > 70, 'signal'] = -1
        
        # 2. Calculate Returns
        # Return = % change in price * direction of signal
        df['market_return'] = df['close'].pct_change()
        df['strategy_return'] = df['market_return'] * df['signal'].shift(1)
        
        # 3. Apply Risk Management (Simplified)
        # Subtract spread/commissions (e.g., 0.01% per trade)
        trades_count = (df['signal'].diff() != 0).sum()
        df['strategy_return'] = df['strategy_return'] - (trades_count * 0.0001 / len(df))
        
        # 4. Cumulative Performance
        df['cum_return'] = (1 + df['strategy_return']).cumprod()
        df['balance'] = self.initial_balance * df['cum_return']
        
        # 5. Drawdown
        df['peak'] = df['balance'].cummax()
        df['drawdown'] = (df['peak'] - df['balance']) / df['peak']
        
        return df

    def get_stats(self, df):
        """Returns key performance metrics."""
        return {
            "Final Balance": df['balance'].iloc[-1],
            "Total Return %": ((df['balance'].iloc[-1] / self.initial_balance) - 1) * 100,
            "Max Drawdown %": df['drawdown'].max() * 100,
            "Total Trades": (df['signal'].diff() != 0).sum()
        }
