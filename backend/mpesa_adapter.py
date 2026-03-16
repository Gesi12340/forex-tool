import requests
import json
import logging
import base64
from datetime import datetime

class MpesaAdapter:
    """
    Handles M-Pesa integration via Safaricom Daraja API.
    Securely handles deposits via STK Push.
    """
    def __init__(self, consumer_key, consumer_secret, shortcode, passkey, env="sandbox"):
        self.base_url = "https://sandbox.safaricom.co.ke" if env == "sandbox" else "https://api.safaricom.co.ke"
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.shortcode = shortcode
        self.passkey = passkey

    def get_access_token(self):
        """Retrieves OAuth2 access token from Safaricom API."""
        api_url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        try:
            response = requests.get(api_url, auth=(self.consumer_key, self.consumer_secret))
            response.raise_for_status()
            return response.json().get("access_token")
        except Exception as e:
            logging.error(f"Failed to get M-Pesa access token: {e}")
            return None

    def initiate_stk_push(self, phone_number, amount, account_reference, callback_url, transaction_type="CustomerBuyGoodsOnline"):
        """
        Triggers an M-Pesa STK Push to the user's phone.
        phone_number: Format 2547XXXXXXXX
        transaction_type: CustomerBuyGoodsOnline (Till) or CustomerPayBillOnline (PayBill)
        """
        access_token = self.get_access_token()
        if not access_token:
            return {"ResponseCode": "1", "CustomerMessage": "Authentication Failed. Check Consumer Key and Secret."}

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = base64.b64encode(f"{self.shortcode}{self.passkey}{timestamp}".encode()).decode()
        
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": transaction_type,
            "Amount": amount,
            "PartyA": phone_number,
            "PartyB": self.shortcode, # For BuyGoods, this is the Till Number
            "PhoneNumber": phone_number,
            "CallBackURL": callback_url,
            "AccountReference": account_reference,
            "TransactionDesc": "Trading Account Deposit"
        }

        api_url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
        try:
            response = requests.post(api_url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_details = e.response.json() if e.response else str(e)
            logging.error(f"STK Push failed: {error_details}")
            return {"ResponseCode": "1", "CustomerMessage": str(error_details)}
        except Exception as e:
            logging.error(f"STK Push failed: {e}")
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
