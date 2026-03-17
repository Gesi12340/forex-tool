import sys
import os
import subprocess
import time
from backend.relay_manager import RelayManager
from backend.mpesa_adapter import MpesaAdapter
from dotenv import load_dotenv

# Mock dependencies if they block initialization
class MockBroker:
    def get_account_summary(self): return {"balance": 1000, "equity": 1050}
    def get_candles(self, i, count=1): return [{"mid": {"c": 1.085}}]

class MockEngine:
    def __init__(self):
        self.is_running = False
        self.broker = MockBroker()
    def start(self): self.is_running = True
    def stop(self): self.is_running = False

load_dotenv()

def run_diagnostics():
    print("--- GESI RELAY DIAGNOSTICS ---")
    
    # 1. Check Credentials
    print(f"Shortcode: {os.getenv('MPESA_SHORTCODE')}")
    
    # 2. Run Relay with reduced timeout for quick check
    engine = MockEngine()
    mpesa = MpesaAdapter(
        os.getenv("MPESA_CONSUMER_KEY"),
        os.getenv("MPESA_CONSUMER_SECRET"),
        os.getenv("MPESA_SHORTCODE"),
        os.getenv("MPESA_PASSKEY"),
        os.getenv("MPESA_ENV", "sandbox")
    )
    
    relay = RelayManager(engine, mpesa)
    print(f"Testing Connectivity to Blob: {relay.relay_id}")
    
    # Capture first few sync attempts
    import threading
    log_output = []
    
    def relay_runner():
        relay.main_loop()

    # Small hack to stop the loop after a few iterations
    def stopper():
        time.sleep(15)
        relay.running = False
    
    t1 = threading.Thread(target=relay_runner)
    t2 = threading.Thread(target=stopper)
    
    t1.start()
    t2.start()
    
    t1.join()
    print("\n--- Diagnostics Complete ---")

if __name__ == "__main__":
    run_diagnostics()
