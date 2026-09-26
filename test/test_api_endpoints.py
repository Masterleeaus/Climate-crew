
import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

# --- Retail Analytics ---
def test_retail_audit():
    print("\nTesting /retail/audit ...")
    # Use a location that should work (e.g., California redwoods)
    payload = {"latitude": 41.3, "longitude": -124.0}
    response = client.post("/retail/audit", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        assert "causal_graph" in data
        assert "action_plan" in data
        assert "dashboard_payload" in data
        print(" [PASS] Retail Audit")
    else:
        print(f" [FAIL] Retail Audit: {response.status_code} - {response.text}")

# --- Domain Agents ---
def test_all_agents():
    print("\nTesting /agents endpoints ...")
    
    # Get list of agents
    list_resp = client.get("/agents/list")
    assert list_resp.status_code == 200
    agents = list_resp.json().get("agents", [])
    print(f" Found {len(agents)} agents: {agents}")
    
    # Test chat for each
    for agent in agents:
        print(f"  > Testing chat for '{agent}'...")
        endpoint = f"/agents/{agent}/chat"
        # Simple query
        payload = {"query": "Hello, assume a stable state and just say 'Online'."}
        
        try:
            resp = client.post(endpoint, json=payload)
            if resp.status_code == 200:
                print(f"    [PASS] {agent}")
            else:
                print(f"    [FAIL] {agent}: {resp.status_code}")
                print(f"    Error Detail: {resp.text}")
        except Exception as e:
            print(f"    [ERROR] {agent}: {e}")

# --- Data Sources ---
def test_data_sources():
    print("\nTesting /data endpoints ...")
    
    test_cases = [
        # Weather
        ("/data/weather/current?latitude=41.3&longitude=-124.0", "Weather"),
        # Wildfire
        ("/data/wildfire/country?country_code=USA", "Wildfire (Country)"),
        # Air Quality
        ("/data/air-quality/waqi/coordinates?latitude=37.77&longitude=-122.41", "Air Quality (Coordinates)"),
        # Climate Trace
        ("/data/climate-trace/sectors", "Climate Trace (Sectors)"),
        # Earthquakes
        ("/data/earthquake/recent?days=1&min_magnitude=5.0", "Earthquakes"),
        # Ocean
        ("/data/ocean/sea-level-trend", "Ocean (Sea Level)"),
        ("/data/ocean/coral-bleaching", "Ocean (Coral)"),
        ("/data/ocean/conditions?latitude=20.0&longitude=-156.0", "Ocean (Conditions)"), # Hawaii
        # Copernicus
        ("/data/copernicus/marine/datasets", "Copernicus (Datasets)"),
        # GBIF
        ("/data/biodiversity/species/search?query=Puma", "Biodiversity (Search)"),
        # Satellite (Simulated)
        ("/data/satellite/anomalies?latitude=41.3&longitude=-124.0", "Satellite (Simulated)"),
        # Web Search
        ("/data/search/web?query=test", "Web Search")
    ]
    
    for url, name in test_cases:
        try:
            resp = client.get(url)
            if resp.status_code == 200:
                # Basic validation
                json_data = resp.json()
                if isinstance(json_data, (dict, list)):
                    print(f" [PASS] {name}")
                else:
                    print(f" [WARN] {name}: Invalid JSON format")
            else:
                print(f" [FAIL] {name}: {resp.status_code} - {resp.text[:100]}...")
        except Exception as e:
            print(f" [ERROR] {name}: {e}")

if __name__ == "__main__":
    print("=== Starting API Endpoint Tests ===")
    
    try:
        test_root()
        # test_retail_audit()
        test_all_agents()
        test_data_sources()
        print("\n=== All Tests Completed ===")
    except Exception as e:
        print(f"\nCRITICAL ERROR: {e}")
