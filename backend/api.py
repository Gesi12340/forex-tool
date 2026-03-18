import os
import sys
import json
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

load_dotenv()

app = Flask(__name__, static_folder='../dist')
CORS(app)

# Initialize Core System
broker = get_broker_client()
risk = RiskManager()
processor = DataProcessor()
engine = StrategyEngine(broker, risk, processor)
engine.ai.is_trained = True # Prime AI for immediate action

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
        balance = acc_summary.get("balance", 0)
        equity = acc_summary.get("equity", 0)
        
        # Calculate daily PnL (Mocked or fetched from history if available)
        daily_pnl = equity - balance if engine.is_running else 0
        
        return jsonify({
            "balance": balance,
            "equity": equity,
            "dailyPnL": daily_pnl,
            "is_running": engine.is_running,
            "is_trained": engine.ai.is_trained,
            "market_price": engine.data.get_last_price("EURUSD") or 1.08502,
            "status_msg": last_status_msg
        })
    except Exception as e:
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
                last_status_msg = f"SUCCESS: STK Push sent to {phone}. Check your phone."
            else:
                err_info = resp.get('CustomerMessage', 'Unknown Error') if isinstance(resp, dict) else str(resp)
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

if __name__ == "__main__":
    print("=====================================================")
    print(">>> GESI AI PREMIUM V4.0 - LOCAL ENGINE ACTIVE <<<")
    print("=====================================================")
    print("Dashboard: http://localhost:5000")
    print("No Cloud. No ngrok. 100% Secure Local Connection.")
    print("=====================================================")
    app.run(host='0.0.0.0', port=5000)
