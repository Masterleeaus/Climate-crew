import sys
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Add properties relative to location
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from examples.retail_analytics.src.agents.retail_analytics.orchestrator import RetailSwarm

from src.agents.flood_agent import FloodAgent
from src.agents.wildfire_agent import WildfireAgent

def verify_integration():
    api_key = os.getenv("GOOGLE_API_KEY", "dummy_key")
    
    # Real domain agents
    flood_agent = FloodAgent(google_api_key=api_key, memory_manager=None)
    wildfire_agent = WildfireAgent(google_api_key=api_key, memory_manager=None)
        
    real_agents = {
        "Flood Agent": flood_agent,
        "Wildfire Agent": wildfire_agent
    }

    print("Initializing RetailSwarm (Loading ML Models)...")
    swarm = RetailSwarm(
        google_api_key=api_key,
        memory_manager=None,
        domain_agents=real_agents
    )
    
    # Test Scenario: High Wind event (Simulating Hurricane Ian conditions)
    # We construct a scenario text that should trigger high predictions if extraction works
    test_scenario = """
    Major Hurricane Warning. 
    Wind speeds reaching 130 km/h. 
    Heavy rainfall expected: 150mm in next 24 hours.
    Temperature dropping to 20C.
    High humidity of 90%.
    """
    
    print("\n--- Running Audit with Test Scenario ---")
    result = swarm.audit(test_scenario)
    
    print("\n--- Audit Result Summary ---")
    graph = result.get("causal_graph", {})
    print(graph)
    
    print(f"Root Event: {graph.get('description')}")
    print(f"Impact Score: {graph.get('impact_score')} (Should be close to ML prediction)")
    print(f"Probability: {graph.get('probability')}")
    print(f"Evidence: {graph.get('evidence')}")
    
    if graph.get('impact_score', 0) > 7.0 and "ML" in graph.get('evidence', ''):
        print("\n✅ SUCCESS: verification complete. Real-time ML inference is working.")
    else:
        print("\n❌ FAILURE: Model did not predict high impact or evidence missing.")

if __name__ == "__main__":
    verify_integration()
