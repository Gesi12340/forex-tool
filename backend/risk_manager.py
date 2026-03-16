class RiskManager:
    """
    Handles position sizing and risk validation before trade execution.
    """
    def __init__(self, risk_per_trade=0.02, daily_loss_limit=0.05, max_drawdown=0.15):
        self.risk_per_trade = risk_per_trade  # Base risk (2% for high growth)
        self.daily_loss_limit = daily_loss_limit
        self.max_drawdown = max_drawdown
        self.growth_multiplier = 2.0  # Scales risk as balance increases

    def calculate_position_size(self, balance, entry_price, stop_loss_price, confidence=0.90, instrument="EUR_USD"):
        """
        Hyper-Growth Position Sizing:
        Scales risk based on AI confidence (0.90 - 1.0) and balance growth.
        """
        if not stop_loss_price or entry_price == stop_loss_price:
            return 0

        # Hyper-Growth Compound Risk Scaling:
        # Base risk: 2%. Scaled for confidence and target growth (10x-100x).
        risk_percent = self.risk_per_trade 
        
        if confidence >= 0.98:
            risk_percent = 0.15 # 15% risk for "Ultra Gold" signals (Hyper-growth)
        elif confidence >= 0.95:
            risk_percent = 0.08 # 8% risk
        elif confidence >= 0.92:
            risk_percent = 0.04 # 4% risk

        # Compounding multiplier: increase leverage slightly as balance grows
        if balance > 10000:
            risk_percent *= 1.2
        if balance > 100000:
            risk_percent *= 1.5

        risk_amount = balance * risk_percent
        pip_distance = abs(entry_price - stop_loss_price)
        
        if pip_distance == 0: return 0
        
        # Standard unit calculation
        units = int(risk_amount / pip_distance)
        
        # Super-Intelligent Leverage: Allow higher leverage (up to 100:1) for hyper-targeted entries
        max_leverage = 100 if confidence >= 0.95 else 30
        max_units = int(balance * max_leverage / entry_price) 
        
        return min(units, max_units)

    def validate_trade_limits(self, current_balance, daily_pnl, peaks_equity):
        """
        Strict circuit breakers to protect capital and realized profits.
        """
        # 1. Daily Loss Limit
        if daily_pnl <= -(current_balance * self.daily_loss_limit):
            return False, "Daily loss limit reached. Cooling down."

        # 2. Maximum Drawdown from Peak
        if peaks_equity > 0:
            drawdown = (peaks_equity - current_balance) / peaks_equity
            if drawdown >= self.max_drawdown:
                return False, f"Max drawdown ({self.max_drawdown*100}%) reached. Stopping to save capital."

        # 3. "Market Change" Protection (Placeholder for external signal)
        return True, "Safe to trade."
