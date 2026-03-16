import time
import requests
import json
import os
import threading

class RelayManager:
    """
    Connects the local MT5 engine to the Cloud Dashboard without ngrok.
    Uses npoint.io as a secure JSON relay.
    """
    def __init__(self, engine, mpesa, relay_id="e6b7d9b9f0a2d4c3e1b8"): # Unique ID for Gesi12340
        self.relay_id = relay_id
        self.api_url = f"https://api.npoint.io/{self.relay_id}"
        self.running = False
        self.engine = engine
        self.mpesa = mpesa
        
    def get_cloud_state(self):
        try:
            resp = requests.get(self.api_url, timeout=5)
            if resp.status_code == 200:
                return resp.json()
        except:
            pass
        return {}

    def main_loop(self):
        print(f"[RELAY] Cloud Sync Started. ID: {self.relay_id}")
        self.running = True
        while self.running:
            try:
                # 1. Get Local Data
                acc = self.engine.broker.get_account_summary()
                status = {
                    "balance": acc.get('balance', 0) if acc else 0,
                    "equity": acc.get('equity', 0) if acc else 0,
                    "dailyPnL": 0, # To be calculated
                    "is_trained": True,
                    "is_running": self.engine.is_running
                }
                
                # 2. Fetch current cloud state to see if there's a command
                cloud_state = self.get_cloud_state()
                command = cloud_state.get("command")
                
                # 3. Handle Commands
                status_msg = cloud_state.get("status", "")
                if command:
                    print(f"[RELAY] Command Received from Web: {command}")
                    action = command.get("action") if isinstance(command, dict) else command
                    
                    if action == "START":
                        if not self.engine.is_running:
                            t = threading.Thread(target=self.engine.start)
                            t.daemon = True
                            t.start()
                            status_msg = "STARTED"
                    elif action == "STOP":
                        self.engine.stop()
                        status_msg = "HALTED"
                    elif action == "DEPOSIT":
                        phone = command.get("phone")
                        amount = command.get("amount")
                        print(f"[RELAY] Initiating deposit for {amount} to {phone}")
                        resp = self.mpesa.initiate_stk_push(phone, amount, "TradingBot", "https://your-domain.com/api/mpesa/callback", os.getenv("MPESA_TYPE", "CustomerBuyGoodsOnline"))
                        if resp.get("ResponseCode") == "0":
                            status_msg = f"SUCCESS"
                        else:
                            status_msg = f"ERROR: {resp.get('CustomerMessage', 'Unknown Error')}"
                            
                    # Clear command after processing
                    command = None
                
                # 4. Sync new state to Cloud
                payload = {
                    "stats": status,
                    "command": command,
                    "status": status_msg,
                    "last_update": time.time()
                }
                requests.post(self.api_url, json=payload, timeout=5)

            except Exception as e:
                pass # Silently retry on network drops
            
            time.sleep(2) # Faster polling for responsive UX

    def start(self):
        t = threading.Thread(target=self.main_loop)
        t.daemon = True
        t.start()
