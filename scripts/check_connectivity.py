import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.mpesa_adapter import MpesaAdapter
from backend.broker_client import MT5Client

def check_env():
    print("\n--- [1] Environment Variables Check ---")
    load_dotenv()
    vars_to_check = [
        "MT5_LOGIN", "MT5_PASSWORD", "MT5_SERVER",
        "MPESA_CONSUMER_KEY", "MPESA_CONSUMER_SECRET", 
        "MPESA_SHORTCODE", "MPESA_PASSKEY"
    ]
    
    missing = []
    for var in vars_to_check:
        val = os.getenv(var)
        if not val or any(placeholder in val for placeholder in ["your_", "placeholder", "12345678"]):
            print(f"[-] {var}: Missing or Placeholder ({val})")
            missing.append(var)
        else:
            # Mask sensitive values - be explicit for type checker
            v_str = str(val)
            masked = v_str[:4] + "*" * (len(v_str) - 4) if len(v_str) > 4 else "****"
            print(f"[+] {var}: OK ({masked})")
            
    return len(missing) == 0

def check_mt5():
    print("\n--- [2] MetaTrader 5 Connectivity Check ---")
    try:
        # Check if MetaTrader5 is even installed
        import MetaTrader5 as mt5
        print("[*] MT5 Library found. Attempting initialization...")
        client = MT5Client()
        if client.is_connected:
            print("[+] SUCCESS: Connected to MT5 Terminal and Broker.")
            summary = client.get_account_summary()
            print(f"[+] Account Balance: {summary['balance']} {summary['currency']}")
            return True
        else:
            print("[-] FAILED: Could not connect to MT5. Ensure MT5 Terminal is open and credentials are correct.")
            return False
    except ImportError:
        print("[-] ERROR: MetaTrader5 library not installed. Run 'pip install MetaTrader5'")
        return False
    except Exception as e:
        print(f"[-] ERROR during MT5 check: {e}")
        return False

def check_mpesa():
    print("\n--- [3] M-Pesa API Connectivity Check ---")
    consumer_key = os.getenv("MPESA_CONSUMER_KEY")
    consumer_secret = os.getenv("MPESA_CONSUMER_SECRET")
    shortcode = os.getenv("MPESA_SHORTCODE")
    passkey = os.getenv("MPESA_PASSKEY")
    
    if not all([consumer_key, consumer_secret]):
        print("[-] SKIP: M-Pesa credentials missing.")
        return False
        
    adapter = MpesaAdapter(consumer_key, consumer_secret, shortcode, passkey)
    token = adapter.get_access_token()
    
    if token:
        print("[+] SUCCESS: Obtained M-Pesa OAuth Access Token.")
        return True
    else:
        print("[-] FAILED: Could not authenticate with Safaricom Daraja API. Check keys/secrets.")
        return False

def main():
    print("========================================")
    print("   AI TRADING BOT CONNECTIVITY CHECK    ")
    print("========================================")
    
    env_ok = check_env()
    mt5_ok = check_mt5()
    mpesa_ok = check_mpesa()
    
    print("\n========================================")
    if env_ok and mt5_ok and mpesa_ok:
        print("   SUMMARY: EVERYTHING IS WELL CONNECTED! ")
    else:
        print("   SUMMARY: SOME COMPONENTS ARE NOT CONNECTED ")
        if not mt5_ok:
            print("   - FIX MT5: Open Terminal & check .env")
        if not mpesa_ok:
            print("   - FIX M-Pesa: Check credentials in .env")
    print("========================================")

if __name__ == "__main__":
    main()
