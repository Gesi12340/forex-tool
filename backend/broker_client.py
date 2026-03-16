import os
import random
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

try:
    import MetaTrader5 as mt5
    HAS_MT5 = True
except ImportError:
    HAS_MT5 = False

class MT5Client:
    """
    Universal MetaTrader 5 Client.
    Supports Exness, FXPesa, XM, HFM, etc. - all major Kenyan M-Pesa brokers.
    """
    def __init__(self):
        if not HAS_MT5:
            print("WARNING: MetaTrader5 library not installed. Use 'pip install MetaTrader5'")
            self.is_connected = False
            return
            
        paths_to_try = [
            None, # Default MT5 behavior
            r"C:\Program Files\EGM Securities MetaTrader 5 Terminal\terminal64.exe",
            r"C:\Program Files\InstaForex MT5 Terminal\terminal64.exe",
            r"C:\Program Files\MetaTrader 5\terminal64.exe",
            r"C:\Program Files\FXPesa MT5 Terminal\terminal64.exe"
        ]
        
        init_success = False
        for path in paths_to_try:
            if path is None:
                if mt5.initialize():
                    init_success = True
                    break
            elif os.path.exists(path):
                if mt5.initialize(path=path):
                    print(f"MT5 Initialized successfully using path: {path}")
                    init_success = True
                    break

        if not init_success:
            print("MT5 initialization failed across all known paths. Ensure MT5 Terminal is open and Python has Administrator privileges.")
            self.is_connected = False
            return

        # Attempt to login using environment variables
        login = int(os.getenv("MT5_LOGIN", 0))
        password = os.getenv("MT5_PASSWORD", "")
        server = os.getenv("MT5_SERVER", "")
        
        if login and password and server:
            if not mt5.login(login, password=password, server=server):
                print(f"MT5 login failed (error {mt5.last_error()}). Check credentials in .env")
                self.is_connected = False
            else:
                print(f"MT5 Connected & Logged in as {login} Successfully!")
                self.is_connected = True
        else:
            print("MT5 Credentials missing in .env. Falling back to Terminal default login.")
            self.is_connected = True

    def get_account_summary(self):
        if not self.is_connected: return {"balance": 0, "equity": 0}
        acc_info = mt5.account_info()
        return {
            "balance": acc_info.balance if acc_info else 0,
            "equity": acc_info.equity if acc_info else 0,
            "currency": acc_info.currency if acc_info else "USD"
        }

    def get_candles(self, instrument, count=100, granularity=None):
        """Fetches historical OHLC data from MT5."""
        if not self.is_connected: return []
        
        # Mapping standard names to MT5 symbols if necessary
        symbol = instrument.replace("_", "") 
        
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, count)
        if rates is None:
            print(f"Failed to fetch rates for {symbol}")
            return []
            
        candles = []
        for rate in rates:
            candles.append({
                "time": datetime.fromtimestamp(rate['time']).isoformat(),
                "mid": {
                    "o": str(rate['open']),
                    "h": str(rate['high']),
                    "l": str(rate['low']),
                    "c": str(rate['close'])
                },
                "volume": int(rate['tick_volume'])
            })
        return candles

    def create_order(self, instrument, units, order_type="MARKET", price=None, take_profit=None, stop_loss=None):
        """Places a trade on MT5."""
        if not self.is_connected: return {"error": "Not connected"}
        
        symbol = instrument.replace("_", "")
        mt5_order_type = mt5.ORDER_TYPE_BUY if units > 0 else mt5.ORDER_TYPE_SELL
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(abs(units) / 100000.0), # Convert units to lots
            "type": mt5_order_type,
            "price": mt5.symbol_info_tick(symbol).ask if units > 0 else mt5.symbol_info_tick(symbol).bid,
            "sl": float(stop_loss) if stop_loss else 0.0,
            "tp": float(take_profit) if take_profit else 0.0,
            "magic": 123456,
            "comment": "AI Bot Trade",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Order failed, retcode={result.retcode}")
            return {"error": str(result.retcode)}
        
        print(f"MT5 Order Executed: {result.order}")
        return {"id": str(result.order), "status": "FILLED"}

    def get_open_positions(self, symbol=None):
        """Retrieves active positions from MT5."""
        if not self.is_connected: return []
        positions = mt5.positions_get(symbol=symbol) if symbol else mt5.positions_get()
        if positions is None: return []
        
        result = []
        for p in positions:
            result.append({
                "ticket": p.ticket,
                "symbol": p.symbol,
                "type": "BUY" if p.type == mt5.POSITION_TYPE_BUY else "SELL",
                "volume": p.volume,
                "price_open": p.price_open,
                "sl": p.sl,
                "tp": p.tp,
                "price_current": p.price_current,
                "profit": p.profit
            })
        return result

    def update_order_sl(self, ticket, symbol, new_sl):
        """Modifies the Stop-Loss of an existing position."""
        if not self.is_connected: return False
        
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "symbol": symbol,
            "position": ticket,
            "sl": float(new_sl),
            "tp": 0.0, # TP remains unchanged if not specified, but MT5 usually needs current TP
        }
        
        # Fetch current position to get TP
        pos = mt5.positions_get(ticket=ticket)
        if pos:
            request["tp"] = pos[0].tp

        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"SL Update failed for ticket {ticket}, retcode={result.retcode}")
            return False
        return True

def get_broker_client():
    """Returns the MT5 client, the gold standard for Kenyan brokers."""
    return MT5Client()
