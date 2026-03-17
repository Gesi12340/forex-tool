from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
import os
import sys
import threading
import time
from dotenv import load_dotenv

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.mpesa_adapter import MpesaAdapter
from backend.strategy_engine import StrategyEngine
from backend.broker_client import MT5Client
from backend.risk_manager import RiskManager
from backend.data_processor import DataProcessor

load_dotenv()

app = Flask(__name__, static_folder="../dist")
CORS(app)

# Initialize Real Components
broker = MT5Client()
risk = RiskManager()
processor = DataProcessor()
engine = StrategyEngine(broker, risk, processor)

mpesa = MpesaAdapter(
    os.getenv("MPESA_CONSUMER_KEY"),
    os.getenv("MPESA_CONSUMER_SECRET"),
    os.getenv("MPESA_SHORTCODE"),
    os.getenv("MPESA_PASSKEY"),
    os.getenv("MPESA_ENV", "sandbox")
)

@app.route("/")
def serve_dashboard():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/<path:path>")
def serve_static(path):
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")

@app.route("/api/status")
def get_status():
    acc = broker.get_account_summary()
    
    # Try to get real market price for XAUUSD
    price = 0
    try:
        candles = broker.get_candles("XAUUSD", count=1)
        if candles:
            price = float(candles[-1]['mid']['c'])
    except:
        price = 1.08502 # Fallback
        
    return jsonify({
        "stats": {
            "balance": acc.get('balance', 0),
            "equity": acc.get('equity', 0),
            "dailyPnL": 0,
            "is_trained": True,
            "is_running": engine.is_running,
            "market_price": price
        },
        "status": "System Online (Local Mode)",
        "last_update": time.time()
    })

@app.route("/api/command", methods=["POST"])
def handle_command():
    data = request.json
    action = data.get("action")
    print(f"[SERVER] Received command: {action}")
    
    if action == "START":
        if not engine.is_running:
            # We run the engine loop in a background thread
            t = threading.Thread(target=engine.start)
            t.daemon = True
            t.start()
            return jsonify({"status": "SUCCESS: AI Engine Started."})
        return jsonify({"status": "INFO: Already running."})
        
    elif action == "STOP":
        engine.stop()
        return jsonify({"status": "SUCCESS: AI Engine Halted."})
        
    elif action == "DEPOSIT":
        phone = data.get("phone")
        amount = data.get("amount")
        # In local mode, callback URL should point to a public IP or be skipped for testing
        resp = mpesa.initiate_stk_push(phone, amount, "GesiTrader", "https://gesi-relay.vercel.app/api/mpesa/callback")
        return jsonify(resp)

    return jsonify({"error": "Unknown action"}), 400

@app.route("/api/mpesa/callback", methods=["POST"])
def mpesa_callback():
    data = request.json
    print(f"[SERVER] M-Pesa Callback Received: {data}")
    return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"})

if __name__ == "__main__":
    print("\n" + "="*50)
    print("GESI AI TRADING BOT - LOCAL SERVER")
    print(f"Dashboard: http://localhost:5000")
    print("="*50 + "\n")
    app.run(host="127.0.0.1", port=5000, debug=False)
