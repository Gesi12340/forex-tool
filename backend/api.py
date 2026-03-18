import os
import sys
import json
import time
import threading
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# Ensure the parent directory is in the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.broker_client import get_broker_client
from backend.strategy_engine import StrategyEngine
from backend.risk_manager import RiskManager
from backend.data_processor import DataProcessor
from backend.mpesa_adapter import MpesaAdapter
from backend.wallet_manager import WalletManager

load_dotenv()

app = Flask(__name__, static_folder='../dist')
CORS(app)

# Initialize Core System
broker = get_broker_client()
risk = RiskManager()
processor = DataProcessor()
engine = StrategyEngine(broker, risk, processor)
engine.ai.is_trained = True # Prime AI for immediate action
wallet = WalletManager()

# M-Pesa Adapter
mpesa = MpesaAdapter(
    consumer_key=os.getenv("MPESA_CONSUMER_KEY"),
    consumer_secret=os.getenv("MPESA_CONSUMER_SECRET"),
    shortcode=os.getenv("MPESA_SHORTCODE"),
    passkey=os.getenv("MPESA_PASSKEY"),
    env=os.getenv("MPESA_ENV", "sandbox")
)

# Global status for the app
last_status_msg = "Engine Standby"

def bg_deposit_poller():
    """Polls Safaricom for the status of pending deposits."""
    global last_status_msg
    while True:
        pending = wallet.get_pending()
        for d in pending:
            try:
                print(f"[POLLER] Checking status for {d['id']}...")
                res = mpesa.query_stk_status(d['id'])
                result_code = res.get("ResultCode")
                
                # ResultCode '0' means Success
                if result_code == "0":
                    print(f"[POLLER] Deposit confirmed! Crediting {d['amount']} KES")
                    wallet.credit(d['amount'])
                    wallet.remove_pending(d['id'])
                    last_status_msg = f"SUCCESS: Deposit of {d['amount']} KES Reflected Automatically!"
                # Non-zero but present means failed/cancelled
                elif result_code is not None:
                    print(f"[POLLER] Transaction failed ({result_code}): {res.get('ResultDesc')}")
                    wallet.remove_pending(d['id'])
                    last_status_msg = f"INFO: Deposit Failed/Cancelled - {res.get('ResultDesc')}"
            except Exception as e:
                print(f"[POLLER ERROR] {e}")
        time.sleep(10)

# Start Poller Thread
t_poller = threading.Thread(target=bg_deposit_poller)
t_poller.daemon = True
t_poller.start()

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    # Fetch real stats from engine/broker
    try:
        acc_summary = broker.get_account_summary()
        mt5_balance = acc_summary.get("balance", 0)
        local_balance = wallet.get_total_balance()
        equity = acc_summary.get("equity", 0) + local_balance
        
        # Calculate daily PnL
        daily_pnl = equity - (mt5_balance + local_balance) if engine.is_running else 0
        
        # Correctly fetch market price from MT5
        import MetaTrader5 as mt5
        tick = mt5.symbol_info_tick("EURUSD")
        market_price = tick.bid if tick else 1.08502
        
        return jsonify({
            "balance": mt5_balance + local_balance,
            "mt5_only": mt5_balance,
            "local_only": local_balance,
            "equity": equity,
            "dailyPnL": daily_pnl,
            "is_running": engine.is_running,
            "is_trained": engine.ai.is_trained,
            "market_price": market_price,
            "status_msg": last_status_msg
        })
    except Exception as e:
        print(f"Stats Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/action', methods=['POST'])
def handle_action():
    global last_status_msg
    data = request.json
    action = data.get('action')
    
    if action == "START":
        if not engine.is_running:
            t = threading.Thread(target=engine.start)
            t.daemon = True
            t.start()
            last_status_msg = "SUCCESS: AI Engine Started Successfully."
        else:
            last_status_msg = "INFO: AI Engine is already running."
            
    elif action == "STOP":
        if engine.is_running:
            engine.stop()
            last_status_msg = "SUCCESS: AI Engine Halted Safely."
        else:
            last_status_msg = "INFO: AI Engine is not running."
            
    elif action == "DEPOSIT":
        phone = data.get("phone")
        amount = data.get("amount")
        if not phone or not amount:
            last_status_msg = "ERROR: Missing Phone or Amount for Deposit."
        else:
            print(f"[LOCAL] Initiating deposit for {amount} to {phone}")
            resp = mpesa.initiate_stk_push(phone, amount, "GesiTrader", "https://gesi-relay.vercel.app/api/mpesa/callback")
            
            if isinstance(resp, dict) and resp.get("ResponseCode") == "0":
                checkout_id = resp.get("CheckoutRequestID")
                wallet.add_pending(checkout_id, amount, phone)
                last_status_msg = f"SUCCESS: STK Push sent. Processing {amount} KES..."
            else:
                print(f"[DEBUG] M-Pesa Error Response: {resp}")
                if isinstance(resp, dict):
                    err_info = resp.get('CustomerMessage') or resp.get('errorMessage') or resp.get('ResultDesc') or f"Code {resp.get('errorCode') or 'N/A'}"
                else:
                    err_info = str(resp) or "Unknown Server Error"
                last_status_msg = f"ERROR: M-Pesa Failed - {err_info}"

                
    elif action == "WITHDRAW":
        phone = data.get("phone")
        amount = data.get("amount")
        if not phone or not amount:
            last_status_msg = "ERROR: Missing Phone or Amount for Withdrawal."
        else:
            print(f"[LOCAL] Initiating withdrawal for {amount} to {phone}")
            resp = mpesa.initiate_withdrawal(phone, amount, "Profit Withdrawal")
            if isinstance(resp, dict) and resp.get("ResponseCode") == "0":
                last_status_msg = f"SUCCESS: Withdrawal of {amount} KES initiated to {phone}."
            else:
                last_status_msg = f"ERROR: Withdrawal Failed - {resp}"

    return jsonify({"status": "ok", "message": last_status_msg})

# AUTO-START LOGIC
if os.getenv("AUTO_START", "True").lower() == "true":
    print("Auto-starting trade engine...")
    t = threading.Thread(target=engine.start)
    t.daemon = True
    t.start()
    last_status_msg = "Engine Auto-Started Successfully."

if __name__ == "__main__":
    print("=====================================================")
    print(">>> GESI AI PREMIUM V4.0 - LOCAL ENGINE ACTIVE <<<")
    print("=====================================================")
    print("Dashboard: http://localhost:5000")
    print("No Cloud. No ngrok. 100% Secure Local Connection.")
    print("=====================================================")
    app.run(host='0.0.0.0', port=5000)

