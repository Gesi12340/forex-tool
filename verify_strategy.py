import os
import sys
import pandas as pd
import numpy as np
from unittest.mock import MagicMock

# Add current directory to path
sys.path.append(os.getcwd())

from backend.strategy_engine import StrategyEngine
from backend.risk_manager import RiskManager
from backend.data_processor import DataProcessor

def run_simulation():
    print("--- Starting AI Strategy Simulation ---")
    
    # 1. Mock the Broker Client
    mock_broker = MagicMock()
    
    # Create mock candles for a "Moonshot" (Strong Bullish Trend)
    # Price goes from 1800 to 2000 over 100 candles
    base_price = 1800
    mock_candles = []
    for i in range(100):
        day = i // 24
        hour = i % 24
        price = base_price + (i * 0.5) + (np.random.normal(0, 1))
        mock_candles.append({
            "time": f"2023-10-{day+1:02}T{hour:02}:00:00Z",
            "mid": {"o": str(price-1), "h": str(price+2), "l": str(price-2), "c": str(price)},
            "volume": 1000
        })
    
    mock_broker.get_candles.return_value = mock_candles
    mock_broker.get_account_summary.return_value = {"balance": 500, "equity": 500}
    mock_broker.get_open_positions.return_value = []
    
    # 2. Initialize Engine
    risk = RiskManager()
    processor = DataProcessor()
    engine = StrategyEngine(mock_broker, risk, processor)
    
    # Force AI to suggest BUY with high confidence for testing
    engine.ai.forecast_and_classify = MagicMock(return_value=("BUY", 0.99))
    
    print("\n[Step 1] Verifying Entry Logic for Moonshot...")
    engine.run_cycle("XAUUSD")
    
    # Check if create_order was called
    if mock_broker.create_order.called:
        args = mock_broker.create_order.call_args[0]
        kwargs = mock_broker.create_order.call_args[1]
        print(f"SUCCESS: Trade Executed!")
        print(f"Instrument: {args[0]}")
        print(f"Units: {args[1]}")
        print(f"TP Price: {kwargs.get('take_profit')}")
        print(f"SL Price: {kwargs.get('stop_loss')}")
    else:
        print("FAILED: No trade executed.")

    print("\n[Step 2] Verifying Trailing Stop Logic...")
    # Mock an open position
    current_price = 1950
    mock_broker.get_open_positions.return_value = [{
        "ticket": 12345,
        "type": "BUY",
        "price_open": 1800,
        "price_current": current_price,
        "sl": 1780,
        "volume": 1.0
    }]
    
    # Run another cycle to trigger trailing stop update
    engine.run_cycle("XAUUSD")
    
    if mock_broker.update_order_sl.called:
        args = mock_broker.update_order_sl.call_args[0]
        print(f"SUCCESS: Trailing Stop Updated for Ticket {args[0]} to {args[2]:.5f}")
    else:
        print("FAILED: Trailing stop not adjusted.")

    print("\n--- Simulation Complete ---")

if __name__ == "__main__":
    run_simulation()
