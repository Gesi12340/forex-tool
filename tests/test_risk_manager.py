import unittest
from backend.risk_manager import RiskManager

class TestSafetyMechanisms(unittest.TestCase):
    def setUp(self):
        self.rm = RiskManager(daily_loss_limit=0.05, max_drawdown=0.15)

    def test_daily_loss_limit(self):
        # Case: Daily P&L is -6% of balance
        balance = 10000
        pnl = -600
        is_allowed, reason = self.rm.validate_trade_limits(balance, pnl, balance)
        self.assertFalse(is_allowed)
        self.assertEqual(reason, "Daily loss limit reached.")

    def test_max_drawdown(self):
        # Case: Equity dropped 20% from peak
        peak = 10000
        current = 8000
        is_allowed, reason = self.rm.validate_trade_limits(current, 0, peak)
        self.assertFalse(is_allowed)
        self.assertEqual(reason, "Maximum drawdown threshold reached.")

    def test_position_sizing(self):
        # Risk 1% ($100) on $10,000 balance
        # Stop loss is 20 pips away (0.0020)
        # Expected units: 100 / 0.0020 = 50,000 units
        units = self.rm.calculate_position_size(10000, 1.0850, 1.0830)
        self.assertEqual(units, 50000)

if __name__ == '__main__':
    unittest.main()
