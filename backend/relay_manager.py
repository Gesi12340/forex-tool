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
        self.relay_id = "019cff51-9acf-75cc-9685-304ab695d7a7"
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
        
        # Initialize Firebase object if empty or missing 'stats'
        initial_payload = {
            "stats": {"balance": 0, "equity": 0, "dailyPnL": 0, "is_trained": True, "is_running": False, "market_price": 1.085},
            "command": None,
            "status": "System Online",
            "processed_command": None,
            "last_update": time.time()
        }
        cloud = self.get_cloud_state()
        if not cloud or "stats" not in cloud:
            print("[RELAY] Initializing fresh cloud state...")
            requests.put(self.api_url, json=initial_payload, timeout=10)
        else:
            print("[RELAY] Connected to existing cluster.")
            
        while self.running:
            try:
                # 1. Fetch current cloud state to see if there's a command
                cloud_state = self.get_cloud_state()
                print(f"[RELAY DEBUG] Received: {cloud_state}")
                command = cloud_state.get("command")
                
                # 3. Handle Commands
                status_msg = cloud_state.get("status", "")
                if command and command != cloud_state.get("processed_command"):
                    print(f"[RELAY] Command Received from Web: {command}")
                    action = command.get("action") if isinstance(command, dict) else command
                    
                    if action == "START":
                        if not self.engine.is_running:
                            t = threading.Thread(target=self.engine.start)
                            t.daemon = True
                            t.start()
                            status_msg = "SUCCESS: AI Engine Started Successfully."
                        else:
                            status_msg = "INFO: AI Engine is already running."
                    elif action == "STOP":
                        if self.engine.is_running:
                            self.engine.stop()
                            status_msg = "SUCCESS: AI Engine Halted Safely."
                        else:
                            status_msg = "INFO: AI Engine is not running."
                    elif action == "DEPOSIT":
                        phone = command.get("phone")
                        amount = command.get("amount")
                        if not phone or not amount:
                            status_msg = "ERROR: Missing Phone or Amount for Deposit."
                        else:
                            print(f"[RELAY] Initiating deposit for {amount} to {phone}")
                            resp = self.mpesa.initiate_stk_push(phone, amount, "GesiTrader", "https://gesi-relay.vercel.app/api/mpesa/callback")
                            if isinstance(resp, dict) and resp.get("ResponseCode") == "0":
                                status_msg = f"SUCCESS: STK Push sent to {phone}. Enter PIN to complete."
                            else:
                                err_info = resp.get('CustomerMessage', 'Unknown Error') if isinstance(resp, dict) else str(resp)
                                status_msg = f"ERROR: M-Pesa Failed - {err_info}"
                            
                    elif action == "WITHDRAW":
                        phone = command.get("phone")
                        amount = command.get("amount")
                        if not phone or not amount:
                            status_msg = "ERROR: Missing Phone or Amount for Withdrawal."
                        else:
                            print(f"[RELAY] Initiating withdrawal for {amount} to {phone}")
                            sec_cred = os.getenv("MPESA_SEC_CREDENTIAL", "MOCK_ENCRYPTED_PASS")
                            resp = self.mpesa.initiate_withdrawal(phone, amount, "https://gesi-relay.vercel.app/api/mpesa/withdraw-callback", sec_cred)
                            if resp.get("ResponseCode") == "0":
                                status_msg = f"SUCCESS: Withdrawal of {amount} KES initiated."
                            else:
                                status_msg = f"ERROR: Withdrawal failed - {resp.get('CustomerMessage', 'Internal Error')}"
                            
                    # Mark command as processed
                    if isinstance(cloud_state, dict):
                        cloud_state["processed_command"] = command
                    command = None
                
                # 1. Get Local Data & Market Price
                acc = self.engine.broker.get_account_summary()
                
                # Fetch live price for the main instrument (e.g., EURUSD)
                instrument = "EURUSD"
                curr_price = 0
                try:
                    candles = self.engine.broker.get_candles(instrument, count=1)
                    if candles:
                        curr_price = float(candles[-1]['mid']['c'])
                except:
                    pass

                status = {
                    "balance": acc.get('balance', 0) if acc else 0,
                    "equity": acc.get('equity', 0) if acc else 0,
                    "dailyPnL": 0, 
                    "is_trained": True,
                    "is_running": self.engine.is_running,
                    "market_price": curr_price
                }
                
                # 4. Sync new state to Cloud
                # If we processed a command, we clear it in the cloud. 
                # If command is None it means it was handled or wasn't there.
                payload = {
                    "stats": status,
                    "command": None if command is None else cloud_state.get("command"),
                    "processed_command": cloud_state.get("processed_command"),
                    "status": status_msg,
                    "last_update": time.time()
                }
                requests.put(self.api_url, json=payload, timeout=8)

            except Exception as e:
                print(f"[RELAY ERROR] Sync failed: {e}")
                import traceback
                traceback.print_exc()
                pass # Silently retry on network drops
            
            time.sleep(5.0) # Balanced polling

    def start(self):
        t = threading.Thread(target=self.main_loop)
        t.daemon = True
        t.start()
