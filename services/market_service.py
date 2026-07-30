# backend/services/market_service.py
import os
import csv
from pathlib import Path
import requests

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "sample_prices.csv"
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
AGMARKNET_BASE_URL = os.getenv("AGMARKNET_BASE_URL", "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070")
AGMARKNET_API_KEY = os.getenv("AGMARKNET_API_KEY", "")

def _load_dataset():
    with open(DATA_FILE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

_DATASET = _load_dataset()

def get_market_data(crop: str, location: str = None):
    """Fetches real-time price data for a crop from Agmarknet API or sample data."""
    formatted_location = location.title() if location else "Indore"
    formatted_crop = crop.title() if crop else "Wheat"

    if not DEMO_MODE and AGMARKNET_API_KEY:
        live_data = _fetch_live_from_agmarknet(formatted_crop, formatted_location)
        if live_data:
            return live_data

    # Sample dataset fallback matching requested crop
    rows = [r for r in _DATASET if r["crop"].lower() == formatted_crop.lower()]
    if rows:
        rows.sort(key=lambda r: r["date"])
        latest = rows[-1]
        history = [float(r["price_per_quintal_inr"]) for r in rows]
        return {
            "market": formatted_location,  # Preserve requested location
            "current_price": float(latest.get("price_per_quintal_inr", 2400)),
            "history": history[-14:],
            "source": "fallback"
        }

    return {
        "market": formatted_location,
        "current_price": 2400.0,
        "history": [2350, 2370, 2380, 2390, 2400, 2410, 2400],
        "source": "default"
    }

def _fetch_live_from_agmarknet(crop: str, location: str):
    """Queries Agmarknet API with strict Title-Case parameters."""
    params = {
        "api-key": AGMARKNET_API_KEY,
        "format": "json",
        "filters[commodity]": crop,
        "limit": 20
    }
    
    if location:
        params["filters[district]"] = location

    try:
        response = requests.get(AGMARKNET_BASE_URL, params=params, timeout=5)
        response.raise_for_status()
        records = response.json().get("records", [])

        # If district filter returned empty, query by commodity only
        if not records and location:
            del params["filters[district]"]
            response = requests.get(AGMARKNET_BASE_URL, params=params, timeout=5)
            records = response.json().get("records", [])

        if records:
            latest = records[0]
            modal_price = float(latest.get("modal_price", 2400))
            history = [float(r.get("modal_price", modal_price)) for r in records if "modal_price" in r]
            if len(history) < 3:
                history = [modal_price - 20, modal_price - 10, modal_price]

            return {
                "market": location or latest.get("market", "Local Mandi"),
                "current_price": modal_price,
                "history": history[-14:],
                "source": "live_agmarknet"
            }
    except Exception as e:
        print(f"[Agmarknet API Fetch Notice]: {e}")
        
    return None