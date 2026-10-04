import sys
import os
import json
from fastapi.testclient import TestClient
from dotenv import load_dotenv

load_dotenv()

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

# Import the router directly to test it
# We need to create a dummy app to mount the router
from fastapi import FastAPI
from examples.retail_analytics.src.agents.retail_analytics.router import router

app = FastAPI()
app.include_router(router)

client = TestClient(app)

def test_endpoint():
    print("Testing /retail/audit endpoint...")
    
    # Coordinates for Florida (Hurricane Ian zone)
    payload = {
        "latitude": 26.6406,
        "longitude": -81.8723
    }
    
    try:
        response = client.post("/retail/audit", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ API Call Successful")
            
            # Verify ML Integration
            causal_graph = data.get("causal_graph", {})
            evidence = causal_graph.get("evidence", "")
            impact = causal_graph.get("impact_score", 0)
            prob = causal_graph.get("probability", 0)
            
            print(f"Impact Score: {impact}")
            print(f"Probability: {prob}")
            print(f"Evidence: {evidence}")
            
            if "ML" in evidence:
                print("✅ ML Model Used")
            else:
                print("❌ ML Model NOT Used (Evidence missing)")
                
        else:
            print(f"\n❌ API Call Failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"\n❌ Test Exception: {e}")

if __name__ == "__main__":
    test_endpoint()
