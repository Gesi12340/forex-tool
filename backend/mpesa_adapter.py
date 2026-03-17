import requests
import json
import logging
import base64
import os
import time
from datetime import datetime

class MpesaAdapter:
    """
    Handles M-Pesa integration via Safaricom Daraja API.
    Securely handles deposits via STK Push.
    """
    def __init__(self, consumer_key, consumer_secret, shortcode, passkey, env="sandbox"):
        self.env = env.lower()
        self.base_url = "https://sandbox.safaricom.co.ke" if self.env == "sandbox" else "https://api.safaricom.co.ke"
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.shortcode = str(shortcode)
        self.passkey = passkey
        self._token = None
        self._token_expiry = 0
        
        # Critical Sandbox Warning
        if self.env == "sandbox" and self.shortcode != "174379":
            print(f"!!! [MPESA WARNING] !!!\nYou are in SANDBOX mode but using Shortcode: {self.shortcode}.\nSafaricom Sandbox ONLY supports STK Push with Shortcode: 174379.\nPlease update your .env to use 174379 for testing.")

    def get_access_token(self):
        """Retrieves and caches OAuth2 access token from Safaricom API."""
        if self._token and time.time() < self._token_expiry:
            return self._token

        api_url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        try:
            response = requests.get(api_url, auth=(self.consumer_key, self.consumer_secret))
            response.raise_for_status()
            data = response.json()
            self._token = data.get("access_token")
            # Safaricom tokens last 3599 seconds (~1 hour). We cache for 50 mins.
            self._token_expiry = time.time() + 3000 
            return self._token
        except Exception as e:
            logging.error(f"Failed to get M-Pesa access token: {e}")
            return None

    def format_phone(self, phone):
        """Formats phone to 2547XXXXXXXX."""
        phone = str(phone).strip().replace("+", "")
        if phone.startswith("0"):
            return "254" + phone[1:]
        elif phone.startswith("7") or phone.startswith("1"):
            return "254" + phone
        return phone

    def initiate_stk_push(self, phone_number, amount, account_reference, callback_url, transaction_type="CustomerBuyGoodsOnline"):
        """
        Triggers an M-Pesa STK Push.
        """
        access_token = self.get_access_token()
        if not access_token:
            print("[MPESA] Auth Failed - No Access Token")
            return {"ResponseCode": "1", "CustomerMessage": "Auth Failed"}

        phone_number = self.format_phone(phone_number)
        
        # Determine transaction type
        final_transaction_type = transaction_type
        if len(str(self.shortcode)) >= 8:
            final_transaction_type = "CustomerPayBillOnline"
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = base64.b64encode(f"{self.shortcode}{self.passkey}{timestamp}".encode()).decode()
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Payload construction - strictly follow Daraja API requirements
        payload = {
            "BusinessShortCode": str(self.shortcode),
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": final_transaction_type,
            "Amount": int(float(amount)),
            "PartyA": str(phone_number),
            "PartyB": str(self.shortcode), 
            "PhoneNumber": str(phone_number),
            "CallBackURL": callback_url,
            "AccountReference": str(account_reference)[:12],
            "TransactionDesc": "GesiTrade"
        }

        print(f"[MPESA DEBUG] Final Payload: {json.dumps(payload)}")
        api_url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
        try:
            response = requests.post(api_url, json=payload, headers=headers)
            res_json = response.json()
            if response.status_code != 200:
                print(f"[MPESA ERROR] API returned {response.status_code}: {res_json}")
            else:
                print(f"[MPESA SUCCESS] {res_json.get('CustomerMessage')}")
            return res_json
        except Exception as e:
            print(f"[MPESA EXCEPTION] {e}")
            return {"ResponseCode": "1", "CustomerMessage": str(e)}

    def initiate_withdrawal(self, phone_number, amount, callback_url, security_credential):
        """
        Triggers an M-Pesa B2C payment to the user's phone.
        phone_number: Format 2547XXXXXXXX
        security_credential: Encrypted initiator password
        """
        access_token = self.get_access_token()
        if not access_token:
            return {"ResponseCode": "1", "CustomerMessage": "Auth Failed"}

        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        payload = {
            "InitiatorName": "TradingBotAPI",
            "SecurityCredential": security_credential,
            "CommandID": "BusinessPayment",
            "Amount": amount,
            "PartyA": self.shortcode,
            "PartyB": phone_number,
            "Remarks": "Profit Withdrawal",
            "QueueTimeOutURL": callback_url,
            "ResultURL": callback_url,
            "Occasion": "Trading Profit"
        }

        api_url = f"{self.base_url}/mpesa/b2c/v1/paymentrequest"
        try:
            response = requests.post(api_url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"B2C Withdrawal failed: {e}")
            return {"ResponseCode": "1", "CustomerMessage": str(e)}

    def handle_webhook(self, data):
        """
        Processes Callback data from Safaricom.
        """
        stk_callback = data.get('Body', {}).get('stkCallback', {})
        result_code = stk_callback.get('ResultCode')
        merchant_request_id = stk_callback.get('MerchantRequestID')
        
        if result_code == 0:
            logging.info(f"Transaction Successful for ID: {merchant_request_id}")
            # Logic to credit the trading account would be triggered here
            return True
        else:
            reason = stk_callback.get('ResultDesc')
            logging.warning(f"Transaction Failed: {reason}")
            return False
