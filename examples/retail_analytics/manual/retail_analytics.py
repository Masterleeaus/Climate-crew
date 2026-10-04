import sys
import os
import json
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from examples.retail_analytics.src.agents.retail_analytics import RetailSwarm
from src.agents.air_quality_agent import AirQualityAgent
from src.agents.wildfire_agent import WildfireAgent
from src.agents.flood_agent import FloodAgent
from src.agents.biodiversity_agent import BiodiversityAgent
from src.agents.deforestation_agent import DeforestationAgent
from src.agents.climate_anomaly_agent import ClimateAnomalyAgent

def print_recursive_tree(node, level=0):
    indent = "   " * level
    print(f"{indent}|- {node.get('description')} ({node.get('category')} - Impact: {node.get('impact_score')})")
    for child in node.get('children', []):
        print_recursive_tree(child, level + 1)

def test_retail_swarm():
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not found.")
        return

    print("Initializing Retail Analytics Swarm...")
    
    domain_agents = {
        "Air Quality": AirQualityAgent(api_key),
        "Wildfire": WildfireAgent(google_api_key=api_key),
        "Flood": FloodAgent(google_api_key=api_key),
        "Biodiversity": BiodiversityAgent(google_api_key=api_key),
        "Deforestation": DeforestationAgent(google_api_key=api_key),
        "Climate Anomaly": ClimateAnomalyAgent(google_api_key=api_key)
    }
    
    swarm = RetailSwarm(
        google_api_key=api_key,
        memory_manager=None,
        domain_agents=domain_agents
    )
    
    print("\n[Real-Time Check] AUTOMATICALLY Auditing used Location Coordinates (41.3, -124.0)...")
    
    try:
        # One-line call: Input coordinates -> Output Audit
        results = swarm.audit_location(41.3, -124.0)
        
        output_file = "artifacts/retail_audit_log.txt"
        os.makedirs("artifacts", exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("--- Retail Audit Results ---\n")
            
            f.write("\n1. Causal Graph (Full Tree):\n")
            root = results.get("causal_graph", {})
            
            def write_recursive(node, level=0):
                indent = "   " * level
                f.write(f"{indent}|- {node.get('description')} ({node.get('category')} - Impact: {node.get('impact_score')})\n")
                for child in node.get('children', []):
                    write_recursive(child, level + 1)
            
            write_recursive(root)
            
            f.write("\n2. Action Plan:\n")
            plan = results.get("action_plan", {})
            for item in plan.get("items", []):
                f.write(f"   [{item.get('priority')}] {item.get('action')}\n")
                f.write(f"      -> Owner: {item.get('assigned_to', 'Unassigned')}\n")
                
            f.write("\n3. Communications:\n")
            comms = results.get("communications", {})
            for alert in comms.get("alerts", []):
                f.write(f"   [{alert.get('role')}] Subject: {alert.get('subject')}\n")
                
            f.write("\n4. Public Advisory (Citizen Recommendations):\n")
            f.write(f"   {comms.get('public_advisory', 'No advisory generated')}\n")
            
            f.write("\n5. Command Center Dashboard (New UI Payload):\n")
            dash = results.get("dashboard_payload", {})
            f.write(f"   [Risk Score]: {dash.get('risk_score', 0)}/100\n")
            
            f.write("   [Breaking News Ticker]:\n")
            for news in dash.get("news_ticker", []):
                f.write(f"    * {news}\n")
                
            f.write("   [Live Map Markers]:\n")
            for marker in dash.get("markers", []):
                f.write(f"    * [{marker.get('type')}] {marker.get('label')} ({marker.get('status')})\n")
                
            f.write("   [Real-Time KPIs]:\n")
            for kpi in dash.get("kpis", []):
                f.write(f"    * {kpi.get('label')}: {kpi.get('value')} {kpi.get('unit')} ({kpi.get('threshold')})\n")
                
        print(f"\nTest Passed! Results saved to {output_file}")
        
    except Exception as e:
        print(f"\nTest Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_retail_swarm()
