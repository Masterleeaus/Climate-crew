import unittest
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
load_dotenv()

from src.agents.climate_time_machine.agent import ClimateTimeMachineAgent

class TestClimateTimeMachine(unittest.TestCase):
    def setUp(self):
        self.agent = ClimateTimeMachineAgent()

    def test_simulation(self):
        print("Starting Climate Time Machine Simulation...")
        event = "Massive wildfire breaking out in Yellowstone National Park"
        
        report = self.agent.run_simulation(event)
        
        print("\n=== SIMULATION REPORT ===")
        print(report)
        
        self.assertIn("Climate Time Machine Simulation", report)
        self.assertIn(".mp4", report)

if __name__ == "__main__":
    unittest.main()
