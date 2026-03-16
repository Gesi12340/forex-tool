import os
import sys
try:
    from dotenv import load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_env():
    print("\n--- Environment Variables Check ---")
    if HAS_DOTENV:
        load_dotenv()
    else:
        print("[!] Warning: python-dotenv not installed. Using system environment variables only.")
    vars_to_check = [
        "MT5_LOGIN", "MT5_PASSWORD", "MT5_SERVER",
        "MPESA_CONSUMER_KEY", "MPESA_CONSUMER_SECRET", 
        "MPESA_SHORTCODE", "MPESA_PASSKEY"
    ]
    
    missing = []
    for var in vars_to_check:
        val = os.getenv(var)
        if not val or "your_" in val or "placeholder" in val or val == "12345678":
            print(f"[-] {var}: Missing/Placeholder")
            missing.append(var)
        else:
            print(f"[+] {var}: OK")
            
    return len(missing) == 0

if __name__ == "__main__":
    check_env()
    print("\n[INFO] Basic environment check complete. To test MT5, ensure the terminal is open.")
    print("[INFO] To test M-Pesa, run: python -c \"from backend.mpesa_adapter import MpesaAdapter; print(MpesaAdapter(...).get_access_token())\"")
