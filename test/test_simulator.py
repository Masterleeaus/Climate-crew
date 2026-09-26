import sys
import os
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.climate_time_machine.simulator import DigitalTwinSimulator

def test_forest_fire_simulation():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not found in environment variables.")
        return

    simulator = DigitalTwinSimulator(google_api_key=api_key)
    
    # Specific scenario for a location as requested
    event = "Catastrophic forest fire in California's Redwood National Park during an extreme heatwave."
    result = simulator.run_simulation(event)
    
    print("\nSimulation Complete!")
    print(f"Event: {result['event']}")
    for scenario in result['scenarios']:
        print(f"\n{'='*40}")
        print(f"Scenario: {scenario['title']}")
        print(f"General Analysis: {scenario['general_analysis']}...")
        print(f"Video: {scenario['video_path']}")
        
        print(f"\n--- Domain Expert Analysis ---")
        for domain, report in scenario['domain_reports'].items():
            print(f"\n>> {domain}:")
            print(report[:300] + "...") # Truncate for display

if __name__ == "__main__":
    test_forest_fire_simulation()
