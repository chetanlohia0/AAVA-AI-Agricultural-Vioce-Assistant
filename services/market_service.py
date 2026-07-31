# backend/services/market_service.py
import os
import csv
from pathlib import Path
import requests

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "sample_prices.csv"
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
AGMARKNET_BASE_URL = os.getenv("AGMARKNET_BASE_URL", "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070")
AGMARKNET_API_KEY = os.getenv("AGMARKNET_API_KEY", "")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

COMMODITY_MAP = {
    "cotton": "Cotton",
    "wheat": "Wheat",
    "onion": "Onion",
    "potato": "Potato",
    "tomato": "Tomato"
}

LOCATION_TO_STATE = {
    "indore": "Madhya Pradesh",
    "bhopal": "Madhya Pradesh",
    "chennai": "Tamil Nadu",
    "vellore": "Tamil Nadu",
    "krishnagiri": "Tamil Nadu",
    "nashik": "Maharashtra",
    "pune": "Maharashtra",
    "mumbai": "Maharashtra",
    "andhra pradesh": "Andhra Pradesh",
    "palnadu": "Andhra Pradesh",
    "ananthapuramu": "Andhra Pradesh"
}

def _load_dataset():
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

_DATASET = _load_dataset()

def get_market_data(crop: str, location: str = None):
    formatted_loc = location.strip() if location else "Madhya Pradesh"
    clean_crop = crop.lower().strip() if crop else "wheat"
    canonical_commodity = COMMODITY_MAP.get(clean_crop, crop.title().strip())

    if not DEMO_MODE and AGMARKNET_API_KEY:
        live_data = _fetch_live_from_agmarknet(canonical_commodity, formatted_loc)
        if live_data:
            return live_data

    print(f"📁 [Offline Fallback] Reading local baseline dataset for '{canonical_commodity}'")
    rows = [r for r in _DATASET if r.get("crop", "").lower() == canonical_commodity.lower()]
    
    if rows:
        rows.sort(key=lambda r: r.get("date", ""))
        latest = rows[-1]
        history = [float(r["price_per_quintal_inr"]) for r in rows if "price_per_quintal_inr" in r]
        current_price = float(latest.get("price_per_quintal_inr", 2410.0))
    else:
        defaults = {"Cotton": 8000.0, "Wheat": 2410.0, "Onion": 3500.0, "Potato": 1850.0, "Tomato": 2200.0}
        current_price = defaults.get(canonical_commodity, 2400.0)
        history = [current_price - 40, current_price - 20, current_price]

    return {
        "requested_location": formatted_loc,
        "actual_market": formatted_loc,
        "market": formatted_loc,
        "state": formatted_loc,
        "current_price": current_price,
        "history": history[-14:],
        "exact_match": True,
        "source": "fallback_dataset"
    }

def _fetch_live_from_agmarknet(commodity: str, location: str):
    loc_clean = location.lower().strip()
    target_state = LOCATION_TO_STATE.get(loc_clean, location.title())

    params = {
        "api-key": AGMARKNET_API_KEY,
        "format": "json",
        "filters[commodity]": commodity,
        "limit": 25
    }

    if target_state:
        params["filters[state]"] = target_state

    print(f"\n📡 [Agmarknet API] Fetching '{commodity}' in State: '{target_state}'...")

    try:
        res = requests.get(AGMARKNET_BASE_URL, headers=HEADERS, params=params, timeout=5)
        res.raise_for_status()
        records = res.json().get("records", [])

        if not records and target_state:
            del params["filters[state]"]
            res = requests.get(AGMARKNET_BASE_URL, headers=HEADERS, params=params, timeout=5)
            records = res.json().get("records", [])

        if not records:
            return None

        matched_records = []
        exact_match = True

        for r in records:
            m_name = str(r.get("market", "")).lower()
            d_name = str(r.get("district", "")).lower()
            if loc_clean in m_name or loc_clean in d_name:
                matched_records.append(r)

        if not matched_records:
            matched_records = records
            exact_match = False

        latest = matched_records[0]
        modal_price = float(latest.get("modal_price", 0))
        actual_market = latest.get("market") or latest.get("district") or location
        actual_state = latest.get("state") or location

        history = [float(r.get("modal_price", modal_price)) for r in matched_records if "modal_price" in r]
        if len(history) < 3:
            history = [modal_price - 30, modal_price - 10, modal_price]

        print(f"✅ [Agmarknet Success] Mandi: {actual_market} ({actual_state}) | Price: ₹{modal_price}/quintal | Exact Match: {exact_match}\n")

        return {
            "requested_location": location,
            "actual_market": actual_market,
            "market": actual_market,
            "state": actual_state,
            "current_price": modal_price,
            "history": history[-14:],
            "exact_match": exact_match,
            "source": "live_agmarknet"
        }

    except Exception as e:
        print(f"⚠️ [Agmarknet API Notice]: {e}")

    return None