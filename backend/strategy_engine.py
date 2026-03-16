import time
from backend.risk_manager import RiskManager
from backend.data_processor import DataProcessor
from backend.ml.trainer import HybridPredictor

class StrategyEngine:
    """
    Bridge between data, AI predictions, and trade execution.
    """
    def __init__(self, broker_client, risk_manager, data_processor):
        self.broker = broker_client
        self.risk = risk_manager
        self.processor = data_processor
        self.ai = HybridPredictor()
        self.is_running = False

    def run_cycle(self, instrument="XAUUSD"):
        """Executes one iteration with advanced regime detection and safety locks."""
        print(f"[{time.ctime()}] Starting cycle for {instrument}...")
        
        # 1. Fetch Data & Calculate Indicators
        candles = self.broker.get_candles(instrument, count=100)
        df = self.processor.prepare_dataframe(candles)
        df = self.processor.add_indicators(df)
        
        row = df.iloc[-1]
        last_rsi = row['rsi']
        last_adx = row['adx']
        last_atr = row['atr']
        last_roc = row['roc']
        
        # 2. Safety Watchdog: Halt if market is changing too fast (Flash spikes/crashes)
        if abs(last_roc) > 0.5: # 0.5% move in a short window is extreme
            print(f"CRITICAL: Market changing too fast (ROC: {last_roc:.4f}). Halting cycle to protect capital.")
            return

        # 3. Market Regime Analysis
        # ADX > 25 indicates a strong trend. ADX > 40 indicates a "Super Trend" (Moonshot).
        is_trending = last_adx > 25
        is_moonshot = last_adx > 40
        strategy_name = "MOONSHOT" if is_moonshot else ("TREND_FOLLOWING" if is_trending else "MEAN_REVERSION")
        print(f"Active Strategy: {strategy_name} | ADX: {last_adx:.2f} | RSI: {last_rsi:.2f}")

        # 4. Get AI Prediction
        if len(df) < 60: return
        
        sequence = df[['close', 'ema_fast', 'ema_slow', 'rsi', 'macd']].tail(60).values.reshape(1, 60, 5)
        latest_features = df[['ema_fast', 'ema_slow', 'rsi', 'macd', 'upper_band']].tail(1).values
        pred_signal, confidence = self.ai.forecast_and_classify(sequence, latest_features)
        
        # 5. Account & Positioning
        account = self.broker.get_account_summary()
        balance = float(account['balance'])
        
        # 6. Ultra-Selectivity: Only trade on 90%+ confidence for "Zero Loss" goal
        if pred_signal != "HOLD" and confidence >= 0.90:
            current_price = row['close']
            
            # Hyper-Growth Targets: Unlimited TP for Moonshots, 8x-15x for Trends
            sl_mult = 1.2 if is_moonshot else (1.5 if is_trending else 1.2)
            tp_mult = 0.0 if is_moonshot else (15.0 if is_trending else 5.0) 
            
            sl_dist = last_atr * sl_mult
            
            # If in MOONSHOT mode, we set no Take-Profit (tp_price=0.0)
            sl_price = current_price - sl_dist if pred_signal == "BUY" else current_price + sl_dist
            tp_price = 0.0 if is_moonshot else (current_price + (last_atr * tp_mult) if pred_signal == "BUY" else current_price - (last_atr * tp_mult))
            
            units = self.risk.calculate_position_size(balance, current_price, sl_price, confidence=confidence)
            
            is_allowed, reason = self.risk.validate_trade_limits(balance, 0, balance)
            
            if is_allowed and units > 0:
                msg = "MOONSHOT DETECTED" if is_moonshot else "GOLD SIGNAL"
                print(f"{msg}: Executing {pred_signal} on {instrument}. Compounding returns for 10x+ profit!")
                print(f"Targets: SL {sl_price:.5f} | TP {'Unlimited (Trailing Mode)' if is_moonshot else f'{tp_price:.5f}'}")
                self.broker.create_order(
                    instrument, 
                    units if pred_signal == "BUY" else -units,
                    order_type="MARKET",
                    take_profit=tp_price,
                    stop_loss=sl_price
                )
            else:
                print(f"Trade blocked: {reason if not is_allowed else 'Insufficient units'}")
        
        # 7. Manage Trailing Stops & Autonomous Exit for active positions
        self.manage_active_positions(instrument, last_atr, row)

    def manage_active_positions(self, instrument, atr, current_row):
        """
        Dynamically adjusts SL and handles autonomous exits based on market change.
        """
        symbol = instrument.replace("_", "")
        positions = self.broker.get_open_positions(symbol=symbol)
        
        for pos in positions:
            current_price = pos['price_current']
            open_price = pos['price_open']
            current_sl = pos['sl']
            
            # 1. Autonomous Exit: Close if market changes against the trend direction
            # If we are BUYING, and EMA_fast crosses below EMA_slow, exit immediately.
            if pos['type'] == "BUY" and current_row['ema_fast'] < current_row['ema_slow']:
                print(f"Autonomous Exit: Bullish trend broken on {pos['ticket']}. Closing for profit protection.")
                # We reuse create_order with negative units to close (or a dedicated close_position if available)
                self.broker.create_order(instrument, -pos['volume'], order_type="MARKET")
                continue

            if pos['type'] == "SELL" and current_row['ema_fast'] > current_row['ema_slow']:
                print(f"Autonomous Exit: Bearish trend broken on {pos['ticket']}. Closing for profit protection.")
                self.broker.create_order(instrument, pos['volume'], order_type="MARKET")
                continue
            
            # 2. Dynamic Trailing Stop
            # Distance = 1.2 * ATR for aggressive locking of "10x" target profits
            trail_dist = atr * 1.2
            
            if pos['type'] == "BUY":
                new_sl = current_price - trail_dist
                # Only move SL up, never down. Lock in profit once price > open.
                if new_sl > current_sl and current_price > open_price:
                    print(f"Trailing Stop: Updating BUY {pos['ticket']} SL to {new_sl:.5f}")
                    self.broker.update_order_sl(pos['ticket'], symbol, new_sl)
            
            elif pos['type'] == "SELL":
                new_sl = current_price + trail_dist
                if (new_sl < current_sl or current_sl == 0) and current_price < open_price:
                    print(f"Trailing Stop: Updating SELL {pos['ticket']} SL to {new_sl:.5f}")
                    self.broker.update_order_sl(pos['ticket'], symbol, new_sl)

    def get_ai_prediction(self, features):
        """
        Placeholder for the LSTM/XGBoost prediction logic.
        """
        # Mock signal: Buy if RSI < 30, Sell if RSI > 70
        if features['rsi'] < 40:
            return "BUY", 0.85
        elif features['rsi'] > 60:
            return "SELL", 0.85
        return "HOLD", 0.50

    def start(self):
        self.is_running = True
        while self.is_running:
            self.run_cycle()
            time.sleep(60) # Interval for H1 or similar

    def stop(self):
        self.is_running = False
        print("Strategy Engine Stopped.")
