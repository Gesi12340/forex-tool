import requests
import json
import time

def test_blob_robust(blob_id):
    url = f"https://jsonblob.com/api/jsonBlob/{blob_id}"
    print(f"--- Testing Blob: {blob_id} ---")
    
    # Test GET
    try:
        start = time.time()
        resp = requests.get(url, timeout=10)
        elapsed = time.time() - start
        print(f"GET Status: {resp.status_code} ({elapsed:.2f}s)")
        if resp.status_code == 200:
            print(f"Content Preview: {json.dumps(resp.json())[:100]}...")
        else:
            print(f"GET Failed: {resp.text}")
    except Exception as e:
        print(f"GET Exception: {e}")

    # Test PUT (to verify write access)
    try:
        if resp.status_code == 200:
            data = resp.json()
            data["last_debug_test"] = time.time()
            start = time.time()
            put_resp = requests.put(url, json=data, timeout=10)
            elapsed = time.time() - start
            print(f"PUT Status: {put_resp.status_code} ({elapsed:.2f}s)")
        else:
            print("Skipping PUT test due to GET failure.")
    except Exception as e:
        print(f"PUT Exception: {e}")

if __name__ == "__main__":
    # Test the ID currently in the codebase
    test_blob_robust("019cfb2c-7fb6-776c-a002-1ab4d15dfef2")
    
    print("\n" + "="*30 + "\n")
    
    # Test a fresh ID just in case
    print("Creating fresh test blob...")
    try:
        create_resp = requests.post("https://jsonblob.com/api/jsonBlob", 
                                   json={"test": True}, 
                                   headers={"Content-Type": "application/json"})
        if create_resp.status_code == 201:
            fresh_id = create_resp.headers.get("Location").split("/")[-1]
            print(f"Fresh ID Created: {fresh_id}")
            test_blob_robust(fresh_id)
        else:
            print(f"Failed to create fresh blob: {create_resp.status_code}")
    except Exception as e:
        print(f"Create Exception: {e}")
