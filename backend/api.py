import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from backend.broker_client import get_broker_client
from backend.strategy_engine import StrategyEngine
from backend.risk_manager import RiskManager
from backend.data_processor import DataProcessor
from backend.mpesa_adapter import MpesaAdapter
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

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
    env=os.getenv("MPESA_ENV", "sandbox") # Now reads from .env, defaults to sandbox
)

@app.route('/api/deposit/mpesa', methods=['POST'])
def mpesa_deposit():
    data = request.json
    amount = data.get('amount', 1)
    phone = data.get('phone') # Expected format: 2547XXXXXXXX
    account_ref = data.get('reference', 'TradingBot')
    callback = data.get('callback', 'https://your-domain.com/api/mpesa/callback')
    
    transaction_type = os.getenv("MPESA_TYPE", "CustomerBuyGoodsOnline")
    response = mpesa.initiate_stk_push(phone, amount, account_ref, callback, transaction_type)
    
    if response.get("ResponseCode") == "0":
        return jsonify({"status": "SUCCESS", "message": "STK Push Sent", "details": response})
    return jsonify({"status": "FAILED", "message": response.get("CustomerMessage", "Unknown Error")})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    account = broker.get_account_summary()
    return jsonify({
        "balance": account['balance'],
        "equity": account['equity'],
        "dailyPnL": 0.0,
        "drawdown": 0.0,
        "is_trained": engine.ai.is_trained
    })

@app.route('/api/train', methods=['POST'])
def manual_train():
    """Manually flag AI as trained for testing."""
    engine.ai.is_trained = True
    return jsonify({"status": "TRAINED", "is_trained": True})

@app.route('/api/start', methods=['POST'])
def start_trading():
    if not engine.is_running:
        import threading
        thread = threading.Thread(target=engine.start)
        thread.start()
        return jsonify({"status": "STARTED"})
    return jsonify({"status": "ALREADY_RUNNING"})

@app.route('/api/stop', methods=['POST'])
def stop_trading():
    engine.stop()
    return jsonify({"status": "HALTED"})

if __name__ == '__main__':
    # Auto-start trading engine in a background thread on launch
    import threading
    trading_thread = threading.Thread(target=engine.start, daemon=True)
    trading_thread.start()
    print(">>> AUTO-START: Trading Engine is now LIVE and searching for profits...")
    
    app.run(port=5000, debug=False)
