import os
import requests
import json
from dotenv import load_dotenv
from backend.mpesa_adapter import MpesaAdapter

load_dotenv()

def test_jsonblob():
    relay_id = "019cfa7b-ea2c-7b12-a1b2-c3d4e5f6a7b8"
    url = f"https://jsonblob.com/api/jsonBlob/{relay_id}"
    print(f"Testing JSONBlob: {url}")
    try:
        resp = requests.get(url, timeout=10)
        print(f"Status Code: {resp.status_code}")
        if resp.status_code == 200:
            print(f"Content: {resp.json()}")
            return True
        else:
            print("Failed to reach relay blob.")
    except Exception as e:
        print(f"Blob Error: {e}")
    return False

def test_mpesa_auth():
    print("\nTesting M-Pesa Auth...")
    mpesa = MpesaAdapter(
        os.getenv("MPESA_CONSUMER_KEY"),
        os.getenv("MPESA_CONSUMER_SECRET"),
        os.getenv("MPESA_SHORTCODE"),
        os.getenv("MPESA_PASSKEY"),
        os.getenv("MPESA_ENV", "sandbox")
    )
    token = mpesa.get_access_token()
    if token:
        print("SUCCESS: Access Token retrieved.")
        return mpesa
    else:
        print("FAILED: Could not get access token. Check Consumer Key/Secret.")
    return None

if __name__ == "__main__":
    blob_ok = test_jsonblob()
    mpesa = test_mpesa_auth()
    
    if mpesa and blob_ok:
        print("\nSystem looks reachable. Checking STK Push parameters...")
        # Check if shortcode/passkey look like valid lengths (simple heuristic)
        shortcode = os.getenv("MPESA_SHORTCODE")
        passkey = os.getenv("MPESA_PASSKEY")
        print(f"Shortcode: {shortcode}")
        print(f"Passkey Length: {len(passkey) if passkey else 0}")
        
        if len(shortcode) > 6:
            print("WARNING: Shortcode looks like a phone number. For STK Push, it should be a Till/Paybill/ShortCode.")
