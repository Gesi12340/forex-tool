import os
import time
import requests
import threading
from dotenv import load_dotenv
from backend.relay_manager import RelayManager
from backend.mpesa_adapter import MpesaAdapter

load_dotenv()

class MockBroker:
    def get_account_summary(self):
        return {"balance": 1000, "equity": 1050}
    def get_candles(self, instrument, count=1):
        return [{"mid": {"c": 1.0850}}]
    def get_open_positions(self, symbol=""):
        return []

class MockEngine:
    def __init__(self):
        self.is_running = False
        self.broker = MockBroker()
    def start(self):
        self.is_running = True
        print("MOCK: Engine Started")
    def stop(self):
        self.is_running = False
        print("MOCK: Engine Stopped")

def simulate_web_command(action, data=None):
    relay_id = "019cfb6a-5670-7f08-b572-eb65ed439b6f"
    url = f"https://jsonblob.com/api/jsonBlob/{relay_id}"
    print(f"\nSIMULATOR: Sending {action} to cloud...")
    try:
        resp = requests.get(url)
        payload = resp.json()
        payload["command"] = {"action": action, **(data or {})}
        requests.put(url, json=payload)
        print(f"SIMULATOR: Command {action} queued.")
    except Exception as e:
        print(f"SIMULATOR ERROR: {e}")

if __name__ == "__main__":
    engine = MockEngine()
    mpesa = MpesaAdapter(
        os.getenv("MPESA_CONSUMER_KEY"),
        os.getenv("MPESA_CONSUMER_SECRET"),
        os.getenv("MPESA_SHORTCODE"),
        os.getenv("MPESA_PASSKEY"),
        os.getenv("MPESA_ENV", "sandbox")
    )
    
    relay = RelayManager(engine, mpesa)
    
    # Start relay in thread
    relay_thread = threading.Thread(target=relay.main_loop)
    relay_thread.daemon = True
    relay_thread.start()
    
    time.sleep(2)
    # Simulate a START command
    simulate_web_command("START")
    time.sleep(5)
    
    if engine.is_running:
        print("\nVERIFICATION: Relay START command successful!")
    else:
        print("\nVERIFICATION: Relay START command FAILED.")

    # Simulate a DEPOSIT command (STK Push check)
    simulate_web_command("DEPOSIT", {"phone": "254700000000", "amount": "10"})
    time.sleep(5)
    
    print("\nVERIFICATION: Check logs above for M-Pesa response.")
    
    # Simulate a STOP command
    simulate_web_command("STOP")
    time.sleep(5)
    
    if not engine.is_running:
        print("\nVERIFICATION: Relay STOP command successful!")
    else:
        print("\nVERIFICATION: Relay STOP command FAILED.")
