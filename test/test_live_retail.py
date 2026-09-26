import requests
import json
import time
import sys

def test_live_endpoint():
    url = "http://localhost:8000/retail/audit"
    print(f"Testing Live Endpoint: {url}")
    
    # Wait for server to come up
    for i in range(10):
        try:
            requests.get("http://localhost:8000/health")
            print("Server is up!")
            break
        except:
            print(f"Waiting for server... {i+1}/10")
            time.sleep(2)
            
    # Coordinates for Florida (Hurricane Ian zone)
    payload = {
        "latitude": 26.6406,
        "longitude": -81.8723
    }
    
    try:
        print(f"Sending payload: {payload}")
        response = requests.post(url, json=payload, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ Live API Call Successful")
            
            # Verify ML Integration
            causal_graph = data.get("causal_graph", {})
            evidence = causal_graph.get("evidence", "")
            impact = causal_graph.get("impact_score", 0)
            prob = causal_graph.get("probability", 0)
            
            print(f"Impact Score: {impact}")
            print(f"Probability: {prob}")
            print(f"Evidence: {evidence}")
            print(f"Full Graph Description: {causal_graph.get('description')}")
            
        else:
            print(f"\n❌ API Call Failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"\n❌ Test Exception: {e}")

if __name__ == "__main__":
    test_live_endpoint()
