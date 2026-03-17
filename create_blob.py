import requests

def create_blob():
    url = "https://jsonblob.com/api/jsonBlob"
    payload = {
        "stats": {
            "balance": 0,
            "equity": 0,
            "dailyPnL": 0,
            "is_running": False,
            "is_trained": True,
            "market_price": 0
        },
        "command": None,
        "status": "System Initialized",
        "processed_command": None,
        "last_update": 0
    }
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    try:
        resp = requests.post(url, json=payload, headers=headers)
        if resp.status_code == 201:
            # Handle both header and potential body response for ID
            location = resp.headers.get("Location")
            if location:
                blob_id = location.split("/")[-1]
                print(f"NEW_BLOB_ID:{blob_id}")
            else:
                # Some APIs return the created object with the ID
                print(f"RESPONSE:{resp.text}")
        else:
            print(f"FAILED:{resp.status_code} {resp.text}")
    except Exception as e:
        print(f"ERROR:{e}")

if __name__ == "__main__":
    create_blob()
