import os
import time
from backend.broker_client import get_broker_client
from backend.strategy_engine import StrategyEngine
from backend.risk_manager import RiskManager
from backend.data_processor import DataProcessor
from backend.mpesa_adapter import MpesaAdapter
from backend.relay_manager import RelayManager
from dotenv import load_dotenv

load_dotenv()

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

# Start Cloud Relay
relay = RelayManager(engine, mpesa)
relay.start()

print("=====================================================")
print(">>> TRADING BOT STARTED IN CLOUD RELAY MODE <<<")
print("=====================================================")
print(f"Cloud Relay ID : {relay.relay_id}")
print("No ngrok needed. Connecting securely to the dashboard...")
print("=====================================================")

# Auto-start trading engine based on start command or just keep process alive
# Keeping main thread alive
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Exiting...")
    engine.stop()
