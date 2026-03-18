import json
import os

WALLET_FILE = os.path.join(os.path.dirname(__file__), "wallet.json")

class WalletManager:
    """Handles persistence of local deposits."""
    def __init__(self):
        self.wallet = self._load()

    def _load(self):
        if os.path.exists(WALLET_FILE):
            try:
                with open(WALLET_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"balance": 0.0, "pending_deposits": []}

    def _save(self):
        with open(WALLET_FILE, 'w') as f:
            json.dump(self.wallet, f, indent=2)

    def add_pending(self, checkout_id, amount, phone):
        self.wallet["pending_deposits"].append({
            "id": checkout_id,
            "amount": float(amount),
            "phone": phone,
            "timestamp": os.path.getmtime(__file__) # Approximate
        })
        self._save()

    def credit(self, amount):
        self.wallet["balance"] += float(amount)
        self._save()

    def get_pending(self):
        return self.wallet["pending_deposits"]

    def remove_pending(self, checkout_id):
        self.wallet["pending_deposits"] = [d for d in self.wallet["pending_deposits"] if d["id"] != checkout_id]
        self._save()

    def get_total_balance(self):
        return self.wallet["balance"]
