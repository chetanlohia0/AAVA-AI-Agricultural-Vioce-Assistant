# backend/test_agmarknet_standalone.py
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("AGMARKNET_API_KEY")
BASE_URL = os.getenv("AGMARKNET_BASE_URL", "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070")

# Standard Browser Header to bypass government firewall rate-limiting
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

def run_isolated_test(commodity: str, state: str = None, district: str = None):
    print("\n==================================================")
    print(f"🧪 TESTING AGMARKNET ENDPOINT ISOLATION")
    print(f"   Commodity: {commodity} | State: {state} | District: {district}")
    print("==================================================")

    if not API_KEY or "your_" in API_KEY:
        print("❌ AGMARKNET_API_KEY is missing or invalid in your .env file!")
        return False

    # Construct explicit indexed query parameters
    params = {
        "api-key": API_KEY,
        "format": "json",
        "filters[commodity]": commodity.title(),
        "limit": 10
    }

    if state:
        params["filters[state]"] = state.title()
    if district:
        params["filters[district]"] = district.title()

    start_time = time.time()
    print(f"📡 Sending HTTP GET Request to data.gov.in...")
    print(f"🔗 Target Params: {params}")

    try:
        response = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=12)
        latency = round(time.time() - start_time, 2)
        
        print(f"⏱️ Response Received in {latency} seconds | Status Code: {response.status_code}")
        response.raise_for_status()

        data = response.json()
        records = data.get("records", [])
        total = len(records)

        print(f"📊 Total Records Returned: {total}")

        if total > 0:
            print("\n✅ SUCCESS! Raw Government Records:")
            for idx, r in enumerate(records[:3], 1):
                print(f"  [{idx}] State: {r.get('state')} | District: {r.get('district')} | Mandi: {r.get('market')}")
                print(f"      Commodity: {r.get('commodity')} | Date: {r.get('arrival_date')} | Modal Price: ₹{r.get('modal_price')}/quintal\n")
            return True
        else:
            print("⚠️ Request succeeded but 0 records matched this exact filter combination.")
            print("   Try running without district filter or check official state spelling.")
            return False

    except requests.exceptions.Timeout:
        latency = round(time.time() - start_time, 2)
        print(f"❌ TIMEOUT after {latency}s! The government server did not respond in time.")
    except Exception as e:
        print(f"❌ API Request Error: {e}")

    return False

if __name__ == "__main__":
    print("🚀 Starting Agmarknet Standalone Diagnostic Tool...\n")
    
    # Test 1: Cotton in Andhra Pradesh
    run_isolated_test(commodity="Cotton", state="Andhra Pradesh")
    
    # Test 2: Wheat in Madhya Pradesh
    run_isolated_test(commodity="Wheat", state="Madhya Pradesh", district="Indore")
    
    # Test 3: Onion in Tamil Nadu
    run_isolated_test(commodity="Onion", state="Tamil Nadu")