import time
import requests
import json
import os
import threading

class RelayManager:
    """
    Connects the local MT5 engine to the Cloud Dashboard without ngrok.
    Uses Firebase Realtime Database REST API.
    """
    def __init__(self, engine, mpesa):
        # Using JSONBlob as a more stable alternative to Firebase/npoint
        self.relay_id = "019cfa65-ac81-7121-a9ac-bcc786dcf68e"
        self.api_url = f"https://jsonblob.com/api/jsonBlob/{self.relay_id}"
        self.running = False
        self.engine = engine
        self.mpesa = mpesa
        
    def get_cloud_state(self):
        try:
            resp = requests.get(self.api_url, timeout=15)
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    return data if data else {}
                except Exception as e:
                    print(f"[RELAY DEBUG] Failed to parse JSON: {e}")
            else:
                print(f"[RELAY DEBUG] Status Code: {resp.status_code}")
        except Exception as e:
            print(f"[RELAY DEBUG] Get Error: {e}")
        return {}

    def main_loop(self):
        print(f"[RELAY] Cloud Sync Started on Firebase. ID: {self.relay_id}")
        self.running = True
        
        # Initialize Firebase object if empty
        if not self.get_cloud_state():
            requests.put(self.api_url, json={"stats": {}, "command": None, "status": ""})
            
        while self.running:
            try:
                # 1. Fetch current cloud state to see if there's a command
                cloud_state = self.get_cloud_state()
                print(f"[RELAY DEBUG] Received: {cloud_state}")
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
                            status_msg = f"SUCCESS: STK Push sent to {phone}. Check phone to complete deposit."
                        else:
                            status_msg = f"ERROR: {resp.get('CustomerMessage', 'Unknown Error')}"
                            
                    elif action == "WITHDRAW":
                        phone = command.get("phone")
                        amount = command.get("amount")
                        print(f"[RELAY] Initiating withdrawal for {amount} to {phone}")
                        # In production, SecurityCredential would be managed via environment or vault
                        sec_cred = os.getenv("MPESA_SEC_CREDENTIAL", "MOCK_ENCRYPTED_PASS")
                        resp = self.mpesa.initiate_withdrawal(phone, amount, "https://your-domain.com/api/mpesa/withdraw-callback", sec_cred)
                        if resp.get("ResponseCode") == "0":
                            status_msg = f"SUCCESS: Withdrawal of {amount} KES initiated. Funds will arrive shortly."
                        else:
                            status_msg = f"ERROR: Withdrawal failed. {resp.get('CustomerMessage', 'Internal Error')}"
                            
                    # Clear command after processing
                    command = None
                
                # 1. Get Local Data & Market Price
                acc = self.engine.broker.get_account_summary()
                
                # Fetch live price for the main instrument (e.g., EURUSD)
                instrument = "EURUSD"
                candles = self.engine.broker.get_candles(instrument, count=1)
                curr_price = 0
                if candles:
                    curr_price = float(candles[-1]['mid']['c'])

                status = {
                    "balance": acc.get('balance', 0) if acc else 0,
                    "equity": acc.get('equity', 0) if acc else 0,
                    "dailyPnL": 0, # To be calculated
                    "is_trained": True,
                    "is_running": self.engine.is_running,
                    "market_price": curr_price
                }
                
                # 4. Sync new state to Cloud using PUT to overwrite the exact node
                payload = {
                    "stats": status,
                    "command": command,
                    "status": status_msg,
                    "last_update": time.time()
                }
                requests.put(self.api_url, json=payload, timeout=5)

            except Exception as e:
                print(f"[RELAY ERROR] Sync failed: {e}")
                import traceback
                traceback.print_exc()
                pass # Silently retry on network drops
            
            time.sleep(2) # Faster polling for responsive UX

    def start(self):
        t = threading.Thread(target=self.main_loop)
        t.daemon = True
        t.start()
