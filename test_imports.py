try:
    import requests
    print("SUCCESS: requests imported")
except ImportError as e:
    print(f"FAILED: requests import failed: {e}")

try:
    from backend import broker_client
    print("SUCCESS: backend.broker_client imported")
except ImportError as e:
    print(f"FAILED: backend.broker_client import failed: {e}")
